
import argparse
import os
import sys


if "--headless" in sys.argv:
    os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame as pg
from stable_baselines3 import PPO

import constants as c
from game import Game
from levels_data import PATHS, TOWER_SPOTS
from ai_common import (
    build_observation, apply_action, action_name, FRAMES_PER_STEP,
    ACTION_START_LEVEL, ACTION_WAIT,
)
from recording import ActionLogger, VideoRecorder, snapshot

END_SCREEN_SECONDS = 2.0


def main(model_path, speed, log_path=None, log_waits=False, record_path=None,
         headless=False, episodes=None):
    if episodes is None:
        episodes = 1 if headless else 0
    auto_restart = episodes > 0

    pg.init()
    clock = pg.time.Clock()
    screen = pg.display.set_mode((c.screen_width + c.side_panel, c.screen_height))
    pg.display.set_caption("Tower Defence -- AI jatszik")

    text_font = pg.font.SysFont("Consolas", 24, bold=True)
    large_font = pg.font.SysFont("Consolas", 36)

    def draw_text(text, x, y, color="grey100"):
        img = text_font.render(text, True, color)
        screen.blit(img, (x, y))

    # -- kepek betoltese, pontosan ugyanugy, mint a main.py-ban --
    map_image = pg.transform.scale(
        pg.image.load("levels/level_snow2.png").convert_alpha(),
        (c.screen_width, c.screen_height),
    )
    turret_spritesheets = [
        pg.image.load(f"assets/images/turrets/canonanim{x}.png").convert_alpha()
        for x in range(1, c.TURRET_LEVELS + 1)
    ]
    enemy_images = {
        "weak": pg.transform.scale(
            pg.image.load("assets/images/enemies/enemyweak.png").convert_alpha(), (50, 50)
        ),
        "medium": pg.transform.scale(
            pg.image.load("assets/images/enemies/snow_enemy_2.png").convert_alpha(), (60, 60)
        ),
        "strong": pg.transform.scale(
            pg.image.load("assets/images/enemies/enemystrong.png").convert_alpha(), (70, 70)
        ),
    }
    panel_image = pg.transform.scale(
        pg.image.load("assets/images/buttons/panel.png").convert_alpha(),
        (c.side_panel, c.screen_height),
    )

    game = Game(map_image, enemy_images, turret_spritesheets, PATHS, TOWER_SPOTS)
    model = PPO.load(model_path)
    print(f"Betanitott modell betoltve: {model_path}")

    logger = ActionLogger(log_path, log_waits) if log_path else None
    recorder = VideoRecorder(record_path, c.fps) if record_path else None
    draw_frames = (not headless) or (recorder is not None)

    last_action_name = "-"
    tick_in_step = 0

    episode = 1
    decision = 0               # az ugynok dontesenek sorszama az aktualis jatekban
    game_over_logged = False
    end_hold_frames = 0
    hold_limit = int(END_SCREEN_SECONDS * c.fps)
    results = []               # egy elem minden befejezett jatekhoz
    stats = {"lerakott": 0, "fejlesztett": 0}

    run = True
    try:
        while run:
            if not headless:
                clock.tick(c.fps * speed)

            if not game.game_over and tick_in_step == 0:
                obs = build_observation(game)
                action, _ = model.predict(obs, deterministic=True)
                last_action_name = action_name(action)
                decision += 1

                action_id = int(action)
                snap = snapshot(game)              # a dontes ELOTTI allapot
                was_started = game.level_started
                placed, upgraded = apply_action(game, action)

                if action_id == ACTION_WAIT:
                    success = True
                elif action_id == ACTION_START_LEVEL:
                    success = (not was_started) and game.level_started
                else:
                    success = placed or upgraded
                stats["lerakott"] += 1 if placed else 0
                stats["fejlesztett"] += 1 if upgraded else 0

                if logger:
                    logger.log_decision(episode, decision, snap, action_id,
                                        last_action_name, success,
                                        is_wait=(action_id == ACTION_WAIT))

            if not game.game_over:
                game.update_frame()
            tick_in_step = (tick_in_step + 1) % FRAMES_PER_STEP

            if game.game_over and not game_over_logged:
                game_over_logged = True
                outcome_text = "GYOZELEM" if game.game_outcome == 1 else "VESZTES"
                if logger:
                    logger.log_game_over(episode, decision, snapshot(game), outcome_text)
                results.append({
                    "jatek": episode,
                    "eredmeny": outcome_text,
                    "szint": game.world.level,
                    "elet": game.world.health,
                    "ido_s": game.world.tick / c.fps,
                    "dontesek": decision,
                    "lerakott": stats["lerakott"],
                    "fejlesztett": stats["fejlesztett"],
                })
                print(f"[{episode}. jatek] {outcome_text} -- szint: {game.world.level}, "
                      f"megmaradt elet: {game.world.health}")

            if draw_frames:
                screen.fill("grey100")
                game.draw(screen)

                screen.blit(panel_image, (c.screen_width, 0))
                draw_text("AI JATSZIK", c.screen_width + 50, 20)
                draw_text("LEVEL: " + str(game.world.level), c.screen_width + 50, 55)
                draw_text("health: " + str(game.world.health), c.screen_width + 50, 80)
                draw_text("money: " + str(game.world.money), c.screen_width + 50, 105)
                draw_text("utolso akcio:", c.screen_width + 50, 145)
                draw_text(last_action_name, c.screen_width + 50, 170)

                if game.game_over:
                    pg.draw.rect(screen, "dodgerblue", (200, 200, 400, 200), border_radius=30)
                    msg = "AZ AI NYERT!" if game.game_outcome == 1 else "AZ AI VESZITETT"
                    img = large_font.render(msg, True, "grey0")
                    screen.blit(img, (250, 230))
                    if not auto_restart:
                        draw_text("nyomj R-t az ujrainditashoz", 220, 280, "grey0")

                if recorder:
                    # pygame: (szelesseg, magassag, 3) -> video: (magassag, szelesseg, 3)
                    recorder.add_frame(pg.surfarray.array3d(screen).swapaxes(0, 1))

            restart = False
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    run = False
                if event.type == pg.KEYDOWN and event.key == pg.K_r and game.game_over:
                    restart = True

            if auto_restart and game.game_over:
                end_hold_frames += 1
                if end_hold_frames >= hold_limit:
                    if episode >= episodes:
                        run = False
                    else:
                        restart = True

            if restart and run:
                game.reset()
                tick_in_step = 0
                last_action_name = "-"
                episode += 1
                decision = 0
                game_over_logged = False
                end_hold_frames = 0
                stats = {"lerakott": 0, "fejlesztett": 0}

            if draw_frames and not headless:
                pg.display.flip()
    finally:
        if recorder:
            recorder.close()
        if logger:
            logger.close()
        pg.quit()

    print_summary(results, log_path, logger, record_path, recorder)


