from dataclasses import dataclass

@dataclass
class CoreRunParameters:
    run_profile = ''
    asin_selection = 1
    logging_level = 'DEBUG'
    start_date = '2019-01-01'
    time_increment = 'daily'
    time_horizon = 100
    simulation_seed = 12345
CORE_DEFAULT_RUN_PARAMETERS = CoreRunParameters()
