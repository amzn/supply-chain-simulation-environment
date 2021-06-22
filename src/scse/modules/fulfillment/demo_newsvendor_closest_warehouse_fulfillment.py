"""
Agent that fulfills orders always from the closest warehouse.
"""
import networkx as nx
from scse.api.module import Agent
from scse.api.network import get_asin_inventory_in_node
import logging
logger = logging.getLogger(__name__)


class ClosestWarehouseFulfillment(Agent):
    def __init__(self, run_parameters):
        self._simulation_seed = run_parameters['simulation_seed']

    def get_name(self):
        return 'fulfiller'

    def reset(self, context, state):
        self._asin_list = context['asin_list']

    def compute_actions(self, state):
        # Get locations of customer orders, match with closest warehouse with sufficient inventory, and fulfill it.
        actions = []
        G = state['network']
        # We need to virtually track the inventory as we allocate it, so we don't reuse inventory in separate orders
        inventory_tracker = {}
        for node, node_data in G.nodes(data=True):
            if node_data.get('node_type') == 'warehouse':
                inventory_tracker[node] = {"location":node_data.get('location')}
                for asin in G.nodes[node]['inventory']:
                    inventory_tracker[node][asin] = G.nodes[node]['inventory'][asin]

        for order in state['customer_orders']:

            # Logically, each order is attributed with a single ASIN (should we change this?)
            asin = order['asin']
            quantity = order['quantity']

            customer_id = order['destination']
            customer_location = G.nodes[customer_id]['location']

            warehouses_with_inventory = {}
            for warehouse in inventory_tracker:
                if inventory_tracker[warehouse][asin] >= quantity:
                    distance = _distance(inventory_tracker[warehouse]['location'], customer_location)
                    warehouses_with_inventory[warehouse] = distance

            if warehouses_with_inventory:
                logger.debug(
                    "There are {} warehouses with inventory for ASIN {}.".format(
                        len(warehouses_with_inventory), asin))
                closest_warehouse = min(warehouses_with_inventory.keys(), key=(lambda k: warehouses_with_inventory[k]))

                if closest_warehouse:
                    logger.debug("Fulfilling order {} from warehouse {}.".format(
                        order, closest_warehouse))

                    action = {
                        'type': 'outbound_shipment',
                        'asin': asin,
                        'origin': closest_warehouse,
                        'destination': customer_id,
                        'schedule': order['schedule'],
                        'quantity': order['quantity'],
                        'uuid': order['uuid']
                    }
                    actions.append(action)
                    inventory_tracker[closest_warehouse][asin] -= quantity

        return actions


def _distance(s, d):
    return (s[0] - d[0])**2 + (s[1] - d[1])**2
