import logging

from scse.api.module import Env

logger = logging.getLogger(__name__)


class SourcesSelectionAgent(Env):
    def __init__(self, run_parameters):
        """
        Types of electricity generation being modelled.
        """
        self._asin_selection = run_parameters['asin_selection']

    def get_name(self):
        return 'asin_list'

    def get_context(self):
        if isinstance(self._asin_selection, list):
            asin_list = self._asin_selection
        elif isinstance(self._asin_selection, int):
            if self._asin_selection == 0:
                # Default to return all supported electricity source types
                asin_list = [
                    "solar",
                    "wind_onshore",
                    "fossil_gas",
                ]
            else:
                raise ValueError("""
                National Grid profile does not accept selecting a subset of electricity
                sources - set asin_selection run parameter to 0.
                """)
        else:
            raise ValueError("""
            National Grid profile selection reqires list (e.g. ['solar']) or 0 
            asin_selection run parameter.
            """)

        # Add generic "electricity" to list
        # This is what substations (aka ports) and batteries (aka warehouses) deal in
        asin_list.append("electricity")

        logger.debug(f"Electricity sources selected = {asin_list}.")
        return asin_list
