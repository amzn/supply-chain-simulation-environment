"""
Selection for Newsvendor Demo
"""
from scse.api.module import Env
import logging

logger = logging.getLogger(__name__)


class SimpleSelectionAgent(Env):
    def __init__(self, run_parameters):
        self._asin_selection = run_parameters['asin_selection']

    def get_name(self):
        return 'asin_list'

    def get_context(self):
        if isinstance(self._asin_selection, list):
            asin_list = self._asin_selection
        elif isinstance(self._asin_selection, int):
            if self._asin_selection == 1:
                asin_list = ["9780465024759"]
            else:
                raise ValueError("Newsvendor demo only supports a single ASIN")
        else:
            raise ValueError("Newsvendor demo selection reqires list (e.g. ['9780465024759']) or int (e.g. 1) asin_selection run parameter")

        logger.debug("asins selected = {}".format(asin_list))
        return asin_list