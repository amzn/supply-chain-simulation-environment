"""
Rewards for the simulation, cash accounting
"""
import logging
from os.path import dirname, join
import csv
logger = logging.getLogger(__name__)


class CashAccounting():
    def __init__(self, run_parameters):
        self._time_horizon = run_parameters['time_horizon']
        # Hardcoding vendor cost, customer price, holding cost, and lost demand penalty
        self._cost = 5
        self._price = 10
        self._holding_cost = 0.5
        self._lost_demand_penalty = 0

    def reset(self, context, state):
        self._context = {}
        self._context['asin_list'] = context['asin_list']
        
        self._timestep_revenue = 0
        self._timestep_vendor_cost = 0
        self._timestep_holding_cost = 0
        self._timestep_sales_quantity = 0
        # We'll use this to track unfilled demand, since this builds up
        self._cumulative_customer_orders = []
        # We'll print a csv log, with structure:
        self._log_header = [
            "timestep", 
            "revenue", 
            "vendor_cost", 
            "holding_cost", 
            "customer_demand_quantity", 
            "sales_quantity",
            "unfilled_demand"
        ]
        self._metrics_log = [self._log_header]

    def compute_reward(self, state, action):
        # cash accounting
        actionType = action['type']
        quantity = action['quantity']
        asin = action['asin']

        if actionType == 'outbound_shipment':

            revenue = self._price * quantity

            # add to timestep aggregate metrics, to be logged later
            self._timestep_revenue += revenue
            self._timestep_sales_quantity += quantity

            reward = revenue

        elif actionType == 'inbound_shipment':
            
            cost = self._cost * quantity

            # add to timestep aggregate metrics, to be logged later
            self._timestep_vendor_cost += cost

            reward = -1 * cost

        elif actionType == 'advance_time':
            reward = {}
            reward_by_asin = {k: 0 for k in self._context['asin_list']}
            reward['total'] = 0
            timestep_inventory_by_asin_fc = {}
            total_holding_cost = 0
            G = state['network']
            for node, node_data in G.nodes(data=True):
                if node_data['node_type'] == 'warehouse':
                    for asin in G.nodes[node]['inventory']:
                        asin_holding_cost = self._holding_cost
                        reward_by_asin[asin] -= asin_holding_cost
                        total_holding_cost += G.nodes[node]['inventory'][
                            asin] * asin_holding_cost

            self._timestep_holding_cost += total_holding_cost

            # aggregating and outputting the metrics logging

            timestep_unfilled_demand = 0

            for order in state['customer_orders']:
                if order not in self._cumulative_customer_orders:
                    quantity = order['quantity']
                    timestep_unfilled_demand += quantity
                    self._cumulative_customer_orders.append(order)

                    lost_demand_penalty = self._lost_demand_penalty

                    reward['total'] -= lost_demand_penalty*quantity
                    reward_by_asin[order['asin']] -= lost_demand_penalty*quantity

            timestep_log = [
                str(state['clock']), self._timestep_revenue,
                self._timestep_vendor_cost, self._timestep_holding_cost,
                self._timestep_sales_quantity + timestep_unfilled_demand,
                self._timestep_sales_quantity, timestep_unfilled_demand
            ]
            self._metrics_log.append(timestep_log)

            self._timestep_revenue = 0
            self._timestep_vendor_cost = 0
            self._timestep_holding_cost = 0
            self._timestep_sales_quantity = 0

            # If we're at the end of the episode, print the csv log
            if state['clock'] == (self._time_horizon - 1):
                module_path = dirname(__file__)
                filename = "metrics_log.csv"
                filepath = join(module_path, filename)
                with open(filepath, "w", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerows(self._metrics_log)

            reward['total'] -= total_holding_cost
            reward['by_asin'] = reward_by_asin

        else:
            raise ValueError(
                "Unknown action type {}, no reward to vend".format(actionType))

        return reward
