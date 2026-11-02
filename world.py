import pygame as pg
import random
from enemy_data import ENEMY_SPAWN_DATA
import constants as c

class World():
    def __init__(self, map_image):
        self.level = 1
        self.health = c.HEALTH
        self.money = c.MONEY
        self.image = map_image
        self.enemy_list = []
        self.spawned_enemies = 0
        self.killed_enemies = 0
        self.missed_enemies = 0

        self.tick = 0

    def advance_tick(self):
        self.tick += 1

    def process_enemies(self):
        enemies = ENEMY_SPAWN_DATA[self.level-1]
        for enemy_type in enemies:
            enemies_to_spawn = enemies[enemy_type]
            for enemy in range(enemies_to_spawn):
                self.enemy_list.append(enemy_type)
        #now randomize list to shuffle enemies
        random.shuffle(self.enemy_list)

    def check_level_complete(self):
        if (self.killed_enemies + self.missed_enemies) == len(self.enemy_list):
            return True


    def reset_level(self):
        #reset enemy variales
        self.enemy_list = []
        self.spawned_enemies = 0
        self.killed_enemies = 0
        self.missed_enemies = 0

    def draw(self, surface):
        surface.blit(self.image, (0,0))
