import logging

from scse.api.module import Agent
from scse.services.service_registry import singleton as registry

logger = logging.getLogger(__name__)


class ElectricityDemand(Agent):
    _DEFAULT_ASIN = 'electricity'
    _DEFAULT_CUSTOMER = 'Consumers'

    def __init__(self, run_parameters):
        """
        Simulates electricity demand from a single consumer/customer.

        Demand forecast is provided by a service.
        """
        self._demand_forecast_service = registry.load_service('electricity_demand_forecast_service', run_parameters)
        self._asin = run_parameters.get('constant_demand_asin', self._DEFAULT_ASIN)
        self._customer = run_parameters.get('constant_demand_customer', self._DEFAULT_CUSTOMER)

    def get_name(self):
        return 'constant_demand'

    def reset(self, context, state):
        self._asin_list = context['asin_list']

    def compute_actions(self, state):
        """
        Creates a single action/order for a constant amount of electricity.
        """
        actions = []
        current_time = state['date_time']

        forecasted_demand = self._demand_forecast_service.get_forecast(current_time)

        action = {
            'type': 'customer_order',
            'asin': self._asin,
            'origin': None,  # The customer cannot request where the electricity comes from
            'destination': self._customer,
            'quantity': forecasted_demand,
            'schedule': state['clock']
        }
            
        logger.debug(f"{self._customer} requested {forecasted_demand} units of {self._asin}.")

        actions.append(action)

        return actions
