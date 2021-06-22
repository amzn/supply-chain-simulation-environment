"""
Simple implementation of an infinite inventory vendor that places in the
closest warehouse.
"""
from scse.api.module import Agent
import logging
logger = logging.getLogger(__name__)


class InfiniteInventoryVendor(Agent):
    def __init__(self, run_parameters):
        self._simulation_seed = run_parameters['simulation_seed']
        # TODO Hardcoding the location and name of the vendor here
        # We can also find this in the state graph, which is more robust
        self._VENDOR_LOCATION = (39.0997, -94.5786)
        self._SINGLE_VENDOR_ID = 'Manufacturer'

    def reset(self, context, state):
        self._asin_list = context['asin_list']

    def get_name(self):
        return 'vendor'

    def compute_actions(self, state):
        G = state['network']

        # TODO there is a better way of doing this by leveraging the graph itself...
        warehouse_locations = []
        for _, node_data in G.nodes(data=True):
            if node_data['node_type'] == 'warehouse':
                warehouse_locations.append(node_data['location'])

        closest_warehouse_location = min(
                        warehouse_locations,
                        key=lambda p: _distance(p, self._VENDOR_LOCATION))

        # Invariant: there should be 0 or 1 warehouses
        closest_warehouse_name = next(
            ((n)
             for n, d in G.nodes(data=True)
             if d.get('location') == closest_warehouse_location))           

        # For each pending PO, fulfill everything, immediately and transfer to closest warehouse.
        actions = []
        for po in state['purchase_orders']:
            ## Complete action_form with the origin node, confirm the quantity we can fulfill,
            ## and schedule when it ships (e.g. 2 timesteps from now)

            action = {
                'type': 'inbound_shipment',
                'asin': po['asin'],
                'quantity': po['quantity'],
                'schedule': state['clock'],
                'origin': self._SINGLE_VENDOR_ID,
                'destination': closest_warehouse_name,
                'uuid': po['uuid']
            }
            actions.append(action)

        return actions


def _distance(s, d):
    return (s[0] - d[0])**2 + (s[1] - d[1])**2
