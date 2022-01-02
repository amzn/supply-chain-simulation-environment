from scse.main.notebook_interface import miniSCOTnotebook
from scse.default_run_parameters.national_grid_default_run_parameters import DEFAULT_RUN_PARAMETERS

import logging


def run_simulation(logging_level=DEFAULT_RUN_PARAMETERS.simulation_logging_level,
                   simulation_seed=DEFAULT_RUN_PARAMETERS.simulation_seed,
                   start_date=DEFAULT_RUN_PARAMETERS.start_date,
                   time_increment=DEFAULT_RUN_PARAMETERS.time_increment,
                   time_horizon=DEFAULT_RUN_PARAMETERS.time_horizon,
                   num_batteries=DEFAULT_RUN_PARAMETERS.num_batteries,
                   max_battery_capacity=DEFAULT_RUN_PARAMETERS.max_battery_capacity,
                   battery_penalty=DEFAULT_RUN_PARAMETERS.battery_penalty):

    logger = logging.getLogger()
    if logging_level == 'DEBUG':
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.CRITICAL)

    m = miniSCOTnotebook(simulation_seed, start_date, time_increment,
                         time_horizon, num_batteries, max_battery_capacity,
                         battery_penalty)
    cum_reward = m.run()

    return cum_reward


# Leaving this here to make testing run_simulation easy
if __name__ == '__main__':
    # Print the final reward from the simulation
    print(run_simulation()[-1])
