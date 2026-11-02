import pygame as pg
import constants as c
from button import Button
from game import Game
from levels_data import WAYPOINTS, WAYPOINTS_GREEN, WAYPOINTS_BLUE, PATHS, TOWER_SPOTS

#initialise pygame
pg.init()

#clock
clock = pg.time.Clock()

#create game window
screen = pg.display.set_mode((c.screen_width + c.side_panel, c.screen_height))
pg.display.set_caption("Tower Defence")

#UI allapot (ez csak a megjeleniteshez kell, a jatek logikaja a Game-ben van)
placing_turrets = False

# DEBUG NEZET: a 'D' billentyuvel kapcsolhato be/ki. Kirajzolja az
# utvonalat es az osszes toronyhelyet (sorszammal egyutt), hogy
# latvanyosan ellenorizni lehessen, hogy uj/modositott koordinatak
# tenyleg jo helyre esnek-e a valodi (fakkal, sziklakkal kirajzolt)
# palyan. Jobb egerkattintasra (barmikor, debug nezet nelkul is)
# kiirja a konzolra a kattintott pixel-koordinatat -- ezzel lehet
# pl. egy uj utvonal pontjait "lekattintgatni" es atmasolni a
# levels_data.py-ba.
debug_mode = False

#load images
#map
map_image = pg.image.load('levels/level_snow2.png').convert_alpha()
#turret spritesheets
turret_spritesheets = []
for x in range(1, c.TURRET_LEVELS+1):
    turret_sheet = pg.image.load(f'assets/images/turrets/canonanim{x}.png').convert_alpha()
    turret_spritesheets.append(turret_sheet)

#turret image for mouse cursor
cursor_turret = pg.image.load('assets/images/turrets/canon.png').convert_alpha()
#enemy
enemy_images = {
    "weak" : pg.transform.scale(
        pg.image.load("assets/images/enemies/enemyweak.png").convert_alpha(),
        (50, 50)
    ),
    "medium" : pg.transform.scale(
        pg.image.load("assets/images/enemies/snow_enemy_2.png").convert_alpha(),
        (60, 60)
    ),
    "strong" : pg.transform.scale(
        pg.image.load("assets/images/enemies/enemystrong.png").convert_alpha(),
        (70, 70)
    )
}

#buttons
buy_turret_image = pg.image.load('assets/images/buttons/buy_turret.png').convert_alpha()
cancel_image = pg.image.load('assets/images/buttons/cancel.png').convert_alpha()
upgrade_turret_image = pg.image.load('assets/images/buttons/upgrade_turret.png').convert_alpha()
begin_image = pg.image.load('assets/images/buttons/start.png').convert_alpha()
restart_image = pg.image.load('assets/images/buttons/restart.png').convert_alpha()
fast_forward_image = pg.image.load('assets/images/buttons/fastforward.png').convert_alpha()
panel_image = pg.image.load('assets/images/buttons/panel.png').convert_alpha()
#image scale
cursor_turret = pg.transform.scale(cursor_turret, (80, 80))
map_image = pg.transform.scale(map_image, (c.screen_width, c.screen_height))
buy_turret_image = pg.transform.scale(buy_turret_image, (270, 210))
cancel_image = pg.transform.scale(cancel_image, (270, 210))
upgrade_turret_image = pg.transform.scale(upgrade_turret_image, (270, 210))
begin_image = pg.transform.scale(begin_image, (280, 180))
restart_image = pg.transform.scale(restart_image, (300, 200))
panel_image = pg.transform.scale(panel_image, (c.side_panel, c.screen_height))

#load fonts for text on screen
text_font = pg.font.SysFont("Consolas", 24, bold = True)
large_font = pg.font.SysFont("Consolas", 36)

#function for outputting text onto the screen
def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img,(x, y))

def display_data():
    screen.blit(panel_image, (c.screen_width, 0))

    draw_text("LEVEL: " + str(game.world.level), text_font, "grey100", c.screen_width + 50, 45)
    draw_text("health: "+str(game.world.health), text_font, "grey100", c.screen_width + 50, 70)
    draw_text("money: "+str(game.world.money), text_font, "grey100", c.screen_width + 50, 95)

def get_tower_spot_index(mouse_pos):
    for i, spot in enumerate(TOWER_SPOTS):
        dx = mouse_pos[0] - spot[0]
        dy = mouse_pos[1] - spot[1]
        distance = (dx ** 2 + dy ** 2) ** 0.5
        if distance < 30:  # kattintasi sugar
            return i
    return None


