import logging
import datetime

from scse.api.module import Agent
from scse.api.network import get_asin_inventory_on_inbound_arcs_to_node
from scse.services.service_registry import singleton as registry
from scse.constants.national_grid_constants import (
    ELECTRICITY_ASIN, PERIOD_LENGTH_HOURS
)

logger = logging.getLogger(__name__)


class BatteryDrawdown(Agent):
    _DEFAULT_ASIN = ELECTRICITY_ASIN

    def __init__(self, run_parameters):
        """
        Identifies what the supply deficit at substations will be in the next
        timestep and attempts to draw from battery reserves to compensate.
        This should only fail if there is not sufficient reserve.

        Electricity is sent during the current timestep to maintain balance at
        the substation in the next timestep.
        """
        self._asin = self._DEFAULT_ASIN
        self._demand_forecast_service = registry.load_service(
            'electricity_demand_forecast_service', run_parameters)
        self._supply_forecast_service = registry.load_service(
            'electricity_supply_forecast_service', run_parameters)

    def get_name(self):
        return 'battery_drawdown'

    def reset(self, context, state):
        self._asin_list = context['asin_list']

    def compute_actions(self, state):
        """
        Determine if there will be a supply deficit at any substation, and
        attempt to meet this with battery reserves.
        """
        actions = []
        current_clock = state['clock']
        current_time = state['date_time']
        next_time = current_time + \
            datetime.timedelta(hours=PERIOD_LENGTH_HOURS)

        G = state['network']

        # Get a list of substations - remember that these have the type `port` for now
        # Determine the supply deficit for each in the next timestep
        substations = {}
        for node, node_data in G.nodes(data=True):
            if node_data.get('node_type') in ['port']:
                # Would want to pass the node as an argument to the service, in due time
                future_demand = self._demand_forecast_service.get_forecast(
                    clock=current_clock,
                    time=next_time
                )

                # Current capacity should be zero most of the time.
                # Deviations will occur when battery capacity falls to zero.
                current_holding = node_data['inventory'][self._asin]

                # Find all the inbound supply that's on its way
                inbound_supply = get_asin_inventory_on_inbound_arcs_to_node(
                    G, self._asin, node)

                # Calculate the actual deficit in the next timestep
                substations[node] = future_demand - \
                    inbound_supply - current_holding

        total_future_deficit = sum(list(substations.values()))
        logger.debug(
            f'Total supply deficit in the next timestep: {total_future_deficit}')

        # If the future supply exceeds demand then nothing needs to be done
        if total_future_deficit < 0:
            logger.debug('No action required')
            return actions

        # Get a list of batteries - remember that these have the type `warehouse` for now
        # Store current inventory plus any incoming inventory
        # A substation could currently have an excess of electricity, but a future deficit
        batteries = {}
        for node, node_data in G.nodes(data=True):
            if node_data.get('node_type') in ['warehouse']:
                # TODO: miniSCOT does not support inclusion of inbound inventory as this
                # can result in negative inventory at node in the current timestep.
                # inbound_excess = get_asin_inventory_on_inbound_arcs_to_node(
                #     G, self._asin, node)
                inbound_excess = 0

                batteries[node] = node_data['inventory'][self._asin] + \
                    inbound_excess

        available_stored_electricity = sum(list(batteries.values()))
        logger.debug(
            f'Capacity currently held in network batteries: {available_stored_electricity}')

        # If all the batteries are empty, nothing can be done
        if available_stored_electricity == 0:
            logger.debug('No stored capacity in the network')
            return actions

        # If the future deficit exceeds the available stored electricity then raise warning
        # Batteries will be depleted to meet as much of the shortfall as possible
        if total_future_deficit > available_stored_electricity:
            logger.debug(
                f'Not enough stored capacity to meet supply shortfall in the next timestep - batteries will be depleted')

        # Perform transfers to drawdown from batteries. Note the requirement to keep track
        # of battery capacities as they're being drawn down.
        # Potential future improvements:
        # - Substations with the greatest predicted deficit are serviced first
        # - Electricity is drawn down from the closest batteries first
        for substation in list(substations.keys()):
            for battery in list(batteries.keys()):
                # Initial available capacity
                battery_capacity = batteries[battery]

                # If capacity exceeds the substation's forcasted deficit then fully meet that deficit
                # Otherwise, drain the battery and remove it from the list
                if battery_capacity >= substations[substation]:
                    drawdown_amount = substations[substation]
                    batteries[battery] -= substations[substation]
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
                if substations[substation] == 0:
                    del substations[substation]
                    logger.debug(
                        f"Met supply deficit at substation {substation} in next timestep.")
                    break

            # If all batteries have been depleted than break out of loop
            if len(batteries) == 0:
                logger.debug("All batteries have been depleted.")
                break

        # Report on any future deficit still remaining
        for substation, remaining_deficit in substations.items():
            logger.debug(
                f"Substation {substation} will have a deficit of {remaining_deficit} in the next timestep."
            )

        return actions
