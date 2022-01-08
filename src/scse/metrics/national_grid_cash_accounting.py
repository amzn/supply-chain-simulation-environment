"""
Rewards for the simulation, cash accounting
"""
import logging
from os.path import dirname, join
import csv
from scse.constants.national_grid_constants import (
    DEFAULT_BALANCE_SOURCE, DEFAULT_BALANCE_SINK, ELECTRICITY_ASIN
)
logger = logging.getLogger(__name__)


class CashAccounting():
    def __init__(self, run_parameters):
        self._time_horizon = run_parameters['time_horizon']
        # Hardcoding vendor cost, customer price, holding cost, and lost demand penalty

        # updated for realistic values, w/ units £/MWh
        self._source_request = -149.8
        self._sink_deposit = 32.0

        self._battery_charging = -32.0
        self._battery_drawdown = 149.8
        # self._cost = 5
        # self._price = 10
        self._transfer_cost = 0  # 2 # cost to move from the batteries

        self._lost_demand_penalty = 0

        # how much to reward/penalize battery use
        self._holding_cost = 0  # -20

    def reset(self, context, state, battery_penalty=50):
        self._context = {}
        self._context['asin_list'] = context['asin_list']

        self._timestep_revenue = 0
        self._timestep_vendor_cost = 0
        self._timestep_holding_cost = 0
        self._timestep_transfer_cost = 0
        self._timestep_sales_quantity = 0
        self._upfront_battery_cost = 0

        # penalize the use of many batteries
        # penalty scaled by capacity of battery
        # TODO: check that this makes sense
        G = state["network"]
        for node, node_data in G.nodes(data=True):
            if "Battery" in node:
                # self._upfront_battery_cost += - \
                #     (battery_penalty) * \
                #     node_data["max_inventory"][ELECTRICITY_ASIN]
                self._upfront_battery_cost += - \
                    (battery_penalty)

        # We'll use this to track unfilled demand, since this builds up
        self._cumulative_customer_orders = []
        # We'll print a csv log, with structure:
        self._log_header = [
            "timestep",
            "revenue",
            "vendor_cost",
            "transfer_cost",
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
            # substations => consumers/sink

            # we only care about the case where we interact w/ balance scheme
            if action['destination'] == DEFAULT_BALANCE_SINK:
                revenue = self._sink_deposit * quantity

                # add to timestep aggregate metrics, to be logged later
                self._timestep_revenue += revenue
                self._timestep_sales_quantity += quantity

                # note: depending on view, when we give to sink:
                # unused supply can either be good or bad
                reward = revenue
            else:
                # note: could return to positive reward when give to consumers
                # for now, ignore
                reward = 0

        elif actionType == 'inbound_shipment':
            # substations => vendors/source

            # we only care about the case where we interact w/ balance scheme
            if action['origin'] == DEFAULT_BALANCE_SOURCE:
                cost = self._source_request * quantity

                # add to timestep aggregate metrics, to be logged later
                self._timestep_vendor_cost += cost

                # bad when we draw from the source
                reward = cost  #  assumes penalty is already negative
            else:
                # note: could also penalize when draw from other sources
                reward = 0

        elif actionType == 'transfer':
            # substations => batteries

            # cost of charging a battery
            cost = self._battery_charging * quantity

            self._timestep_transfer_cost += cost

            reward = cost

        elif actionType == 'advance_time':
            reward = {}
            reward_by_asin = {k: 0 for k in self._context['asin_list']}
            reward['total'] = 0
            timestep_inventory_by_asin_fc = {}
            total_holding_cost = 0
            G = state['network']

            # accounts for cost w/ keeping energy in the batteries
            for node, node_data in G.nodes(data=True):
                if node_data['node_type'] == 'warehouse':
                    for asin in G.nodes[node]['inventory']:
                        asin_holding_cost = self._holding_cost
                        reward_by_asin[asin] -= asin_holding_cost
                        total_holding_cost += G.nodes[node]['inventory'][
                            asin] * asin_holding_cost

            self._timestep_holding_cost += total_holding_cost

            # NOTE: we care about when the source > 0 (unfilled demand)
            timestep_unfilled_demand = 0

            for order in state['customer_orders']:
                if order not in self._cumulative_customer_orders:
                    quantity = order['quantity']
                    timestep_unfilled_demand += quantity
                    self._cumulative_customer_orders.append(order)

                    lost_demand_penalty = self._lost_demand_penalty

                    reward['total'] -= lost_demand_penalty*quantity
                    reward_by_asin[order['asin']
                                   ] -= lost_demand_penalty*quantity

            timestep_log = [
                str(state['clock']), self._timestep_revenue,
                self._timestep_vendor_cost, self._timestep_transfer_cost,
                self._timestep_holding_cost,
                self._timestep_sales_quantity + timestep_unfilled_demand,
                self._timestep_sales_quantity, timestep_unfilled_demand
            ]
            self._metrics_log.append(timestep_log)

            self._timestep_revenue = 0
            self._timestep_vendor_cost = 0
            self._timestep_transfer_cost = 0
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
