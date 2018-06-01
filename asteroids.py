#! python3
'''
Program             :   Asteroids
Programmer          :   Damian Duffy
Date                :   April 2018
Description         :   Game based on the classic Asteroids arcade game
'''

# import required packages
import sys
import os
import random
import math
import pygame
from pygame.locals import *
from pygame.math import Vector2
import config
# from config.locals import *           TBC - See if this works???

# initialise pygame
pygame.init()
if config.FULLSCREEN == False:
    screen = pygame.display.set_mode(config.SCREENSIZE)
else:
    screen = pygame.display.set_mode(config.SCREENSIZE, pygame.FULLSCREEN)
pygame.mouse.set_visible(config.DISPLAY_MOUSE)
pygame.display.set_caption(config.TITLE)
clock = pygame.time.Clock()
font = pygame.font.Font(None, 25)

# Set globals
enemy_group = set([])
missile_group = set([])
explosion_group = set([])

# pause the game
def pause_game():
    pass

# exit the game
def exit_game():
    pygame.quit()
    sys.exit()

# start a new game
def new_game():
    pass

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

# load image files
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

# load sound files
def load_sound(name):
    class NoneSound:
        def play(self):
            pass

    if not pygame.mixer:
        return NoneSound()

    fullname = os.path.join('snd/', name)

    try:
        sound = pygame.mixer.Sound(fullname)
    except pygame.error as message:
        print('Cannot load sound:', name)
        raise SystemExit(message)

    return sound

# helper functions to handle transformations
def angle_to_vector(ang):
    ang *= -0.01745329252
    return [math.cos(ang), math.sin(ang)]

