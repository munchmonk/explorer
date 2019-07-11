#!/Library/Frameworks/Python.framework/Versions/2.7/bin/python2.7
# coding: utf-8

import pygame
import sys
import os
import time
import pickle




class Utils:
	def __init__(self):
		pass

	def quit(self):
		pygame.quit()
		sys.exit()

	def index_to_coord(self, indexes):
		x = indexes[0] * Game.TILESIZE
		y = indexes[0] * Game.TILESIZE
		return x, y




class Camera:
	def __init__(self, game):
		# Hint: think of the camera as a moving rectangle, draw it on paper, and the lower/upper bounds will make sense - you have to keep the rectangle inside the map
		self.game = game
		self.screen_width = game.screen.get_width()
		self.screen_height = game.screen.get_height()
		self.map_width = game.map.get_width()
		self.map_height = game.map.get_height()
		self.x = 0
		self.y = 0

	def apply(self, target):
		return pygame.Rect(target.rect.x - self.x, target.rect.y - self.y, target.rect.width, target.rect.height)

	def update(self, target):
		# Center camera on target
		self.x = target.rect.centerx - self.screen_width / 2
		self.y = target.rect.centery - self.screen_height / 2

		# Move camera left/top half a tile if the map width/height has an even number of tiles - avoid cutting tiles in half
		if not(self.screen_width / Game.TILESIZE % 2):
			self.x += Game.TILESIZE / 2
		if not(self.screen_height / Game.TILESIZE % 2):
			self.y += Game.TILESIZE / 2

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

		

		"""
		if self.x == self.game.TILESIZE / 2:
			self.x = 0
		if self.y == self.game.TILESIZE / 2:
			self.y = 0
		if self.x == self.map_width - self.screen_width - self.game.TILESIZE / 2:
			self.x = self.map_width - self.screen_width
		if self.y == self.map_height - self.screen_height - self.game.TILESIZE / 2:
			self.y = self.map_height - self.screen_height
		"""

		



class Player(pygame.sprite.Sprite):
	IMG = 'player.jpg'
	MOVEMENT_COOLDOWN = 0.1
	SPEED = 0.3

	def __init__(self, game):
		self.game = game
		self.util = Utils()
		self.groups = game.allsprites, game.allplayers
		pygame.sprite.Sprite.__init__(self, self.groups)

		self.curr_tile = [2, 2]
		self.image = pygame.image.load(os.path.join(os.path.dirname(__file__), Player.IMG))
		self.rect = self.image.get_rect(topleft=(self.util.index_to_coord(self.curr_tile)))

		self.last_movement = 0
		self.dir = [0, 0]
		self.target_tile = None
		self.target_x = None
		self.target_y = None

	def get_dir(self):
		# Don't accept input if player is already moving
		if self.dir != [0, 0]:
			return

		keys = pygame.key.get_pressed()
		if keys[pygame.K_w] or keys[pygame.K_UP]:
			self.dir = [0, -1]
		elif keys[pygame.K_a] or keys[pygame.K_LEFT]:
			self.dir = [-1, 0]
		elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
			self.dir = [0, 1]
		elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
			self.dir = [1, 0]

	def is_tile_legal(self, tile):
		# Check edges
		if tile[0] < 0 or tile[1] < 0:
			return False
		if tile[0] > self.game.map.get_horiz_tiles() - 1 or tile[1] > self.game.map.get_vert_tiles() - 1:
			return False

		# Custom rules
		metadata = self.game.map.get_tile_metadata(tile)
		if not metadata:
			return True
		if 'FIRE' in metadata:
			return False

		# Base case
		return True

	def move(self):
		if self.dir != [0, 0] and time.time() - self.last_movement >= Player.MOVEMENT_COOLDOWN and not self.target_tile:
			self.target_tile = [0, 0]
			self.target_tile[0] = self.curr_tile[0] + self.dir[0]
			self.target_tile[1] = self.curr_tile[1] + self.dir[1]

			if not self.is_tile_legal(self.target_tile):
				self.target_tile = None
				self.dir = [0, 0]
			else:
				self.last_movement = time.time()
				self.target_x = self.rect.x + self.dir[0] * Game.TILESIZE
				self.target_y = self.rect.y + self.dir[1] * Game.TILESIZE	

		if self.target_tile:
			# Calculate base dx and dy tied to FPS
			dx = self.dir[0] * Player.SPEED * self.game.dt
			dy = self.dir[1] * Player.SPEED * self.game.dt

			# Make sure dx and dy are at least 1 if the player is moving - it can round down to 0 keeping it still if not
			if self.dir[0] and abs(dx) < 1:
				dx = self.dir[0]
			if self.dir[1] and abs(dy) < 1:
				dy = self.dir[1]

			# Move player, making sure not to move them past the target tile
			if dx > 0:
				self.rect.x = min(self.rect.x + dx, self.target_x)
			if dy > 0:
				self.rect.y = min(self.rect.y + dy, self.target_y)
			if dx < 0:
				self.rect.x = max(self.rect.x + dx, self.target_x)
			if dy < 0:
				self.rect.y = max(self.rect.y + dy, self.target_y)

			if self.rect.x == self.target_x and self.rect.y == self.target_y:
				self.curr_tile = self.target_tile
				self.dir = [0, 0]
				self.target_tile = None
				self.target_x = None
				self.target_y = None




			

	def update(self):
		self.get_dir()
		self.move()

	def draw(self):
		pass


