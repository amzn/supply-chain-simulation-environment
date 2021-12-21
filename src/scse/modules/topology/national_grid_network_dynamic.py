import os
import networkx as nx

from scse.api.module import Env
from scse.constants.national_grid_constants import (
    ELECTRICITY_ASIN,
    ENERGY_GENERATION_ASINS,
    ENERGY_GENERATION_LABELS,
    DEFAULT_CONSUMER,
    DEFAULT_BALANCE_SOURCE,
    DEFAULT_BALANCE_SINK
)

class NationalGridNetwork(Env):
    # Start with nothing, and allow 1 period for transit
    # Technically transfer should be instantaneous, but lets cheat a bit
    _DEFAULT_INITIAL_INVENTORY = 0
    _DEFAULT_TRANSIT_TIME = 1

    _DEFAULT_MAX_BATTERY_CAPACITY = 50  #  size of a unit battery
    _DEFAULT_INIT_BATTERY_CAPACITY = int(_DEFAULT_MAX_BATTERY_CAPACITY * 0.2)

    _DEFAULT_NUM_BATTERIES = 25

    def __init__(self, run_parameters):
        """
        Highly simplified digital twin of the network.
        """
        self._initial_inventory = run_parameters.get(
            'initial_inventory', self._DEFAULT_INITIAL_INVENTORY)
        self._transit_time = run_parameters.get(
            'transit_time', self._DEFAULT_TRANSIT_TIME)
        self._max_battery_capacity = run_parameters.get(
            'max_battery_capacity', self._DEFAULT_MAX_BATTERY_CAPACITY)
        self._init_battery_capacity = run_parameters.get(
            'init_battery_capacity', self._DEFAULT_INIT_BATTERY_CAPACITY)

        if os.environ.get('num_batteries') is not None:
            self._num_batteries = run_parameters.get(
                'num_batteries', os.environ.get('num_batteries'))
        else:
            self._num_batteries = run_parameters.get(
                'num_batteries', self._DEFAULT_NUM_BATTERIES)

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
        # G.add_node(ENERGY_GENERATION_LABELS.solar,
        #            node_type='vendor',
        #            asins_produced=[ENERGY_GENERATION_ASINS.solar],
        #            location=(-3.7210765082286055, 50.51499818530821)
        #            )
        # G.add_node(ENERGY_GENERATION_LABELS.wind_onshore,
        #            node_type='vendor',
        #            asins_produced=[ENERGY_GENERATION_ASINS.wind_onshore],
        #            location=(-2.692165321894899, 56.541558049898015)
        #            )
        # G.add_node(ENERGY_GENERATION_LABELS.wind_offshore,
        #            node_type='vendor',
        #            asins_produced=[ENERGY_GENERATION_ASINS.wind_offshore],
        #            location=(-0.054598091962716026, 57.08463527849611)
        #            )
        G.add_node(ENERGY_GENERATION_LABELS.wind_combined,
                   node_type='vendor',
                   asins_produced=[ENERGY_GENERATION_ASINS.wind_combined],
                   location=(-2.692165321894899, 56.541558049898015)
                   )
        G.add_node(ENERGY_GENERATION_LABELS.hydro_storage,
                   node_type='vendor',
                   asins_produced=[ENERGY_GENERATION_ASINS.hydro_storage],
                   location=(-3.9283652263011684, 56.95581355412285)
                   )
        G.add_node(ENERGY_GENERATION_LABELS.hydro_river,
                   node_type='vendor',
                   asins_produced=[ENERGY_GENERATION_ASINS.hydro_river],
                   location=(-6.296549071193306, 58.38822970631145)
                   )
        G.add_node(ENERGY_GENERATION_LABELS.biomass,
                   node_type='vendor',
                   asins_produced=[ENERGY_GENERATION_ASINS.biomass],
                   location=(-4.882288111035016, 54.991766558790935)
                   )
        G.add_node(ENERGY_GENERATION_LABELS.fossil_gas,
                   node_type='vendor',
                   asins_produced=[ENERGY_GENERATION_ASINS.fossil_gas],
                   location=(-3.7542647293810076, 51.67830989320217)
                   )
        G.add_node(ENERGY_GENERATION_LABELS.fossil_oil,
                   node_type='vendor',
                   asins_produced=[ENERGY_GENERATION_ASINS.fossil_oil],
                   location=(-3.7542647293810076, 52.48838509810871)
                   )
        G.add_node(ENERGY_GENERATION_LABELS.fossil_coal,
                   node_type='vendor',
                   asins_produced=[ENERGY_GENERATION_ASINS.fossil_coal],
                   location=(-3.7542647293810076, 53.268407629435465)
                   )
        G.add_node(ENERGY_GENERATION_LABELS.nuclear,
                   node_type='vendor',
                   asins_produced=[ENERGY_GENERATION_ASINS.nuclear],
                   location=(-4.576878528603206, 50.547804052206494)
                   )
        G.add_node(ENERGY_GENERATION_LABELS.interconnector,
                   node_type='vendor',
                   asins_produced=[ENERGY_GENERATION_ASINS.interconnector],
                   location=(2.1426203852648205, 51.00722532120002)
                   )
        G.add_node(ENERGY_GENERATION_LABELS.other,
                   node_type='vendor',
                   asins_produced=[ENERGY_GENERATION_ASINS.other],
                   location=(-1.7187199226929328, 55.56573138678091)
                   )

        # "Port": electricity substations
        # Could also define as warehouses, but provides differentiation
        # Further analysis of how `node_type` is used required
        # Only one for now - more can be added at later date
        # Added `allow_negative` property
        G.add_node("Substation",
                   node_type='port',
                   location=(-1.47591978069484, 53.02151541873239),
                   inventory=dict.fromkeys(asin_list, self._initial_inventory),
                   allow_negative=True
                   )

        # Define axes for battery placement in the visualisation
        axis_one = -3
        axis_two = 51

        for battery_idx in range(self._num_batteries):
            battery_loc = (axis_one, axis_two)
            # "Warehouse": batteries
            # note, assumes:
            # - batteries all in same loc
            # - batteries all have same max inventory (capacity)
            # - batteries all have same initial inventory
            G.add_node(f"Battery{battery_idx}",
                       node_type='warehouse',
                       location=battery_loc,
                       inventory={
                           ELECTRICITY_ASIN: self._init_battery_capacity},
                       max_inventory={
                           ELECTRICITY_ASIN: self._max_battery_capacity}
                       )

            # Shift new battery very slightly right to have a marginally better visual of the no. of batteries
            axis_one += 0.4

            # Shift vertical axis down every 10 batteries and reset horizontal position
            if (battery_idx+1) % 10 == 0:
                axis_two -= 0.4
                axis_one -= 4.0

        # Consumers
        # Only one for now - more can be added at later date
        G.add_node(DEFAULT_CONSUMER,
                   node_type='customer',
                   location=(0.7925228523731638, 52.18170700596113),
                   delivered=0
                   )

        # Balance Mechanism
        # Source and sink for maintaining balance at substations.
        # Note that the source has been modelled as a vendor, and the sink
        # as a customer.
        G.add_node(DEFAULT_BALANCE_SOURCE,
                   node_type='vendor',
                   asins_produced=[ELECTRICITY_ASIN],
                   location=(1.7925228523731638, 54.63535939082493)
                   )
        G.add_node(DEFAULT_BALANCE_SINK,
                   node_type='customer',
                   location=(1.7925228523731638, 53.55853319839303),
                   delivered=0
                   )

        ##############
        # Define Edges
        ##############

        # Electricity sources to substation
        # G.add_edge(ENERGY_GENERATION_LABELS.solar, "Substation",
        #            ** {'transit_time': self._transit_time, 'shipments': []})
        # G.add_edge(ENERGY_GENERATION_LABELS.wind_onshore, "Substation",
        #            ** {'transit_time': self._transit_time, 'shipments': []})
        # G.add_edge(ENERGY_GENERATION_LABELS.wind_offshore, "Substation",
        #            ** {'transit_time': self._transit_time, 'shipments': []})
        G.add_edge(ENERGY_GENERATION_LABELS.wind_combined, "Substation",
                   ** {'transit_time': self._transit_time, 'shipments': []})
        G.add_edge(ENERGY_GENERATION_LABELS.hydro_storage, "Substation",
                   ** {'transit_time': self._transit_time, 'shipments': []})
        G.add_edge(ENERGY_GENERATION_LABELS.hydro_river, "Substation",
                   ** {'transit_time': self._transit_time, 'shipments': []})
        G.add_edge(ENERGY_GENERATION_LABELS.biomass, "Substation",
                   ** {'transit_time': self._transit_time, 'shipments': []})
        G.add_edge(ENERGY_GENERATION_LABELS.fossil_gas, "Substation",
                   ** {'transit_time': self._transit_time, 'shipments': []})
        G.add_edge(ENERGY_GENERATION_LABELS.fossil_oil, "Substation",
                   ** {'transit_time': self._transit_time, 'shipments': []})
        G.add_edge(ENERGY_GENERATION_LABELS.fossil_coal, "Substation",
                   ** {'transit_time': self._transit_time, 'shipments': []})
        G.add_edge(ENERGY_GENERATION_LABELS.nuclear, "Substation",
                   ** {'transit_time': self._transit_time, 'shipments': []})
        G.add_edge(ENERGY_GENERATION_LABELS.interconnector, "Substation",
                   ** {'transit_time': self._transit_time, 'shipments': []})
        G.add_edge(ENERGY_GENERATION_LABELS.other, "Substation",
                   ** {'transit_time': self._transit_time, 'shipments': []})

        for battery_idx in range(self._num_batteries):
            # Substation to battery
            # Note: At later date may want to model direct source -> battery storage
            G.add_edge("Substation", f"Battery{battery_idx}",
                       ** {'transit_time': self._transit_time, 'shipments': []})
            # Battery to to substation
            # Could use different substation to prevent cycle
            G.add_edge(f"Battery{battery_idx}", "Substation",
                       ** {'transit_time': self._transit_time, 'shipments': []})

        # Substation to customer
        G.add_edge("Substation", DEFAULT_CONSUMER,
                   ** {'transit_time': self._transit_time, 'shipments': []})

        # Balance source to substation
        G.add_edge(DEFAULT_BALANCE_SOURCE, "Substation",
                   ** {'transit_time': self._transit_time, 'shipments': []})

        # Substation to balance sink
        G.add_edge("Substation", DEFAULT_BALANCE_SINK,
                   ** {'transit_time': self._transit_time, 'shipments': []})

        return G
