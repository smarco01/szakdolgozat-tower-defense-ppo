

import numpy as np
from env import TowerDefenseEnv


def run_episode(env, seed=None):
    obs, info = env.reset(seed=seed)
    total_reward = 0.0
    terminated = truncated = False
    while not (terminated or truncated):
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
        total_reward += reward
    return total_reward, info


def main(num_episodes=20):
    env = TowerDefenseEnv()
    rewards = []
    levels = []
    for ep in range(num_episodes):
        total_reward, info = run_episode(env, seed=ep)
        rewards.append(total_reward)
        levels.append(info["level"])
        print(f"epizod {ep+1:2d}: reward={total_reward:8.2f}  elert szint={info['level']}")

    print("-" * 40)
    print(f"atlagos reward:       {np.mean(rewards):.2f}")
    print(f"atlagosan elert szint: {np.mean(levels):.2f}")
    env.close()


if __name__ == "__main__":
    main()
