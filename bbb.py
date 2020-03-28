#!/Library/Frameworks/Python.framework/Versions/2.7/bin/python2.7
# coding: utf-8


"""
	
	next:
		vary water tile
		do 2 missing water tiles
		enlarge water/grass tiles to make it clear whether player can or can't walk there

	todo:
		links (e.g. enter a house, new path, etc.)
		(tile animations?)
		os agnostic image load path (hardcoded at the moment)
		sanitize input like for real


"""

import pygame
import sys
import os
import time
import pickle
import copy




class Utils:
	RIGHT, LEFT, UP, DOWN = range(4)

	def __init__(self):
		pass

	def quit(self):
		pygame.quit()
		sys.exit()

	def index_to_coord(self, indexes):
		x = indexes[0] * Game.TILESIZE
		y = indexes[1] * Game.TILESIZE
		return x, y


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


class Player(pygame.sprite.Sprite):
	IMG =  {Utils.RIGHT:	[pygame.image.load(os.path.join(os.path.dirname(__file__), 'assets/player/player_right_0.png')),
						 	pygame.image.load(os.path.join(os.path.dirname(__file__), 'assets/player/player_right_1.png'))],

			Utils.LEFT: 	[pygame.image.load(os.path.join(os.path.dirname(__file__), 'assets/player/player_left_0.png')),
						 	pygame.image.load(os.path.join(os.path.dirname(__file__), 'assets/player/player_left_1.png'))],

			Utils.UP: 		[pygame.image.load(os.path.join(os.path.dirname(__file__), 'assets/player/player_up_0.png')),
						 	pygame.image.load(os.path.join(os.path.dirname(__file__), 'assets/player/player_up_1.png')),
						 	pygame.image.load(os.path.join(os.path.dirname(__file__), 'assets/player/player_up_2.png'))],

			Utils.DOWN: 	[pygame.image.load(os.path.join(os.path.dirname(__file__), 'assets/player/player_down_0.png')),
						 	pygame.image.load(os.path.join(os.path.dirname(__file__), 'assets/player/player_down_1.png')),
						 	pygame.image.load(os.path.join(os.path.dirname(__file__), 'assets/player/player_down_2.png'))]}

	MOVEMENT_COOLDOWN = 0.1
	SPEED = 0.1
	ANIMFRAME_COOLDOWN = 0.2
	
	def __init__(self, game, spawn_x, spawn_y):
		self.game = game
		self.util = Utils()
		self.groups = game.allsprites, game.allplayers
		pygame.sprite.Sprite.__init__(self, self.groups)

		self.reset(spawn_x, spawn_y)

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

		if self.game.joysticks:
			if self.game.joysticks[0].get_axis(0) > 0.5:
				self.dir = [1, 0]
			if self.game.joysticks[0].get_axis(0) < -0.5:
				self.dir = [-1, 0]
			if self.game.joysticks[0].get_axis(1) > 0.5:
				self.dir = [0, 1]
			if self.game.joysticks[0].get_axis(1) < -0.5:
				self.dir = [0, -1]

		if self.dir == [1, 0]:
			self.facing = self.util.RIGHT
		elif self.dir == [-1, 0]:
			self.facing = self.util.LEFT
		elif self.dir == [0, -1]:
			self.facing = self.util.UP
		elif self.dir == [0, 1]:
			self.facing = self.util.DOWN

	def is_tile_legal(self, tile):
		# Check edges
		if tile[0] < 0 or tile[1] < 0:
			return False
		# if tile[0] > self.game.map.get_horiz_tiles() - 1 or tile[1] > self.game.map.get_vert_tiles() - 1:
		if tile[0] > self.game.horiz_tiles - 1 or tile[1] > self.game.vert_tiles - 1:
			return False

		# Custom rules
		tags = []

		for t in self.game.find_tile_by_coord(tile):
			if t.tile_data:
				for tag in t.tile_data:
					tags.append(tag)

		if 'WATER' in tags:
			return False

		if 'CASA' in tags:
			if any(tag in ('BOTTOM_LEFT', 'BOTTOM_RIGHT', 'TOP_LEFT', 'MID_TOP', 'TOP_RIGHT') for tag in tags):
				return False

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
				self.target_tile = None
				self.target_x = None
				self.target_y = None

				# This helps keeping the walking animation smooth instead of restarting it every tile
				old_dir = self.dir
				self.dir = [0, 0]
				self.get_dir()
				if self.dir != old_dir:
					self.anim_frame = 0

				# Portals
				for tile in self.game.find_tile_by_coord(self.curr_tile):
					if tile.tile_data:
						for tag in tile.tile_data:
							if 'PORTAL' in tag:
								# Portal tag format: NEWLEVELNAME_PORTAL_SPAWNX_SPAWNY

								tag_string = tag.split('_')
								spawn_x = int(tag_string[-2])
								spawn_y = int(tag_string[-1])
								new_level = '_'.join(tag_string[:-3])

								self.game.curr_level = new_level
								self.game.setup_level(spawn_x, spawn_y)


	def reset(self, spawn_x, spawn_y):
		self.curr_tile = [spawn_x, spawn_y]
		self.facing = self.util.DOWN
		self.anim_frame = 0
		self.image = Player.IMG[self.facing][self.anim_frame]
		self.rect = self.image.get_rect(topleft=(self.util.index_to_coord(self.curr_tile)))

		self.last_anim = 0
		self.last_movement = 0
		self.dir = [0, 0]
		self.target_tile = None
		self.target_x = None
		self.target_y = None


	def update_sprite(self):
		if self.dir == [0, 0]:
			self.anim_frame = 0
		elif self.dir == [0, 1]:
			if time.time() - self.last_anim > Player.ANIMFRAME_COOLDOWN:
				self.anim_frame = (self.anim_frame + 1) % len(Player.IMG[self.util.DOWN])
				self.last_anim = time.time()
		elif self.dir == [0, -1]:
			if time.time() - self.last_anim > Player.ANIMFRAME_COOLDOWN:
				self.anim_frame = (self.anim_frame + 1) % len(Player.IMG[self.util.UP])
				self.last_anim = time.time()
		elif self.dir == [1, 0]:
			if time.time() - self.last_anim > Player.ANIMFRAME_COOLDOWN:
				self.anim_frame = (self.anim_frame + 1) % len(Player.IMG[self.util.RIGHT])
				self.last_anim = time.time()
		elif self.dir == [-1, 0]:
			if time.time() - self.last_anim > Player.ANIMFRAME_COOLDOWN:
				self.anim_frame = (self.anim_frame + 1) % len(Player.IMG[self.util.LEFT])
				self.last_anim = time.time()

		self.image = Player.IMG[self.facing][self.anim_frame]

	def update(self):
		self.get_dir()
		self.move()
		self.update_sprite()

	def draw(self):
		pass




