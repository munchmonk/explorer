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

# bbb -> Game class, main
# ccc -> lots of smaller classes
# ddd -> Player class



import pygame
import sys
import os
import time
import pickle
import copy
import random

import ccc
import const
import ddd


class Game:
	def __init__(self):
		pygame.init()

		# Playing on Mac - fullscreen
		if (1280, 800) in pygame.display.list_modes():
			# self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
			self.screen = pygame.display.set_mode((const.SCREENWIDTH, const.SCREENHEIGHT))

		# Playing on TV - 1024 x 768
		if (1280, 960) in pygame.display.list_modes():
			self.screen = pygame.display.set_mode((const.SCREENWIDTH, const.SCREENHEIGHT), pygame.FULLSCREEN)

		# self.screen = pygame.display.set_mode((const.SCREENWIDTH, const.SCREENHEIGHT), pygame.FULLSCREEN)
		# self.screen = pygame.display.set_mode((const.SCREENWIDTH, const.SCREENHEIGHT))
		# display_info = pygame.display.Info()
		# self.screen = pygame.display.set_mode((display_info.current_w, display_info.current_h))
		# self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

		self.allplayers = pygame.sprite.Group()
		self.allpokemon = pygame.sprite.Group()
		self.allneedles = pygame.sprite.Group()
		self.allpokeballs = pygame.sprite.Group()
		self.allsprites = pygame.sprite.Group()

		self.player = ddd.Player(self, 0, 0)

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

		self.pokedex = []
		self.pokedex_mode = False
		self.curr_pokedex_selection = None
		self.pokedex_background = pygame.image.load(os.path.join(os.path.dirname(__file__), 'assets/pokemon/pokedex_background.png')) 
		self.unknown_pokemon = pygame.image.load(os.path.join(os.path.dirname(__file__), 'assets/pokemon/unknown.png'))

		self.font_size = 16
		self.myfont = pygame.font.Font(os.path.join(os.path.dirname(__file__), 'assets/misc/manti_sans_fixed.otf'), self.font_size)

		self.tile_layers = []

		self.curr_level = 'level_1'
		
		self.setup_joysticks()
		self.setup_level(1, 1, ddd.Player.DOWN)
		# self.setup_level(4, 11, ddd.Player.DOWN)

	def spawn_pokemon(self, pokemon_tag):
		common_odds = 0
		uncommon_odds = 0
		rare_odds = 0

		if 'COMMON' in pokemon_tag:
			common_odds += 0.2
			uncommon_odds += 0.01
		elif 'UNCOMMON' in pokemon_tag:
			common_odds += 0.1
			uncommon_odds += 0.1
		elif 'RARE' in pokemon_tag:
			uncommon_odds += 0.2
			rare_odds += 0.05

		common_pool, uncommon_pool, rare_pool = self.populate_spawn_pools()

		if random.random() < rare_odds and rare_pool:
			self.start_fight(random.choice(rare_pool))
		elif random.random() < uncommon_odds and uncommon_pool:
			self.start_fight(random.choice(uncommon_pool))
		elif random.random() < common_odds and common_pool:
			self.start_fight(random.choice(common_pool))


	def populate_spawn_pools(self):
		common_pool = list()
		uncommon_pool = list()
		rare_pool = list()

		if self.curr_level == 'forest':
			common_pool += [1, 4, 7]
			uncommon_pool += [25]

		return common_pool, uncommon_pool, rare_pool
	

	def start_fight(self, dex_id):
		self.fight_mode = True
		self.play_fight_transition()
		new_mon = ccc.Pokemon(self, dex_id)
		self.player.curr_pokemon = new_mon
		self.player.curr_needle = new_mon.catch_needle

		if new_mon not in self.player.pokemon_seen:
			self.player.pokemon_seen.append(dex_id)
			self.player.pokemon_seen.sort()


	def play_fight_transition(self):
		thickness = 1

		while thickness < min(const.SCREENWIDTH, const.SCREENHEIGHT):
			pygame.draw.rect(self.screen, (0, 0, 0), pygame.Rect(0, 0, const.SCREENWIDTH, const.SCREENHEIGHT), thickness)
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
					self.base_tiles[text[0]] = ccc.BaseTile(text, self.curr_level)

	def build_portals(self):
		# To be fed via file in the future

		if self.curr_level == 'level_1':
			self.add_portal(4, 10, 'level_2_PORTAL_3_4', ddd.Player.DOWN)
			self.add_portal(8, 12, 'level_2_PORTAL_9_8', ddd.Player.DOWN)
			self.add_portal(1, 0, 'forest_PORTAL_1_18', ddd.Player.UP)

		if self.curr_level == 'level_2':
			self.add_portal(3, 3, 'level_1_PORTAL_4_11', ddd.Player.DOWN)
			self.add_portal(9, 7, 'level_1_PORTAL_8_13', ddd.Player.DOWN)

		if self.curr_level == 'forest':
			self.add_portal(1, 19, 'level_1_PORTAL_1_1', ddd.Player.DOWN)
			self.add_portal(18, 0, 'cave_PORTAL_3_14', ddd.Player.UP)

		if self.curr_level == 'cave':
			self.add_portal(3, 15, 'forest_PORTAL_18_1', ddd.Player.DOWN)

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
					self.map_width = self.horiz_tiles * const.TILESIZE
					self.map_height = self.vert_tiles * const.TILESIZE

					for y in range(len(metadata)):
						for x in range(len(metadata[y])):
							# Below code was creating a bug where two different tiles overlap; I'll leave it commented for now in case there is a valid reason
							# I wanted to overwrite the tile. I can't think of any now

							# # Overwrites existing tiles
							# existing_tiles = self.find_tile_by_coord((x, y))
							# if existing_tiles:
							# 	for existing_tile in existing_tiles:
							# 		# existing_tile.tile_data = None

							curr_layer.append(ccc.Tile(self, x, y, metadata[y][x]))

				self.tile_layers.append(curr_layer)
				i += 1

			except:
				break

	def quit(self):
		pygame.quit()
		sys.exit()

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
		self.camera = ccc.Camera(self)
		self.fight_mode = False
		self.pokedex_mode = False
		self.pokedex = []
		self.curr_pokedex_selection = None

	def show_curr_tile(self):
		# For debugging/mapbuilding only
		for player in self.allplayers:
			print(player.curr_tile)


	def index_to_coord(self, indexes):
		x = indexes[0] * const.TILESIZE
		y = indexes[1] * const.TILESIZE
		return x, y


	def update(self):
		self.allsprites.update()
		self.camera.update(self.player)

		# Comment out if not debugging/mapbuilding
		# self.show_curr_tile()

	def draw_fight_mode(self):
		self.screen.blit(self.fight_background, (0, 0))

		for sprite in self.allpokemon:
			self.screen.blit(sprite.image, sprite.rect)

			bar_surf, bar_rect = sprite.get_catch_bar()
			self.screen.blit(bar_surf, bar_rect)

		for sprite in self.allneedles:
			self.screen.blit(sprite.image, sprite.rect)

		for sprite in self.allpokeballs:
			self.screen.blit(sprite.image, sprite.rect)

	def get_pokedex(self):
		empty_string = '----------'
		pokedex = []

		if not self.player.pokemon_seen:
			pokedex.append((empty_string, False))

		else:
			for i in range(1, self.player.pokemon_seen[-1] + 1):
				if i in self.player.pokemon_seen:
					if i in self.player.pokemon_caught:
						pokedex.append((self.get_pokemon_name(i), True))
					else:
						pokedex.append((self.get_pokemon_name(i), False))
				else:
					pokedex.append((empty_string, False))

		self.curr_pokedex_selection = 0
		return pokedex




	def draw_pokedex_mode(self):
		self.screen.blit(self.pokedex_background, (0, 0))

		# # 10 = longest pokemon name (kangaskhan); a manti_sans_fixed with font_size of 16 makes each character 11px wide
		# # this aligns to the left and rescales if the font has been enlarged
		left = const.SCREENWIDTH - 10 * 11 * (self.font_size / 16)
		centery = const.SCREENHEIGHT / 2
		pokeball_img = ccc.Pokeball.IMG[ccc.Pokeball.SMALL]

		# Print currently selected pokemon name
		surf = self.myfont.render(self.pokedex[self.curr_pokedex_selection][0], False, (0, 0, 255), (0, 0, 0))
		self.screen.blit(surf, surf.get_rect(left=left, centery=centery))
		if self.pokedex[self.curr_pokedex_selection][1]:
			self.screen.blit(pokeball_img, pokeball_img.get_rect(left=left-16, centery=centery))

		# Print names above
		for i in range(self.curr_pokedex_selection - 1, -1, -1):
			surf = self.myfont.render(self.pokedex[i][0], False, (0, 0, 255))
			self.screen.blit(surf, surf.get_rect(left=left, centery=centery - (self.curr_pokedex_selection - i) * self.font_size / 16 * 20))
			if self.pokedex[i][1]:
				self.screen.blit(pokeball_img, pokeball_img.get_rect(left=left-16, centery=centery - (self.curr_pokedex_selection - i) * self.font_size / 16 * 20))

		# Print names below
		for i in range(self.curr_pokedex_selection + 1, len(self.pokedex)):
			surf = self.myfont.render(self.pokedex[i][0], False, (0, 0, 255))
			self.screen.blit(surf, surf.get_rect(left=left, centery=centery + (i - self.curr_pokedex_selection) * self.font_size / 16 * 20))
			if self.pokedex[i][1]:
				self.screen.blit(pokeball_img, pokeball_img.get_rect(left=left-16, centery=centery + (i - self.curr_pokedex_selection) * self.font_size / 16 * 20))
		
		# Print pokemon image
		img = self.unknown_pokemon

		if self.pokedex[self.curr_pokedex_selection][0][0] != '-':
			img = pygame.image.load(ccc.Pokemon.MAIN_PATH + ccc.Pokemon.INDIVIDUAL_PATH[self.curr_pokedex_selection + 1])

		self.screen.blit(img, img.get_rect(left=const.SCREENWIDTH / 6, centery=centery))


	def get_pokemon_name(self, dex_id):
		all_pokemon =  {1: 'Bulbasaur',
						4: 'Charmander',
						7: 'Squirtle',
						25: 'Pikachu'}

		return all_pokemon[dex_id]



	def draw_walking_mode(self):
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


	def draw(self):
		self.screen.fill((0, 0, 0))

		if self.fight_mode:
			self.draw_fight_mode()

		elif self.pokedex_mode:
			self.draw_pokedex_mode()

		else:
			self.draw_walking_mode()

		pygame.display.flip()


	def play(self):
		while True:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self.quit()
				elif event.type == pygame.KEYDOWN:
					if event.key == pygame.K_ESCAPE:
						self.quit()

			self.update()
			self.draw()
			self.dt = self.clock.tick(45)

if __name__ == '__main__':
	Game().play()







