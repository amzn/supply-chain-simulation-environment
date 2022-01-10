import logging
import datetime

from scse.api.module import Agent
from scse.api.network import get_asin_inventory_on_inbound_arcs_to_node
from scse.services.service_registry import singleton as registry
from scse.constants.national_grid_constants import (
    ELECTRICITY_ASIN, PERIOD_LENGTH_HOURS, DEFAULT_BALANCE_SOURCE
)

logger = logging.getLogger(__name__)


class BalanceExcessDemand(Agent):
    _DEFAULT_ASIN = ELECTRICITY_ASIN
    _DEFAULT_BALANCE_SOURCE = DEFAULT_BALANCE_SOURCE

    def __init__(self, run_parameters):
        """
        Identifies what the supply deficit at substations will be in the next
        timestep. Any shortfall is met by the balance mechanism source.

        Electricity is sent during the current timestep to maintain balance at 
        the substation in the next timestep.

        NOTE: If considering batteries, this module must be executed after the 
        drawdown module, else the entire deficit will be met by the balance
        mechanism source.
        """
        self._asin = self._DEFAULT_ASIN
        self._balance_source = self._DEFAULT_BALANCE_SOURCE
        self._demand_forecast_service = registry.load_service('electricity_demand_forecast_service', run_parameters)
        self._supply_forecast_service = registry.load_service('electricity_supply_forecast_service', run_parameters)

    def get_name(self):
        return 'balance_excess_demand'

    def reset(self, context, state):
        self._asin_list = context['asin_list']

    def compute_actions(self, state):
        """
        Determine if there will be a supply deficit at any substation, and
        meet this with the balance mechanism source.
        """
        actions = []
        current_clock = state['clock']
        current_time = state['date_time']
        next_time = current_time + datetime.timedelta(hours=PERIOD_LENGTH_HOURS)
        
        G = state['network']

        # Get a list of substations - remember that these have the type `port` for now
        # Determine the supply deficit for each in the next timestep
        for node, node_data in G.nodes(data=True):
            if node_data.get('node_type') in ['port']:
                # Would want to pass the node as an argument to the service, in due time
                future_demand = self._demand_forecast_service.get_forecast(
                    clock=current_clock,
                    time=next_time
                )

                # Current capacity should be zero most of the time, as long as the balance
                # mechanism source is in use.
                current_holding = node_data['inventory'][self._asin]

                # Find all the inbound supply that's on its way.
                # This will include any being sent by any batteries.
                inbound_supply = get_asin_inventory_on_inbound_arcs_to_node(G, self._asin, node)

                # Calculate the actual deficit in the next timestep
                supply_deficit = future_demand - inbound_supply - current_holding

                # If there is no deficit then continue to the next substation
                if supply_deficit < 0:
                    logger.debug(f"No deficit at substation {node} in next timestep.")
                    continue

                logger.debug(
                    f"Sourcing deficit of {supply_deficit} ASIN {self._asin} to substation {node}."
                )

                action = {
                    'type': 'inbound_shipment',
                    'asin': self._asin,
                    'origin': self._balance_source,
                    'destination': node,
                    'quantity': supply_deficit,
                    'schedule': current_clock
                }
                actions.append(action)

        return actions
