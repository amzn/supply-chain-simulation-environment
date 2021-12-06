"""
Simple implementation of a placement heuristic that evenly sends inventory downstream
from a port to 3 warehouses
"""
import networkx as nx
from scse.api.module import Agent
from scse.api.network import get_asin_inventory_in_node
import math
import logging
logger = logging.getLogger(__name__)


class PlacementHeuristic(Agent):
    def __init__(self, run_parameters):
        self._simulation_seed = run_parameters['simulation_seed']

    def reset(self, context, state):
        self._asin_list = context['asin_list']

    def get_name(self):
        return 'placement heuristic'

    def compute_actions(self, state):
        G = state['network']
        actions = []

        for asin in self._asin_list:
            for node, node_data in G.nodes(data=True):
                onhand = get_asin_inventory_in_node(node_data, asin)
                if onhand >= 3 and node_data.get('node_type') in ['port']:
                    port_name = node
                    port_onhand = onhand

                    for origin, destination, edge_data in G.edges(data = True):
                        if origin == port_name:
                            action = {
                                'type': 'transfer',
                                'asin': asin,
                                'quantity': math.floor(port_onhand/3),
                                'schedule': state['clock'],
                                'origin': port_name,
                                'destination': destination
                            }
                            actions.append(action)

        return actions