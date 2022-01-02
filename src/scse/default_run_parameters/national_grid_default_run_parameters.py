from dataclasses import dataclass

from scse.default_run_parameters.core_default_run_parameters import CoreRunParameters

@dataclass
class _RunParameters(CoreRunParameters):
    # Override certain core parameters
    run_profile = 'national_grid_profile.json'
    asin_selection = 0  # Use 0 for national grid simulation
    logging_level = 'DEBUG'  # May need to set to critical occassionally
    time_increment = 'half-hourly'

    # Bespoke parameters
    num_batteries = 1
    max_battery_capacity = 50
    battery_penalty = 500
DEFAULT_RUN_PARAMETERS = _RunParameters()
