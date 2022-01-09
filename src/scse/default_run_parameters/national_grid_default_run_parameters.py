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
    num_batteries = 1  # 5

    # Penalty and reward prices, w/ units £/MWh
    source_request_reward_penalty = -36.65
    sink_deposit_reward_penalty = 27.63
    battery_drawdown_reward_penalty = 36.65
    battery_charging_reward_penalty = -27.63

    # Other penalties
    transfer_penalty = 0  # 2
    lost_demand_penalty = 0
    holding_cost_penalty = 0  # -20

    # for now, assumes all batteries are of same capacity
    # TODO: modify to handle capacity which scales with cost

    '''
    potential battery types:
    - tesla's megapack (£735916.40, capacity = 15 MWh)
        - https://electrek.co/2020/07/06/tesla-deploys-megapack-autobidder/
        - https://electrek.co/2021/07/26/tesla-reveals-megapack-prices/
    '''
    # battery_penalty = 735916.40  # units in £s
    # max_battery_capacity = 15  # 1000  #  units in MWh
    # using stat of ~$150/kWh => ~$150,000/MWh
    battery_penalty = 110387.46  # units in £s
    max_battery_capacity = 1  # 1000  #  units in MWh
    init_battery_capacity = int(max_battery_capacity * 0.2)  # 0.2)


DEFAULT_RUN_PARAMETERS = _RunParameters()
