import logging

from scse.api.module import Agent

logger = logging.getLogger(__name__)


class ClosestSubstationFulfillment(Agent):
    def __init__(self, run_parameters):
        """
        Customer orders for electricity are fulfilled by the nearest substation.
        """
        pass

    def get_name(self):
        return 'fulfiller'

    def reset(self, context, state):
        self._asin_list = context['asin_list']

    def compute_actions(self, state):
        """
        Get locations of customer orders, match with closest substation, and fulfill the order.
        """

        actions = []
        G = state['network']

        # Get a list of substations - remember that these have the type `port` for now
        # Distance information has been kept for potential future use
        substations = {}
        for node, node_data in G.nodes(data=True):
            if node_data.get('node_type') == 'port':
                substations[node] = {
                    "location": node_data.get('location'),
                }

        # Error is thrown if there is not at least one substation
        if not substations:
            raise ValueError("No substations (i.e. ports) found - check the network topology.")
        logger.debug(f"There are {len(substations)} substations")

        # Loop through and fulfil customer orders
        for order in state['customer_orders']:
            asin = order['asin']
            if asin != 'electricity':
                raise ValueError("At present, only customer orders for generic electricity are supported.")

            customer_id = order['destination']
            customer_location = G.nodes[customer_id]['location']

            # Determine the distance to each substation
            substation_distances = {}
            for substation in substations:
                distance = _distance(substations[substation]['location'], customer_location)
                substation_distances[substation] = distance
            closest_substation = min(substation_distances.keys(), key=(lambda k: substation_distances[k]))

            logger.debug(f"Fulfilling order {order} from substation {closest_substation}.")

            action = {
                'type': 'outbound_shipment',
                'asin': asin,
                'origin': closest_substation,
                'destination': customer_id,
                'schedule': order['schedule'],
                'quantity': order['quantity'],
                'uuid': order['uuid']
            }

            actions.append(action)

        return actions


def _distance(s, d):
    return (s[0] - d[0])**2 + (s[1] - d[1])**2
