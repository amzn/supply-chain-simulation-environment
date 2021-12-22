from scse.main.notebook_interface import miniSCOTnotebook

def run_simulation():
    m = miniSCOTnotebook(999, '2019-01-02', 'daily', 5, 5)
    rewards = m.run()
    episode_reward = rewards.get('episode_reward').get('total')

    return episode_reward


if __name__ == "__main__":
    print(run_simulation())

