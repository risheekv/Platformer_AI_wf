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
import pandas as pd
from datetime import datetime

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

def draw_gradient_box(surface, rect, color1, color2, alpha=200):
    """
    Draw a gradient box with rounded corners and transparency
    """
    # Create a surface for the gradient with per-pixel alpha
    gradient_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    
    # Draw vertical gradient
    for y in range(rect.height):
        # Calculate interpolation factor (0.0 to 1.0)
        factor = y / rect.height
        
        # Interpolate between colors
        r = int(color1[0] * (1 - factor) + color2[0] * factor)
        g = int(color1[1] * (1 - factor) + color2[1] * factor)
        b = int(color1[2] * (1 - factor) + color2[2] * factor)
        
        # Draw horizontal line with interpolated color and alpha
        pygame.draw.line(gradient_surface, (r, g, b, alpha), (0, y), (rect.width, y))
    
    # Add a subtle border
    pygame.draw.rect(gradient_surface, (255, 255, 255, 100), (0, 0, rect.width, rect.height), 3)
    
    # Blit the gradient surface to the main surface
    surface.blit(gradient_surface, rect.topleft)

# dimensions: 18 x 20
screen_width = GameConfig.SCREEN_WIDTH 			# screen width
screen_height = GameConfig.SCREEN_HEIGHT 			# screen height
tile_size = GameConfig.TILE_SIZE				# tile size
world_tiles = []				# first layer

pygame.init()