class Map:
	def __init__(self):
		self.image = None
		self.rect = None
		self.metadata = None

		self.horiz_tiles = None
		self.vert_tiles = None

		self.load()

	def load(self):
		self.image = pygame.image.load(os.path.join(os.path.dirname(__file__), 'map.jpeg'))
		self.rect = self.image.get_rect()
		with open(os.path.join(os.path.dirname(__file__), 'metadata.p'), 'rb') as in_file:
			self.metadata = pickle.load(in_file)

		self.horiz_tiles = self.image.get_width() / Game.TILESIZE
		self.vert_tiles = self.image.get_height() / Game.TILESIZE

	def get_tile_metadata(self, indexes):
		# Note: second index first as it's columns -> rows
		return self.metadata[indexes[1]][indexes[0]]

	def get_horiz_tiles(self):
		return self.horiz_tiles

	def get_vert_tiles(self):
		return self.vert_tiles

	def get_width(self):
		return self.image.get_width()

	def get_height(self):
		return self.image.get_height()


class Game:
	# N.B. the number of tiles per side has to be odd to display the player in the middle of the screen!
	TILESIZE = 32
	SCREENWIDTH = TILESIZE * 10
	SCREENHEIGHT = TILESIZE * 11

	def __init__(self):
		pygame.init()

		self.screen = pygame.display.set_mode((Game.SCREENWIDTH, Game.SCREENHEIGHT))
		# self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

		self.allplayers = pygame.sprite.Group()
		self.allsprites = pygame.sprite.Group()

		self.util = Utils()
		self.clock = pygame.time.Clock()
		self.dt = 0

		self.map = None

		self.setup()

	def setup(self):
		self.player = Player(self)
		self.map = Map()
		self.camera = Camera(self)

	def update(self):
		self.allsprites.update()
		self.camera.update(self.player)

	def draw(self):
		self.screen.fill((0, 0, 0))
		self.screen.blit(self.map.image, (self.camera.apply(self.map)))
		# self.screen.blit(self.map.image, (0, 0))


		for sprite in self.allsprites:
			# self.screen.blit(sprite.image, sprite.rect)
			# rect = self.camera.apply_to_sprite(sprite)
			self.screen.blit(sprite.image, self.camera.apply(sprite))

			# Don't draw off-screen sprites
			# if rect.right < 0 or rect.bottom < 0 or rect.left > Game.SCREENWIDTH or rect.top > Game.SCREENHEIGHT:
			#		continue

			
		
		pygame.display.flip()

	def play(self):
		while True:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self.util.quit()
				elif event.type == pygame.KEYDOWN:
					if event.key == pygame.K_ESCAPE:
						self.util.quit()

			self.update()
			self.draw()
			self.dt = self.clock.tick(45)

if __name__ == '__main__':
	Game().play()













