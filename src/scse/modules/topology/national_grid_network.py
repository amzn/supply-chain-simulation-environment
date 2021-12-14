import networkx as nx
from scse.api.module import Env


class NationalGridNetwork(Env):
    # Start with nothing, and allow 1 period for transit
    # Technically transfer should be instantaneous, but lets cheat a bit
    _DEFAULT_INITIAL_INVENTORY = 0
    _DEFAULT_TRANSIT_TIME = 1

    def __init__(self, run_parameters):
        """
        Highly simplified digital twin of the network.
        """
        self._initial_inventory = run_parameters.get('initial_inventory', self._DEFAULT_INITIAL_INVENTORY)
        self._transit_time = run_parameters.get('transit_time', self._DEFAULT_TRANSIT_TIME)

    def get_name(self):
        return 'network'

    def get_initial_state(self, context):
        G = nx.DiGraph()
        asin_list = context['asin_list']

        ##############
        # Define Nodes
        ##############

        # "Vendors": electricity sources
        # These could be further broken down
        # Have only added a subset for now
        # Added `asins_produced` property
        G.add_node("Solar",
                    node_type = 'vendor',
                    asins_produced = ['solar'],
                    location = (0.0, 0.0)
                    )
        G.add_node("Wind Onshore",
                    node_type = 'vendor',
                    asins_produced = ['wind_onshore'],
                    location = (0.1, 0.1)
                    )
        G.add_node("Fossil Gas",
                    node_type = 'vendor',
                    asins_produced = ['fossil_gas'],
                    location = (0.2, 0.2)
                    )

        # "Port": electricity substations
        # Could also define as warehouses, but provides differentiation
        # Further analysis of how `node_type` is used required
        # Only one for now - more can be added at later date
        # Added `allow_negative` property
        G.add_node("Substation",
                    node_type = 'port',
                    location = (1.0, 1.0),
                    inventory = dict.fromkeys(asin_list, self._initial_inventory),
                    allow_negative = True
                    )

        # "Warehouse": batteries
        # Only one for now - more can be added at later date
        G.add_node("Battery",
                    node_type = 'warehouse',
                    location = (2.0, 2.0),
                    inventory = dict.fromkeys(asin_list, self._initial_inventory)
                    )

        # Consumers
        # Only one for now - more can be added at later date
        G.add_node("Consumers",
                    node_type = 'customer',
                    location = (0.0, 0.0),
                    delivered = 0
                    )

        ##############
        # Define Edges
        ##############

        # Electricity sources to substation
        G.add_edge("Solar", "Substation", **{'transit_time': self._transit_time, 'shipments': []})
        G.add_edge("Wind Onshore", "Substation", **{'transit_time': self._transit_time, 'shipments': []})
        G.add_edge("Fossil Gas", "Substation", **{'transit_time': self._transit_time, 'shipments': []})

        # Substation to battery
        # Note: At later date may want to model direct source -> battery storage
        G.add_edge("Substation", "Battery", **{'transit_time': self._transit_time, 'shipments': []})

        # Battery to to substation
        # Could use different substation to prevent cycle
        G.add_edge("Battery", "Substation", **{'transit_time': self._transit_time, 'shipments': []})

        # Substation to customer
        G.add_edge("Substation", "Consumers", **{'transit_time': self._transit_time, 'shipments': []})

        return G
