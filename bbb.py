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
import random




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



class CatchNeedle(pygame.sprite.Sprite):
	def __init__(self, game, difficulty, succes_edges):
		self.game = game
		self.groups = game.allsprites, game.allneedles
		pygame.sprite.Sprite.__init__(self, self.groups)

		self.image = pygame.Surface((10, 45))
		self.image.fill((255, 0, 128))
		self.rect = self.image.get_rect(topleft=(0, Game.SCREENHEIGHT - 65))
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

		if (self.rect.x <= 0 and self.dir < 0) or (self.rect.x >= Game.SCREENWIDTH - self.rect.width and self.dir > 0):
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
	INDIVIDUAL_PATH =  {1: 'bulbasaur.png',
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
		self.rect = self.image.get_rect(centerx=(Game.SCREENWIDTH / 2), centery=(Game.SCREENHEIGHT / 3))

		self.difficulty = 0
		self.green_bar_edges = (Game.SCREENWIDTH / 3, Game.SCREENWIDTH * 2 / 3)
		self.catch_needle = CatchNeedle(self.game, self.difficulty, self.green_bar_edges)

		self.set_difficulty()

	def set_difficulty(self):
		if self.dex_id in (1, 4, 7):
			self.difficulty = 0
		elif self.dex_id in (25, 25):
			self.difficulty = 1

	def get_catch_bar(self):
		# to use difficulty in the future
		green_bar_width = self.green_bar_edges[1] - self.green_bar_edges[0]
		red_bar_width = (Game.SCREENWIDTH - green_bar_width) / 2
		bar_height = 15
		bar_top = Game.SCREENHEIGHT - 50

		green_bar = pygame.Surface((green_bar_width, bar_height))
		green_bar.fill((0, 255, 0))
		left_red_bar = pygame.Surface((red_bar_width, bar_height))
		left_red_bar.fill((255, 0, 0))
		right_red_bar = pygame.Surface((red_bar_width, bar_height))
		right_red_bar.fill((255, 0, 0))

		ret_surface = pygame.Surface((Game.SCREENWIDTH, bar_height))
		ret_surface.blit(left_red_bar, (0, 0))
		ret_surface.blit(green_bar, (red_bar_width, 0))
		ret_surface.blit(right_red_bar, (red_bar_width + green_bar_width, 0))

		ret_rect = pygame.Rect(0, bar_top, Game.SCREENWIDTH, bar_height)

		return ret_surface, ret_rect




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

		# This below is a copy of reset() but I'd rather it be clear what attributes Player has instead of declaring them outside of init()
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

		self.curr_pokemon = None
		self.curr_needle = None

	def get_dir(self):
		if self.game.fight_mode:
			return

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

		# Custom rules - to be processed by an external function and potentially level by level in the future
		tags = []

		for t in self.game.find_tile_by_coord(tile):
			if t.tile_data:
				for tag in t.tile_data:
					tags.append(tag)

		# To be extended
		if any(tag in ('WATER') for tag in tags):
			return False

		if 'TREE' in tags and 'BOTTOM' in tags:
			return False

		if 'CASA' in tags:
			if any(tag in ('BOTTOM_LEFT', 'BOTTOM_RIGHT', 'TOP_LEFT', 'MID_TOP', 'TOP_RIGHT') for tag in tags):
				return False

		return True


	def fight(self):
		if not self.game.fight_mode:
			return

		keys = pygame.key.get_pressed()

		if keys[pygame.K_q]:
			self.game.fight_mode = False
			self.curr_pokemon.kill()
			self.curr_pokemon = None
			self.curr_needle.kill()
			self.curr_needle = None

		elif keys[pygame.K_SPACE]:
			self.curr_needle.stop()
			if self.curr_needle.success():
				print('Caught!')
			else:
				print('Missed!')



	def move(self):
		if self.game.fight_mode:
			return

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

				# Special actions
				for tile in self.game.find_tile_by_coord(self.curr_tile):
					if tile.tile_data:
						for tag in tile.tile_data:
							if 'PORTAL' in tag:
								self.go_through_portal(tag)

							if 'POKEMON_SPAWN_POINT' in tag:
								# This avoids a bug where by having a nonzero dir, it "moves" to the current tile that spawned a pokemon thus spawning a second one
								# it also prevents the player from moving after fighting a pokemon
								self.dir = [0, 0]
								self.game.spawn_pokemon(tile.tile_data)


	def go_through_portal(self, portal_tag):
		# Portal tag format: NEWLEVELNAME_PORTAL_SPAWNX_SPAWNY_FACING
		tag_string = portal_tag.split('_')

		spawn_x = int(tag_string[-3])
		spawn_y = int(tag_string[-2])
		facing = int(tag_string[-1])
		new_level = '_'.join(tag_string[:-4])

		self.game.curr_level = new_level
		self.game.setup_level(spawn_x, spawn_y, facing)



	def reset(self, spawn_x, spawn_y, facing):
		self.curr_tile = [spawn_x, spawn_y]
		self.facing = facing
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
		self.fight()
		self.get_dir()
		self.move()
		self.update_sprite()

	def draw(self):
		pass




class BaseTile:
	# Obviously level will have to be fed into __init__ in the future
	# PATH = os.path.join('assets', 'level_1')

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

		self.util = Utils()

		self.x = x
		self.y = y
		self.coord = self.util.index_to_coord((self.x, self.y))
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





class Game:
	TILESIZE = 32
	SCREENWIDTH = TILESIZE * 11 # 11
	SCREENHEIGHT = TILESIZE * 10 # 10

	def __init__(self):
		pygame.init()

		# Playing on Mac - fullscreen
		if (1280, 800) in pygame.display.list_modes():
			# self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
			# self.screen = pygame.display.set_mode((32 * 15, 32 * 12))
			self.screen = pygame.display.set_mode((Game.SCREENWIDTH, Game.SCREENHEIGHT))

		# Playing on TV - 1024 x 768
		if (1280, 960) in pygame.display.list_modes():
			self.screen = pygame.display.set_mode((Game.SCREENWIDTH, Game.SCREENHEIGHT), pygame.FULLSCREEN)

		# self.screen = pygame.display.set_mode((Game.SCREENWIDTH, Game.SCREENHEIGHT), pygame.FULLSCREEN)
		# self.screen = pygame.display.set_mode((Game.SCREENWIDTH, Game.SCREENHEIGHT))
		# display_info = pygame.display.Info()
		# self.screen = pygame.display.set_mode((display_info.current_w, display_info.current_h))
		# self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

		self.allplayers = pygame.sprite.Group()
		self.allpokemon = pygame.sprite.Group()
		self.allneedles = pygame.sprite.Group()
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

		self.fight_mode = False
		self.fight_background = pygame.image.load(os.path.join(os.path.dirname(__file__), 'assets/pokemon/fight_background.png'))

		self.tile_layers = []

		self.curr_level = 'level_1'
		
		self.setup_joysticks()
		self.setup_level(1, 1, self.util.DOWN)
		# self.setup_level(4, 11, self.util.DOWN)

	def spawn_pokemon(self, pokemon_tag):
		common_odds = 0
		uncommon_odds = 0

		if 'COMMON' in pokemon_tag:
			common_odds += 0.2
		if 'UNCOMMON' in pokemon_tag:
			common_odds += 0.1
			uncommon_odds += 0.1

		if random.random() < common_odds:
			self.start_fight(random.choice((1, 4, 7)))

		elif random.random() < uncommon_odds:
			self.start_fight(random.choice((25, 25)))


	def start_fight(self, dex_id):
		self.fight_mode = True
		self.play_fight_transition()
		new_mon = Pokemon(self, dex_id)
		self.player.curr_pokemon = new_mon
		self.player.curr_needle = new_mon.catch_needle


	def play_fight_transition(self):
		thickness = 1

		while thickness < min(Game.SCREENWIDTH, Game.SCREENHEIGHT):
			pygame.draw.rect(self.screen, (0, 0, 0), pygame.Rect(0, 0, Game.SCREENWIDTH, Game.SCREENHEIGHT), thickness)
			pygame.display.flip()
			thickness += 10
			pygame.time.wait(35)




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
					self.base_tiles[text[0]] = BaseTile(text, self.curr_level)

	def build_portals(self):
		# To be fed via file in the future

		if self.curr_level == 'level_1':
			self.add_portal(4, 10, 'level_2_PORTAL_3_4', self.util.DOWN)
			self.add_portal(8, 12, 'level_2_PORTAL_9_8', self.util.DOWN)
			self.add_portal(1, 0, 'forest_PORTAL_1_18', self.util.UP)

		if self.curr_level == 'level_2':
			self.add_portal(3, 3, 'level_1_PORTAL_4_11', self.util.DOWN)
			self.add_portal(9, 7, 'level_1_PORTAL_8_13', self.util.DOWN)

		if self.curr_level == 'forest':
			self.add_portal(1, 19, 'level_1_PORTAL_1_1', self.util.DOWN)

	def add_portal(self, x, y, portal_tag, facing):
		# N.B. use deep copies for tile tags
		portal_tag = portal_tag + '_' + str(facing)

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

							# Below code was creating a bug where two different tiles overlap; I'll leave it commented for now in case there is a valid reason
							# I wanted to overwrite the tile. I can't think of any now

							# # Overwrites existing tiles
							# existing_tiles = self.find_tile_by_coord((x, y))
							# if existing_tiles:
							# 	for existing_tile in existing_tiles:
							# 		# existing_tile.tile_data = None

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

	def setup_level(self, spawn_x, spawn_y, facing):
		self.load_tiles()
		self.build_map()
		self.build_portals()
		self.player.reset(spawn_x, spawn_y, facing)
		self.camera = Camera(self)
		self.fight_mode = False

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

		if self.fight_mode:
			self.screen.blit(self.fight_background, (0, 0))

			for sprite in self.allpokemon:
				self.screen.blit(sprite.image, sprite.rect)

				bar_surf, bar_rect = sprite.get_catch_bar()
				self.screen.blit(bar_surf, bar_rect)

			for sprite in self.allneedles:
				self.screen.blit(sprite.image, sprite.rect)				

		else:
			# Draw everything 'below' the player
			for layer in self.tile_layers:
				for tile in layer:
					if not tile.print_above_player and not tile.invisible:
						self.screen.blit(tile.image, self.camera.apply(tile))	

			# Draw the player
			for sprite in self.allplayers:
				self.screen.blit(sprite.image, self.camera.apply(sprite))

			# Draw everything 'above' the player
			for layer in self.tile_layers:
				for tile in layer:
					if tile.print_above_player and not tile.invisible:
						self.screen.blit(tile.image, self.camera.apply(tile))	
		
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













