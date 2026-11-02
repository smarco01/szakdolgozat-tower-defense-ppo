import pygame as pg
from pygame.math import Vector2
import math
import constants as c
from enemy_data import ENEMY_DATA

class Enemy(pg.sprite.Sprite):
    def __init__(self, enemy_type, waypoints, images):
        pg.sprite.Sprite.__init__(self)
        self.waypoints = waypoints
        self.pos = Vector2(self.waypoints[0])
        self.target_waypoint = 1
        self.health = ENEMY_DATA.get(enemy_type)["health"]
        self.speed = ENEMY_DATA.get(enemy_type)["speed"]
        self.original_image = images.get(enemy_type)
        self.image_left = images.get(enemy_type)
        self.image_right = pg.transform.flip(images.get(enemy_type), True, False)

        self.facing_right = True
        self.image = self.image_right
        self.rect = self.image.get_rect()
        self.rect.center = self.pos

    def update(self, world):
        self.move(world)
        self.check_alive(world)


    def move(self, world):
        #define target wp
        if self.target_waypoint < len(self.waypoints):
            self.target = Vector2(self.waypoints[self.target_waypoint])
            self.movement = self.target - self.pos
            if self.movement.x > 0:
                self.facing_right = True
                self.image = self.image_right
            elif self.movement.x < 0:
                self.facing_right = False
                self.image = self.image_left
        else:
            #enemy has reached the end of the path
            self.kill()
            world.health -= 1
            world.missed_enemies += 1

        #calculate distance to target
        dist = self.movement.length()
        #chec if rem dist > enemy speed
        if dist >= self.speed:
            self.pos += self.movement.normalize() * self.speed
        else:
            if dist != 0:
                self.pos += self.movement.normalize() * dist
            self.target_waypoint += 1
        self.rect = self.image.get_rect()
        self.rect.center = self.pos


    def check_alive(self, world):
        if self.health <= 0:
            world.killed_enemies += 1
            world.money += c.KILL_REWARD
            self.kill()
