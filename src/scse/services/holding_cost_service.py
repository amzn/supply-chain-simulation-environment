"""
Holding Cost data service
"""

import logging
from scse.api.module import Service
logger = logging.getLogger(__name__)

class HoldingCost(Service):

    def __init__(self, run_parameters):
        logger.debug("initializing HoldingCost service")
        self._asin_list = None
        self._DEFAULT_HOLDING_COST = 0.05

    def get_name(self):
        return "holding_cost_service"

    def reset(self, context):
        logger.debug("resetting holding_cost_service")
        # So we don't have to reload the data every reset
        if context['asin_list'] != self._asin_list:
            self._asin_list = context['asin_list']
            
    def get_holding_cost(self, asin):
        # Check for data entry errors
        if asin not in self._asin_list:
            raise ValueError("Holding Cost query failed: ASIN not in asin_list of environment")

        # Query dict for data
        holding_cost = self._DEFAULT_HOLDING_COST

        return holding_cost