

import pygame as pg
import constants as c
from enemy import Enemy
from world import World
from turret import Turret


class Game:
    def __init__(self, map_image, enemy_images, turret_spritesheets, paths, tower_spots):
        self.enemy_images = enemy_images
        self.turret_spritesheets = turret_spritesheets
        self.paths = paths
        self.tower_spots = tower_spots
        self.map_image = map_image

        self.reset()

    def reset(self):
        """Uj jatek kezdese (uj World, ures csoportok, alapallapot)."""
        self.world = World(self.map_image)
        self.world.process_enemies()

        self.enemy_group = pg.sprite.Group()
        self.turret_group = pg.sprite.Group()

        self.game_over = False
        self.game_outcome = 0  # -1 vereseg / 1 gyozelem
        self.level_started = False
        self.last_enemy_spawn = 0  # world.tick ertek
        self.selected_turret = None
        # korbe-osztashoz (round-robin): melyik utvonal jon legkozelebb
        self._next_path_index = 0


    def start_level(self):
        """Hullam elinditasa, ha meg nem fut."""
        if not self.level_started and not self.game_over:
            self.level_started = True
            self.last_enemy_spawn = self.world.tick
            return True
        return False

    def get_turret_at_spot(self, spot_index):
        tile_x = self.tower_spots[spot_index][0] // c.TILE_SIZE
        tile_y = self.tower_spots[spot_index][1] // c.TILE_SIZE
        for turret in self.turret_group:
            if (turret.tile_x, turret.tile_y) == (tile_x, tile_y):
                return turret
        return None

    def can_place_turret(self, spot_index):
        if self.game_over:
            return False
        if self.world.money < c.BUY_COST:
            return False
        if self.get_turret_at_spot(spot_index) is not None:
            return False
        return True

    def place_turret(self, spot_index):
        """Torony lerakasa a spot_index. helyre. Visszaadja, hogy sikerult-e."""
        if not self.can_place_turret(spot_index):
            return False

        pos = self.tower_spots[spot_index]
        tile_x = pos[0] // c.TILE_SIZE
        tile_y = pos[1] // c.TILE_SIZE

        turret = Turret(self.turret_spritesheets, pos, tile_x, tile_y, self.world)
        self.turret_group.add(turret)
        self.world.money -= c.BUY_COST
        return True

    def can_upgrade(self, spot_index):
        if self.game_over:
            return False
        turret = self.get_turret_at_spot(spot_index)
        if turret is None:
            return False
        if turret.upgrade_level >= c.TURRET_LEVELS:
            return False
        if self.world.money < c.UPGRADE_COST:
            return False
        return True

    def upgrade_turret(self, spot_index):
        if not self.can_upgrade(spot_index):
            return False
        turret = self.get_turret_at_spot(spot_index)
        turret.upgrade()
        self.world.money -= c.UPGRADE_COST
        return True

    def select_turret(self, spot_index):
        self.clear_selection()
        turret = self.get_turret_at_spot(spot_index)
        self.selected_turret = turret
        if turret:
            turret.selected = True
        return turret

    def clear_selection(self):
        for turret in self.turret_group:
            turret.selected = False
        self.selected_turret = None


    def update_frame(self):
        self.world.advance_tick()

        if self.game_over:
            return

        # vereseg / gyozelem ellenorzese
        if self.world.health <= 0:
            self.game_over = True
            self.game_outcome = -1
            return
        if self.world.level > c.TOTAL_LEVELS:
            self.game_over = True
            self.game_outcome = 1
            return

        self.enemy_group.update(self.world)
        self.turret_group.update(self.enemy_group, self.world)

        if self.level_started:
            spawn_cooldown_ms_elapsed = (self.world.tick - self.last_enemy_spawn) * c.MS_PER_TICK
            if spawn_cooldown_ms_elapsed > c.SPAWN_COOLDOWN:
                if self.world.spawned_enemies < len(self.world.enemy_list):
                    enemy_type = self.world.enemy_list[self.world.spawned_enemies]
                    path = self.paths[self._next_path_index % len(self.paths)]
                    self._next_path_index += 1
                    enemy = Enemy(enemy_type, path, self.enemy_images)
                    self.enemy_group.add(enemy)
                    self.world.spawned_enemies += 1
                    self.last_enemy_spawn = self.world.tick

        if self.world.check_level_complete():
            self.world.money += c.LEVEL_COMPLETE_REWARD
            self.world.level += 1
            self.level_started = False
            self.last_enemy_spawn = self.world.tick
            self.world.reset_level()
            if self.world.level > c.TOTAL_LEVELS:
                self.game_over = True
                self.game_outcome = 1
            else:
                self.world.process_enemies()



    def draw(self, surface):
        self.world.draw(surface)
        self.enemy_group.draw(surface)
        for turret in self.turret_group:
            turret.draw(surface)
