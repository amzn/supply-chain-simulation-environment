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
    num_batteries = 25

    # for now, assumes all batteries are of same capacity
    # TODO: modify to handle capacity which scales with cost

    '''
    potential battery types:
    - tesla's megapack (£735916.40, capacity = 15 MWh)
        - https://electrek.co/2020/07/06/tesla-deploys-megapack-autobidder/
        - https://electrek.co/2021/07/26/tesla-reveals-megapack-prices/
    '''
    max_battery_capacity = 15  #  units in MWh
    init_battery_capacity = int(max_battery_capacity * 0.2)
    battery_penalty = 735916.40  # units in £s

DEFAULT_RUN_PARAMETERS = _RunParameters()
