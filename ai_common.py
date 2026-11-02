import numpy as np

import constants as c
from levels_data import PATHS, TOWER_SPOTS

NUM_SPOTS = len(TOWER_SPOTS)
NUM_PATHS = len(PATHS)

# akciok:
#   0 .. NUM_SPOTS-1                -> torony lerakasa a spot_index helyre
#   NUM_SPOTS .. 2*NUM_SPOTS-1      -> torony fejlesztese a (spot_index - NUM_SPOTS) helyen
#   2*NUM_SPOTS                     -> hullam inditasa
#   2*NUM_SPOTS + 1                 -> varakozas (nem csinal semmit ebben a lepesben)
ACTION_START_LEVEL = 2 * NUM_SPOTS
ACTION_WAIT = 2 * NUM_SPOTS + 1
NUM_ACTIONS = 2 * NUM_SPOTS + 2

FRAMES_PER_STEP = 10


def build_observation(game):
    w = game.world
    obs = [
        w.health / c.HEALTH,
        min(w.money / 2000.0, 1.0),
        w.level / c.TOTAL_LEVELS,
        1.0 if game.level_started else 0.0,
        min(len(game.enemy_group) / 50.0, 1.0),
    ]
    for spot_index in range(NUM_SPOTS):
        turret = game.get_turret_at_spot(spot_index)
        if turret is None:
            obs.append(0.0)
            obs.append(0.0)
        else:
            obs.append(1.0)
            obs.append(turret.upgrade_level / c.TURRET_LEVELS)


    for path in game.paths:
        count = sum(1 for e in game.enemy_group if e.waypoints is path)
        obs.append(min(count / 20.0, 1.0))

    return np.array(obs, dtype=np.float32)


def apply_action(game, action):
    action = int(action)
    placed = False
    upgraded = False
    if action < NUM_SPOTS:
        placed = game.place_turret(action)
    elif action < 2 * NUM_SPOTS:
        upgraded = game.upgrade_turret(action - NUM_SPOTS)
    elif action == ACTION_START_LEVEL:
        game.start_level()
    elif action == ACTION_WAIT:
        pass
    return placed, upgraded


def action_name(action):

    action = int(action)
    if action < NUM_SPOTS:
        return f"torony lerakasa (#{action} hely)"
    if action < 2 * NUM_SPOTS:
        return f"torony fejlesztese (#{action - NUM_SPOTS} hely)"
    if action == ACTION_START_LEVEL:
        return "HULLAM INDITASA"
    return "varakozas"
