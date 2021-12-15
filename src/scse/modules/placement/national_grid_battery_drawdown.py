import logging
import datetime

from scse.api.module import Agent
from scse.api.network import get_asin_inventory_on_inbound_arcs_to_node
from scse.services.service_registry import singleton as registry

logger = logging.getLogger(__name__)


class BatteryDrawdown(Agent):
    _DEFAULT_ASIN = 'electricity'

    def __init__(self, run_parameters):
        """
        Predicts what the supply deficit at substations will be in the next
        timestep and attempts to draw from battery reserves to compensate.

        Electricity is sent during the current timestep in the hope to maintain
        balance at the substation in the next timestep.
        """
        self._asin = self._DEFAULT_ASIN
        self._demand_forecast_service = registry.load_service('electricity_demand_forecast_service', run_parameters)
        self._supply_forecast_service = registry.load_service('electricity_supply_forecast_service', run_parameters)

    def get_name(self):
        return 'battery_drawdown'

    def reset(self, context, state):
        self._asin_list = context['asin_list']

    def compute_actions(self, state):
        """
        Determine if there is due to be a supply deficit at any substation, and
        attempt to meet this with battery reserves.
        """
        actions = []
        current_clock = state['clock']
        current_time = state['date_time']
        next_time = current_time + datetime.timedelta(hours=0.5)
        
        G = state['network']

        # Get a list of substations - remember that these have the type `port` for now
        # Determine the forecasted supply deficit for each in the next timestep
        substations = {}
        for node, node_data in G.nodes(data=True):
            if node_data.get('node_type') in ['port']:
                # Would want to pass the node as an argument to the service, in due time
                demand_forecast = self._demand_forecast_service.get_forecast(time=next_time)

                # Current capacity will hopefully be close to zero most of the time.
                # Deviations will occur when supply/demand deviates from what's the forecast,
                # or when battery capacity falls to zero.
                current_holding = node_data['inventory'][self._asin]

                # Find all the inbound supply that's on its way
                inbound_supply = get_asin_inventory_on_inbound_arcs_to_node(G, self._asin, node)

                # Calculate the forecasted deficit
                substations[node] = demand_forecast - inbound_supply - current_holding

        total_forecasted_deficit = sum(list(substations.values()))
        logger.debug(f'Total forcasted supply deficit: {total_forecasted_deficit}')

        # If the forecasted supply exceeds demand then nothing needs to be done
        if total_forecasted_deficit < 0:
            logger.debug('No action required')
            return actions

        # Get a list of batteries - remember that these have the type `warehouse` for now
        # Store current inventory plus any incoming inventory
        # A substation could currently have an excess of electricity, but a forecasted deficit
        batteries = {}
        for node, node_data in G.nodes(data=True):
            if node_data.get('node_type') in ['warehouse']:
                inbound_excess = get_asin_inventory_on_inbound_arcs_to_node(G, self._asin, node)
                batteries[node] = node_data['inventory'][self._asin] + inbound_excess

        available_stored_electricity = sum(list(batteries.values()))
        logger.debug(f'Capacity currently held in network batteries: {available_stored_electricity}')

        # If all the batteries are empty, nothing can be done
        if available_stored_electricity == 0:
            logger.debug('No stored capacity in the network')
            return actions

        # If the forecasted deficit exceeds the available stored electricity then raise warning
        # Batteries will be depleted to meet as much of the shortfall as possible
        if total_forecasted_deficit > available_stored_electricity:
            logger.debug(f'Not enough stored capacity to meet forecasted full supply shortfall - batteries will be depleted')

        # Perform transfers to drawdown from batteries. Note the requirement to keep track
        # of battery capacities as they're being drawn down.
        # Potential future improvements:
        # - Substations with the greatest predicted deficit are serviced first
        # - Electricity is drawn down from the closest batteries first
        for substation in list(substations.keys()):
            # Starting deficit figure
            forecasted_deficit = substations[substation]
            
            for battery in list(batteries.keys()):
                # Initial available capacity
                battery_capacity = batteries[battery]

                # If capacity exceeds the substation's forcasted deficit then fully meet that deficit
                # Otherwise, drain the battery and remove it from the list
                if battery_capacity >= forecasted_deficit:
                    drawdown_amount = forecasted_deficit
                    batteries[battery] -= forecasted_deficit
                else:
                    drawdown_amount = battery_capacity
                    del batteries[battery]
                    logger.debug(f"Battery {battery} will be drained.")

                # Update the substation's deficit
                substations[substation] -= drawdown_amount

                logger.debug(
                    f"Transferring {drawdown_amount} of ASIN {self._asin} from battery {battery} to substation {substation}."
                )

                action = {
                    'type': 'transfer',
                    'asin': self._asin,
                    'origin': battery,
                    'destination': substation,
                    'quantity': drawdown_amount,
                    'schedule': current_clock
                }
                actions.append(action)

                # If the substation's deficit has now bene met then break
                if forecasted_deficit == 0:
                    del substations[substation]
                    logger.debug(f"Met forecasted supply deficit at substation {substation}.")
                    break

            # If all batteries have been depleted than break out of loop
            if len(batteries) == 0:
                logger.debug("All batteries have been depleted.")
                break
        
        # Report on any forecasted deficit still remaining
        for substation, remaining_deficit in substations.items():
            logger.debug(
                f"Substation {substation} still has a forecasted deficit of {remaining_deficit}"
            )

        return actions
