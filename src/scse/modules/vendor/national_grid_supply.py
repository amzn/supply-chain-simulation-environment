from scse.api.module import Agent
from scse.services.service_registry import singleton as registry

import logging
logger = logging.getLogger(__name__)


class ElectricitySupply(Agent):

    def __init__(self, run_parameters):
        """
        Simulates electricity supply.

        Supply forecast is provided by a service.
        """
        self._supply_forecast_service = registry.load_service('electricity_supply_forecast_service', run_parameters)

    def get_name(self):
        return 'vendor'

    def reset(self, context, state):
        self._asin_list = context['asin_list']

    def compute_actions(self, state):
        """
        Create constant supply from each source.
        """
        actions = []
        current_time = state['date_time']
        current_clock = state['clock']
        
        G = state['network']

        # Get a list of substations - remember that these have the type `port` for now
        substations = []
        for node, node_data in G.nodes(data=True):
            if node_data.get('node_type') == 'port':
                substations.append(node)
        
        if len(substations) == 0:
            raise ValueError('Could not identify any substations.')
        elif len(substations) > 1:
            raise ValueError('Identified multiple substations - this is not yet supported.')
        
        substation = substations[0]

        # Create shipment from every vendor (i.e. electricity supply) to substation
        for node, node_data in G.nodes(data=True):
            if node_data.get('node_type') == 'vendor':
                # Determine how the vendor produces electricity
                generation_types = node_data.get('asins_produced')
                if generation_types is None:
                    raise ValueError('Expect all sources to have `asins_produced` property, indicating their generation type.')
                elif len(generation_types) != 1:
                    raise ValueError('All sources must have only one generation type - multiple not yet supported.')
                
                generation_type = generation_types[0]
                forecasted_supply = self._supply_forecast_service.get_forecast(generation_type, current_time)
                
                logger.debug(f"Supply for {forecasted_supply} quantity of ASIN {generation_type}.")

                action = {
                    'type': 'inbound_shipment',
                    'asin': generation_type,
                    'origin': node,
                    'destination': substation,
                    'quantity': forecasted_supply,
                    'schedule': current_clock
                }

                actions.append(action)

        return actions
