import logging

from scse.api.module import Service

logger = logging.getLogger(__name__)


class ElectricityDemandForecast(Service):
    _DEFAULT_AMOUNT = 40

    def __init__(self, run_parameters):
        """
        Return the forcasted electricity demand.
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
        NOTE: Given a time, the forecast must be deterministic.
        i.e. the same forecast is returned when the same arguments
        are passed.
        """

        # Return the default value
        # TODO: Replace with trained models/emulators which use time
        demand_amount = self._amount

        return demand_amount
