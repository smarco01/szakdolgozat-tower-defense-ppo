
import constants as c


def play_heuristic(game, max_ticks=2_000_000, verbose=False):
    num_spots = len(game.tower_spots)
    tick_count = 0

    while not game.game_over and tick_count < max_ticks:
        acted = False
        for spot in range(num_spots):
            if game.can_place_turret(spot):
                game.place_turret(spot)
                acted = True
                break
        if not acted:
            # fejlesszuk a legalacsonyabb szintu tornyot, ha van penz
            upgrade_candidates = [
                t for t in game.turret_group if t.upgrade_level < c.TURRET_LEVELS
            ]
            upgrade_candidates.sort(key=lambda t: t.upgrade_level)
            for t in upgrade_candidates:
                spot = None
                for s in range(num_spots):
                    other = game.get_turret_at_spot(s)
                    if other is t:
                        spot = s
                        break
                if spot is not None and game.can_upgrade(spot):
                    game.upgrade_turret(spot)
                    break

        if not game.level_started:
            game.start_level()

        game.update_frame()
        tick_count += 1

        if verbose and tick_count % 500 == 0:
            print(f"  tick={tick_count} level={game.world.level} "
                  f"health={game.world.health} money={game.world.money}")

    return {
        "ticks": tick_count,
        "level_reached": game.world.level,
        "health_left": game.world.health,
        "outcome": game.game_outcome,
        "killed": game.world.killed_enemies,
        "missed": game.world.missed_enemies,
    }