def print_summary(results, log_path, logger, record_path, recorder):
    if results:
        print("\n" + "=" * 72)
        print(f"{'jatek':>6} {'eredmeny':>10} {'szint':>6} {'elet':>5} {'ido (s)':>8} "
              f"{'dontes':>7} {'torony':>7} {'fejl.':>6}")
        print("-" * 72)
        for r in results:
            print(f"{r['jatek']:>6} {r['eredmeny']:>10} {r['szint']:>6} {r['elet']:>5} "
                  f"{r['ido_s']:>8.1f} {r['dontesek']:>7} {r['lerakott']:>7} "
                  f"{r['fejlesztett']:>6}")
        print("=" * 72)
    else:
        print("\nEgy jatek sem ert veget (az ablak ido elott be lett zarva).")
    if logger:
        print(f"Akcionaplo mentve: {log_path} ({logger.rows_written} sor)")
    if recorder:
        print(f"Videofelvetel mentve: {record_path} ({recorder.frames} kepkocka, "
              f"{recorder.frames / c.fps:.1f} mp)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", type=str, default="models/best_model",
                         help="A betoltendo modell utvonala (kiterjesztes nelkul)")
    parser.add_argument("--speed", type=float, default=1.0,
                         help="Sebesseg-szorzo (1.0 = normal, 2.0 = 2x gyorsabb, "
                              "0.5 = felsebesseg)")
    parser.add_argument("--log", type=str, default=None, metavar="FAJL.csv",
                         help="Az AI donteseinek mentese CSV-fajlba (Excelben nyithato)")
    parser.add_argument("--log-waits", action="store_true",
                         help="A 'varakozas' donteseket is irja a naploba (alapbol kihagyja)")
    parser.add_argument("--record", type=str, default=None, metavar="FAJL.mp4",
                         help="Videofelvetel mentese MP4-be (imageio + imageio-ffmpeg kell)")
    parser.add_argument("--headless", action="store_true",
                         help="Ablak nelkul fut, a lehetseges leggyorsabban "
                              "(a videofelvetel igy is valos sebessegu)")
    parser.add_argument("--episodes", type=int, default=None,
                         help="Ennyi jatek utan kilep (alapertelmezes: ablakos modban "
                              "a bezarasig fut, --headless modban 1 jatek)")
    args = parser.parse_args()
    main(args.model_path, args.speed, args.log, args.log_waits, args.record,
         args.headless, args.episodes)
