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

        # In this demo, we create the entire 6 node network here for clarity.  
        # In other use-cases, we may only create the fulfillment network here
        # And let the customer and vendor modules create their nodes on the fly
        # Also bear in mind we can create this networkx graph from a .csv, instead
        G.add_node("Beijing Manufacturer",
                    node_type = 'vendor',
                    location = (39.9042,116.4074)
                    )
        G.add_node("Seattle Port",
                    node_type = 'port',
                    location = (47.6062,122.3321),
                    inventory = dict.fromkeys(asin_list, self._initial_inventory)
                    )
        G.add_node("Iowa Warehouse",
                    node_type = 'warehouse',
                    location = (41.7436169,-92.7281291),
                    inventory = dict.fromkeys(asin_list, self._initial_inventory)
                    )
        G.add_node("Kansas City Warehouse",
                    node_type = 'warehouse',
                    location = (39.0997, -94.5786),
                    inventory = dict.fromkeys(asin_list, self._initial_inventory)
                    )
        G.add_node("Seattle Warehouse",
                    node_type = 'warehouse',
                    location = (47.6062,122.3321),
                    inventory = dict.fromkeys(asin_list, self._initial_inventory)
                    )
        G.add_node("Chicago Customer",
                    node_type = 'customer',
                    location = (41.8339037,-87.8720468),
                    delivered = 0
                    )
        # Create edges from manufacturer to port, port to 3 warehouses, 3 warehouses to customer
        # manufacturer to port
        edge_data_manufacturer = {'transit_time': self._transit_time+5, 'shipments': []}
        G.add_edge("Beijing Manufacturer", "Seattle Port", **edge_data_manufacturer)
        # port to 3 warehouses
        edge_data_port_to_iowa = {'transit_time': self._transit_time, 'shipments': []}
        edge_data_port_to_kc = {'transit_time': self._transit_time+1, 'shipments': []}
        edge_data_port_to_seattle = {'transit_time': self._transit_time-2, 'shipments': []}
        G.add_edge("Seattle Port", "Iowa Warehouse", **edge_data_port_to_iowa)
        G.add_edge("Seattle Port", "Kansas City Warehouse", **edge_data_port_to_kc)
        G.add_edge("Seattle Port", "Seattle Warehouse", **edge_data_port_to_seattle)
        # 3 warehouses to the customer
        edge_data_iowa_to_chicago = {'transit_time': self._transit_time-1, 'shipments': []}
        edge_data_kc_to_chicago = {'transit_time': self._transit_time, 'shipments': []}
        edge_data_seattle_to_chicago = {'transit_time': self._transit_time+2, 'shipments': []}
        G.add_edge("Iowa Warehouse", "Chicago Customer", **edge_data_iowa_to_chicago)
        G.add_edge("Kansas City Warehouse", "Chicago Customer", **edge_data_kc_to_chicago)
        G.add_edge("Seattle Warehouse", "Chicago Customer", **edge_data_seattle_to_chicago)

        return G
