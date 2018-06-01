#! python3

import sys
import os
import random
import math
import pygame
from pygame.locals import *
import config

pygame.init()
screen = pygame.display.set_mode(config.SCREENSIZE)
clock = pygame.time.Clock()
font = pygame.font.Font(None, 30)

def exit_game():
    pygame.quit()
    sys.exit()

# Event handler
def key_down(event, player):
    if event.key == K_ESCAPE:
        exit_game()
    if event.key == K_p:
        pause_game()
    if event.key == K_UP:
        player.set_thrust(True)
    if event.key == K_LEFT:
        player.set_turn(-1)
    if event.key == K_RIGHT:
        player.set_turn(1)
    if event.key == K_SPACE:
        player.shoot()

def key_up(event, player):
    if event.key == K_ESCAPE:
        exit_game()
    if event.key == K_p:
        pause_game()
    if event.key == K_UP:
        player.set_thrust(False)
    if event.key == K_LEFT:
        player.set_turn(1)
    if event.key == K_RIGHT:
        player.set_turn(-1)

def load_image(name, colorkey = None):
    fullname = os.path.join('gfx/', name)

    try:
        image = pygame.image.load(fullname)
    except pygame.error as message:
        print('Cannot load image:', name)
        print(os.getcwd())
        raise SystemExit(message)

    if colorkey is not None:
        image = image.convert()
        if colorkey is -1:
            colorkey = image.get_at((0,0))
        image.set_colorkey(colorkey, RLEACCEL)
    else:
        image = image.convert_alpha()

    return image # , image.get_rect()

class ImageInfo:
    def __init__(self, center, size, radius = 0, lifespan = None, frames = 1, animated = False):
        self.center = center
        self.size = size
        self.radius = radius
        if lifespan:
            self.lifespan = lifespan
        else:
            self.lifespan = float('inf')
        self.frames = frames
        self.animated = animated

    def get_center(self):
        return self.center

    def get_size(self):
        return self.size

    def get_radius(self):
        return self.radius

    def get_lifespan(self):
        return self.lifespan

    def get_frames(self):
        return self.frames

    def get_animated(self):
        return self.animated

class Sprite:
    def __init__(self, pos, vel, ang, ang_vel, image, info, sound = None):
        self.pos = pos
        self.vel = vel
        self.angle = ang
        self.angle_vel = ang_vel
        self.image = image
        self.image_center = info.get_center()
        self.image_size = info.get_size()
        self.radius = info.get_radius()
        self.lifespan = info.get_lifespan()
        self.animated = info.get_animated()
        self.age = 0
        if sound:
            sound.stop()
            sound.play()

    def draw(self):
        screen.blit(self.image, self.pos)

    def update(self):
        # update angle
        self.angle += self.angle_vel

        # update position
        self.pos[0] = (self.pos[0] + self.vel[0])
        self.pos[1] = (self.pos[1] + self.vel[1])

        if self.pos[0] < 0 - self.image_size[0]:
            self.pos[0] = config.SCREENSIZE[0]
        if self.pos[1] < 0 - self.image_size[1]:
            self.pos[1] = config.SCREENSIZE[1]
        if self.pos[0] > config.SCREENSIZE[0]:
            self.pos[0] = 0 - self.image_size[0]
        if self.pos[1] > config.SCREENSIZE[1]:
            self.pos[1] = 0 - self.image_size[0]

        self.age += 1

        if self.age >= self.lifespan:
            return True
        else:
            return False

    def get_radius(self):
        return self.radius

    def get_position(self):
        return self.pos

    def get_centre(self):
        return [self.pos[0] + self.image_center[0], self.pos[1] + self.center[1]]

    def set_vel(self, x_vel = None, y_vel = None):
        if x_vel:
            self.vel[0] += x_vel
        if y_vel:
            self.vel[1] += y_vel

    # check if the sprite was involved in a collision and return true if it has
    def collide(self, other_object):
        if dist(self.get_centre(), other_object.get_centre()) < (self.get_radius() + other_object.get_radius()):
            return True
        else:
            return False


# Spaceship class
class Spaceship(Sprite):
    def __init__ (self, pos, vel, ang, ang_vel, image, info, sound = None):
        Sprite.__init__(self, pos, vel, ang, ang_vel, image, info, sound = None)
        self.original_image = image
        self.image = self.original_image
        self.thrust = False
        self.turn = 0
        self.rect = self.image.get_rect().move(pos)

    def set_thrust(self, engaged = True):
        self.thrust = engaged

    def set_turn(self, direction):
        self.turn += direction

        if self.turn == 0:
            # turn velocity should be 0; update ang_vel
            self.angle_vel = 0
        elif self.turn < 0:
            # turn velocity should be anti-clockwise; update ang_vel
            self.angle_vel = 5
        elif self.turn > 0:
            # turn velocity should be clockwise; update ang_vel
            self.angle_vel = -5

    def shoot(self):
        pass

    def update(self):
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        self.angle += self.angle_vel % 360
        '''
        x, y = self.rect.center  # Save its current center.
        self.rect = self.image.get_rect()  # Replace old rect with new rect.
        self.rect.center = (45, 45)  # Put the new rect's center at old center.
        '''

    def draw(self):
        w, h = self.image.get_width(), self.image.get_width()
        self.pos[0] = 150 - (w // 2)
        self.pos[1] = 150 - (h // 2)
        if self.thrust == False:
            screen.blit(self.image, self.pos, (0, 0, self.image_size[0] + 20, self.image_size[1] + 20))
        else:
            screen.blit(self.image, self.pos, (self.image_size[0] + 2, 0, self.image_size[0] + self.image_size[0], self.image_size[1]))

# load game resources (graphics)
nebula_info = ImageInfo([400, 300], [800, 600])
nebula_image = load_image("nebula_blue.png")
ship_info = ImageInfo([45, 45], [90, 90], 35)
ship_image = load_image("ship.png")


# main game loop - one loop to rule them all
def main():
    player = Spaceship([100, 100], [0, 0], 0, 0, ship_image, ship_info)

    while True:
        # event handlers
        for event in pygame.event.get():
            if event.type == KEYDOWN:
                key_down(event, player)
            if event.type == KEYUP:
                key_up(event, player)

        # write game logic here

        # draw the game arena
        screen.blit(nebula_image, [0, 0])
        fps = font.render(str(int(clock.get_fps())), True, pygame.Color('white'))
        screen.blit(fps, (50, 50))

        # sprite draw code here
        player.update()
        player.draw()

        # display whatever is drawn
        pygame.display.update()
        clock.tick(config.FPS)

if __name__ == '__main__':
    main()
