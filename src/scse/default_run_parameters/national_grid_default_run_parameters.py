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
    max_battery_capacity = 50  # 1000  #  units in MWh
    init_battery_charge_frac = 0.2  # 0.2
    battery_penalty = 200 * 1000 # units in £/MWh
    lifetime_years = 10 # number of years over which price is spread


DEFAULT_RUN_PARAMETERS = _RunParameters()
