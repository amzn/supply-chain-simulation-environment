import logging
import math

from scse.api.module import Agent
from scse.api.network import (
    get_asin_inventory_in_node, get_asin_max_inventory_in_node
)
from scse.constants.national_grid_constants import (
    ELECTRICITY_ASIN, DEFAULT_BALANCE_SINK
)

logger = logging.getLogger(__name__)


class BalanceExcessSupply(Agent):
    _DEFAULT_ASIN = ELECTRICITY_ASIN
    _DEFAULT_BALANCE_SINK = DEFAULT_BALANCE_SINK

    def __init__(self, run_parameters):
        """
        Dispose of excess supply, via designated sink, to ensure 
        the network is not oversupplied.

        As with a number of other modules, only the `electricity`
        ASIN is being considered at this time.

        NOTE: If considering batteries, this module must be executed
        after excess supply is sent to storage, else everything will
        be sent to the sink.

        NOTE: This module does not consider the forecasted demand
        in the next timestep - substations have no storage capacity,
        and so must deposit excess into the sink.
        """
        self._asin = self._DEFAULT_ASIN
        self._balance_sink = self._DEFAULT_BALANCE_SINK

    def reset(self, context, state):
        self._asin_list = context['asin_list']

    def get_name(self):
        return 'balance_excess_supply'

    def compute_actions(self, state):
        G = state['network']
        actions = []

        # Go through the substations and identify any excess
        # Send all excess to balance sink
        # Remember that substations currently have the node type `port`
        for node, node_data in G.nodes(data=True):
            if node_data.get('node_type') in ['port']:
                onhand = get_asin_inventory_in_node(node_data, self._asin)

                if onhand > 0:
                    logger.debug(
                        f"Disposing excess of {onhand} ASIN {self._asin} from substation {node}."
                    )

                    action = {
                        'type': 'outbound_shipment',
                        'asin': self._asin,
                        'quantity': onhand,
                        'schedule': state['clock'],
                        'origin': node,
                        'destination': self._balance_sink
                    }
                    actions.append(action)

        if len(actions) == 0:
            logger.debug("No actions taken")

        return actions
