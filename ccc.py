#!/Library/Frameworks/Python.framework/Versions/2.7/bin/python2.7
# coding: utf-8

import pygame
import os
import time

import const


class Camera:
	def __init__(self, game):
		# Hint: think of the camera as a moving rectangle, draw it on paper, and the lower/upper bounds will make sense - you have to keep the rectangle inside the map
		self.game = game
		self.screen_width = game.screen.get_width()
		self.screen_height = game.screen.get_height()
		self.map_width = self.game.map_width
		self.map_height = self.game.map_height
		self.x = 0
		self.y = 0

	def apply(self, target):
		return pygame.Rect(target.rect.x - self.x, target.rect.y - self.y, target.rect.width, target.rect.height)

	def update(self, target):
		# Center camera on target
		self.x = target.rect.centerx - self.screen_width / 2
		self.y = target.rect.centery - self.screen_height / 2

		# Move camera left/top half a tile if the map width/height has an even number of tiles - avoid cutting tiles in half
		if not(self.screen_width / const.TILESIZE % 2):
			self.x += const.TILESIZE / 2
		if not(self.screen_height / const.TILESIZE % 2):
			self.y += const.TILESIZE / 2

		# Stop updating if target is too close to left/top edges - don't see black bits outside of map
		self.x = max(self.x, 0)
		self.y = max(self.y, 0)

		# Stop updating if target is too close to right/bottom edges - don't see black bits outside of map
		self.x = min(self.x, self.map_width - self.screen_width)
		self.y = min(self.y, self.map_height - self.screen_height)

		# Center the camera if the map is smaller than the screen (note: camera values will be negative)
		if self.map_width <= self.screen_width:
			self.x = -(self.screen_width - self.map_width) / 2
		if self.map_height <= self.screen_height:
			self.y = -(self.screen_height - self.map_height) / 2
			

class BaseTile:
	def __init__(self, tile_data, level):
		self.tile_data = tile_data
		level_path = os.path.join('assets', level)
		tile_path = os.path.join(level_path, self.tile_data[0])
		self.image = pygame.image.load(os.path.join(os.path.dirname(__file__), tile_path)).convert_alpha()


class Tile(pygame.sprite.Sprite):
	ANIMFRAME_COOLDOWN = 1

	def __init__(self, game, x, y, tile_name):
		self.game = game
		self.groups = game.allsprites, game.alltiles
		pygame.sprite.Sprite.__init__(self, self.groups)

		self.x = x
		self.y = y
		self.coord = self.game.index_to_coord((self.x, self.y))
		self.tile_data = self.game.base_tiles[tile_name].tile_data
		self.print_above_player = True if 'TOP_LAYER' in self.tile_data else False
		self.invisible = True if 'INVISIBLE' in self.tile_data else False

		self.images = list()
		self.find_images()
		self.img_index = 0
		self.last_anim = 0
		self.image = self.images[self.img_index]
		self.rect = self.image.get_rect(topleft=(self.coord))



	def find_images(self):
		# Add the default one
		self.images.append(self.game.base_tiles[self.tile_data[0]].image)

		# Add any more tiles with the format TILE_NAME_ID ANIM_TILE_NAME ID
		if self.tile_data[1][:4] == 'ANIM':
			for base_tile in self.game.base_tiles.values():
				# Don't add itself and don't add a tile more than once
				if base_tile.tile_data[0] != self.tile_data[0] and base_tile.tile_data[1] == self.tile_data[1] and base_tile.image not in self.images:
					self.images.insert(int(base_tile.tile_data[2]), base_tile.image)

	def update(self):
		if len(self.images) > 1:
			if time.time() - self.last_anim > Tile.ANIMFRAME_COOLDOWN:
				self.img_index = (self.img_index + 1) % len(self.images)
				self.image = self.images[self.img_index]
				self.last_anim = time.time()


class CatchNeedle(pygame.sprite.Sprite):
	def __init__(self, game, difficulty, succes_edges):
		self.game = game
		self.groups = game.allsprites, game.allneedles
		pygame.sprite.Sprite.__init__(self, self.groups)

		self.image = pygame.Surface((10, 45))
		self.image.fill((255, 0, 128))
		self.rect = self.image.get_rect(topleft=(0, const.SCREENHEIGHT - 65))
		self.succes_edges = succes_edges

		self.dir = 1
		# self.speed = difficulty + 10
		self.speed = 1
		self.stopped = False

	def update(self):
		if self.stopped:
			return

		dx = self.dir * self.speed * self.game.dt
		if abs(dx) < 1:
			dx = self.dir
		self.rect.x += dx

		if (self.rect.x <= 0 and self.dir < 0) or (self.rect.x >= const.SCREENWIDTH - self.rect.width and self.dir > 0):
			self.dir *= -1

	def stop(self):
		self.stopped = True

	def success(self):
		if self.rect.right < self.succes_edges[0]:
			return False
		if self.rect.left > self.succes_edges[1]:
			return False
		return True



