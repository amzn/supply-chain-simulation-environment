from scse.main.notebook_interface import miniSCOTnotebook
import logging

DEFAULT_LOGGING_LEVEL = 'CRITICAL'
DEFAULT_START_DATE = '2019-01-01'
DEFAULT_TIME_INCREMENT = 'half-hourly'
DEFAULT_HORIZON = 100
DEFAULT_SIMULATION_SEED = 12345
DEFAULT_NUM_BATTERIES = 1
DEFAULT_MAX_BATTERY_CAPACITY = 50
DEFAULT_BATTERY_PENALTY = 500


def run_simulation(logging_level=DEFAULT_LOGGING_LEVEL,
                   simulation_seed=DEFAULT_SIMULATION_SEED,
                   start_date=DEFAULT_START_DATE,
                   time_increment=DEFAULT_TIME_INCREMENT,
                   time_horizon=DEFAULT_HORIZON,
                   num_batteries=DEFAULT_NUM_BATTERIES,
                   max_battery_capacity=DEFAULT_MAX_BATTERY_CAPACITY,
                   battery_penalty=DEFAULT_BATTERY_PENALTY):

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
