import logging

from scse.api.module import Service

logger = logging.getLogger(__name__)


class ElectricitySupplyForecast(Service):
    _DEFAULT_AMOUNT = 10

    def __init__(self, run_parameters):
        """
        Return the forcasted electricity supply.
        """
        logger.debug("Initializing electricity supply forecast service.")
        self._asin_list = None
        self._amount = self._DEFAULT_AMOUNT

    def get_name(self):
        return "electricity_supply_forecast_service"

    def reset(self, context):
        logger.debug("Resetting electricity supply forecast service.")
        # So we don't have to reload the data every reset
        if self._asin_list != context['asin_list']:
            self._asin_list = context['asin_list']
            
    def get_forecast(self, asin, time):
        # Check for data entry errors
        if asin not in self._asin_list:
            raise ValueError(f"Electricity supply forecast query failed: {asin} not in asin_list of environment.")

        # Return the default value
        # TODO: Replace with trained models/emulators which use ASIN and time
        supply_amount = self._amount

        return supply_amount
