from scse.main.notebook_interface import miniSCOTnotebook
import logging

DEFAULT_LOGGING_LEVEL = 'CRITICAL'
DEFAULT_START_DATE = '2019-01-01'
DEFAULT_TIME_INCREMENT = 'half-hourly'
DEFAULT_HORIZON = 5
DEFAULT_SIMULATION_SEED = 12345
DEFAULT_NUM_BATTERIES = 1


def run_simulation(logging_level=DEFAULT_LOGGING_LEVEL,
                   simulation_seed=DEFAULT_SIMULATION_SEED,
                   start_date=DEFAULT_START_DATE,
                   time_increment=DEFAULT_TIME_INCREMENT,
                   time_horizon=DEFAULT_HORIZON,
                   num_batteries=DEFAULT_NUM_BATTERIES):

    logger = logging.getLogger()
    if logging_level == 'DEBUG':
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.CRITICAL)

    m = miniSCOTnotebook(simulation_seed, start_date, time_increment, time_horizon, num_batteries)
    cum_reward = m.run()

    return cum_reward


if __name__ == '__main__':
    run_simulation()
