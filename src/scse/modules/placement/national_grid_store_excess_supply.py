import logging
import math

from scse.api.module import Agent
from scse.api.network import (
    get_asin_inventory_in_node, get_asin_max_inventory_in_node
)

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
                # Need to keep track of what excess capacity is already being sent
                module_copy = node_data.copy()
                module_copy['incoming'] = 0
                batteries.append((node, module_copy))

        # Get a list of substations - remember that these have the type `port` for now
        # Could have put below logic here; kept separation for readability
        substations = []
        for node, node_data in G.nodes(data=True):
            if node_data.get('node_type') in ['port']:
                substations.append((node, node_data))

        # Go through the substations and identify any excess they currently have
        # Share the excess evenly across the battery network
        # Potential future improvements:
        # - Each battery fully filled until excess capacity is gone; could do more evenly
        # - Fill closer batteries first
        for substation, substation_data in substations:
            onhand = get_asin_inventory_in_node(substation_data, self._asin)

            if onhand > 0:
                logger.debug(
                    f"Attempting to store excess of {onhand} ASIN {self._asin} from substation {substation}."
                    )

                # Loop through batteries in the network - fill until excess is used, or batteries full
                for battery, battery_data in batteries:
                    current_inventory = get_asin_inventory_in_node(battery_data, self._asin)
                    max_inventory = get_asin_max_inventory_in_node(battery_data, self._asin)
                    available_capacity = max_inventory - current_inventory - battery_data['incoming']

                    if available_capacity == 0:
                        logger.debug(f'Battery {battery} is already full')
                        continue
                    if available_capacity >= onhand:
                        transfer_amount = onhand
                    else:
                        logger.debug(f'Battery {battery} is going to be filled')
                        transfer_amount = available_capacity

                    onhand -= transfer_amount
                    battery_data['incoming'] += transfer_amount

                    logger.debug(
                        f"Transferring {transfer_amount} of ASIN {self._asin} from substation {substation} to battery {battery}."
                    )

                    action = {
                        'type': 'transfer',
                        'asin': self._asin,
                        'quantity': transfer_amount,
                        'schedule': state['clock'],
                        'origin': substation,
                        'destination': battery
                    }
                    actions.append(action)

            if onhand > 0:
                logger.debug(
                    f"Excess of {onhand} ASIN {self._asin} will remain at substation {substation}."
                )

        if len(actions) == 0:
            logger.debug("No actions taken")

        return actions
