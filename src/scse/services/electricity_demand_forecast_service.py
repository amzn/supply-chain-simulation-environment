import logging

from scse.api.module import Service
from scse.constants.national_grid_constants import PERIOD_LENGTH_HOURS

logger = logging.getLogger(__name__)


class ElectricityDemandForecast(Service):
    _DEFAULT_AMOUNT = 80  # 40

    def __init__(self, run_parameters):
        """
        Return the forcasted electricity demand, in MWh.
        """
        logger.debug("Initializing electricity demand forecast service.")
        self._amount = self._DEFAULT_AMOUNT

    def get_name(self):
        return "electricity_demand_forecast_service"

    def reset(self, context):
        logger.debug("Resetting electricity demand forecast service.")
        pass

    def get_forecast(self, time):
        """
        Generate a demand forcast for the given time.

        NOTE: Forecast must be in MWh. Use PERIOD_LENGTH_HOURS as the
        conversion factor from MW.

        NOTE: Given a time, the forecast must be deterministic.
        i.e. the same forecast is returned when the same arguments
        are passed.
        """

        # Return the default value
        # TODO: Replace with trained models/emulators which use time
        demand_amount = int(
            (self._amount * int((time.hour*2) + (time.minute/30) + 1))
            * PERIOD_LENGTH_HOURS
        )

        return demand_amount
