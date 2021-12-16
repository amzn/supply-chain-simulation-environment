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
                    # asins_produced = ['solar'],
                    asins_produced = ['electricity'],
                    location = (-4.216477053445252, 50.7134720325634)
                    )
        G.add_node("Wind Onshore",
                    node_type = 'vendor',
                    # asins_produced = ['wind_onshore'],
                    asins_produced = ['electricity'],
                    location = (-3.0223770988897174, 57.29950745888362)
                    )
        G.add_node("Fossil Gas",
                    node_type = 'vendor',
                    # asins_produced = ['fossil_gas'],
                    asins_produced = ['electricity'],
                    location = (-3.4726115079844275, 52.48838509810871)
                    )

        # "Port": electricity substations
        # Could also define as warehouses, but provides differentiation
        # Further analysis of how `node_type` is used required
        # Only one for now - more can be added at later date
        # Added `allow_negative` property
        G.add_node("Substation",
                    node_type = 'port',
                    location = (-1.47591978069484, 53.02151541873239),
                    inventory = dict.fromkeys(asin_list, self._initial_inventory),
                    allow_negative = True
                    )

        # "Warehouse": batteries
        # Only one for now - more can be added at later date
        G.add_node("Battery",
                    node_type = 'warehouse',
                    location = (-1.207637136122046, 51.547526847219395),
                    # inventory = dict.fromkeys(asin_list, self._initial_inventory),
                    inventory = {'electricity': 100},
                    max_inventory = {'electricity': 200}
                    )

        # Consumers
        # Only one for now - more can be added at later date
        G.add_node("Consumers",
                    node_type = 'customer',
                    location = (-0.17563780900605935, 51.633920790187155),
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
