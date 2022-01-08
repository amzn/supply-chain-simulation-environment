from dataclasses import dataclass

from scse.default_run_parameters.core_default_run_parameters import CoreRunParameters


@dataclass
class _RunParameters(CoreRunParameters):
    # Override certain core parameters
    run_profile = 'national_grid_profile'
    asin_selection = 0  # Use 0 for national grid simulation
    logging_level = 'DEBUG'  #  May need to set to critical occassionally
    time_increment = 'half-hourly'
    time_horizon = 336  #  1 week, if 30 min time increments

    # Bespoke parameters
    simulation_logging_level = 'CRITICAL'
    num_batteries = 1
    max_battery_capacity = 50
    battery_penalty = 5000


DEFAULT_RUN_PARAMETERS = _RunParameters()