class Pokemon(pygame.sprite.Sprite):
	MAIN_PATH = os.path.join(os.path.dirname(__file__), 'assets/pokemon/')
	INDIVIDUAL_PATH =  {0: 'transparent.png',
						1: 'bulbasaur.png',
						4: 'charmander.png',
						7: 'squirtle.png',
						25: 'pikachu.png'
						}

	def __init__(self, game, dex_id):
		self.game = game
		self.groups = game.allsprites, game.allpokemon
		pygame.sprite.Sprite.__init__(self, self.groups)

		self.dex_id = dex_id
		self.image = pygame.image.load(Pokemon.MAIN_PATH + Pokemon.INDIVIDUAL_PATH[self.dex_id])
		self.rect = self.image.get_rect(centerx=(const.SCREENWIDTH / 2), centery=(const.SCREENHEIGHT / 3))
		self.transparent = False

		self.difficulty = 0
		self.green_bar_edges = (0, 0)
		self.set_difficulty()

		self.catch_needle = CatchNeedle(self.game, self.difficulty, self.green_bar_edges)

	def update(self):
		if self.transparent:
			self.image = pygame.image.load(Pokemon.MAIN_PATH + Pokemon.INDIVIDUAL_PATH[0])

	def set_transparent(self):
		self.transparent = True
		

	def set_difficulty(self):
		if self.dex_id in (1, 4, 7):
			self.difficulty = 0
			self.green_bar_edges = (const.SCREENWIDTH * 1 / 3, const.SCREENWIDTH * 2 / 3)
		elif self.dex_id in (25, 25):
			self.difficulty = 1
			self.green_bar_edges = (const.SCREENWIDTH * 3 / 7, const.SCREENWIDTH * 4 / 7)

	def get_catch_bar(self):
		green_bar_width = self.green_bar_edges[1] - self.green_bar_edges[0]
		red_bar_width = (const.SCREENWIDTH - green_bar_width) / 2
		bar_height = 15
		bar_top = const.SCREENHEIGHT - 50

		green_bar = pygame.Surface((green_bar_width, bar_height))
		green_bar.fill((0, 255, 0))
		left_red_bar = pygame.Surface((red_bar_width, bar_height))
		left_red_bar.fill((255, 0, 0))
		right_red_bar = pygame.Surface((red_bar_width, bar_height))
		right_red_bar.fill((255, 0, 0))

		ret_surface = pygame.Surface((const.SCREENWIDTH, bar_height))
		ret_surface.blit(left_red_bar, (0, 0))
		ret_surface.blit(green_bar, (red_bar_width, 0))
		ret_surface.blit(right_red_bar, (red_bar_width + green_bar_width, 0))

		ret_rect = pygame.Rect(0, bar_top, const.SCREENWIDTH, bar_height)

		return ret_surface, ret_rect


class Pokeball(pygame.sprite.Sprite):
	OPEN, HALF_OPEN, CLOSED, TRANSPARENT, SMALL = 'open', 'half_open', 'closed', 'transparent', 'small'

	IMG =  {OPEN: pygame.image.load(os.path.join(os.path.dirname(__file__), 'assets/pokeballs/pokeball_open.png')),
			HALF_OPEN: pygame.image.load(os.path.join(os.path.dirname(__file__), 'assets/pokeballs/pokeball_half_open.png')),
			CLOSED: pygame.image.load(os.path.join(os.path.dirname(__file__), 'assets/pokeballs/pokeball_closed.png')),
			TRANSPARENT: pygame.image.load(os.path.join(os.path.dirname(__file__), 'assets/pokeballs/transparent.png')),
			SMALL: pygame.image.load(os.path.join(os.path.dirname(__file__), 'assets/pokeballs/pokeball_small.png')),}

	def __init__(self, game, pokemon, success):
		self.game = game
		self.groups = game.allsprites, game.allpokeballs
		pygame.sprite.Sprite.__init__(self, self.groups)

		self.success = success
		self.state = Pokeball.OPEN
		self.image = None
		self.set_image()
		self.rect = self.image.get_rect(centerx=const.SCREENWIDTH / 2, top=const.SCREENHEIGHT)
		self.pokemon = pokemon

		self.speed = -0.6
		self.dead = False
		self.kill_timer = 0

	def set_image(self):
		self.image = Pokeball.IMG[self.state]

	def update(self):
		# Movement
		dy = 0
		if self.speed > 0:
			dy = max(self.speed * self.game.dt, 1)
		elif self.speed < 0:
			dy = min(self.speed * self.game.dt, -1)

		self.rect.y += dy

		# Going up
		if self.state == Pokeball.OPEN and self.rect.y <= 15:
			self.state = Pokeball.HALF_OPEN
			self.set_image()
			self.speed = 0.15

		# Going down
		if self.state == Pokeball.HALF_OPEN and self.rect.y >= 100:
			if self.success:
				self.state = Pokeball.CLOSED
				self.set_image()
				self.speed = 0
				self.pokemon.set_transparent()
			else:
				self.state = Pokeball.TRANSPARENT
				self.set_image()

			self.kill_timer = time.time()

		if self.kill_timer > 0 and time.time() - self.kill_timer > 2.5:
			self.dead = True
			self.kill()


















