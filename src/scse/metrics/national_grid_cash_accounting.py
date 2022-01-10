"""
Rewards for the simulation, cash accounting
"""
import logging
from os.path import dirname, join
import csv
from scse.constants.national_grid_constants import (
    DEFAULT_BALANCE_SOURCE, DEFAULT_BALANCE_SINK, ELECTRICITY_ASIN
)
from scse.default_run_parameters.national_grid_default_run_parameters import (
    DEFAULT_RUN_PARAMETERS
)

logger = logging.getLogger(__name__)


class CashAccounting():
    def __init__(self, run_parameters):

        self._time_horizon = run_parameters['time_horizon']

        # Battery CAPEX/OPEX penalties, w/ units £/MWh
        self._battery_penalty = run_parameters.get(
            'battery_penalty', DEFAULT_RUN_PARAMETERS.battery_penalty
        )
        self._num_batteries = run_parameters.get(
            'num_batteries', DEFAULT_RUN_PARAMETERS.num_batteries
        )
        self._max_battery_capacity = run_parameters.get(
            'max_battery_capacity', DEFAULT_RUN_PARAMETERS.max_battery_capacity
        )
        self._lifetime_years = run_parameters.get(
            'lifetime_years', DEFAULT_RUN_PARAMETERS.lifetime_years
        )
        self._holding_cost = run_parameters.get(
            'holding_cost', DEFAULT_RUN_PARAMETERS.holding_cost_penalty
        )  # how much to reward/penalize battery use
        self._transfer_cost = run_parameters.get(
            'transfer', DEFAULT_RUN_PARAMETERS.transfer_penalty
        )  # cost to move from the batteries

        # Rewards/penalties for using BMRS and batteries
        self._source_request = run_parameters.get(
            'source_request', DEFAULT_RUN_PARAMETERS.source_request_reward_penalty
        )
        self._sink_deposit = run_parameters.get(
            'sink_deposit', DEFAULT_RUN_PARAMETERS.sink_deposit_reward_penalty
        )
        self._battery_charging = run_parameters.get(
            'battery_charging', DEFAULT_RUN_PARAMETERS.battery_charging_reward_penalty
        )
        self._battery_drawdown = run_parameters.get(
            'battery_drawdown', DEFAULT_RUN_PARAMETERS.battery_drawdown_reward_penalty
        )

        # Other penalties
        self._lost_demand_penalty = run_parameters.get(
            'lost_demand', DEFAULT_RUN_PARAMETERS.lost_demand_penalty
        )
        

    def reset(self, context, state):
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
        G = state["network"]

        # Total battery CAPEX, ignoring discounting
        self._upfront_battery_cost = (
            self._battery_penalty * self._max_battery_capacity * self._num_batteries
        )
        # Amortise battery CAPEX over lifetime
        # Even installments every simulation period (30 mins)
        self._amortised_battery_cost = (
            self._upfront_battery_cost / (self._lifetime_years * 365 * 24 * 2)
        )

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
            # substations => batteries and batteries => substation

            # case 1: charge battery_idx
            if action['origin'] == "Substation" and "Battery" in action["destination"]:
                transfer_revenue = self._battery_charging * quantity

            # case 2: discharge/drawdown electricity from battery
            # cost of charging a battery
            if action['destination'] == "Substation" and "Battery" in action["origin"]:
                transfer_revenue = self._battery_drawdown * quantity

            self._timestep_transfer_cost += transfer_revenue

            reward = transfer_revenue  #  positive = good

        elif actionType == 'advance_time':
            # Make sure to see code + comments at the end of this block

            reward = {}
            reward_by_asin = {k: 0 for k in self._context['asin_list']}
            reward['total'] = 0
            timestep_inventory_by_asin_fc = {}
            total_holding_cost = 0
            G = state['network']

            # accounts for cost w/ keeping energy in the batteries
            # subtracted from total cost at the end of this block
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

            # Subtract cost of inventory at hand from total cost
            reward['total'] -= total_holding_cost

            # Per-period payback of amortised battery CAPEX costs
            # No charge for 0th simulation stage
            if state['clock'] != 0:
                reward['total'] += self._amortised_battery_cost

            reward['by_asin'] = reward_by_asin

        else:
            raise ValueError(
                "Unknown action type {}, no reward to vend".format(actionType))

        return reward
