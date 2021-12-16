import logging

from scse.api.module import Service
from scse.constants.national_grid_constants import ENERGY_GENERATION_ASINS

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
        """
        Generate a supply forcast for the given ASIN/electricity generation type,
        and the given time.

        NOTE: Given a time, the forecast must be deterministic.
        i.e. the same forecast is returned when the same arguments
        are passed.
        """

        if asin == ENERGY_GENERATION_ASINS.solar:
            if time.hour <= 8 or time.hour >= 18:
                return 0
            else:
                return self._amount
        elif asin == ENERGY_GENERATION_ASINS.wind_onshore:
            return self._amount * 2
        elif asin == ENERGY_GENERATION_ASINS.fossil_gas:
            return self._amount * 3
        else:
            raise ValueError(f"Electricity supply forecast query failed: {asin} not recognised.")
