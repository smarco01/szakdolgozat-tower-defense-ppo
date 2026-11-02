import os


os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import numpy as np
import pygame as pg
import gymnasium as gym
from gymnasium import spaces

import constants as c
from game import Game
from levels_data import PATHS, TOWER_SPOTS
from ai_common import (
    NUM_SPOTS,
    NUM_PATHS,
    ACTION_START_LEVEL,
    ACTION_WAIT,
    NUM_ACTIONS,
    FRAMES_PER_STEP,
    build_observation,
    apply_action,
)


MAX_STEPS = 20_000

STREAK_BONUS = 0.5

STREAK_CAP = 4


def _load_assets():
    pg.init()
    pg.display.set_mode((1, 1))

    def load_or_placeholder(path, size):
        if os.path.exists(path):
            img = pg.image.load(path).convert_alpha()
            return pg.transform.scale(img, size)
        surf = pg.Surface(size, pg.SRCALPHA)
        surf.fill((120, 120, 120, 255))
        return surf

    map_image = load_or_placeholder("levels/level_snow2.png", (c.screen_width, c.screen_height))

    turret_spritesheets = []
    for x in range(1, c.TURRET_LEVELS + 1):
        turret_spritesheets.append(
            load_or_placeholder(f"assets/images/turrets/canonanim{x}.png", (5 * 64, 100))
        )

    enemy_images = {
        "weak": load_or_placeholder("assets/images/enemies/enemyweak.png", (50, 50)),
        "medium": load_or_placeholder("assets/images/enemies/snow_enemy_2.png", (60, 60)),
        "strong": load_or_placeholder("assets/images/enemies/enemystrong.png", (70, 70)),
    }

    return map_image, enemy_images, turret_spritesheets


class TowerDefenseEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(self):
        super().__init__()
        map_image, enemy_images, turret_spritesheets = _load_assets()
        self.game = Game(map_image, enemy_images, turret_spritesheets, PATHS, TOWER_SPOTS)

        self.action_space = spaces.Discrete(NUM_ACTIONS)
        obs_len = 5 + NUM_SPOTS * 2 + NUM_PATHS
        self.observation_space = spaces.Box(low=0.0, high=1.0, shape=(obs_len,), dtype=np.float32)

        self._steps = 0
        self._prev_killed = 0
        self._prev_missed = 0
        self._prev_level = 1
        self._streak = 0

    # ------------------------------------------------------------------
    def _get_obs(self):
        return build_observation(self.game)

    def _get_info(self):
        return {
            "level": self.game.world.level,
            "health": self.game.world.health,
            "money": self.game.world.money,
            "killed_enemies": self.game.world.killed_enemies,
            "missed_enemies": self.game.world.missed_enemies,
        }

    # ------------------------------------------------------------------
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.game.reset()
        self._steps = 0
        self._prev_killed = 0
        self._prev_missed = 0
        self._prev_level = 1
        self._streak = 0
        return self._get_obs(), self._get_info()

    def step(self, action):
        action = int(action)
        reward = 0.0

        placed, upgraded = apply_action(self.game, action)
        if placed:
            reward += 0.2
        if upgraded:
            reward += 0.1

        # --- szimulacio elorepergetese ---
        for _ in range(FRAMES_PER_STEP):
            self.game.update_frame()
            self._steps += 1
            if self.game.game_over:
                break

        # --- jutalom szamitasa ---
        w = self.game.world
        killed_delta = w.killed_enemies - self._prev_killed
        missed_delta = w.missed_enemies - self._prev_missed
        level_delta = w.level - self._prev_level

        reward += killed_delta * 1.0
        reward -= missed_delta * 2.0
        reward += level_delta * 5.0

        if missed_delta > 0:
            self._streak = 0
        if level_delta > 0:
            reward += min(self._streak, STREAK_CAP) * STREAK_BONUS * level_delta
            self._streak += level_delta

        if not self.game.level_started:
            reward -= 0.01

        self._prev_killed = w.killed_enemies
        self._prev_missed = w.missed_enemies
        self._prev_level = w.level

        terminated = self.game.game_over
        if terminated:
            if self.game.game_outcome == 1:
                reward += 100.0
            elif self.game.game_outcome == -1:
                reward -= 20.0

        truncated = self._steps >= MAX_STEPS

        return self._get_obs(), reward, terminated, truncated, self._get_info()

    def close(self):
        pg.quit()