# calculate the distance between two points
def dist(p, q):
    return math.sqrt((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2)

def group_dist(group, position):
    for sprite in group:
        if dist(position, sprite.get_position()) < (sprite.get_radius() * 4):
            return False
    return True

# Draw and update groups of sprites
def process_sprite_group(sprites):
    expired = set([])
    for sprite in sprites:
        sprite.draw()
        # update() returns true if the sprite has a finite lifespan
        if sprite.update():
            # create set of sprites which exceed their lifespan
            expired.add(sprite)
    # remove sprites that exceed lifespan
    sprites -= expired

def group_collide(group, other_object):
    global lives
    # hit will be returned
    hit = False
    # temp_group used to store sprites for removal after iteration has completed
    temp_group = set([])

    for sprite in group:
        if sprite.collide(other_object):
            # add the collided sprite to the temporary group
            temp_group.add(sprite)
            # add sprite to the explosions group
            explosion_group.add(Sprite(other_object.get_position(), [0, 0], 0, 0, explosion_image, explosion_info, explosion_sound))
            # play the explosion sound
            # explosion_sound.stop()
            # explosion_sound.play()
            hit = True

    # remove sprites from the group which were involved in collisions
    group.difference_update(temp_group)

    return hit

def group_group_collide(other_group, group):
    global score, difficulty
    # temp_group used to store sprites for removal after iteration has completed
    temp_group = set([])

    for sprite in group:
        if group_collide(other_group, sprite):
            temp_group.add(sprite)

            # remove sprites which have been involved in collision
            # group.discard(sprite)
            # increment the score
            score += 1
            # difficulty is incremented with each asteroid destroyed;
            # increasing the probability of higher velocity asteroids
            difficulty += 0.05

    # remove sprites from the group which were involved in collisions
    group.difference_update(temp_group)

def enemy_spawner(player_pos, player_radius):
    # check for the max number of enemies allowed at any time
    if len(enemy_group) < config.MAX_ENEMY_SPRITES:
        # generate enemy properties
        # difficulty is incremented with the player score
        # and results in higher velocity enemies being generated

        # randomly spam all over the screen (like asteroids)
        enemy_pos = [random.randrange(0, config.SCREENSIZE[0]), random.randrange(0, config.SCREENSIZE[1])]
        enemy_vel = [random.random() * config.DIFFICULTY * random.choice([-1, 1]), random.random() * config.DIFFICULTY * random.choice([-1, 1])]
        # enemy_avel = (random.random() / 10) * random.choice([-1, 1])
        # don't spawn asteroids too close to the ship (within twice the distance between centers)
        if dist(enemy_pos, player_pos) > ((asteroid_info.get_radius() + player_radius) * 2):
            enemy_group.add(Asteroid(enemy_pos, enemy_vel, 0, 0, asteroid_image, asteroid_info))

class Background:
    def __init__(self):
        self.nebula = None
        self.debris = None
        self.debris_x_scroll_rate = config.DEBRIS_SCROLL_RATE[0]
        self.debris_y_scroll_rate = config.DEBRIS_SCROLL_RATE[1]
        self.debris_pos = [0, 0]

    def update(self):
        self.debris_pos[0] += self.debris_x_scroll_rate
        self.debris_pos[1] += self.debris_y_scroll_rate
        if self.debris_pos[0] < (0 - config.SCREENSIZE[0]):
            self.debris_pos = [0, 0]

    def draw(self, player):
        screen.blit(nebula_image, (0, 0))
        screen.blit(debris_image, self.debris_pos)
        screen.blit(debris_image, (self.debris_pos[0] + config.SCREENSIZE[0], self.debris_pos[1]))
        # on-screen display of information
        fps = font.render("FPS: " + str(int(clock.get_fps())), True, pygame.Color('white'))
        lives = font.render("Lives: " + str(player.get_lives()), True, pygame.Color('white'))
        score = font.render("Score: " + str(player.get_score()), True, pygame.Color('white'))
        top_score = font.render("Top Score: ", True, pygame.Color('white'))
        screen.blit(lives, (450, 10))
        screen.blit(score, (450, 40))
        screen.blit(top_score, (450, 70))
        if config.SHOW_FPS:
            screen.blit(fps, (550, 10))

# Image class to hold image information
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

# Sprite class to define basic sprite characteristics
class Sprite:
    def __init__(self, pos, vel, ang, ang_vel, image, info, sound = None):
        self.pos = Vector2(pos)  # The original center position/pivot point.
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
        self.orig_image = self.image
        self.rect = self.image.get_rect(center=pos)
        #self.pos = Vector2(pos)  # The original center position/pivot point.
        self.offset = Vector2(0, 0)  # We shift the sprite 50 px to the right.
        #self.angle = 0

    def draw(self):
        screen.blit(self.image, self.rect) #self.pos)
        """
        if self.animated:
            frames = [] # a list for the sprite frames
            # each frame has 128 x 128 pixels
            for nbr in range(1,25,1): # 24 frames in spritesheet
                frames.append(explosion_image.subsurface((127*(nbr-1),0,127,127)))
            for nbr in range(len(frames)):
                windowSurfaceObj.blit(frames[nbr], self.pos)
            '''
            current_animation_index = [self.image_center[0] + (self.image_size[0] * (self.age / 3)), self.image_center[1]]
            windowSurfaceObj.blit(self.image, current_animation_index, self.image_size, self.pos)
            '''
            self.age += 1
        else:
            windowSurfaceObj.blit(self.image, self.pos)
        """
    def rotate(self):
        """Rotate the image of the sprite around a pivot point."""
        # Rotate the image.
        self.image = pygame.transform.rotozoom(self.orig_image, self.angle, 1)
        # Rotate the offset vector.
        offset_rotated = self.offset.rotate(self.angle)
        # Create a new rect with the center of the sprite + the offset.
        self.rect = self.image.get_rect(center=self.pos+offset_rotated)

    def update(self):
        # update angle
        self.angle = (self.angle + self.angle_vel) % 360

        self.set_pos()
        self.rotate()

        self.pos[0] = (self.pos[0] + self.vel[0]) % (config.SCREENSIZE[0] + self.radius)
        self.pos[1] = (self.pos[1] + self.vel[1]) % (config.SCREENSIZE[1] + self.radius)

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

    def set_pos(self):
        self.pos[0] += self.vel[0]
        self.pos[1] += self.vel[1]

    # check if the sprite was involved in a collision and return true if it has
    def collide(self, other_object):
        if dist(self.get_centre(), other_object.get_centre()) < (self.get_radius() + other_object.get_radius()):
            return True
        else:
            return False

# Asteroid class
class Asteroid(Sprite):
    def __init__ (self, pos, vel, ang, ang_vel, image, info, sound = None):
        Sprite.__init__(self, pos, vel, ang, ang_vel, image, info, sound = None)

# Spaceship class
class Spaceship(Sprite):
    def __init__ (self, pos, vel, ang, ang_vel, image, info, sound = None):
        Sprite.__init__(self, pos, vel, ang, ang_vel, image, info, sound = None)
        self.thrust = False
        self.speed = 0.1
        self.accel = config.SHIP_ACCEL
        self.decel = config.SHIP_DECEL
        self.max_speed = config.SHIP_SPEED
        self.turn = 0
        self.lives = 3
        self.score = 0

    def get_score(self):
        return self.score

    def get_lives(self):
        return self.lives

    def set_thrust(self, engaged = True):
        self.thrust = engaged
        pass
        '''
        tmp_vel = angle_to_vector(self.angle)


        if engaged == True:
            print("engaged")
            if self.speed < self.max_speed:
                self.speed *= self.accel
            self.vel = [tmp_vel[0] * self.speed, tmp_vel[1] * self.speed]
        else:
            print("stop")
            print("speed:", self.speed)
            if self.speed > 0.1:
                self.speed *= self.decel
                self.vel = [tmp_vel[0] * self.speed, tmp_vel[1] * self.speed]
            else:
                self.speed = 0.1
                self.vel = [0, 0]

        self.thrust = engaged
        '''

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
        """change ship's position based on rotate and accelerate functions"""
        self.angle = (self.angle + self.angle_vel) % 360
        self.rotate()

        vector = angle_to_vector(self.angle)
        print("vector: ", vector, "Angle:", self.angle, "Ang Vel:", self.angle_vel)
        friction = 0.995
        # accelerate in direction of ship if thrusters engaged
        if self.thrust:
            for i in range(2):
                self.vel[i] += vector[i] * 0.08
        # update position based on velocity
        for i in range(2):
            self.pos[i] = (self.pos[i] + self.vel[i]) % (config.SCREENSIZE[i] + self.radius)
            self.vel[i] *= friction # coefficient of friction


        '''
        ###############################################

        # check x position out of bounds for smooth screen wrapping
        if self.pos[0] + self.radius > WIDTH:
            self.ghostx = True
            self.ghost_pos[0] = self.pos[0] - WIDTH
        elif self.pos[0] - self.radius < 0:
            self.ghostx = True
            self.ghost_pos[0] = self.pos[0] + WIDTH
        else:
            self.ghostx = False
            self.ghost_pos[0] = self.pos[0]

        # check y position out of bounds for smooth screen wrapping
        if self.pos[1] + self.radius > HEIGHT:
            self.ghosty = True
            self.ghost_pos[1] = self.pos[1] - HEIGHT
        elif self.pos[1] - self.radius < 0:
            self.ghosty = True
            self.ghost_pos[1] = self.pos[1] + HEIGHT
        else:
            self.ghosty = False
            self.ghost_pos[1] = self.pos[1]

        ##################### my original bit below ################

        # update angle
        self.angle = (self.angle + self.angle_vel) % 360
        self.set_thrust(self.thrust)

        self.set_pos()
        self.rotate()

        self.pos[0] = (self.pos[0] + self.vel[0]) % (config.SCREENSIZE[0] + self.radius)
        self.pos[1] = (self.pos[1] + self.vel[1]) % (config.SCREENSIZE[1] + self.radius)

        self.age += 1

        if self.age >= self.lifespan:
            return True
        else:
            return False

        '''

    def draw(self):
        screen.blit(self.image, self.rect)


# load game resources (graphics)
nebula_info = ImageInfo([400, 300], [800, 600])
nebula_image = load_image("nebula_blue.png")
debris_info = ImageInfo([320, 240], [640, 480])
debris_image = load_image("debris_blend.png")
ship_info = ImageInfo([45, 45], [90, 90], 35)
ship_image = load_image("ship.png")
asteroid_info = ImageInfo([45, 45], [90, 90], 40)
asteroid_image = load_image("asteroid_blend.png")

''' TBC - temporarily halting loading assets
missile_info = ImageInfo([5,5], [10, 10], 3, 50)
missile_image = load_image("shot1.png")
explosion_info = ImageInfo([64, 64], [128, 128], 17, 24, True)
explosion_image = load_image("explosion.png")
background_info = ImageInfo([400, 300], [800, 600])
background_image = pygame.image.load("../data/img/background1.jpg")
# load game resources (audio)
explosion_sound = load_sound("explosion.ogg")
soundtrack = load_sound("soundtrack.ogg")
'''


# main game loop - one loop to rule them all
def main():
    # start music
    if config.SOUND == True:
        soundtrack.play(-1)

    environment = Background()
    player = Spaceship([100, 100], [0, 0], 0, 0, ship_image, ship_info)

    while True:
        # event handlers
        for event in pygame.event.get():
            if event.type == KEYDOWN:
                key_down(event, player)
            if event.type == KEYUP:
                key_up(event, player)

        # write game logic here
        enemy_spawner(player.get_position(), player.get_radius())

        # draw the game arena
        environment.update()
        environment.draw(player)

        # sprite draw code here
        player.update()
        player.draw()
        for asteroid in enemy_group:
            asteroid.update()
            asteroid.draw()

        # display whatever is drawn
        pygame.display.update()
        clock.tick(config.FPS)

if __name__ == '__main__':
    main()
