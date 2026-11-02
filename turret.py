import pygame as pg
import math
import constants
from turret_data import TURRET_DATA


class Turret(pg.sprite.Sprite):
    def __init__(self, sprite_sheets, pos, tile_x, tile_y, world):
        pg.sprite.Sprite.__init__(self)
        self.upgrade_level = 1
        self.range = TURRET_DATA[self.upgrade_level - 1].get("range")
        self.cooldown = TURRET_DATA[self.upgrade_level - 1].get("cooldown")
        self.damage = TURRET_DATA[self.upgrade_level - 1].get("damage")
        # korabban pg.time.get_ticks() -- most a World szimulacios tick
        # szamlaloja adja az "idot", igy fuggetlen a valos oratol
        self.last_shot = world.tick
        self.selected = False
        self.target = None

        #position
        self.tile_x = tile_x
        self.tile_y = tile_y

        #animation
        self.sprite_sheets = sprite_sheets
        self.animation_list = self.load_images(self.sprite_sheets[self.upgrade_level - 1])
        self.frame_index = 0
        self.update_time = world.tick

        #update image
        self.angle = 90
        self.original_image = self.animation_list[self.frame_index]
        self.image = pg.transform.rotate(self.original_image, self.angle)
        self.rect = self.image.get_rect()
        self.rect.center = pos

        #create range circle
        self.range_image = pg.Surface((self.range*2, self.range*2))
        self.range_image.fill((0, 0, 0))
        self.range_image.set_colorkey((0, 0, 0))
        pg.draw.circle(self.range_image, "grey100", (self.range, self.range), self.range)
        self.range_image.set_alpha(100)
        self.range_rect = self.range_image.get_rect()
        self.range_rect.center = self.rect.center

    def load_images(self, sprite_sheet):
        animation_list = []

        frame_count = 5
        frame_width = sprite_sheet.get_width()// frame_count
        frame_height = sprite_sheet.get_height()

        for x in range(frame_count):
            temp_img = sprite_sheet.subsurface(x*frame_width, 0, frame_width, frame_height)
            temp_img = pg.transform.smoothscale(temp_img, (64, 100))
            animation_list.append(temp_img)
        return animation_list

    def update(self, enemy_group, world):
        #if target picked play fire animation
        if self.target:
            self.play_animation(world)
        else:
            #search for new target once turret cooled down
            elapsed_ms = (world.tick - self.last_shot) * constants.MS_PER_TICK
            if elapsed_ms > self.cooldown:
                self.pick_target(enemy_group)

    def pick_target(self, enemy_group):
        #find an enemy target
        x_dist = 0
        y_dist = 0
        #check distance te each enemy to see if it is in range
        for enemy in enemy_group:
            if enemy.health > 0:
                x_dist = enemy.pos[0] - self.rect.centerx
                y_dist = enemy.pos[1] - self.rect.centery
                dist = math.sqrt(x_dist**2 + y_dist**2)
                if dist < self.range:
                    self.target = enemy
                    self.angle = math.degrees(math.atan2(-y_dist,x_dist))
                    #damage enemy
                    self.target.health -= self.damage
                    break


    def play_animation(self, world):
        #update image
        self.original_image = self.animation_list[self.frame_index]
        #check if enough time has passed
        elapsed_ms = (world.tick - self.update_time) * constants.MS_PER_TICK
        if elapsed_ms > constants.ANIMATION_DELAY:
            self.update_time = world.tick
            self.frame_index += 1
            #check if animation is finished and reset
            if self.frame_index >= len(self.animation_list):
                self.frame_index = 0
                #record completed time and clear target
                self.last_shot = world.tick
                self.target = None

    def upgrade(self):
        self.upgrade_level += 1
        self.range = TURRET_DATA[self.upgrade_level - 1].get("range")
        self.cooldown = TURRET_DATA[self.upgrade_level - 1].get("cooldown")
        self.damage = TURRET_DATA[self.upgrade_level - 1].get("damage")
        #upgrade turret image
        self.animation_list = self.load_images(self.sprite_sheets[self.upgrade_level - 1])
        self.original_image = self.animation_list[self.frame_index]

        #upgrade grey circle
        self.range_image = pg.Surface((self.range * 2, self.range * 2))
        self.range_image.fill((0, 0, 0))
        self.range_image.set_colorkey((0, 0, 0))
        pg.draw.circle(self.range_image, "grey100", (self.range, self.range), self.range)
        self.range_image.set_alpha(100)
        self.range_rect = self.range_image.get_rect()
        self.range_rect.center = self.rect.center


    def draw(self, surface):
        center = self.rect.center

        self.image = pg.transform.rotate(self.original_image, self.angle - 90)
        self.rect = self.image.get_rect()
        self.rect.center = center
        surface.blit(self.image, self.rect)
        if self.selected:
            self.range_rect.center = self.rect.center
            surface.blit(self.range_image, self.range_rect)