class BaseTile:
	# Obviously level will have to be fed into __init__ in the future
	PATH = os.path.join('assets', 'level_1')

	def __init__(self, tile_data):
		self.tile_data = tile_data
		tile_path = os.path.join(BaseTile.PATH, self.tile_data[0])
		self.image = pygame.image.load(os.path.join(os.path.dirname(__file__), tile_path)).convert_alpha()
	


class Tile(pygame.sprite.Sprite):
	ANIMFRAME_COOLDOWN = 1

	def __init__(self, game, x, y, tile_name):
		self.game = game
		self.groups = game.allsprites, game.alltiles
		pygame.sprite.Sprite.__init__(self, self.groups)

		self.util = Utils()

		self.x = x
		self.y = y
		self.coord = self.util.index_to_coord((self.x, self.y))
		self.tile_data = self.game.base_tiles[tile_name].tile_data

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





class Game:
	TILESIZE = 32
	SCREENWIDTH = TILESIZE * 32
	SCREENHEIGHT = TILESIZE * 24

	def __init__(self):
		pygame.init()

		# Playing on Mac - fullscreen
		if (1280, 800) in pygame.display.list_modes():
			# self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
			self.screen = pygame.display.set_mode((32 * 15, 32 * 12))

		# Playing on TV - 1024 x 768
		if (1280, 960) in pygame.display.list_modes():
			self.screen = pygame.display.set_mode((Game.SCREENWIDTH, Game.SCREENHEIGHT), pygame.FULLSCREEN)

		# self.screen = pygame.display.set_mode((Game.SCREENWIDTH, Game.SCREENHEIGHT), pygame.FULLSCREEN)
		# self.screen = pygame.display.set_mode((Game.SCREENWIDTH, Game.SCREENHEIGHT))
		# display_info = pygame.display.Info()
		# self.screen = pygame.display.set_mode((display_info.current_w, display_info.current_h))
		# self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

		self.allplayers = pygame.sprite.Group()
		self.allsprites = pygame.sprite.Group()

		self.player = Player(self, 0, 0)

		self.util = Utils()
		self.clock = pygame.time.Clock()
		self.dt = 0

		self.joysticks = []

		self.base_tiles = dict()
		self.map_width = 0
		self.map_height = 0
		self.horiz_tiles = 0
		self.vert_tiles = 0
		self.alltiles = pygame.sprite.Group()

		self.tile_layers = []

		self.curr_level = 'level_1'
		
		self.setup_joysticks()
		self.setup_level(1, 3)

	def find_tile_by_coord(self, coord):
		# It has to return a list because there might be more than one tile in the same place due to different layers
		tiles = []
		for tile in self.alltiles:
			if tile.x == coord[0] and tile.y == coord[1]:
				tiles.append(tile)
		return tiles

	def load_tiles(self):
		self.base_tiles = dict()
		self.alltiles = pygame.sprite.Group()

		metadata_path = os.path.join('assets', self.curr_level)
		metadata_path = os.path.join(metadata_path, 'metadata.txt')
		metadata_path = os.path.join(os.path.dirname(__file__), metadata_path)

		with open(metadata_path, 'r') as in_file:
			for line in in_file:
				text = line.split()

				if text:
					self.base_tiles[text[0]] = BaseTile(text)

	def build_portals(self):
		# To be fed via file in the future

		if self.curr_level == 'level_1':
			self.add_portal(4, 10, 'level_2_PORTAL_3_4')
			self.add_portal(8, 12, 'level_2_PORTAL_9_8')

		if self.curr_level == 'level_2':
			self.add_portal(3, 3, 'level_1_PORTAL_4_11')
			self.add_portal(9, 7, 'level_1_PORTAL_8_13')


	def add_portal(self, x, y, portal_tag):
		# N.B. use deep copies for tile tags
		tile = [t for t in self.find_tile_by_coord((x, y)) if t.tile_data][0]
		new_data = copy.deepcopy(tile.tile_data)
		new_data.append(portal_tag)
		tile.tile_data = new_data

	def build_map(self):
		self.tile_layers = []

		i = 0
		while True:
			curr_layer = []
			map_file = 'metadata_' + str(i) + '.p'
			map_path = os.path.join('assets', self.curr_level)
			map_path = os.path.join(map_path, map_file)
			
			try:
				with open(os.path.join(os.path.dirname(__file__), map_path), 'rb') as in_file:
					metadata = pickle.load(in_file)

					self.horiz_tiles = len(metadata[0])
					self.vert_tiles = len(metadata)
					self.map_width = self.horiz_tiles * Game.TILESIZE
					self.map_height = self.vert_tiles * Game.TILESIZE

					for y in range(len(metadata)):
						for x in range(len(metadata[y])):

							# Overwrites existing tiles
							existing_tiles = self.find_tile_by_coord((x, y))
							if existing_tiles:
								for existing_tile in existing_tiles:
									existing_tile.tile_data = None

							curr_layer.append(Tile(self, x, y, metadata[y][x]))

				self.tile_layers.append(curr_layer)
				i += 1

			except:
				break

	def setup_joysticks(self):
		pygame.joystick.init()

		for i in range(0, pygame.joystick.get_count()):
			self.joysticks.append(pygame.joystick.Joystick(i))
			self.joysticks[i].init()

	def setup_level(self, spawn_x, spawn_y):
		self.load_tiles()
		self.build_map()
		self.build_portals()
		self.player.reset(spawn_x, spawn_y)
		self.camera = Camera(self)


	def show_curr_tile(self):
		# For debugging/mapbuilding only
		for player in self.allplayers:
			print(player.curr_tile)


	def update(self):
		self.allsprites.update()
		self.camera.update(self.player)

		# Comment out if not debugging/mapbuilding
		# self.show_curr_tile()


	def draw(self):
		self.screen.fill((0, 0, 0))

		for layer in self.tile_layers:
			for tile in layer:
				self.screen.blit(tile.image, self.camera.apply(tile))	

		for sprite in self.allplayers:
			self.screen.blit(sprite.image, self.camera.apply(sprite))
		
		pygame.display.flip()

		# for sprite in self.allsprites:
		# 	self.screen.blit(sprite.image, self.camera.apply(sprite))

			# Don't draw off-screen sprites
			# if rect.right < 0 or rect.bottom < 0 or rect.left > Game.SCREENWIDTH or rect.top > Game.SCREENHEIGHT:
			#		continue

		

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













