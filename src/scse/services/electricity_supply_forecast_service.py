import os
import logging
import datetime

import numpy as np
import GPy

from scse.api.module import Service
from scse.constants.national_grid_constants import (
    ENERGY_GENERATION_ASINS, PERIOD_LENGTH_HOURS
)

logger = logging.getLogger(__name__)


class ElectricitySupplyForecast(Service):
    _DEFAULT_BMRS_SOURCE = 'combined'

    def __init__(self, run_parameters):
        """
        Return the forcasted electricity supply, in MWh.
        """
        logger.debug("Initializing electricity supply forecast service.")
        self._asin_list = None
        self._bmrs_source = self._DEFAULT_BMRS_SOURCE

    def get_name(self):
        return "electricity_supply_forecast_service"

    def reset(self, context):
        logger.debug("Resetting electricity supply forecast service.")
        # So we don't have to reload the data every reset
        if self._asin_list != context['asin_list']:
            self._asin_list = context['asin_list']
            
    def get_forecast(self, asin, clock, time):
        """
        Generate a supply forcast for the given ASIN/electricity generation
        type, and the given time.

        NOTE: Forecast must be in MWh. Use PERIOD_LENGTH_HOURS as the
        conversion factor from MW.

        NOTE: Given a time, the forecast must be deterministic.
        i.e. the same forecast is returned when the same arguments
        are passed.
        """

        # Determine which period of the day is being considered
        # Date information is not yet being used
        period_of_day = int((time.hour*2) + (time.minute/30))

        # Determine the path to the model pickle based on the ASIN
        file_dir = (os.path.dirname(os.path.realpath(__file__)))
        model_dir = os.path.join(file_dir, "bmrs_models")
        gpy_model_pkl = os.path.join(
            model_dir,
            f"supply_{self._bmrs_source}_{asin.lower().replace(' ', '_')}.pkl"
        )

        # Check that the model pickle does exist
        if not os.path.isfile(gpy_model_pkl):
            raise FileNotFoundError(
                f"Could not find supply model for: {asin}."
            )

        # Load the model pickle
        m = GPy.load(gpy_model_pkl)

        # Set random seed based on the timestamp passed.
        # This ensures predictions are deterministic given the
        # ASIN and timestamp passed.
        ref_date = datetime.date(year=2015, month=1, day=1)
        seed = ((time.date() - ref_date).days * 48) + period_of_day
        np.random.seed(seed)

        # Use the model to predict supply from the ASIN
        mw_mean, mw_var = m.predict(np.array([period_of_day])[:, None])
        mw_prediction = np.random.normal(
            loc=mw_mean[0][0],
            scale=np.sqrt(mw_var[0][0]),
            size=1
        )[0]

        # Convert the MW prediction to MWhs
        mwh_prediction = int(np.floor(mw_prediction * PERIOD_LENGTH_HOURS))

        # Not impossible to obtain negative predictions
        # Return 0 if the prediction is negative
        return max(mwh_prediction, 0)
