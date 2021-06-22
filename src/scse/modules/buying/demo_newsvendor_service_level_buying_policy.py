"""
Buying policy that purchases nationally to a given service level (default P90).

Uses a target service level and the forecast to determine TIP, then 
an order-up-to policy given inventory at the national level
"""
import networkx as nx
from scse.api.module import Agent
from scse.api.network import get_asin_inventory_in_network
from scse.api.network import get_asin_inventory_on_all_inbound_arcs
import numpy as np
from scipy.stats import poisson

import logging
logger = logging.getLogger(__name__)


class ServiceLevelBuying(Agent):
    def __init__(self, run_parameters):
        simulation_seed = run_parameters['simulation_seed']
        self._rng = np.random.RandomState(simulation_seed)
        # TODO hardcoding default service level to 0.9 (i.e. buy to P90 of demand forecast)
        _DEFAULT_SERVICE_LEVEL = 0.9
        # TODO hardcoding to planning horizon of 1 (i.e. buy for 1 day of forecasted demand)
        _DEFAULT_PLANNING_HORIZON = 1
        # TODO hardcoding poisson max_mean to 10, to match poisson customer order
        # A more robust way of doing this is to create a poisson service that both modules call
        _DEFAULT_MAX_MEAN = 10
        self._service_level = _DEFAULT_SERVICE_LEVEL
        self._planning_horizon = _DEFAULT_PLANNING_HORIZON
        self._max_mean = _DEFAULT_MAX_MEAN

    def get_name(self):
        return 'buying'

    def reset(self, context, state):
        self._asin_list = context['asin_list']
        self._p90_demand = {}

    def compute_actions(self, state):
        actions = []
        current_time = state['date_time']
        current_clock = state['clock']
        
        G = state['network']

        for asin in self._asin_list:
            # calculate tip for planning period of 7 days (i.e. buy enough to cover 7 days of demand)
            target_inventory_position = self._calculate_tip(asin, current_time, self._planning_horizon)
            logger.debug(
                "Target inventory position for ASIN {} at time {} is {}.".
                format(asin, current_time, target_inventory_position))

            # get total on-hand inventory and inflight of this ASIN, at national level (i.e., summed across all warehouses, inbound arcs)
            total_current_inventory = get_asin_inventory_in_network(G, asin)
            in_flight_inventory = get_asin_inventory_on_all_inbound_arcs(G, asin)

            total_inventory_in_network = total_current_inventory + in_flight_inventory

            logger.debug("Total inventory in network for {} = {}.".format(asin, total_inventory_in_network))

            # Simple order-up-to policy, and no negative order quantities allowed
            buying_PO = round(int(max(
                0, target_inventory_position - total_inventory_in_network)))

            # Submit purchase order
            if buying_PO > 0:
                logger.debug("Purchase Order for {} quantity of ASIN {}.".format(buying_PO, asin))

                action = {
                    'type': 'purchase_order',
                    'asin': asin,
                    'origin': None,
                    'destination': None,
                    'quantity': buying_PO,
                    'schedule': current_clock
                }

                actions.append(action)

        return actions

    def _calculate_tip(self, asin, current_time, planning_period):
        
        self._p90_demand[asin] = 0

        for i in range(0,planning_period):
            mean_demand = self._rng.rand() * self._max_mean
            self._p90_demand[asin] += poisson.ppf(self._service_level, mean_demand)

        tip = self._p90_demand[asin]

        return tip
