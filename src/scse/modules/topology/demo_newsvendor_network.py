"""
Baseline Agent representing the Newsvendor Network.
"""
import networkx as nx
from scse.api.module import Env


class SimpleNetwork(Env):
    # TODO initial inventory is hardcoded, but can be obtained from some source data
    _DEFAULT_INITIAL_INVENTORY = 1
    _DEFAULT_TRANSIT_TIME = 2


    def __init__(self, run_parameters):
        self._simulation_seed = run_parameters['simulation_seed']
        self._initial_inventory = self._DEFAULT_INITIAL_INVENTORY
        self._transit_time = self._DEFAULT_TRANSIT_TIME

    def get_name(self):
        return 'network'

    def get_initial_state(self, context):
        G = nx.DiGraph()
        asin_list = context['asin_list']

        # In this demo, we create the entire 3 node network here for clarity.  
        # In other use-cases, we may only create the fulfillment network here
        # And let the customer and vendor modules create their nodes on the fly
        G.add_node("Manufacturer",
                    node_type = 'vendor',
                    location = (39.0997, -94.5786)
                    )
        G.add_node("Newsvendor",
                    node_type = 'warehouse',
                    location = (41.7436169,-92.7281291),
                    inventory = dict.fromkeys(asin_list, self._initial_inventory)
                    )
        G.add_node("Customer",
                    node_type = 'customer',
                    location = (41.8339037,-87.8720468),
                    delivered = 0
                    )
        
        edge_data_manufacturer = {'transit_time': self._transit_time, 'shipments': []}
        G.add_edge("Manufacturer", "Newsvendor", **edge_data_manufacturer)
        edge_data_newsvendor = {'transit_time': self._transit_time, 'shipments': []}
        G.add_edge("Newsvendor", "Customer", **edge_data_newsvendor)

        return G
