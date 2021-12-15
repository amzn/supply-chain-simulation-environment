import logging
import math

from scse.api.module import Agent
from scse.api.network import get_asin_inventory_in_node

logger = logging.getLogger(__name__)


class StoreExcessSupply(Agent):
    _DEFAULT_ASIN = 'electricity'

    def __init__(self, run_parameters):
        """
        Store all excess supply across battery network.

        As with a number of other modules, only the `electricity`
        ASIN is being considered at this time.

        NOTE: This module does not consider the forecasted demand
        in the next timestep - substations have no storage capacity,
        and so must deposit excess into the battery reserves.
        """
        # Note: Ports demo service takes max capacity into account.
        # We might want to consider doing the same.
        self._asin = self._DEFAULT_ASIN

    def reset(self, context, state):
        self._asin_list = context['asin_list']

    def get_name(self):
        return 'store_excess_supply'

    def compute_actions(self, state):
        G = state['network']
        actions = []

        # Get a list of batteries - remember that these have the type `warehouse` for now
        batteries = []
        for node, node_data in G.nodes(data=True):
            if node_data.get('node_type') in ['warehouse']:
                batteries.append((node, node_data))

        # Get a list of substations - remember that these have the type `port` for now
        # Could have put below logic here; kept separation for readability
        substations = []
        for node, node_data in G.nodes(data=True):
            if node_data.get('node_type') in ['port']:
                substations.append((node, node_data))

        # Go through the substations and identify any excess they currently have
        # Share the excess evenly across the battery network
        for substation, substation_data in substations:
            onhand = get_asin_inventory_in_node(substation_data, self._asin)

            if onhand > 0:
                logger.debug(f"Storing excess of {onhand} ASIN {self._asin} from substation {substation}.")

                for battery, battery_data in batteries:
                    # Note: Whole number of MW being transmitted
                    # Have not yet removed miniscot check preventing float
                    action = {
                        'type': 'transfer',
                        'asin': self._asin,
                        'quantity': math.floor(onhand/len(batteries)),
                        'schedule': state['clock'],
                        'origin': substation,
                        'destination': battery
                    }
                    actions.append(action)

        if len(actions) == 0:
            logger.debug("No action was required")

        return actions
