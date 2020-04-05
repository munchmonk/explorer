#!/Library/Frameworks/Python.framework/Versions/2.7/bin/python2.7
# coding: utf-8

import pygame
import os
import time

import ccc
import const


class Player(pygame.sprite.Sprite):
	RIGHT, LEFT, UP, DOWN = range(4)

	IMG =  {RIGHT: [pygame.image.load(os.path.join(os.path.dirname(__file__), 'assets/player/player_right_0.png')),
					pygame.image.load(os.path.join(os.path.dirname(__file__), 'assets/player/player_right_1.png'))],

			LEFT:  [pygame.image.load(os.path.join(os.path.dirname(__file__), 'assets/player/player_left_0.png')),
					pygame.image.load(os.path.join(os.path.dirname(__file__), 'assets/player/player_left_1.png'))],

			UP:    [pygame.image.load(os.path.join(os.path.dirname(__file__), 'assets/player/player_up_0.png')),
					pygame.image.load(os.path.join(os.path.dirname(__file__), 'assets/player/player_up_1.png')),
					pygame.image.load(os.path.join(os.path.dirname(__file__), 'assets/player/player_up_2.png'))],

			DOWN:  [pygame.image.load(os.path.join(os.path.dirname(__file__), 'assets/player/player_down_0.png')),
					pygame.image.load(os.path.join(os.path.dirname(__file__), 'assets/player/player_down_1.png')),
					pygame.image.load(os.path.join(os.path.dirname(__file__), 'assets/player/player_down_2.png'))]}

	POKEBALL_IMG = {'open': pygame.image.load(os.path.join(os.path.dirname(__file__), 'assets/pokeballs/pokeball_open.png')),
					'half_open': pygame.image.load(os.path.join(os.path.dirname(__file__), 'assets/pokeballs/pokeball_half_open.png')),
					'closed': pygame.image.load(os.path.join(os.path.dirname(__file__), 'assets/pokeballs/pokeball_closed.png'))}

	MOVEMENT_COOLDOWN = 0.1
	SPEED = 0.1
	ANIMFRAME_COOLDOWN = 0.2
	
	def __init__(self, game, spawn_x, spawn_y):
		self.game = game
		self.groups = game.allsprites, game.allplayers
		pygame.sprite.Sprite.__init__(self, self.groups)

		# This below is a copy of reset() but I'd rather it be clear what attributes Player has instead of declaring them outside of init()
		self.curr_tile = [spawn_x, spawn_y]
		self.facing = Player.DOWN
		self.anim_frame = 0
		self.image = Player.IMG[self.facing][self.anim_frame]
		self.rect = self.image.get_rect(topleft=(self.game.index_to_coord(self.curr_tile)))

		self.last_anim = 0
		self.last_movement = 0
		self.dir = [0, 0]
		self.target_tile = None
		self.target_x = None
		self.target_y = None

		self.curr_pokemon = None
		self.curr_needle = None
		self.curr_pokeball = None
		self.pokemon_caught = list()
		self.pokemon_seen = list()

		self.last_pokedex_scroll = 0

	def get_input(self):
		# Don't accept input if player is already moving
		if self.dir != [0, 0]:
			return

		keys = pygame.key.get_pressed()

		# Fight mode
		if self.game.fight_mode:
			if keys[pygame.K_q] and not self.curr_pokeball:
				self.exit_fight_mode()
			elif keys[pygame.K_SPACE] and not self.curr_pokeball:
				self.throw_pokeball()

		# Pokedex mode
		if self.game.pokedex_mode:
			if keys[pygame.K_q]:
				self.exit_pokedex_mode()
			elif keys[pygame.K_w] and time.time() - self.last_pokedex_scroll > 0.15:
				self.move_up_pokedex()
			elif keys[pygame.K_s] and time.time() - self.last_pokedex_scroll > 0.15:
				self.move_down_pokedex()


		# Walking mode
		else:
			if keys[pygame.K_w] or keys[pygame.K_UP]:
				self.dir = [0, -1]
			elif keys[pygame.K_a] or keys[pygame.K_LEFT]:
				self.dir = [-1, 0]
			elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
				self.dir = [0, 1]
			elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
				self.dir = [1, 0]
			elif keys[pygame.K_p]:
				self.game.pokedex_mode = True

			if self.game.joysticks:
				if self.game.joysticks[0].get_axis(0) > 0.5:
					self.dir = [1, 0]
				if self.game.joysticks[0].get_axis(0) < -0.5:
					self.dir = [-1, 0]
				if self.game.joysticks[0].get_axis(1) > 0.5:
					self.dir = [0, 1]
				if self.game.joysticks[0].get_axis(1) < -0.5:
					self.dir = [0, -1]

			self.set_facing()

	def set_facing(self):
		if self.dir == [1, 0]:
			self.facing = Player.RIGHT
		elif self.dir == [-1, 0]:
			self.facing = Player.LEFT
		elif self.dir == [0, -1]:
			self.facing = Player.UP
		elif self.dir == [0, 1]:
			self.facing = Player.DOWN

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

		if any(tag in ('WATER', 'BOULDER', 'ROCK') for tag in tags):
			return False

		if 'TREE' in tags and 'BOTTOM' in tags:
			return False

		if 'CASA' in tags:
			if any(tag in ('BOTTOM_LEFT', 'BOTTOM_RIGHT', 'TOP_LEFT', 'MID_TOP', 'TOP_RIGHT') for tag in tags):
				return False

		return True


	def throw_pokeball(self):
		self.curr_needle.stop()
		self.curr_pokeball = ccc.Pokeball(self.game, self.curr_pokemon, self.curr_needle.success())


	def update_fight(self):
		if not self.game.fight_mode:
			return 

		if self.curr_needle.stopped:
			if self.curr_needle.success():
				if self.curr_pokemon.dex_id not in self.pokemon_caught:
					self.pokemon_caught.append(self.curr_pokemon.dex_id)
					self.pokemon_caught.sort()
			if self.curr_pokeball.dead:
				self.curr_pokeball = None
				self.exit_fight_mode()

	def update_pokedex(self):
		if not self.game.pokedex_mode:
			return

		if not self.game.pokedex:
			self.game.pokedex = self.game.get_pokedex()


	def move_up_pokedex(self):
		if self.game.curr_pokedex_selection > 0:
			self.game.curr_pokedex_selection -= 1
			self.last_pokedex_scroll = time.time()



	def move_down_pokedex(self):
		if self.game.curr_pokedex_selection < len(self.game.pokedex) - 1:
			self.game.curr_pokedex_selection += 1
			self.last_pokedex_scroll = time.time()


	def exit_fight_mode(self):
		self.game.fight_mode = False
		self.curr_pokemon.kill()
		self.curr_pokemon = None
		self.curr_needle.kill()
		self.curr_needle = None

	def exit_pokedex_mode(self):
		self.game.pokedex_mode = False
		self.game.pokedex = []


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
				self.target_x = self.rect.x + self.dir[0] * const.TILESIZE
				self.target_y = self.rect.y + self.dir[1] * const.TILESIZE	

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
				self.get_input()
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
		self.rect = self.image.get_rect(topleft=(self.game.index_to_coord(self.curr_tile)))

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
				self.anim_frame = (self.anim_frame + 1) % len(Player.IMG[Player.DOWN])
				self.last_anim = time.time()
		elif self.dir == [0, -1]:
			if time.time() - self.last_anim > Player.ANIMFRAME_COOLDOWN:
				self.anim_frame = (self.anim_frame + 1) % len(Player.IMG[Player.UP])
				self.last_anim = time.time()
		elif self.dir == [1, 0]:
			if time.time() - self.last_anim > Player.ANIMFRAME_COOLDOWN:
				self.anim_frame = (self.anim_frame + 1) % len(Player.IMG[Player.RIGHT])
				self.last_anim = time.time()
		elif self.dir == [-1, 0]:
			if time.time() - self.last_anim > Player.ANIMFRAME_COOLDOWN:
				self.anim_frame = (self.anim_frame + 1) % len(Player.IMG[Player.LEFT])
				self.last_anim = time.time()

		self.image = Player.IMG[self.facing][self.anim_frame]

	def update(self):
		self.get_input()
		self.move()
		self.update_fight()
		self.update_pokedex()
		self.update_sprite()







		