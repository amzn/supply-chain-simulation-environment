from scse.main.notebook_interface import miniSCOTnotebook

DEFAULT_START_DATE = '2019-01-01'
DEFAULT_TIME_INCREMENT = 'half-hourly'
DEFAULT_HORIZON = 100
DEFAULT_SIMULATION_SEED = 12345
DEFAULT_NUM_BATTERIES = 10


def run_simulation(simulation_seed=DEFAULT_SIMULATION_SEED,
                   start_date=DEFAULT_START_DATE,
                   time_increment=DEFAULT_TIME_INCREMENT,
                   time_horizon=DEFAULT_HORIZON,
                   num_batteries=DEFAULT_NUM_BATTERIES):
    m = miniSCOTnotebook(simulation_seed, start_date, time_increment, time_horizon, num_batteries)
    rewards = m.run()
    episode_reward = rewards.get('episode_reward').get('total')

    return episode_reward
