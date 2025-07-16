import Config
import GameConfig as GameConfig
import Levels
from Button import Button
from QuestionUI import QuestionUI

import random
import pygame
from pygame.locals import *
from pygame import mixer
import heapq
import math
import numpy as np
import json
import os
import traceback  # Add traceback for better error reporting
import tensorflow as tf
import sys

# Get the user's display size
info = pygame.display.Info()
display_width, display_height = info.current_w, info.current_h

# Create the main window at the display size
screen = pygame.display.set_mode((display_width, display_height))
pygame.display.set_caption('Mazer')

# Create a fixed-size game surface for all game rendering
GAME_SURFACE_WIDTH = GameConfig.SCREEN_WIDTH
GAME_SURFACE_HEIGHT = GameConfig.SCREEN_HEIGHT
game_surface = pygame.Surface((GAME_SURFACE_WIDTH, GAME_SURFACE_HEIGHT))

# ------------ Globals ------------

# Utility function for domain selection buttons

def create_text_button(text, x, y, width, height, font, colors):
    button_img = pygame.Surface((width, height))
    gradient = pygame.Surface((width, height))
    for i in range(height):
        ratio = i / height
        r = int(colors[0][0] * (1 - ratio) + colors[1][0] * ratio)
        g = int(colors[0][1] * (1 - ratio) + colors[1][1] * ratio)
        b = int(colors[0][2] * (1 - ratio) + colors[1][2] * ratio)
        pygame.draw.line(gradient, (r, g, b), (0, i), (width, i))
    button_img.blit(gradient, (0, 0))
    pygame.draw.rect(button_img, (255, 255, 255), button_img.get_rect(), 2)
    text_surf = font.render(text, True, (255, 255, 255))
    text_rect = text_surf.get_rect(center=(width // 2, height // 2))
    button_img.blit(text_surf, text_rect)
    return Button(x, y, button_img)

# dimensions: 18 x 20
screen_width = GameConfig.SCREEN_WIDTH 			# screen width
screen_height = GameConfig.SCREEN_HEIGHT 			# screen height
tile_size = GameConfig.TILE_SIZE				# tile size
world_tiles = []				# first layer

pygame.init()

in_menu = True
game_finished = False
game_over = 0 					# Game-Over flag
current_level = 0				# level counter
max_levels = 0					# only one level (level 1)
score_count = 0					# coin score count
points = 0                      # points for correct answers
POINTS_THRESHOLD = GameConfig.POINTS_THRESHOLD           # minimum points needed to progress

	# --> Sounds
pygame.mixer.pre_init(44100, -16, 2, 512)
mixer.init()

plats = []			# group of platforms
check_points = []	# group of checkpoints
lava_tiles = []		# group of lava tiles

# -----------------------------------------------------------------------------------------------------------

class CheckPoint(pygame.sprite.Sprite):
	def __init__(self, x, y, screen):
		pygame.sprite.Sprite.__init__(self)
		img = pygame.image.load(Config.Sprites["sign"])
		self.image = pygame.transform.scale(img, (int(tile_size // 1.3), int(tile_size // 1.3)) )
		self.rect = self.image.get_rect()
		self.rect.x = x
		self.rect.y = y + 63 # adjust the height to go ontop of grass

# -----------------------------------------------------------------------------------------------------------

class Lava(pygame.sprite.Sprite):
	def __init__(self, x, y, screen):
		pygame.sprite.Sprite.__init__(self)
		img = pygame.image.load(Config.Sprites["lava"])
		self.image = pygame.transform.scale(img, (tile_size, tile_size))
		self.rect = self.image.get_rect()
		self.rect.x = x
		self.rect.y = y

# -----------------------------------------------------------------------------------------------------------

class Platform(pygame.sprite.Sprite):
	def __init__(self, x, y, move_x, move_y, screen):
		self.screen = screen
		pygame.sprite.Sprite.__init__(self)
		img = pygame.image.load(Config.Sprites["ground_2"])
		self.image = pygame.transform.scale(img, (tile_size, tile_size // 2))

		self.rect = self.image.get_rect()
		self.rect.x = x
		self.rect.y = y

		self.move_direction = 1
		self.move_counter = random.randint(0, 40)

		self.move_x = move_x # flag to move in x direction
		self.move_y = move_y # flag to move in y direction
		self.question_shown = False  # Flag to track if question has been shown

	# handle platform movement
	def update(self):
		# Original movement speed without any multiplier
		self.rect.x += self.move_direction * self.move_x
		self.rect.y += self.move_direction * self.move_y
		self.move_counter += 1

		if abs(self.move_counter) > 50:
			self.move_direction *= -1
			self.move_counter *= -1

	# Draw the platform
	def draw(self, surface):
		surface.blit(self.image, self.rect)

# -----------------------------------------------------------------------------------------------------------

class World():
	def __init__(self):
		self.assets = {}
		self.load_assets()
		self.initialize_tiles()

	# Load game assets
	def load_assets(self):
		# Load the background
		self.background = pygame.image.load(Config.Sprites["background"])
		self.background = pygame.transform.scale(self.background, (screen_width, screen_height))

		# Create an asset dictionary
		for name, path in Config.Sprites.items():
			if name != "background":
				self.assets[name] =  pygame.image.load(path)

	# Makes an image game object
	def create_tile(self, row, col, name, custom_size, custom_location):
		global tile_size
		global world_tiles

		# default size
		if not custom_size:

			img = pygame.transform.scale(self.assets[name], (tile_size, tile_size))
			img_rect = img.get_rect()

			if not custom_location:
				img_rect.x = col * tile_size
				img_rect.y = row * tile_size
				t = (img, img_rect)
				world_tiles.append(t)
			else:
				img_rect.x = custom_location[0]
				img_rect.y = custom_location[1]
				t = (img, img_rect)
				world_tiles.append(t)

		else:
			img = pygame.transform.scale(self.assets[name], (custom_size[0], custom_size[1]))
			img_rect = img.get_rect()

			if not custom_location:
				img_rect.x = col * tile_size
				img_rect.y = row * tile_size
				t = (img, img_rect)
				world_tiles.append(t)
			else:
				img_rect.x = custom_location[0]
				img_rect.y = custom_location[1]
				t = (img, img_rect)
				world_tiles.append(t)

	# Initialize game tiles
	def initialize_tiles(self):
		global plats
		global check_points
		global environmentals
		global world_tiles
		global current_level

		world_tiles = []

		row = 0
		index = 0
		for r in Levels.level[current_level]:
			col = 0
			for tile in r:
				if (tile == 1):
					self.create_tile(row, col, "ground_1", False, False)

				if (tile == 2):
					self.create_tile(row, col, "ground_2", False, False)

				if (tile == 2.1):	# moving platform (Horizontal)
					platform = Platform(col * tile_size, row * tile_size , 1, 0, screen)
					plats[0].add(platform)

				if (tile == 2.2):	# moving platform (Vertical)
					platform = Platform(col * tile_size, row * tile_size , 0, 1, screen)
					plats[0].add(platform)

				if (tile == 3):
					self.create_tile(row, col, "ground_3", False, False)

				if (tile == 4):
					self.create_tile(row, col, "ground_4", False, False)

				if (tile == 5):
					self.create_tile(row, col, "ground_5", False, False)

				if (tile == 6):
					self.create_tile(row, col, "ground_6", False, False)

				if (tile == 7):
					self.create_tile(row, col, "ground_7", False, False)

				if (tile == 8):
					self.create_tile(row, col, "ground_8", False, False)

				if (tile == 9):
					self.create_tile(row, col, "ground_9", False, False)

				if (tile == 10):
					self.create_tile(row, col, "ground_10", False, False)

				if (tile == 11):
					self.create_tile(row, col, "ground_11", False, False)

				if (tile == 12):
					location = []
					location.append(col * tile_size)
					location.append(row * tile_size + 50)
					self.create_tile(row, col, "grass_1", False, location)

				if (tile == 13):
					location = []
					location.append(col * tile_size)
					location.append(row * tile_size + 50)
					self.create_tile(row, col, "grass_2", False, location)

				if (tile == 14):
					location = []
					location.append(col * tile_size)
					location.append(row * tile_size + 50)
					self.create_tile(row, col, "grass_3", False, location)

				if (tile == 15):
					location = []
					location.append(col * tile_size)
					location.append(row * tile_size + 50)
					self.create_tile(row, col, "grass_4", False, location)

				if (tile == 16):
					location = []
					location.append(col * tile_size)
					location.append(row * tile_size + 50)
					self.create_tile(row, col, "grass_5", False, location)

				if (tile == 17):
					self.create_tile(row, col, "bush_1", False, False)

				if (tile == 18):
					self.create_tile(row, col, "bush_2", False, False)

				if (tile == 19):
					self.create_tile(row, col, "tree_1", False, False)

				if (tile == 20):
					self.create_tile(row, col, "tree_2", False, False)

				if (tile == 21):
					self.create_tile(row, col, "rock_1", False, False)

				if (tile == 22):
					self.create_tile(row, col, "rock_2", False, False)

				if (tile == 23):
					check = CheckPoint(col * tile_size, row * tile_size, screen)
					check_points[0].add(check)

				if (tile == 24):
					lava = Lava(col * tile_size, row * tile_size, screen)
					lava_tiles[0].add(lava)

				index += 1
				col += 1
			row += 1

		# reverse the list so assets are drawn from bottom to top
		world_tiles = [ele for ele in reversed(world_tiles)]

	# Draw the background
	def draw_world(self):
		game_surface.blit(self.background, (0, 0))

	# Draw the world data from the tiles we created
	def draw_tiles(self):
		if world_tiles:
			for tile in world_tiles:
				game_surface.blit(tile[0], tile[1])

# -----------------------------------------------------------------------------------------------------------

class Character():
	def __init__(self, x, y):
		# images
		self.idle_right = []
		self.idle_left = []

		self.run_right = []
		self.run_left = []

		self.death_right = []
		self.death_left = []

		self.jump_right = []
		self.jump_left = []

		self.fall_right = []
		self.fall_left = []

		self.img_index = 0 # current frame
		self.counter = 0 # animation speed
		self.death_counter = 0

		# load assets
		self.load_assets()
		self.image = self.idle_right[self.img_index] # first frame

		# coordinates
		self.rect = self.image.get_rect()
		self.rect.x = x
		self.rect.y = y
		self.rect.w = self.image.get_width()
		self.rect.h = self.image.get_height()

		self.direction = 0
		self.vel_y = 0
		self.jumped = False
		self.in_air = False

		self.animation = "idle"
		self.cool_down = 10 # wait 10 frames before next img animation

	# Load all character images
	def load_assets(self):
		for name, path in Config.Player.items():
			img = pygame.image.load(path)
			img = pygame.transform.scale(img, (tile_size, tile_size))
			img_left = pygame.transform.flip(img, True, False)

			if 'idle' in name:
				self.idle_right.append(img)
				self.idle_left.append(img_left)

			if 'run' in name:
				self.run_right.append(img)
				self.run_left.append(img_left)

			if 'fall' in name:
				self.fall_right.append(img)
				self.fall_left.append(img_left)

			if 'death' in name:
				self.death_right.append(img)
				self.death_left.append(img_left)

			if 'jump' in name:
				self.jump_right.append(img)
				self.jump_left.append(img_left)

	# handle idle animation
	def idle_animation(self):
		if self.counter > self.cool_down:
			self.img_index += 1
			self.counter = 0

		if self.img_index >= len(self.idle_right):
			self.img_index = 0

		if self.direction == 1 or self.direction == 0:
			self.image = self.idle_right[self.img_index]

		if self.direction == -1:
			self.image = self.idle_left[self.img_index]

	# handle jump animation
	def jump_animation(self):
		if self.counter > self.cool_down:
			self.img_index += 1
			self.counter = 0

		if self.img_index >= len(self.jump_right):
			self.img_index = 0

		if self.direction == 1 or self.direction == 0:
			self.image = self.jump_right[self.img_index]

		if self.direction == -1:
			self.image = self.jump_left[self.img_index]

	# handle running animation
	def run_animation(self):
		if self.counter > self.cool_down:
			self.img_index += 1
			self.counter = 0

		if self.img_index >= len(self.run_right):
			self.img_index = 0

		if self.direction == 1 or self.direction == 0:
			self.image = self.run_right[self.img_index]

		if self.direction == -1:
			self.image = self.run_left[self.img_index]

	# handle death animation
	def death_animation(self):
		global game_over

		if self.death_counter > self.cool_down + 1:
			self.death_counter = 0
			game_over = -1
		else:
			self.img_index += 1

		if self.img_index >= len(self.death_right):
			self.img_index = 0

		if self.direction == 1 or self.direction == 0:
			self.image = self.death_right[self.img_index]

		if self.direction == -1:
			self.image = self.death_left[self.img_index]

		self.death_counter += 1


	# handle key presses
	def controller(self, dx, dy, game_paused=False):
		value = []
		key = pygame.key.get_pressed()

		# If game is paused, don't process any movement
		if game_paused:
			return [0, 0]

		# currently idle
		if not key[pygame.K_LEFT] and not key[pygame.K_RIGHT] and not key[pygame.K_SPACE]:
			self.counter += 1
			self.animation = "idle"

		# currently jumping
		if key[pygame.K_SPACE] and self.jumped == False and self.in_air == False:
			self.vel_y = -15 * GameConfig.SCALE_FACTOR  # Scaled jump height
			self.jumped = True
			self.counter += 1
			self.animation = "jump"

		if not key[pygame.K_SPACE]:
			self.jumped = False

		# currently running right
		if key[pygame.K_RIGHT]:
			dx += 5 * GameConfig.SCALE_FACTOR  # Scaled movement speed
			self.counter += 1
			self.direction = 1
			self.animation = "run"

		# currently running left
		if key[pygame.K_LEFT]:
			dx -= 5 * GameConfig.SCALE_FACTOR  # Scaled movement speed
			self.counter += 1
			self.direction = -1
			self.animation = "run"

		value.append(dx)
		value.append(dy)
		return value

	# handle player collision
	def collision(self, dx, dy):
		global plats
		global check_points
		global lava_tiles
		global game_over
		global world_tiles
		global game_finished
		global current_level
		global max_levels

		values = []
		collision_thresh = 20 # distance between moving platform in y dir

		self.in_air = True
		for tile in world_tiles:
			# check for collision in x direction ...
			if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.rect.w, self.rect.h):
				dx = 0 # if we collide, stop player

			# check collision in y direction of expected dy (change in y)
			if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.rect.w, self.rect.h):
				# check if jumping
				if self.vel_y < 0:
					self.vel_y = 0
					dy = tile[1].bottom - self.rect.top # dist between top of player and bottom of block

				# check if falling
				elif self.vel_y >= 0:
					self.vel_y = 0
					self.in_air = False
					dy = tile[1].top - self.rect.bottom

		# check for collision with platforms
		for platform in plats[0]:
			# check for x collision using expected position (dx) value
			if platform.rect.colliderect(self.rect.x + dx, self.rect.y, self.rect.w, self.rect.h):
				dx = 0
			# check for y collision
			if platform.rect.colliderect(self.rect.x, self.rect.y + dy, self.rect.w, self.rect.h):
				# check if below platform
				if abs((self.rect.top + dy) - platform.rect.bottom) < collision_thresh:
					self.vel_y = 0
					dy = platform.rect.bottom - self.rect.top
				# check if above platform
				elif abs((self.rect.bottom + dy) - platform.rect.top) < collision_thresh:
					self.rect.bottom = platform.rect.top - 1
					self.in_air = False
					dy = 0
				# move sideways with the platform
				if platform.move_x != 0:
					self.rect.x += platform.move_direction

		# check for collision with checkpoint
		if pygame.sprite.spritecollide(self, check_points[0], False):
			if current_level + 1 > max_levels:
				game_finished = True
				game_over = 0
			else:
				game_over = 1

		# check for collision with lava
		if pygame.sprite.spritecollide(self, lava_tiles[0], False):
			self.death_animation()
			self.rect.y = self.rect.y
			self.rect.x = self.rect.x

		values.append(dx)
		values.append(dy)
		return values

	# create a 2px rect outline around the player
	def draw_outline(self, surface):
		pygame.draw.rect(surface, (179, 29, 18), self.rect, 2)

	# handle the player
	def draw_player(self, surface, game_paused=False):
		global game_over
		dx = 0
		dy = 0

		if game_over == 0:
			# input handler - pass game_paused state
			key = self.controller(dx, dy, game_paused)
			dx = key[0]
			dy = key[1]

			# Process animations regardless of pause state
			if self.animation == "idle":
				self.idle_animation()
			elif self.animation == "jump":
				self.jump_animation()
			elif self.animation == "run":
				self.run_animation()

			# Only process movement and physics if not paused
			if not game_paused:
				# add gravity
				self.vel_y += 1
				if self.vel_y > 10:
					self.vel_y = 10
				dy += self.vel_y

				# check for collision
				col = self.collision(dx, dy)
				dx = col[0]
				dy = col[1]

				# handle out of bounds
				if self.rect.x + dx >= -25 and self.rect.x + dx <= 977:
					self.rect.x += dx

				if self.rect.y + dy >= 1000:
					game_over = -1
				else:
					self.rect.y += dy

		surface.blit(self.image, self.rect)

# -----------------------------------------------------------------------------------------------------------

class Chaser(pygame.sprite.Sprite):
	def __init__(self, x, y):
		pygame.sprite.Sprite.__init__(self)
		img = pygame.image.load(Config.Sprites["bird"])
		self.image = pygame.transform.scale(img, (int(40 * GameConfig.SCALE_FACTOR), int(40 * GameConfig.SCALE_FACTOR)))
		self.rect = self.image.get_rect()
		self.rect.x = x
		self.rect.y = y
		self.base_speed = 0.6 * GameConfig.SCALE_FACTOR  # Scaled base speed
		self.speed = self.base_speed  # Current speed
		self.model = tf.keras.models.load_model('chaser_model.h5') if os.path.exists('chaser_model.h5') else None
		self.buffer = []
		self.max_buffer_size = 1000
		self.training_enabled = False  # Disable training during gameplay
		self.start_time = pygame.time.get_ticks()  # Record start time
		self.delay = 20000  # 20 seconds delay in milliseconds
		self.is_active = False  # Flag to track if chaser is active
		self.paused_time = 0  # Track time spent paused
		self.last_pause_time = 0  # Track when we last paused

	def update(self, player, game_paused=False):
		current_time = pygame.time.get_ticks()
		
		# If game is paused by question, don't count this time
		if game_paused:
			if self.last_pause_time == 0:  # Just entered pause state
				self.last_pause_time = current_time
			return  # Don't process movement while paused
		else:
			if self.last_pause_time != 0:  # Just exited pause state
				self.paused_time += current_time - self.last_pause_time
				self.last_pause_time = 0

		# Only check activation if not paused
		if not self.is_active and (current_time - self.start_time - self.paused_time) >= self.delay:
			self.is_active = True
			self.speed = self.base_speed * (1 + current_level * 0.16)

		# Only move if active
		if self.is_active:
			dx = player.rect.x - self.rect.x
			dy = player.rect.y - self.rect.y
			
			distance = max(abs(dx), abs(dy))
			if distance > 0:
				dx = dx / distance
				dy = dy / distance
			
			if self.model is not None:
				state = np.array([[dx, dy, distance]])
				action = self.model.predict(state, verbose=0)[0]
				self.rect.x += action[0] * self.speed
				self.rect.y += action[1] * self.speed
			else:
				self.rect.x += dx * self.speed
				self.rect.y += dy * self.speed

	def draw(self, surface):
		surface.blit(self.image, self.rect)

# -----------------------------------------------------------------------------------------------------------

class Game():
	def __init__(self):
		pygame.mixer.pre_init(44100, -16, 2, 512)
		mixer.init()
		self.fps = 60  # Fixed FPS at 60
		self.clock = pygame.time.Clock()
		self.domain_buttons = []
		self.selected_domain = None
		self.question_ui = None
		self.game_menu()
		self.score_font = pygame.font.SysFont('comicsansms', int(25 * GameConfig.SCALE_FACTOR))  # Scaled font size
		self.timer_started = False  # New flag to track if timer has started
		self.insufficient_points = False  # Flag to track if player has insufficient points
		self.start()

	def game_menu(self):
		play_img = pygame.image.load(Config.UI["play"])
		quit_img = pygame.image.load(Config.UI["quit"])
		continue_img = pygame.image.load(Config.UI["continue"])
		resume_img = pygame.image.load(Config.UI["resume"])

		play_img = pygame.transform.scale(play_img, (int(200 * GameConfig.SCALE_FACTOR), int(70 * GameConfig.SCALE_FACTOR)))
		quit_img = pygame.transform.scale(quit_img, (int(200 * GameConfig.SCALE_FACTOR), int(70 * GameConfig.SCALE_FACTOR)))
		continue_img = pygame.transform.scale(continue_img, (int(200 * GameConfig.SCALE_FACTOR), int(70 * GameConfig.SCALE_FACTOR)))
		resume_img = pygame.transform.scale(resume_img, (int(200 * GameConfig.SCALE_FACTOR), int(70 * GameConfig.SCALE_FACTOR)))

		self.play_button = Button(screen_width // 2 - int(100 * GameConfig.SCALE_FACTOR), screen_height // 2, play_img)
		self.quit_button = Button(screen_width // 2 - int(100 * GameConfig.SCALE_FACTOR), screen_height // 2 + int(110 * GameConfig.SCALE_FACTOR), quit_img)
		self.continue_button = Button(screen_width // 2 - int(100 * GameConfig.SCALE_FACTOR), screen_height // 2, continue_img)
		self.resume_button = Button(screen_width // 2 - int(100 * GameConfig.SCALE_FACTOR), screen_height // 2, resume_img)

		# Create domain buttons
		domain_font = pygame.font.SysFont('comicsansms', int(32 * GameConfig.SCALE_FACTOR))
		button_width = int(350 * GameConfig.SCALE_FACTOR)
		button_height = int(70 * GameConfig.SCALE_FACTOR)
		spacing = int(30 * GameConfig.SCALE_FACTOR)
		start_y = screen_height // 2 - ((len(Config.DOMAINS) * (button_height + spacing)) // 2)
		self.domain_buttons = []
		for i, domain in enumerate(Config.DOMAINS.keys()):
			x = screen_width // 2 - button_width // 2
			y = start_y + i * (button_height + spacing)
			btn = create_text_button(domain, x, y, button_width, button_height, domain_font, [(41,128,185), (142,68,173)])
			self.domain_buttons.append((domain, btn))

	def reset_groups(self):
		global plats
		global check_points
		global lava_tiles

		plats = []
		check_points = []
		lava_tiles = []

		self.plat_group.empty()
		self.check_group.empty()
		self.lava_group.empty()

	def properties(self):
		global plats
		global check_points
		global lava_tiles

		self.plat_group = pygame.sprite.Group()
		self.check_group = pygame.sprite.Group()
		self.lava_group = pygame.sprite.Group()

		plats.append(self.plat_group)
		check_points.append(self.check_group)
		lava_tiles.append(self.lava_group)

	def load_level(self):
		global game_over

		self.reset_groups()
		self.properties()
		world = World()
		player = Character(0, screen_height - 130)
		chaser = Chaser(0, screen_height - 130)
		self.chaser = chaser  # Store chaser reference
		game_over = 0

		values = []
		values.append(player)
		values.append(world)
		values.append(chaser)
		return values

	def game_timer(self):
		global current_level
		timer = GameConfig.LEVEL_TIME_SECONDS
		ttext = str(timer)
		self.timer_counter, self.timer_text = timer, ttext.rjust(3)
		pygame.time.set_timer(pygame.USEREVENT, 1000)
		self.timer_font = pygame.font.SysFont('comicsansms', 25)
		# Set the chaser's start time to match the timer start
		if hasattr(self, 'chaser'):
			self.chaser.start_time = pygame.time.get_ticks()
			self.chaser.is_active = False
			self.chaser.paused_time = 0  # Reset paused time
			self.chaser.last_pause_time = 0  # Reset last pause time

	def start(self):
		global in_menu
		global in_domain_select
		global game_over
		global game_finished
		global max_levels
		global current_level
		global points
		global selected_domain

		self.properties()
		world = World()
		player = Character(0, screen_height - 130)
		chaser = Chaser(0, screen_height - 130)
		self.chaser = chaser  # Store chaser reference

		run = True
		while(run):
			# Fill the full window with black
			screen.fill((0, 0, 0))
			# Clear the game surface (optional, for transparency)
			game_surface.fill((0, 0, 0))
			world.draw_world()

			# setup main menu
			if in_menu:
				# --- Draw Game Title ---
				title_font = pygame.font.SysFont('comicsansms', int(48 * GameConfig.SCALE_FACTOR))
				title_text = title_font.render("🎮 MAZE RUNNER 🎮", True, (255, 215, 0))
				title_rect = title_text.get_rect(center=(screen_width // 2, int(80 * GameConfig.SCALE_FACTOR)))
				game_surface.blit(title_text, title_rect)
				
				# --- Draw Rules in Compact Format ---
				rules = [
					("Reach the final flag to finish the game.", 0),
					("30 seconds per level • Bird appears after 20s", 0),
					("Answer questions to earn points:", 0),
					("Level 1 = 3 pts • Level 2 = 5 pts • Level 3 = 8 pts (6 with AI)", 1),
					("15s question timer • Wrong = 0 points", 1),
					("🏆 Legend: 32+ • ⚔️ Gladiator: 24+ • 🛡️ Warrior: 20+", 1),
					("Use AI Assist for hints • Score 20+ to unlock Level 2!", 0)
				]
				rules_font = pygame.font.SysFont('comicsansms', int(22 * GameConfig.SCALE_FACTOR))
				line_height = int(28 * GameConfig.SCALE_FACTOR)
				total_height = len(rules) * line_height
				
				# Position rules in upper portion, above buttons
				start_y = int(150 * GameConfig.SCALE_FACTOR)
				box_width = int(screen_width * 0.75)
				box_height = total_height + int(40 * GameConfig.SCALE_FACTOR)
				box_x = (screen_width - box_width) // 2
				box_y = start_y - int(20 * GameConfig.SCALE_FACTOR)
				
				# Create elegant gradient background
				rules_bg = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
				# Gradient from dark blue to purple
				for y in range(box_height):
					ratio = y / box_height
					r = int(25 * (1 - ratio) + 40 * ratio)
					g = int(25 * (1 - ratio) + 30 * ratio)
					b = int(50 * (1 - ratio) + 80 * ratio)
					pygame.draw.line(rules_bg, (r, g, b), (0, y), (box_width, y))
				
				# Add border and shadow effect
				pygame.draw.rect(rules_bg, (255, 255, 255, 50), rules_bg.get_rect(), 2)
				game_surface.blit(rules_bg, (box_x, box_y))
				
				# Draw rules with better formatting
				left_margin = box_x + int(30 * GameConfig.SCALE_FACTOR)
				for i, (line, indent) in enumerate(rules):
					color = (255, 255, 255) if indent == 0 else (200, 220, 255)
					bullet_str = "▶ " if indent == 0 else "   • "
					text = bullet_str + line
					text_surface = rules_font.render(text, True, color)
					x_pos = left_margin + (indent * int(20 * GameConfig.SCALE_FACTOR))
					y_pos = start_y + i * line_height
					game_surface.blit(text_surface, (x_pos, y_pos))
				
				# --- Draw Buttons in Bottom Section ---
				# Position buttons in the bottom third of the screen
				button_y = screen_height - int(200 * GameConfig.SCALE_FACTOR)
				self.play_button.rect.centery = button_y
				self.quit_button.rect.centery = button_y + int(90 * GameConfig.SCALE_FACTOR)

				surf_x = (display_width - GAME_SURFACE_WIDTH) // 2
				surf_y = (display_height - GAME_SURFACE_HEIGHT) // 2
				if self.quit_button.draw(game_surface, offset=(surf_x, surf_y)):
					run = False
				if self.play_button.draw(game_surface, offset=(surf_x, surf_y)):
					in_menu = False
					in_domain_select = True
					points = 0  # Reset points when starting new game
					self.timer_started = False
			elif in_domain_select:
				# Draw domain selection screen
				title_font = pygame.font.SysFont('comicsansms', int(40 * GameConfig.SCALE_FACTOR))
				title_text = title_font.render("Choose a Domain", True, (255, 215, 0))
				title_rect = title_text.get_rect(center=(screen_width // 2, int(120 * GameConfig.SCALE_FACTOR)))
				game_surface.blit(title_text, title_rect)
				for domain, btn in self.domain_buttons:
					if btn.draw(game_surface, offset=(surf_x, surf_y)):
						selected_domain = domain
						in_domain_select = False
						# Pass the selected domain's XLSX to QuestionUI
						self.question_ui = QuestionUI(game_surface, Config.DOMAINS[selected_domain])
						self.game_timer()  # Start timer only after domain is selected
						self.timer_started = True
			else:
				world.draw_tiles()
				check_points[0].draw(game_surface)
				lava_tiles[0].draw(game_surface)
				player.draw_player(game_surface, self.question_ui.is_game_paused())
				plats[0].draw(game_surface)
				chaser.update(player, self.question_ui.is_game_paused())
				if not self.question_ui.is_game_paused():
					plats[0].update()
					chaser.draw(game_surface)
					if self.timer_started:
						timer_surface = self.timer_font.render(self.timer_text, True, (47, 48, 29))
						timer_rect = timer_surface.get_rect()
						timer_rect.topleft = (60, 42)
						game_surface.blit(timer_surface, timer_rect)

						game_surface.blit(self.score_font.render(f"Score: {points}", True, (47, 48, 29)), (screen_width - 150, 42))
					
					# Check for collision between player and chaser
					if chaser.rect.colliderect(player.rect):
						game_over = -1  # Player caught by chaser
				else:
					# When paused, just draw the chaser without updating
					chaser.draw(game_surface)

				# Draw level indicator as a button beside timer if a question is active (always visible)
				if self.question_ui.is_active() and self.question_ui.current_level and self.timer_started:
					timer_surface = self.timer_font.render(self.timer_text, True, (47, 48, 29))
					timer_rect = timer_surface.get_rect()
					timer_rect.topleft = (60, 42)
					
					level_str = str(self.question_ui.current_level).strip()
					if level_str.lower().startswith('level'):
						level_str = level_str.title()
					else:
						level_str = f"Level {level_str}"
					level_font = pygame.font.SysFont('comicsansms', int(22 * GameConfig.SCALE_FACTOR))
					level_text = level_font.render(level_str, True, (255, 255, 255))
					# Button style background
					padding_x = int(18 * GameConfig.SCALE_FACTOR)
					padding_y = int(8 * GameConfig.SCALE_FACTOR)
					button_width = level_text.get_width() + 2 * padding_x
					button_height = level_text.get_height() + 2 * padding_y
					button_x = timer_rect.right + int(18 * GameConfig.SCALE_FACTOR)
					button_y = timer_rect.top - int(4 * GameConfig.SCALE_FACTOR)
					button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
					# Gradient background
					button_bg = pygame.Surface((button_width, button_height), pygame.SRCALPHA)
					for y in range(button_height):
						ratio = y / button_height
						r = int(41 * (1 - ratio) + 142 * ratio)
						g = int(128 * (1 - ratio) + 68 * ratio)
						b = int(185 * (1 - ratio) + 173 * ratio)
						pygame.draw.line(button_bg, (r, g, b), (0, y), (button_width, y))
					pygame.draw.rect(button_bg, (255, 255, 255, 80), button_bg.get_rect(), 2, border_radius=12)
					game_surface.blit(button_bg, (button_x, button_y))
					# Draw level text centered
					level_text_rect = level_text.get_rect(center=button_rect.center)
					game_surface.blit(level_text, level_text_rect)

				# Check for collision with moving platforms in level 1
				if current_level == 0:  # Level 1
					platform_list = list(plats[0])
					for idx, platform in enumerate(platform_list):
						# Check if player is on top of the platform with a small tolerance
						if (not platform.question_shown and 
							abs(player.rect.bottom - platform.rect.top) <= 2 and  # Small tolerance for exact position
							player.rect.right > platform.rect.left + 5 and   # Small margin from edges
							player.rect.left < platform.rect.right - 5 and
							not player.in_air):  # Player is not jumping/falling
							
							platform.question_shown = True
							show_ask_ai = (idx == 3 or idx == 5)
							# Select question complexity based on platform index
							if idx in [2, 4]:
								complexity = 'Level 1'
							elif idx in [0, 1]:
								complexity = 'Level 2'
							elif idx in [3, 5]:
								complexity = 'Level 3'
							else:
								complexity = ''  # fallback: any
							self.question_ui.show_random_question_by_complexity(complexity, show_ask_ai=show_ask_ai)
							self.question_ui.set_game_paused(True)

				# Draw question UI if active
				if self.question_ui.is_active():
					self.question_ui.update()
					self.question_ui.draw()

				# player active
				if game_over == 0:
					pass  # Removed redundant platform update

				# player finished level
				if game_over == 1:
					self.timer_counter = 0
					# Check if player has enough points to progress
					if points >= POINTS_THRESHOLD:
						game_finished = True
					else:
						# Show insufficient points message
						self.insufficient_points = True
						game_over = -1  # Treat as game over

				# player death or insufficient points
				if game_over == -1:
					self.timer_counter = 0
					self.timer_started = False  # Reset timer started flag
					
					# Draw game over message and score
					title_font = pygame.font.SysFont('comicsansms', 50)
					subtitle_font = pygame.font.SysFont('comicsansms', 30)
					
					if self.insufficient_points:
						# Main title for insufficient points
						title = title_font.render("Better Luck Next Time!", True, (255, 0, 0))
						title_rect = title.get_rect(center=(screen_width//2, screen_height//2 - 100))
						
						# Score message
						score_text = subtitle_font.render(f"Points Required: {POINTS_THRESHOLD}, Your Score: {points}", True, (255, 255, 255))
						score_rect = score_text.get_rect(center=(screen_width//2, screen_height//2 - 30))
					else:
						# Regular game over message
						title = title_font.render("Game Over!", True, (255, 0, 0))
						title_rect = title.get_rect(center=(screen_width//2, screen_height//2 - 100))
						
						# Score message
						score_text = subtitle_font.render(f"Total Score: {points}", True, (255, 255, 255))
						score_rect = score_text.get_rect(center=(screen_width//2, screen_height//2 - 30))
					
					# Draw the messages
					game_surface.blit(title, title_rect)
					game_surface.blit(score_text, score_rect)

					# --- Show Rank (Game Over) ---
					rank = None
					if points >= 30:
						rank = 'Legend'
					elif points >= 24:
						rank = 'Gladiator'
					elif points >= 20:
						rank = 'Warrior'
					if rank:
						rank_font = pygame.font.SysFont('comicsansms', 40)
						rank_text = rank_font.render(f'Rank: {rank}', True, (255, 215, 0))
						rank_rect = rank_text.get_rect(center=(screen_width//2, score_rect.bottom + 50))
						game_surface.blit(rank_text, rank_rect)

					if self.resume_button.draw(game_surface, offset=(surf_x, surf_y)):
						values = self.load_level()
						player = values[0]
						world = values[1]
						chaser = values[2]
						self.game_timer()
						self.timer_started = True  # Mark timer as started
						self.insufficient_points = False  # Reset insufficient points flag
						points = 0  # Reset points when restarting after game over
					if self.quit_button.draw(game_surface, offset=(surf_x, surf_y)):
						run = False

				# player won
				if game_finished:
					self.timer_counter = 0
					self.timer_started = False  # Reset timer started flag
					# Draw improved congratulatory message
					title_font = pygame.font.SysFont('comicsansms', 56)
					subtitle_font = pygame.font.SysFont('comicsansms', 32)

					# Main title with emojis and celebratory text
					title = title_font.render("🏁 Level Complete! 🏁", True, (255, 215, 0))
					subtitle = subtitle_font.render(f"Congratulations! You finished the game! Final Score: {points}", True, (255, 255, 255))

					# Calculate background box size
					padding_x = int(60 * GameConfig.SCALE_FACTOR)
					padding_y = int(40 * GameConfig.SCALE_FACTOR)
					box_width = max(title.get_width(), subtitle.get_width()) + 2 * padding_x
					box_height = title.get_height() + subtitle.get_height() + 3 * padding_y
					box_x = (screen_width - box_width) // 2
					box_y = (screen_height - box_height) // 2

					# Draw semi-transparent background box
					bg_surf = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
					bg_surf.fill((30, 30, 30, 220))
					pygame.draw.rect(bg_surf, (0, 0, 0, 255), bg_surf.get_rect(), border_radius=18)
					game_surface.blit(bg_surf, (box_x, box_y))

					# Draw the messages with extra spacing
					title_rect = title.get_rect(center=(screen_width//2, box_y + padding_y + title.get_height()//2))
					subtitle_rect = subtitle.get_rect(center=(screen_width//2, title_rect.bottom + padding_y + subtitle.get_height()//2))
					game_surface.blit(title, title_rect)
					game_surface.blit(subtitle, subtitle_rect)

					# --- Show Rank (Game Finished) ---
					rank = None
					if points >= 30:
						rank = 'Legend'
					elif points >= 24:
						rank = 'Gladiator'
					elif points >= 20:
						rank = 'Warrior'
					if rank:
						rank_font = pygame.font.SysFont('comicsansms', 44)
						rank_text = rank_font.render(f'Rank: {rank}', True, (255, 215, 0))
						rank_rect = rank_text.get_rect(center=(screen_width//2, subtitle_rect.bottom + 60))
						game_surface.blit(rank_text, rank_rect)

					if self.quit_button.draw(game_surface, offset=(surf_x, surf_y)):
						run = False

			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					run = False

				# Handle question UI events with offset
				if self.question_ui:
					result = self.question_ui.handle_events(event, offset=(surf_x, surf_y))
					if result is not None:
						is_correct, used_ask_ai = result
						# Question was answered, check if correct
						if is_correct:
							# Get complexity from current question
							complexity = self.question_ui.current_question.get('complexity', '').strip().lower()
							if complexity in ['1', 'level 1']:
								points += GameConfig.POINTS['level_1']
							elif complexity in ['2', 'level 2']:
								points += GameConfig.POINTS['level_2']
							elif complexity in ['3', 'level 3']:
								if used_ask_ai:
									points += GameConfig.POINTS['level_3_ai']
								else:
									points += GameConfig.POINTS['level_3']
							else:
								# fallback if complexity missing
								points += GameConfig.POINTS['fallback_ai'] if used_ask_ai else GameConfig.POINTS['fallback']
						# Don't reset or unpause here - let QuestionUI handle the delay
						# The game will automatically unpause when QuestionUI is done

				# game timer - only process if timer has started
				if event.type == pygame.USEREVENT and self.timer_started and not self.question_ui.is_game_paused():
					self.timer_counter -= 1
					if self.timer_counter > 0:
						self.timer_text = str(self.timer_counter).rjust(3)
					else:
						# player ran out of time
						self.timer_text = '0'.rjust(3)
						if not game_finished:
							game_over = -1

				# After handling question UI events and update, check for timeout game over
				if self.question_ui and self.question_ui.active and self.question_ui.question_answered and self.question_ui.show_feedback and self.question_ui.feedback_message.startswith("⏰ Time's up!"):
					game_over = -1

			# At the end of the frame, blit the game_surface centered on the screen
			surf_x = (display_width - GAME_SURFACE_WIDTH) // 2
			surf_y = (display_height - GAME_SURFACE_HEIGHT) // 2
			screen.blit(game_surface, (surf_x, surf_y))
			pygame.display.update()

# Start the game
try:
	game = Game()
	pygame.quit()
except Exception as e:
	print(f"Fatal error: {str(e)}")
	print(traceback.format_exc())
	pygame.quit()