in_menu = True
in_domain_select = False        # Domain selection screen flag
selected_domain = None          # Selected domain for questions
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
		self.move_counter = random.randint(0, 20)

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
			self.vel_y = -15 * GameConfig.SCALE_FACTOR  # Scaled jump height using physics-appropriate scaling
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

				# handle out of bounds - dynamic boundaries that scale with SCALE_FACTOR
				left_boundary = int(-25 * GameConfig.SCALE_FACTOR)
				right_boundary = int(977 * GameConfig.SCALE_FACTOR)
				bottom_boundary = int(1000 * GameConfig.SCALE_FACTOR)
				
				if self.rect.x + dx >= left_boundary and self.rect.x + dx <= right_boundary:
					self.rect.x += dx

				if self.rect.y + dy >= bottom_boundary:
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
		self.delay = GameConfig.CHASER_DELAY_MS  # Use config value for delay
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
		self.username = ""  # Store username
		self.username_active = False  # Track if username field is active
		self.cursor_blink_timer = 0  # Timer for cursor blinking
		self.player_details_saved = False  # Flag to prevent multiple saves
		self.show_duplicate_message = False  # Flag to show duplicate username message
		self.duplicate_message_timer = 0  # Timer for duplicate message display
		self.show_instructions = False  # Flag to show instructions screen
		self.username_error_type = ""  # Type of username error: "missing" or "duplicate"
		self.level1_wrong_answers = 0  # Counter for Level 1 wrong answers
		self.game_menu()
		self.score_font = pygame.font.SysFont('comicsansms', int(25 * GameConfig.SCALE_FACTOR))  # Scaled font size
		self.timer_started = False  # New flag to track if timer has started
		self.insufficient_points = False  # Flag to track if player has insufficient points
		self.start()

	def game_menu(self):
		play_img = pygame.image.load(Config.UI["play"])
		continue_img = pygame.image.load(Config.UI["continue"])

		play_img = pygame.transform.scale(play_img, (int(200 * GameConfig.SCALE_FACTOR), int(70 * GameConfig.SCALE_FACTOR)))
		continue_img = pygame.transform.scale(continue_img, (int(200 * GameConfig.SCALE_FACTOR), int(70 * GameConfig.SCALE_FACTOR)))

		self.play_button = Button(screen_width // 2 - int(100 * GameConfig.SCALE_FACTOR), screen_height // 2, play_img)
		self.continue_button = Button(screen_width // 2 - int(100 * GameConfig.SCALE_FACTOR), screen_height // 2, continue_img)
		
		# Create instructions button as text button
		instructions_font = pygame.font.SysFont('comicsansms', int(28 * GameConfig.SCALE_FACTOR))
		instructions_colors = ((52, 152, 219), (155, 89, 182))  # Light blue to purple gradient
		instructions_button_width = int(200 * GameConfig.SCALE_FACTOR)
		instructions_button_height = int(60 * GameConfig.SCALE_FACTOR)
		instructions_x = screen_width // 2 - instructions_button_width // 2
		instructions_y = screen_height // 2
		self.instructions_button = create_text_button("📚 Instructions", instructions_x, instructions_y, instructions_button_width, instructions_button_height, instructions_font, instructions_colors)
		

		# Create restart button as text button instead of using resume image
		restart_font = pygame.font.SysFont('comicsansms', int(32 * GameConfig.SCALE_FACTOR))
		restart_colors = ((41, 128, 185), (142, 68, 173))  # Blue to purple gradient
		restart_button_width = int(200 * GameConfig.SCALE_FACTOR)
		restart_button_height = int(70 * GameConfig.SCALE_FACTOR)
		restart_x = screen_width // 2 - restart_button_width // 2
		restart_y = screen_height // 2
		self.resume_button = create_text_button("Restart", restart_x, restart_y, restart_button_width, restart_button_height, restart_font, restart_colors)

		# Create domain buttons using configurable domains with improved layout
		domain_font = pygame.font.SysFont('comicsansms', int(24 * GameConfig.SCALE_FACTOR))  # Smaller font
		button_width = int(300 * GameConfig.SCALE_FACTOR)  # Smaller button width
		button_height = int(60 * GameConfig.SCALE_FACTOR)  # Smaller button height
		spacing = int(25 * GameConfig.SCALE_FACTOR)  # Smaller spacing
		
		# Get enabled domains from GameConfig
		enabled_domains = GameConfig.get_enabled_domains()
		enabled_domains_list = list(enabled_domains.items())
		num_domains = len(enabled_domains_list)
		
		self.domain_buttons = []
		
		if num_domains <= 4:
			# Single column layout in the middle
			start_y = screen_height // 2 - ((num_domains * (button_height + spacing)) // 2)
			for i, (domain_name, sheet_name) in enumerate(enabled_domains_list):
				x = screen_width // 2 - button_width // 2
				y = start_y + i * (button_height + spacing)
				# Get domain-specific colors
				colors = GameConfig.get_domain_colors(domain_name)
				btn = create_text_button(domain_name, x, y, button_width, button_height, domain_font, colors)
				self.domain_buttons.append((domain_name, btn))
		else:
			# Two-column layout: 4 on left, remaining on right
			left_domains = enabled_domains_list[:4]
			right_domains = enabled_domains_list[4:8]  # Max 4 on right side
			
			# Calculate positions for left column
			left_start_y = screen_height // 2 - ((len(left_domains) * (button_height + spacing)) // 2)
			left_x = screen_width // 2 - button_width - int(50 * GameConfig.SCALE_FACTOR)  # Left side
			
			# Calculate positions for right column
			right_start_y = screen_height // 2 - ((len(right_domains) * (button_height + spacing)) // 2)
			right_x = screen_width // 2 + int(50 * GameConfig.SCALE_FACTOR)  # Right side
			
			# Create left column buttons
			for i, (domain_name, sheet_name) in enumerate(left_domains):
				y = left_start_y + i * (button_height + spacing)
				colors = GameConfig.get_domain_colors(domain_name)
				btn = create_text_button(domain_name, left_x, y, button_width, button_height, domain_font, colors)
				self.domain_buttons.append((domain_name, btn))
			
			# Create right column buttons
			for i, (domain_name, sheet_name) in enumerate(right_domains):
				y = right_start_y + i * (button_height + spacing)
				colors = GameConfig.get_domain_colors(domain_name)
				btn = create_text_button(domain_name, right_x, y, button_width, button_height, domain_font, colors)
				self.domain_buttons.append((domain_name, btn))

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
	
	def reset_platform_states(self):
		"""Reset all platform states (like question_shown flags)"""
		for platform in self.plat_group:
			platform.question_shown = False

	def wrap_text(self, text, font, max_width):
		"""Wrap text to fit within max_width"""
		words = text.split(' ')
		lines = []
		current_line = []
		
		for word in words:
			# Test if adding this word exceeds the width
			test_line = ' '.join(current_line + [word])
			test_width = font.size(test_line)[0]
			
			if test_width <= max_width:
				current_line.append(word)
			else:
				if current_line:
					lines.append(' '.join(current_line))
				current_line = [word]
		
		if current_line:
			lines.append(' '.join(current_line))
			
		return lines

	def save_player_details(self, username, points, rank=None, game_status="Completed"):
		"""Save player details to PlayerDetails sheet in questions.xlsx"""
		try:
			excel_file = 'scripts/questions.xlsx'
			
			# Check if file exists
			if not os.path.exists(excel_file):
				print(f"Excel file {excel_file} not found. Cannot save player details.")
				return False
			
			# Read existing data or create new
			try:
				with pd.ExcelFile(excel_file) as xls:
					if 'PlayerDetails' in xls.sheet_names:
						# Read existing PlayerDetails sheet
						df = pd.read_excel(excel_file, sheet_name='PlayerDetails')
						# Check if GameStatus column exists, if not add it
						if 'GameStatus' not in df.columns:
							df['GameStatus'] = 'Completed'  # Default for existing entries
					else:
						# Create new PlayerDetails sheet with headers
						df = pd.DataFrame(columns=['Username', 'Score', 'Rank', 'Date', 'Time', 'GameStatus'])
			except Exception as e:
				print(f"Error reading Excel file: {e}")
				# Create new DataFrame if reading fails
				df = pd.DataFrame(columns=['Username', 'Score', 'Rank', 'Date', 'Time', 'GameStatus'])
			
			# Get current date and time
			now = datetime.now()
			current_date = now.strftime("%Y-%m-%d")
			current_time = now.strftime("%H:%M:%S")
			
			# Create new row
			new_row = {
				'Username': username if username else 'Anonymous',
				'Score': points,
				'Rank': rank if rank else 'None',
				'Date': current_date,
				'Time': current_time,
				'GameStatus': game_status
			}
			
			# Add new row to DataFrame
			df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
			
			# Save to Excel file
			with pd.ExcelWriter(excel_file, mode='a', if_sheet_exists='replace') as writer:
				df.to_excel(writer, sheet_name='PlayerDetails', index=False)
			
			print(f"Player details saved successfully: {username} - {points} points - {rank} - {game_status}")
			return True
			
		except Exception as e:
			print(f"Error saving player details: {e}")
			traceback.print_exc()
			return False

	def get_leaderboard_data(self):
		"""Get top 5 players from PlayerDetails sheet based on points"""
		try:
			excel_file = 'scripts/questions.xlsx'
			
			if not os.path.exists(excel_file):
				return []
			
			# Read PlayerDetails sheet
			df = pd.read_excel(excel_file, sheet_name='PlayerDetails')
			
			if df.empty:
				return []
			
			# Sort by Score in descending order and get top 5
			df_sorted = df.sort_values('Score', ascending=False).head(5)
			
			# Convert to list of dictionaries
			leaderboard = []
			for _, row in df_sorted.iterrows():
				leaderboard.append({
					'username': str(row['Username']),
					'score': int(row['Score']),
					'rank': str(row['Rank']) if pd.notna(row['Rank']) else 'None',
					'date': str(row['Date']) if pd.notna(row['Date']) else 'Unknown'
				})
			
			return leaderboard
			
		except Exception as e:
			print(f"Error reading leaderboard data: {e}")
			return []

	def check_username_exists(self, username):
		"""Check if a username already exists in the PlayerDetails sheet"""
		try:
			excel_file = 'scripts/questions.xlsx'
			
			if not os.path.exists(excel_file):
				return False
			
			# Read PlayerDetails sheet
			df = pd.read_excel(excel_file, sheet_name='PlayerDetails')
			
			if df.empty:
				return False
			
			# Check if username exists (case-insensitive)
			username_exists = df['Username'].str.lower().str.contains(username.lower(), na=False).any()
			return username_exists
			
		except Exception as e:
			print(f"Error checking username: {e}")
			return False

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
			self.chaser.delay = GameConfig.CHASER_DELAY_MS  # Ensure delay is always set from config

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
		# Create a gradient background surface for the full display size
		gradient_bg = pygame.Surface((display_width, display_height))
		# Sky blue gradient: top is light blue, bottom is deeper blue
		top_color = (135, 206, 250)    # Light sky blue (top)
		bottom_color = (70, 130, 180)  # Steel blue (bottom)
		for y in range(display_height):
			ratio = y / display_height
			r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
			g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
			b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
			pygame.draw.line(gradient_bg, (r, g, b), (0, y), (display_width, y))
		# Add subtle clouds
		cloud_colors = [
			(255, 255, 255, 38), (245, 245, 245, 32), (230, 240, 255, 26), (255, 255, 255, 18)
		]
		num_clouds = max(10, display_width // 160)
		for _ in range(num_clouds):
			cw = random.randint(180, 320)
			ch = random.randint(60, 110)
			cloud_surface = pygame.Surface((cw, ch), pygame.SRCALPHA)
			base_x = random.randint(0, display_width - cw)
			base_y = random.randint(20, int(display_height * 0.45))
			# Draw 3-5 overlapping ellipses for a soft cloud
			for _ in range(random.randint(3, 5)):
				ellipse_w = random.randint(int(cw * 0.4), cw)
				ellipse_h = random.randint(int(ch * 0.5), ch)
				ellipse_x = random.randint(-20, cw - ellipse_w + 20)
				ellipse_y = random.randint(0, int(ch * 0.5))
				color = random.choice(cloud_colors)
				pygame.draw.ellipse(cloud_surface, color, (ellipse_x, ellipse_y, ellipse_w, ellipse_h))
			# Add a gentle vertical alpha fade to the cloud for realism
			fade = pygame.Surface((cw, ch), pygame.SRCALPHA)
			for y in range(ch):
				fade_alpha = int(255 * (1 - (y / ch))**1.5)  # More transparent at bottom
				pygame.draw.line(fade, (255, 255, 255, fade_alpha), (0, y), (cw, y))
			cloud_surface.blit(fade, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
			gradient_bg.blit(cloud_surface, (base_x, base_y), special_flags=pygame.BLEND_PREMULTIPLIED)
		while(run):
			# Draw the gradient background
			screen.blit(gradient_bg, (0, 0))
			# Clear the game surface (optional, for transparency)
			game_surface.fill((0, 0, 0))
			world.draw_world()

			# Check for instructions screen first
			if self.show_instructions:
				print("Rendering instructions screen!")  # Debug print
				# Instructions Screen with Professional Black Gradient Background
				# Create sophisticated gradient background
				for y in range(screen_height):
					ratio = y / screen_height
					r = int(10 * (1 - ratio) + 25 * ratio)
					g = int(10 * (1 - ratio) + 25 * ratio)
					b = int(15 * (1 - ratio) + 35 * ratio)
					pygame.draw.line(game_surface, (r, g, b), (0, y), (screen_width, y))
				
				# Add subtle animated stars effect
				star_positions = [(100, 150), (300, 200), (500, 180), (700, 220), (900, 160)]
				for i, (x, y) in enumerate(star_positions):
					star_alpha = int(100 + 50 * abs(math.sin(pygame.time.get_ticks() * 0.001 + i)))
					star_surface = pygame.Surface((4, 4), pygame.SRCALPHA)
					pygame.draw.circle(star_surface, (255, 255, 255, star_alpha), (2, 2), 2)
					game_surface.blit(star_surface, (x, y))
				
				# Main title with glow effect
				title_font = pygame.font.SysFont('comicsansms', int(48 * GameConfig.SCALE_FACTOR))
				title_text = title_font.render("📚 GAME INSTRUCTIONS 📚", True, (255, 215, 0))
				title_rect = title_text.get_rect(center=(screen_width // 2, int(80 * GameConfig.SCALE_FACTOR)))
				
				# Add glow effect to title
				glow_surface = pygame.Surface((title_rect.width + 20, title_rect.height + 20), pygame.SRCALPHA)
				for i in range(10):
					alpha = 50 - i * 5
					glow_text = title_font.render("📚 GAME INSTRUCTIONS 📚", True, (255, 215, 0))
					glow_rect = glow_text.get_rect(center=(glow_surface.get_width() // 2, glow_surface.get_height() // 2))
					glow_surface.blit(glow_text, glow_rect)
				game_surface.blit(glow_surface, (title_rect.x - 10, title_rect.y - 10))
				game_surface.blit(title_text, title_rect)
				
				# Create elegant content container
				content_width = int(800 * GameConfig.SCALE_FACTOR)
				content_height = int(600 * GameConfig.SCALE_FACTOR)
				content_x = (screen_width - content_width) // 2
				content_y = int(140 * GameConfig.SCALE_FACTOR)
				
				# Glass effect background for content
				content_bg = pygame.Surface((content_width, content_height), pygame.SRCALPHA)
				for y in range(content_height):
					ratio = y / content_height
					r = int(20 * (1 - ratio) + 40 * ratio)
					g = int(20 * (1 - ratio) + 40 * ratio)
					b = int(30 * (1 - ratio) + 60 * ratio)
					pygame.draw.line(content_bg, (r, g, b, 200), (0, y), (content_width, y))
				
				# Add glass border with glow
				pygame.draw.rect(content_bg, (255, 255, 255, 40), content_bg.get_rect(), 3, border_radius=25)
				pygame.draw.rect(content_bg, (100, 150, 255, 120), content_bg.get_rect(), 1, border_radius=25)
				game_surface.blit(content_bg, (content_x, content_y))
				
				# Professional instructions content
				instructions_content = [
					("Your mission: Reach the final flag to complete the game and secure your victory.", 0),
					("Each level is timed — you have 60 seconds to reach the end.", 0),
					("Stay alert: A dangerous bird enemy appears after 40 seconds to increase the challenge.", 0),
					("Earn points by answering questions that appear during the level.", 0),
					
					("Scoring System:", 1),
					("• Level 1 questions = 3 points", 1),
					("• Level 2 questions = 5 points", 1),
					("• Level 3 questions = 8 points (or 6 points when using AI Assist)", 1),
					("• You have 15 seconds to answer each question", 1),
					("• Incorrect answers earn 0 points — choose carefully!", 1),

					("Ranks & Achievements:", 1),
					("• 🏆 Legend: Score 32 points or more", 1),
					("• ⚔️ Gladiator: Score 24 points or more", 1),
					("• 🛡️ Warrior: Score 20 points or more", 1),
					
					("Need help? Use AI Assist to receive intelligent hints during tough questions.", 0)
				]

				
				# Render instructions with professional formatting
				section_font = pygame.font.SysFont('comicsansms', int(22 * GameConfig.SCALE_FACTOR))
				content_font = pygame.font.SysFont('comicsansms', int(18 * GameConfig.SCALE_FACTOR))
				line_height = int(28 * GameConfig.SCALE_FACTOR)
				section_spacing = int(35 * GameConfig.SCALE_FACTOR)
				
				current_y = content_y + int(40 * GameConfig.SCALE_FACTOR)
				left_margin = content_x + int(40 * GameConfig.SCALE_FACTOR)
				right_margin = content_x + content_width - int(40 * GameConfig.SCALE_FACTOR)
				
				for instruction_text, indent_level in instructions_content:
					# Calculate indentation based on indent level
					indent_offset = int(30 * GameConfig.SCALE_FACTOR * indent_level)
					text_x = left_margin + indent_offset
					
					# Add bullet point for indented items
					if indent_level > 0:
						bullet_text = "• " + instruction_text
					else:
						bullet_text = instruction_text
					
					# Render instruction text with proper wrapping
					content_lines = self.wrap_text(bullet_text, content_font, right_margin - text_x)
					for line in content_lines:
						content_surface = content_font.render(line, True, (220, 220, 220))
						game_surface.blit(content_surface, (text_x, current_y))
						current_y += line_height
					
					# Add small spacing between instructions
					current_y += int(10 * GameConfig.SCALE_FACTOR)
				
				# Back button with professional styling
				back_button_width = int(200 * GameConfig.SCALE_FACTOR)
				back_button_height = int(50 * GameConfig.SCALE_FACTOR)
				back_button_x = (screen_width - back_button_width) // 2
				back_button_y = content_y + content_height + int(30 * GameConfig.SCALE_FACTOR)
				
				# Create gradient background for back button
				back_button_bg = pygame.Surface((back_button_width, back_button_height), pygame.SRCALPHA)
				for y in range(back_button_height):
					ratio = y / back_button_height
					r = int(60 * (1 - ratio) + 100 * ratio)
					g = int(80 * (1 - ratio) + 120 * ratio)
					b = int(120 * (1 - ratio) + 160 * ratio)
					pygame.draw.line(back_button_bg, (r, g, b, 220), (0, y), (back_button_width, y))
				
				# Add button border and glow
				pygame.draw.rect(back_button_bg, (255, 255, 255, 60), back_button_bg.get_rect(), 2, border_radius=15)
				pygame.draw.rect(back_button_bg, (100, 150, 255, 150), back_button_bg.get_rect(), 1, border_radius=15)
				game_surface.blit(back_button_bg, (back_button_x, back_button_y))
				
				# Back button text
				back_text_font = pygame.font.SysFont('comicsansms', int(20 * GameConfig.SCALE_FACTOR))
				back_text = back_text_font.render("← Back to Menu", True, (255, 255, 255))
				back_text_rect = back_text.get_rect(center=(back_button_x + back_button_width // 2, back_button_y + back_button_height // 2))
				game_surface.blit(back_text, back_text_rect)
				
				# Handle back button click
				back_button_rect = pygame.Rect(back_button_x, back_button_y, back_button_width, back_button_height)
				if pygame.mouse.get_pressed()[0]:  # Left mouse button
					mouse_pos = pygame.mouse.get_pos()
					adjusted_mouse_pos = (mouse_pos[0] - surf_x, mouse_pos[1] - surf_y)
					if back_button_rect.collidepoint(adjusted_mouse_pos):
						self.show_instructions = False
			
			# setup main menu
			elif in_menu:
				# Create beautiful gradient black background for main menu
				menu_bg = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
				# Create a sophisticated dark gradient: black to dark blue to dark purple
				for y in range(screen_height):
					ratio = y / screen_height
					# Start with pure black, transition to dark blue, then to dark purple
					if ratio < 0.3:
						# Black to dark blue (first 30%)
						progress = ratio / 0.3
						r = int(0 + 20 * progress)
						g = int(0 + 30 * progress)
						b = int(0 + 50 * progress)
					elif ratio < 0.7:
						# Dark blue to dark purple (30% to 70%)
						progress = (ratio - 0.3) / 0.4
						r = int(20 + 30 * progress)
						g = int(30 + 20 * progress)
						b = int(50 + 40 * progress)
					else:
						# Dark purple to very dark purple (last 30%)
						progress = (ratio - 0.7) / 0.3
						r = int(50 + 20 * progress)
						g = int(50 + 15 * progress)
						b = int(90 + 25 * progress)
					
					pygame.draw.line(menu_bg, (r, g, b, 255), (0, y), (screen_width, y))
				
				# Add subtle animated stars/particles effect
				star_alpha = int(100 + 50 * (pygame.time.get_ticks() % 2000) / 2000)
				for i in range(20):
					star_x = (i * 97) % screen_width
					star_y = (i * 73 + pygame.time.get_ticks() // 50) % screen_height
					star_size = 1 + (i % 3)
					pygame.draw.circle(menu_bg, (255, 255, 255, star_alpha), (star_x, star_y), star_size)
				
				game_surface.blit(menu_bg, (0, 0))
				
				# --- Draw Game Title with Glow Effect ---
				title_font = pygame.font.SysFont('comicsansms', int(48 * GameConfig.SCALE_FACTOR))
				title_text = title_font.render("🎮 MAZE RUNNER 🎮", True, (255, 215, 0))
				title_rect = title_text.get_rect(center=(screen_width // 2, int(80 * GameConfig.SCALE_FACTOR)))
				
				# Draw title glow effect
				glow_font = pygame.font.SysFont('comicsansms', int(48 * GameConfig.SCALE_FACTOR))
				glow_text = glow_font.render("🎮 MAZE RUNNER 🎮", True, (255, 215, 0, 50))
				glow_rect = glow_text.get_rect(center=(screen_width // 2 + 2, int(80 * GameConfig.SCALE_FACTOR) + 2))
				game_surface.blit(glow_text, glow_rect)
				
				# Draw main title
				game_surface.blit(title_text, title_rect)
				
				# --- Clean Two-Column Layout ---
				# Calculate column positions for perfect symmetry
				column_width = int(400 * GameConfig.SCALE_FACTOR)
				column_spacing = int(100 * GameConfig.SCALE_FACTOR)
				total_width = (2 * column_width) + column_spacing
				start_x = (screen_width - total_width) // 2
				
				# Column 1: Username Input and Play Button (Left)
				left_x = start_x
				left_y = int(180 * GameConfig.SCALE_FACTOR)
				left_width = column_width
				left_height = int(450 * GameConfig.SCALE_FACTOR)
				
				# Create left section background with glass effect
				left_bg = pygame.Surface((left_width, left_height), pygame.SRCALPHA)
				for y in range(left_height):
					ratio = y / left_height
					r = int(40 * (1 - ratio) + 70 * ratio)
					g = int(50 * (1 - ratio) + 60 * ratio)
					b = int(90 * (1 - ratio) + 130 * ratio)
					pygame.draw.line(left_bg, (r, g, b, 180), (0, y), (left_width, y))
				
				# Add glass border
				pygame.draw.rect(left_bg, (255, 255, 255, 30), left_bg.get_rect(), 3, border_radius=20)
				pygame.draw.rect(left_bg, (100, 150, 255, 100), left_bg.get_rect(), 1, border_radius=20)
				game_surface.blit(left_bg, (left_x, left_y))
				
				# Left section title
				left_title_font = pygame.font.SysFont('comicsansms', int(26 * GameConfig.SCALE_FACTOR))
				left_title = left_title_font.render("🎮 START GAME 🎮", True, (255, 215, 0))
				left_title_rect = left_title.get_rect(center=(left_x + left_width // 2, left_y + int(30 * GameConfig.SCALE_FACTOR)))
				game_surface.blit(left_title, left_title_rect)
				
				# Username label
				username_label_font = pygame.font.SysFont('comicsansms', int(22 * GameConfig.SCALE_FACTOR))
				username_label = username_label_font.render("Enter Username:", True, (255, 255, 255))
				label_x = left_x + int(40 * GameConfig.SCALE_FACTOR)
				label_y = left_y + int(100 * GameConfig.SCALE_FACTOR)
				game_surface.blit(username_label, (label_x, label_y))
				
				# Username input field
				username_y = label_y + username_label.get_height() + int(20 * GameConfig.SCALE_FACTOR)
				username_width = left_width - int(80 * GameConfig.SCALE_FACTOR)
				username_height = int(55 * GameConfig.SCALE_FACTOR)
				username_x = left_x + int(40 * GameConfig.SCALE_FACTOR)
				
				# Create gradient background for username field
				username_bg = pygame.Surface((username_width, username_height), pygame.SRCALPHA)
				if self.username_active:
					# Active state: Blue to purple gradient with glow effect
					for y in range(username_height):
						ratio = y / username_height
						r = int(100 * (1 - ratio) + 150 * ratio)
						g = int(150 * (1 - ratio) + 100 * ratio)
						b = int(255 * (1 - ratio) + 200 * ratio)
						pygame.draw.line(username_bg, (r, g, b, 180), (0, y), (username_width, y))
					
					# Add glowing border
					pygame.draw.rect(username_bg, (255, 255, 255, 100), username_bg.get_rect(), 4, border_radius=15)
					pygame.draw.rect(username_bg, (100, 200, 255, 255), username_bg.get_rect(), 2, border_radius=15)
				else:
					# Inactive state: Subtle gradient with border
					for y in range(username_height):
						ratio = y / username_height
						r = int(60 * (1 - ratio) + 80 * ratio)
						g = int(80 * (1 - ratio) + 100 * ratio)
						b = int(120 * (1 - ratio) + 140 * ratio)
						pygame.draw.line(username_bg, (r, g, b, 120), (0, y), (username_width, y))
					
					pygame.draw.rect(username_bg, (255, 255, 255, 80), username_bg.get_rect(), 2, border_radius=15)
				
				game_surface.blit(username_bg, (username_x, username_y))
				
				# Username text inside the field
				username_font = pygame.font.SysFont('comicsansms', int(22 * GameConfig.SCALE_FACTOR))
				if self.username:
					username_text = username_font.render(self.username, True, (255, 255, 255))
				else:
					username_text = username_font.render("Type here...", True, (200, 200, 200))
				
				text_x = username_x + int(25 * GameConfig.SCALE_FACTOR)
				text_y = username_y + (username_height - username_text.get_height()) // 2
				game_surface.blit(username_text, (text_x, text_y))
				
				# Animated cursor with glow effect
				if self.username_active and (self.cursor_blink_timer // 30) % 2 == 0:
					cursor_x = text_x + username_text.get_width() + 3
					cursor_y = text_y
					cursor_height = username_text.get_height()
					# Draw glowing cursor
					pygame.draw.line(game_surface, (255, 255, 255, 100), (cursor_x-1, cursor_y), (cursor_x-1, cursor_y + cursor_height), 4)
					pygame.draw.line(game_surface, (100, 200, 255, 255), (cursor_x, cursor_y), (cursor_x, cursor_y + cursor_height), 2)
				
				# Username input box click detection and cursor change
				username_rect = pygame.Rect(username_x, username_y, username_width, username_height)
				if username_rect.collidepoint(pygame.mouse.get_pos()):
					pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_IBEAM)
				else:
					pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

				# Play button below username field
				play_button_y = username_y + username_height + int(40 * GameConfig.SCALE_FACTOR)
				self.play_button.rect.topleft = (left_x + (left_width - self.play_button.rect.width) // 2, play_button_y)
				
				# Position instructions button
				instructions_button_y = play_button_y + self.play_button.rect.height + int(25 * GameConfig.SCALE_FACTOR)
				self.instructions_button.rect.topleft = (left_x + (left_width - self.instructions_button.rect.width) // 2, instructions_button_y)
				

				
				# Display username error message if needed
				if self.show_duplicate_message:
					error_font = pygame.font.SysFont('comicsansms', int(18 * GameConfig.SCALE_FACTOR))
					if self.username_error_type == "missing":
						error_text = error_font.render("⚠️  Please enter a username to continue!", True, (255, 100, 100))
					else:  # duplicate
						error_text = error_font.render("Username has already been used!", True, (255, 100, 100))
					error_rect = error_text.get_rect(center=(left_x + left_width // 2, play_button_y + self.play_button.rect.height + int(100 * GameConfig.SCALE_FACTOR)))
					game_surface.blit(error_text, error_rect)
				
				# Column 2: Leaderboard (Right)
				leaderboard_x = start_x + column_width + column_spacing
				leaderboard_y = int(180 * GameConfig.SCALE_FACTOR)
				leaderboard_width = column_width
				leaderboard_height = int(450 * GameConfig.SCALE_FACTOR)
				
				# Create leaderboard background with glass effect
				leaderboard_bg = pygame.Surface((leaderboard_width, leaderboard_height), pygame.SRCALPHA)
				for y in range(leaderboard_height):
					ratio = y / leaderboard_height
					alpha = int(180 * (1 - ratio) + 220 * ratio)
					pygame.draw.line(leaderboard_bg, (20, 30, 50, alpha), (0, y), (leaderboard_width, y))
				
				# Add glass border
				pygame.draw.rect(leaderboard_bg, (255, 255, 255, 30), leaderboard_bg.get_rect(), 3, border_radius=20)
				pygame.draw.rect(leaderboard_bg, (100, 150, 255, 80), leaderboard_bg.get_rect(), 1, border_radius=20)
				game_surface.blit(leaderboard_bg, (leaderboard_x, leaderboard_y))
				
				# Leaderboard title
				leaderboard_title_font = pygame.font.SysFont('comicsansms', int(26 * GameConfig.SCALE_FACTOR))
				leaderboard_title = leaderboard_title_font.render("🏆 LEADERBOARD 🏆", True, (255, 215, 0))
				leaderboard_title_rect = leaderboard_title.get_rect(center=(leaderboard_x + leaderboard_width // 2, leaderboard_y + int(30 * GameConfig.SCALE_FACTOR)))
				game_surface.blit(leaderboard_title, leaderboard_title_rect)
				
				# Get and display leaderboard data
				leaderboard_data = self.get_leaderboard_data()
				if leaderboard_data:
					entry_height = int(50 * GameConfig.SCALE_FACTOR)
					entry_spacing = int(12 * GameConfig.SCALE_FACTOR)
					start_y = leaderboard_y + int(80 * GameConfig.SCALE_FACTOR)
					
					for i, entry in enumerate(leaderboard_data):
						entry_y = start_y + i * (entry_height + entry_spacing)
						
						# Medal emojis for top 3
						medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
						
						# Entry background with rank-based colors
						entry_bg = pygame.Surface((leaderboard_width - int(40 * GameConfig.SCALE_FACTOR), entry_height), pygame.SRCALPHA)
						if i == 0:  # Gold
							color = (255, 215, 0, 100)
						elif i == 1:  # Silver
							color = (192, 192, 192, 100)
						elif i == 2:  # Bronze
							color = (205, 127, 50, 100)
						else:  # Regular
							color = (255, 255, 255, 60)
						
						entry_bg.fill(color)
						pygame.draw.rect(entry_bg, (255, 255, 255, 80), entry_bg.get_rect(), 2, border_radius=12)
						
						entry_x = leaderboard_x + int(20 * GameConfig.SCALE_FACTOR)
						game_surface.blit(entry_bg, (entry_x, entry_y))
						
						# Medal and rank
						medal_font = pygame.font.SysFont('comicsansms', int(22 * GameConfig.SCALE_FACTOR))
						medal_text = medal_font.render(medal, True, (255, 255, 255))
						medal_rect = medal_text.get_rect(midleft=(entry_x + int(15 * GameConfig.SCALE_FACTOR), entry_y + entry_height // 2))
						game_surface.blit(medal_text, medal_rect)
						
						# Username
						username_font = pygame.font.SysFont('comicsansms', int(18 * GameConfig.SCALE_FACTOR))
						username_text = username_font.render(entry['username'][:15], True, (255, 255, 255))
						username_rect = username_text.get_rect(midleft=(entry_x + int(70 * GameConfig.SCALE_FACTOR), entry_y + entry_height // 2))
						game_surface.blit(username_text, username_rect)
						
						# Score
						score_font = pygame.font.SysFont('comicsansms', int(20 * GameConfig.SCALE_FACTOR))
						score_text = score_font.render(str(entry['score']), True, (255, 215, 0))
						score_rect = score_text.get_rect(midright=(entry_x + leaderboard_width - int(60 * GameConfig.SCALE_FACTOR), entry_y + entry_height // 2))
						game_surface.blit(score_text, score_rect)
						
						# Rank (if available)
						if entry['rank'] != 'None':
							rank_font = pygame.font.SysFont('comicsansms', int(14 * GameConfig.SCALE_FACTOR))
							rank_text = rank_font.render(entry['rank'], True, (200, 220, 255))
							rank_rect = rank_text.get_rect(midright=(entry_x + leaderboard_width - int(20 * GameConfig.SCALE_FACTOR), entry_y + entry_height // 2))
							game_surface.blit(rank_text, rank_rect)
				else:
					# No data message
					no_data_font = pygame.font.SysFont('comicsansms', int(20 * GameConfig.SCALE_FACTOR))
					no_data_text = no_data_font.render("No leaderboard data yet", True, (150, 150, 150))
					no_data_rect = no_data_text.get_rect(center=(leaderboard_x + leaderboard_width // 2, leaderboard_y + int(250 * GameConfig.SCALE_FACTOR)))
					game_surface.blit(no_data_text, no_data_rect)

				surf_x = (display_width - GAME_SURFACE_WIDTH) // 2
				surf_y = (display_height - GAME_SURFACE_HEIGHT) // 2
				

				
				if self.play_button.draw(game_surface, offset=(surf_x, surf_y)):
					# Check if username is entered
					if not self.username.strip():
						self.show_duplicate_message = True
						self.username_error_type = "missing"
						self.duplicate_message_timer = 180  # Show message for 3 seconds (60 FPS * 3)
					# Check if username already exists before proceeding
					elif self.username.strip() and self.check_username_exists(self.username.strip()):
						self.show_duplicate_message = True
						self.username_error_type = "duplicate"
						self.duplicate_message_timer = 180  # Show message for 3 seconds (60 FPS * 3)
					else:
						in_menu = False
						in_domain_select = True
						points = 0  # Reset points when starting new game
						self.timer_started = False
						# Reset all game state variables to ensure clean start
						global selected_domain, game_over, game_finished, current_level
						selected_domain = None
						game_over = 0
						game_finished = False
						current_level = 0
						self.level1_wrong_answers = 0  # Reset Level 1 wrong answer counter
				
				# Handle instructions button click
				if self.instructions_button.draw(game_surface, offset=(surf_x, surf_y)):
					print("Instructions button clicked!")  # Debug print
					self.show_instructions = True
					print(f"show_instructions set to: {self.show_instructions}")  # Debug print

			
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

						# Pass the selected domain's sheet name to QuestionUI
						enabled_domains = GameConfig.get_enabled_domains()
						sheet_name = enabled_domains[selected_domain]

						try:
							self.question_ui = QuestionUI(game_surface, sheet_name)
							# Reload level to get fresh game objects
							values = self.load_level()
							player = values[0]
							world = values[1]
							chaser = values[2]

							# Start timer only after domain is selected
							self.game_timer()
							self.timer_started = True

						except Exception as e:
							print(f"Error loading domain {selected_domain}: {e}")
							# If there's an error, go back to domain selection
							in_domain_select = True
							selected_domain = None

			else:
				world.draw_tiles()
				check_points[0].draw(game_surface)
				lava_tiles[0].draw(game_surface)
				# Draw platforms and labels, then player (so player overlaps label)
				draw_platforms_with_labels(game_surface, self.score_font, draw_labels_only=False)
				player.draw_player(game_surface, self.question_ui.is_game_paused())
				chaser.update(player, self.question_ui.is_game_paused())
				if not self.question_ui.is_game_paused():
					plats[0].update()
					chaser.draw(game_surface)
					if self.timer_started:
						timer_surface = self.timer_font.render(self.timer_text, True, (47, 48, 29))
						timer_rect = timer_surface.get_rect()
						timer_rect.topleft = (60, 42)
						game_surface.blit(timer_surface, timer_rect)

						# Draw score
						game_surface.blit(self.score_font.render(f"Score: {points}", True, (47, 48, 29)), (screen_width - 150, 42))
						
						# Draw username if available
						if self.username:
							username_surface = self.score_font.render(f"Player: {self.username}", True, (47, 48, 29))
							game_surface.blit(username_surface, (60, 70))
					
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
						# Calculate 20% detection range on both sides of the platform
						platform_width = platform.rect.width
						detection_margin = int(platform_width * 0.2)  # 20% of platform width
						
						# Extended detection area: 20% left and 20% right of platform boundaries
						left_detection_bound = platform.rect.left - detection_margin
						right_detection_bound = platform.rect.right + detection_margin
						
						if (
							not platform.question_shown and 
							abs(player.rect.bottom - platform.rect.top) <= 5 and  # Vertical tolerance
							player.rect.right > left_detection_bound and   # Player extends into left detection zone
							player.rect.left < right_detection_bound and   # Player extends into right detection zone
							not player.in_air
						):
							platform.question_shown = True
							# Select question complexity based on platform index
							if idx in [2, 4, 1]:
								complexity = 'Level 1'
							elif idx in [0, 3]:
								complexity = 'Level 2'
							elif idx in [5]:
								complexity = 'Level 3'
							else:
								complexity = ''  # fallback: any
							self.question_ui.show_random_question_by_complexity(complexity, show_ask_ai=True)
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
					
					# Save player details when game ends (game over or insufficient points)
					if not self.player_details_saved:
						rank = None
						if points >= 30:
							rank = 'Legend'
						elif points >= 24:
							rank = 'Gladiator'
						elif points >= 20:
							rank = 'Warrior'
						
						# Save player details with game status
						game_status = "Insufficient Points" if self.insufficient_points else "Game Over"
						if self.save_player_details(self.username, points, rank, game_status):
							self.player_details_saved = True
					
					# Draw game over message and score with gradient box
					title_font = pygame.font.SysFont('comicsansms', int(50 * GameConfig.SCALE_FACTOR))
					subtitle_font = pygame.font.SysFont('comicsansms', int(30 * GameConfig.SCALE_FACTOR))
					
					# Prepare all text elements first to calculate box size
					text_elements = []
					
					if self.insufficient_points:
						# Main title for insufficient points
						title = title_font.render("Better Luck Next Time!", True, (255, 255, 255))
						text_elements.append(title)
						
						# Score message
						score_text = subtitle_font.render(f"Points Required: {POINTS_THRESHOLD}, Your Score: {points}", True, (255, 255, 255))
						text_elements.append(score_text)
					else:
						# Regular game over message
						title = title_font.render("Game Over!", True, (255, 255, 255))
						text_elements.append(title)
						
						# Score message
						score_text = subtitle_font.render(f"Total Score: {points}", True, (255, 255, 255))
						text_elements.append(score_text)
						
						# Username message
						if self.username:
							username_text = subtitle_font.render(f"Player: {self.username}", True, (255, 255, 255))
							text_elements.append(username_text)
					
					# --- Show Rank (Game Over) ---
					rank = None
					rank_text = None
					if points >= 30:
						rank = 'Legend'
					elif points >= 24:
						rank = 'Gladiator'
					elif points >= 20:
						rank = 'Warrior'
					if rank:
						rank_font = pygame.font.SysFont('comicsansms', int(40 * GameConfig.SCALE_FACTOR))
						rank_text = rank_font.render(f'Rank: {rank}', True, (255, 215, 0))
						text_elements.append(rank_text)
					
					# Calculate box dimensions based on text elements
					max_width = max([text.get_width() for text in text_elements]) if text_elements else 400
					padding = int(60 * GameConfig.SCALE_FACTOR)
					box_width = max_width + padding * 2
					box_height = int(350 * GameConfig.SCALE_FACTOR)  # Fixed height for consistent appearance
					
					# Center the box on screen
					box_x = (screen_width - box_width) // 2
					box_y = (screen_height - box_height) // 2 - int(50 * GameConfig.SCALE_FACTOR)
					box_rect = pygame.Rect(box_x, box_y, box_width, box_height)
					
					# Draw gradient background box
					if self.insufficient_points:
						# Red gradient for insufficient points
						draw_gradient_box(game_surface, box_rect, (80, 20, 20), (40, 10, 10), 220)
					else:
						# Blue-purple gradient for regular game over
						draw_gradient_box(game_surface, box_rect, (30, 30, 80), (15, 15, 40), 220)
					
					# Position and draw text elements within the box
					current_y = box_y + padding
					line_spacing = int(50 * GameConfig.SCALE_FACTOR)
					
					# Draw title
					title_rect = title.get_rect(center=(screen_width//2, current_y + title.get_height()//2))
					game_surface.blit(title, title_rect)
					current_y += title.get_height() + line_spacing
					
					# Draw score
					score_rect = score_text.get_rect(center=(screen_width//2, current_y + score_text.get_height()//2))
					game_surface.blit(score_text, score_rect)
					current_y += score_text.get_height() + line_spacing
					
					# Draw username if present
					if self.username and not self.insufficient_points:
						username_text = subtitle_font.render(f"Player: {self.username}", True, (255, 255, 255))
						username_rect = username_text.get_rect(center=(screen_width//2, current_y + username_text.get_height()//2))
						game_surface.blit(username_text, username_rect)
						current_y += username_text.get_height() + line_spacing
					
					# Draw rank if present
					if rank_text:
						rank_rect = rank_text.get_rect(center=(screen_width//2, current_y + rank_text.get_height()//2))
						game_surface.blit(rank_text, rank_rect)
						current_y += rank_text.get_height() + line_spacing
					
					# Update bottom_text_y for button positioning
					bottom_text_y = current_y
					
					# Position restart button below all text with generous spacing
					restart_button_y = bottom_text_y + int(80 * GameConfig.SCALE_FACTOR)
					
					# Ensure button doesn't go below screen bounds
					if restart_button_y + self.resume_button.rect.height > screen_height - int(50 * GameConfig.SCALE_FACTOR):
						restart_button_y = screen_height - int(50 * GameConfig.SCALE_FACTOR) - self.resume_button.rect.height
					
					# Update button position
					restart_x = screen_width // 2 - self.resume_button.rect.width // 2
					self.resume_button.rect.topleft = (restart_x, restart_button_y)

					if self.resume_button.draw(game_surface, offset=(surf_x, surf_y)):
						# Reset game state and go back to main menu
						current_level = 0
						points = 0
						game_finished = False
						game_over = 0
						in_menu = True
						in_domain_select = False
						
						# Reset timer
						self.timer_counter = 0
						self.timer_started = False
						
						# Reset insufficient points flag
						self.insufficient_points = False
						
						# Reset question UI and question pool
						if self.question_ui:
							self.question_ui.reset()
							self.question_ui.reset_question_pool()
						
						# Reset platform states
						self.reset_platform_states()
						
						# Reset player details saved flag for new game
						self.player_details_saved = False
						
						# Reset Level 1 wrong answer counter
						self.level1_wrong_answers = 0

				# player won
				if game_finished:
					self.timer_counter = 0
					self.timer_started = False  # Reset timer started flag
					
					# Save player details to Excel when game is finished (only once)
					if not self.player_details_saved:
						rank = None
						if points >= 30:
							rank = 'Legend'
						elif points >= 24:
							rank = 'Gladiator'
						elif points >= 20:
							rank = 'Warrior'
						
						# Save player details
						if self.save_player_details(self.username, points, rank, "Completed"):
							self.player_details_saved = True
					
					# Draw improved congratulatory message
					title_font = pygame.font.SysFont('comicsansms', 56)
					subtitle_font = pygame.font.SysFont('comicsansms', 32)

					# Main title with emojis and celebratory text
					title = title_font.render("🏁 Level Complete! 🏁", True, (255, 215, 0))
					subtitle = subtitle_font.render(f"Congratulations! You finished the game! Final Score: {points}", True, (255, 255, 255))

					# Calculate background box size
					padding_x = int(60 * GameConfig.SCALE_FACTOR)
					padding_y = int(40 * GameConfig.SCALE_FACTOR)
					box_width = max(title.get_width(), subtitle.get_width(), username_text.get_width()) + 2 * padding_x
					box_height = title.get_height() + subtitle.get_height() + username_text.get_height() + 4 * padding_y
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
					username_rect = username_text.get_rect(center=(screen_width//2, subtitle_rect.bottom + padding_y + username_text.get_height()//2))
					game_surface.blit(title, title_rect)
					game_surface.blit(subtitle, subtitle_rect)
					game_surface.blit(username_text, username_rect)

					# --- Show Rank (Game Finished) ---
					if rank:
						rank_font = pygame.font.SysFont('comicsansms', 44)
						rank_text = rank_font.render(f'Rank: {rank}', True, (255, 215, 0))
						rank_rect = rank_text.get_rect(center=(screen_width//2, subtitle_rect.bottom + 60))
						game_surface.blit(rank_text, rank_rect)

					# --- Add Restart Button ---
					restart_font = pygame.font.SysFont('comicsansms', int(32 * GameConfig.SCALE_FACTOR))
					restart_colors = ((41, 128, 185), (142, 68, 173))  # Blue to purple gradient
					restart_button_width = int(200 * GameConfig.SCALE_FACTOR)
					restart_button_height = int(60 * GameConfig.SCALE_FACTOR)
					
					# Position restart button below rank or subtitle
					if rank:
						restart_y = rank_rect.bottom + int(40 * GameConfig.SCALE_FACTOR)
					else:
						restart_y = subtitle_rect.bottom + int(40 * GameConfig.SCALE_FACTOR)
					
					restart_x = screen_width // 2 - restart_button_width // 2
					restart_button = create_text_button("Restart", restart_x, restart_y, restart_button_width, restart_button_height, restart_font, restart_colors)
					
					if restart_button.draw(game_surface, offset=(surf_x, surf_y)):
						# Reset game state and go back to main menu
						current_level = 0
						points = 0
						game_finished = False
						game_over = 0
						in_menu = True
						in_domain_select = False
						
						# Reset timer
						self.timer_counter = 0
						self.timer_started = False
						
						# Reset insufficient points flag
						self.insufficient_points = False
						
						# Reset question UI and question pool
						if self.question_ui:
							self.question_ui.reset()
							self.question_ui.reset_question_pool()
						
						# Reset platform states
						self.reset_platform_states()
						
						# Reset player details saved flag for new game
						self.player_details_saved = False
						
						# Reset Level 1 wrong answer counter
						self.level1_wrong_answers = 0


			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					run = False

				# Handle username input events
				if in_menu:
					if event.type == pygame.MOUSEBUTTONDOWN:
						# Check if username field was clicked - account for screen offset
						# Calculate column positions for perfect symmetry
						column_width = int(400 * GameConfig.SCALE_FACTOR)
						column_spacing = int(100 * GameConfig.SCALE_FACTOR)
						total_width = (2 * column_width) + column_spacing
						start_x = (screen_width - total_width) // 2
						
						# Left column position
						left_x = start_x
						left_y = int(180 * GameConfig.SCALE_FACTOR)
						
						# Username field position in left column
						username_label_font = pygame.font.SysFont('comicsansms', int(22 * GameConfig.SCALE_FACTOR))
						username_label = username_label_font.render("Enter Username:", True, (255, 255, 255))
						username_y = left_y + int(100 * GameConfig.SCALE_FACTOR) + username_label.get_height() + int(20 * GameConfig.SCALE_FACTOR)
						username_width = column_width - int(80 * GameConfig.SCALE_FACTOR)
						username_height = int(55 * GameConfig.SCALE_FACTOR)
						username_x = left_x + int(40 * GameConfig.SCALE_FACTOR)
						
						# Calculate screen offset
						surf_x = (display_width - GAME_SURFACE_WIDTH) // 2
						surf_y = (display_height - GAME_SURFACE_HEIGHT) // 2
						
						# Adjust mouse position for screen offset
						adjusted_pos = (event.pos[0] - surf_x, event.pos[1] - surf_y)
						username_rect = pygame.Rect(username_x, username_y, username_width, username_height)
						
						if username_rect.collidepoint(adjusted_pos):
							self.username_active = True
						else:
							self.username_active = False
					
					elif event.type == pygame.KEYDOWN and self.username_active:
						if event.key == pygame.K_RETURN:
							# Check if username already exists
							if self.username.strip() and self.check_username_exists(self.username.strip()):
								self.show_duplicate_message = True
								self.duplicate_message_timer = 180  # Show message for 3 seconds (60 FPS * 3)
							else:
								self.username_active = False
						elif event.key == pygame.K_BACKSPACE:
							self.username = self.username[:-1]
						elif event.key == pygame.K_TAB:
							self.username_active = False
						elif len(self.username) < 20:  # Limit username length
							# Only allow alphanumeric characters and spaces
							if event.unicode.isalnum() or event.unicode.isspace():
								self.username += event.unicode

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
						else:
							# Question was answered incorrectly
							# Get complexity from current question
							complexity = self.question_ui.current_question.get('complexity', '').strip().lower()
							if complexity in ['2', 'level 2', '3', 'level 3']:
								# Game ends for incorrect Level 2 or Level 3 answers
								game_over = -1
								print(f"Game over: Incorrect answer for {complexity} question")
							elif complexity in ['1', 'level 1']:
								# Increment Level 1 wrong answer counter
								self.level1_wrong_answers += 1
								print(f"Level 1 wrong answer #{self.level1_wrong_answers}")
								if self.level1_wrong_answers >= 2:
									# Game ends after 2 incorrect Level 1 answers
									game_over = -1
									print(f"Game over: {self.level1_wrong_answers} incorrect Level 1 answers")
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

			# Update cursor blink timer
			if in_menu:
				self.cursor_blink_timer += 1
				
				# Update duplicate message timer
				if self.show_duplicate_message:
					self.duplicate_message_timer -= 1
					if self.duplicate_message_timer <= 0:
						self.show_duplicate_message = False

			# At the end of the frame, blit the game_surface centered on the screen
			surf_x = (display_width - GAME_SURFACE_WIDTH) // 2
			surf_y = (display_height - GAME_SURFACE_HEIGHT) // 2
			screen.blit(game_surface, (surf_x, surf_y))
			pygame.display.update()
			self.clock.tick(self.fps)

def draw_platforms_with_labels(surface, font, draw_labels_only=False):
    """
    Draw all platforms and overlay a modern, color-coded level label above each platform.
    If draw_labels_only is True, only draw the labels (not the platforms).
    """
    import pygame
    import GameConfig
    # Define color mapping for levels
    level_colors = {
        'Level 1': ((41, 128, 185), (142, 68, 173)),   # Blue to purple
        'Level 2': ((39, 174, 96), (241, 196, 15)),    # Green to yellow
        'Level 3': ((192, 57, 43), (211, 84, 0)),      # Red to orange
    }
    # Platform index to level mapping
    def get_level_label(idx):
        if idx in [2, 4, 1]:
            return 'Level 1'
        elif idx in [0, 3]:
            return 'Level 2'
        elif idx in [5]:
            return 'Level 3'
        else:
            return ''
    platform_list = list(plats[0]) if plats and len(plats) > 0 else []
    if not draw_labels_only:
        for idx, platform in enumerate(platform_list):
            platform.draw(surface)
    for idx, platform in enumerate(platform_list):
        label = get_level_label(idx)
        if label:
            color1, color2 = level_colors[label]
            # Use a smaller font size for narrower labels
            label_font = pygame.font.SysFont('comicsansms', int(14 * GameConfig.SCALE_FACTOR))
            label_text = label_font.render(label, True, (255, 255, 255))
            padding_x = int(6 * GameConfig.SCALE_FACTOR)
            padding_y = int(2* GameConfig.SCALE_FACTOR)
            label_width = label_text.get_width() + 2 * padding_x
            label_height = label_text.get_height() + 2 * padding_y
            label_x = platform.rect.centerx - label_width // 2
            label_y = platform.rect.top - label_height - 4
            label_bg = pygame.Surface((label_width, label_height), pygame.SRCALPHA)
            for y in range(label_height):
                ratio = y / label_height
                r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
                g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
                b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
                pygame.draw.line(label_bg, (r, g, b), (0, y), (label_width, y))
            pygame.draw.rect(label_bg, (255, 255, 255, 80), label_bg.get_rect(), 2, border_radius=8)
            surface.blit(label_bg, (label_x, label_y))
            text_rect = label_text.get_rect(center=(platform.rect.centerx, label_y + label_height // 2))
            surface.blit(label_text, text_rect)

# Start the game
try:
	game = Game()
	# Save player details when game exits if not already saved
	if hasattr(game, 'username') and hasattr(game, 'player_details_saved') and not game.player_details_saved:
		rank = None
		if points >= 30:
			rank = 'Legend'
		elif points >= 24:
			rank = 'Gladiator'
		elif points >= 20:
			rank = 'Warrior'
		game.save_player_details(game.username, points, rank, "Game Exited")
	pygame.quit()
except Exception as e:
	print(f"Fatal error: {str(e)}")
	print(traceback.format_exc())
	pygame.quit()