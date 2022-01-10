import logging

from scse.api.module import Agent
from scse.services.service_registry import singleton as registry
from scse.constants.national_grid_constants import DEFAULT_BALANCE_SOURCE, ELECTRICITY_ASIN

logger = logging.getLogger(__name__)


class ElectricitySupply(Agent):
    _DEFAULT_SUPPLY_ASIN = ELECTRICITY_ASIN

    def __init__(self, run_parameters):
        """
        Simulates electricity supply from all sources.

        Supply forecast is provided by a service.

        NOTE: The balance mechanism source is currently modelled as a
        vendor. Therefore, we cannot simply loop through all
        vendors - we must exclude the balance source. A simple method
        of doing this is implemented below, but we may want to find a
        more robust solution.
        """
        self._supply_asin = self._DEFAULT_SUPPLY_ASIN
        self._supply_forecast_service = registry.load_service('electricity_supply_forecast_service', run_parameters)

    def get_name(self):
        return 'vendor'

    def reset(self, context, state):
        self._asin_list = context['asin_list']

    def compute_actions(self, state):
        """
        Simulate a supply of electricity from each source.

        NOTE: Only supports having a single substation currently.
        """
        actions = []
        current_time = state['date_time']
        current_clock = state['clock']
        
        G = state['network']

        # Get a list of substations - remember that these have the type `port` for now
        substations = []
        for node, node_data in G.nodes(data=True):
            if node_data.get('node_type') in ['port']:
                substations.append(node)
        
        if len(substations) == 0:
            raise ValueError('Could not identify any substations.')
        elif len(substations) > 1:
            raise ValueError('Identified multiple substations - this is not yet supported.')
        
        substation = substations[0]

        # Create shipment from every vendor (i.e. electricity supply) to substation
        # NOTE: Do not create demand from balance source. TODO: Find a better method of avoiding.
        for node, node_data in G.nodes(data=True):
            if node_data.get('node_type') == 'vendor' and node != DEFAULT_BALANCE_SOURCE:
                # Determine how the vendor produces electricity
                generation_types = node_data.get('asins_produced')
                if generation_types is None:
                    raise ValueError('Expect all sources to have `asins_produced` property, indicating their generation type.')
                elif len(generation_types) != 1:
                    raise ValueError('All sources must have only one generation type - multiple not yet supported.')
                
                generation_type = generation_types[0]
                forecasted_supply = self._supply_forecast_service.get_forecast(
                    asin=generation_type, clock=current_clock, time=current_time
                )
                
                logger.debug(f"Supply for {forecasted_supply} quantity of ASIN {generation_type}.")

                # Note: The default ASIN is sent (i.e. electricity), regardless of generation type
                action = {
                    'type': 'inbound_shipment',
                    'asin': self._supply_asin,
                    'origin': node,
                    'destination': substation,
                    'quantity': forecasted_supply,
                    'schedule': current_clock
                }

                actions.append(action)

        return actions
