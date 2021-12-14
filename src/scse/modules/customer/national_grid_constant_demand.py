import logging

from scse.api.module import Agent

logger = logging.getLogger(__name__)


class ConstantDemand(Agent):
    _DEFAULT_AMOUNT = 10
    _DEFAULT_ASIN = 'electricity'
    _DEFAULT_CUSTOMER = 'Consumers'

    def __init__(self, run_parameters):
        """
        Simulates time invariant electricity demand from a single customer.
        """
        self._amount = run_parameters.get('constant_demand_amount', self._DEFAULT_AMOUNT)
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

        action = {
            'type': 'customer_order',
            'asin': self._asin,
            'origin': None,  # The customer cannot request where the electricity comes from
            'destination': self._customer,
            'quantity': self._amount,
            'schedule': state['clock']
        }
            
        logger.debug(f"{self._customer} requested {self._amount} units of {self._asin}.")

        actions.append(action)

        return actions
