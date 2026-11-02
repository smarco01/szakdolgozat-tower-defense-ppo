
import argparse

import numpy as np
import pygame as pg
from stable_baselines3 import PPO

import constants as c
from env import TowerDefenseEnv, NUM_ACTIONS
from game import Game
from levels_data import PATHS, TOWER_SPOTS
from heuristic_agent import play_heuristic


def eval_random(num_episodes):
    env = TowerDefenseEnv()
    rewards, levels, wins = [], [], 0
    for ep in range(num_episodes):
        obs, info = env.reset(seed=ep)
        terminated = truncated = False
        total_reward = 0.0
        while not (terminated or truncated):
            action = env.action_space.sample()
            obs, reward, terminated, truncated, info = env.step(action)
            total_reward += reward
        rewards.append(total_reward)
        levels.append(info["level"])
        wins += 1 if info["level"] > c.TOTAL_LEVELS else 0
    env.close()
    return rewards, levels, wins


def eval_heuristic(num_episodes):
    map_image = pg.Surface((c.screen_width, c.screen_height))
    enemy_images = {k: pg.Surface((50, 50)) for k in ("weak", "medium", "strong")}
    turret_spritesheets = [pg.Surface((5 * 64, 100)) for _ in range(c.TURRET_LEVELS)]

    levels, wins, healths = [], 0, []
    for ep in range(num_episodes):
        game = Game(map_image, enemy_images, turret_spritesheets, PATHS, TOWER_SPOTS)
        r = play_heuristic(game)
        levels.append(r["level_reached"])
        healths.append(r["health_left"])
        wins += 1 if r["outcome"] == 1 else 0
    return levels, healths, wins


def eval_ppo(model, num_episodes):
    env = TowerDefenseEnv()
    rewards, levels, wins = [], [], 0
    for ep in range(num_episodes):
        obs, info = env.reset(seed=ep)
        terminated = truncated = False
        total_reward = 0.0
        while not (terminated or truncated):
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            total_reward += reward
        rewards.append(total_reward)
        levels.append(info["level"])
        wins += 1 if info["level"] > c.TOTAL_LEVELS else 0
    env.close()
    return rewards, levels, wins


def main(model_path, num_episodes):
    print(f"Kiertekeles {num_episodes} epizodon...\n")

    print("Veletlenszeru ugynok...")
    r_rewards, r_levels, r_wins = eval_random(num_episodes)

    print("Heurisztikus ugynok...")
    h_levels, h_healths, h_wins = eval_heuristic(num_episodes)

    print(f"PPO-ugynok betoltese ({model_path})...")
    model = PPO.load(model_path)
    p_rewards, p_levels, p_wins = eval_ppo(model, num_episodes)

    print("\n" + "=" * 60)
    print(f"{'':20s} {'gyozelem':>10s} {'atlag szint':>14s} {'atlag reward':>14s}")
    print("-" * 60)
    print(f"{'Veletlenszeru':20s} {r_wins:>7d}/{num_episodes:<3d}"
          f"{np.mean(r_levels):>14.2f} {np.mean(r_rewards):>14.2f}")
    print(f"{'Heurisztikus':20s} {h_wins:>7d}/{num_episodes:<3d}"
          f"{np.mean(h_levels):>14.2f} {'-':>14s}")
    print(f"{'PPO (betanitott)':20s} {p_wins:>7d}/{num_episodes:<3d}"
          f"{np.mean(p_levels):>14.2f} {np.mean(p_rewards):>14.2f}")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", type=str, default="models/ppo_tower_defense")
    parser.add_argument("--episodes", type=int, default=30)
    args = parser.parse_args()

    main(args.model_path, args.episodes)