#letrehozzuk a kozos jatek-objektumot (ugyanez fut az AI oldalan is, env.py-ban)
game = Game(map_image, enemy_images, turret_spritesheets, PATHS, TOWER_SPOTS)

#create buttons
turret_button = Button(c.screen_width+14,300, buy_turret_image, True)
cancel_button = Button(c.screen_width+14,400, cancel_image, True)
upgrade_turret_button = Button(c.screen_width+14,500, upgrade_turret_image, True)
start_button = Button(c.screen_width+10,200, begin_image, True)
restart_button = Button(250,250, restart_image, True)

#game loop
run = True
while run:

    clock.tick(c.fps)

    screen.fill("grey100")

    #egy szimulacios lepes (a teljes jatekszabaly a game.py-ban van)
    game.update_frame()

    #draw level + sprites
    game.draw(screen)

    #kijelolt torony kiemelese (a .selected flaget mar a Game allitja be)

    if debug_mode:
        path_colors = ["yellow", "lime", "deepskyblue"]
        for path, color in zip(PATHS, path_colors):
            pg.draw.lines(screen, color, False, path, 2)
        for i, spot in enumerate(TOWER_SPOTS):
            pg.draw.circle(screen, "magenta", spot, 30, 2)
            pg.draw.circle(screen, "magenta", spot, 3)
            draw_text(str(i), text_font, "white", spot[0] - 6, spot[1] - 10)

    display_data()

    if game.game_over == False:
        #check if the level has been started
        if game.level_started == False:
            if start_button.draw(screen):
                game.start_level()

        #draw buttons
        #button for turret
        draw_text(str(c.BUY_COST) + " Coins", text_font, "grey100", c.screen_width+95, 430)
        if turret_button.draw(screen):
            placing_turrets = True
        #if placing turrets then show the cancel button as well
        if placing_turrets == True:
            #show cursor turret
            cursor_rect = cursor_turret.get_rect()
            cursor_pos = pg.mouse.get_pos()
            cursor_rect.center = cursor_pos
            if cursor_pos[0] <= c.screen_width:
                screen.blit(cursor_turret, cursor_rect)

            if cancel_button.draw(screen):
                placing_turrets = False
        #if a turret is selected show upgrade button
        if game.selected_turret:
            #if a turret can be upgarded show button
            if game.selected_turret.upgrade_level < c.TURRET_LEVELS:
                draw_text(str(c.UPGRADE_COST) + " Coins", text_font, "grey100", c.screen_width + 95, 650)
                if upgrade_turret_button.draw(screen):
                    if game.world.money >= c.UPGRADE_COST:
                        game.selected_turret.upgrade()
                        game.world.money -= c.UPGRADE_COST
    else:
        pg.draw.rect(screen, "dodgerblue", (200, 200, 400, 200), border_radius= 30)
        if game.game_outcome == -1:
            draw_text("GAME OVER", large_font, "grey0", 310, 230)
        elif game.game_outcome == 1:
            draw_text("YOU WON", large_font, "grey0", 310, 230)
            #restart level
            if restart_button.draw(screen):
                placing_turrets = False
                game.reset()

    #event handler
    for event in pg.event.get():
        #quit
        if event.type == pg.QUIT:
            run = False
        #debug nezet be/ki
        if event.type == pg.KEYDOWN and event.key == pg.K_d:
            debug_mode = not debug_mode
            print(f"[debug] debug nezet: {'BE' if debug_mode else 'KI'}")
        #jobb kattintas: kiirja a pixel-koordinatat a konzolra
        #(uj utvonal/toronyhely koordinatak "lekattintgatasahoz")
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 3:
            print(f"[debug] kattintas: {pg.mouse.get_pos()}")
        #mouse click
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pg.mouse.get_pos()
            #check is mouse on game area
            if mouse_pos[0] < c.screen_width and mouse_pos[1] < c.screen_height:
                #clear selected turrets
                game.clear_selection()
                if placing_turrets == True:
                    spot_index = get_tower_spot_index(mouse_pos)
                    if spot_index is not None:
                        game.place_turret(spot_index)
                else:
                    spot_index = get_tower_spot_index(mouse_pos)
                    if spot_index is not None:
                        game.select_turret(spot_index)

    #update display
    pg.display.flip()

pg.quit()
