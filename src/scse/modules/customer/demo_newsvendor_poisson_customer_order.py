"""
An agent representing the (retail) customer behavior following a Poisson distribution for demand.
"""
import networkx as nx
from scse.api.module import Agent
import numpy as np

import logging
logger = logging.getLogger(__name__)


class PoissonCustomerOrder(Agent):
    _DEFAULT_MAX_MEAN = 10

    def __init__(self, run_parameters):
        simulation_seed = run_parameters['simulation_seed']
        self._rng = np.random.RandomState(simulation_seed)
        self._max_mean = run_parameters.get('customer_max_mean',
                                            self._DEFAULT_MAX_MEAN)
        self._DEFAULT_NEWSVENDOR_CUSTOMER = 'Customer'

    def get_name(self):
        return 'order_generator'

    def reset(self, context, state):
        self._asin_list = context['asin_list']

    def compute_actions(self, state):       
        # There are two modes of operation: (a) simulates the ASIN selection itself, (b) simulates
        # for a requested set of ASINs. This is defined in the context.

        actions = []
        for asin in self._asin_list:
            # Generate demand from poisson distribution with mean in range [0, max]
            mean_demand = self._rng.rand() * self._max_mean
            demand_realization = round(max(1, self._rng.poisson(mean_demand)))
            action = {
                'type': 'customer_order',
                'asin': asin,
                'origin': None,
                'destination': self._DEFAULT_NEWSVENDOR_CUSTOMER,
                'quantity': demand_realization,
                'schedule': state['clock']
            }
            logger.debug("{} bought {} units of {}.".format(
                self._DEFAULT_NEWSVENDOR_CUSTOMER, demand_realization, asin))
            actions.append(action)

        return actions
