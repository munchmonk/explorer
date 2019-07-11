#!/Library/Frameworks/Python.framework/Versions/2.7/bin/python2.7
# coding: utf-8

""" 
	NEXT UP:
	---

	TODO:
	potentially allow for manual metadata override

"""

import pygame
import sys
import pickle
import os
import random


class Camera:
	def __init__(self, screen_size, map_size):
		self.pos = [0, 0]
		self.maxwidth = 0
		self.maxheight = 0

		self.setup(screen_size, map_size)

	def reset(self):
		self.pos = [0, 0]

	def setup(self, screen_size, map_size):
		self.maxwidth = -(map_size[0] - screen_size[0]) if map_size[0] > screen_size[0] else 0
		self.maxheight = -(map_size[1] - screen_size[1]) if map_size[1] > screen_size[1] else 0

	def move(self, x, y):
		self.pos[0] -= x * MapEditor.TILESIZE
		self.pos[1] -= y * MapEditor.TILESIZE

		if self.pos[0] > 0:
			self.pos[0] = 0
		if self.pos[1] > 0:
			self.pos[1] = 0
		if self.pos[0] < self.maxwidth:
			self.pos[0] = self.maxwidth
		if self.pos[1] < self.maxheight:
			self.pos[1] = self.maxheight

	def apply_to_coord(self, coord):
		return coord[0] - self.pos[0], coord[1] - self.pos[1]

	def get_pos(self):
		return self.pos


class Util:
	def __init__(self):
		pass

	def round_down_coords(self, coord):
		# Rounds down coordinates to the nearest TILESIZE
		return (coord[0] / MapEditor.TILESIZE * MapEditor.TILESIZE, coord[1] / MapEditor.TILESIZE * MapEditor.TILESIZE)

	def coord_to_index(self, coord):
		# Converts coordinates to indexes
		return coord[0] / MapEditor.TILESIZE, coord[1] / MapEditor.TILESIZE

	def initialise_tilesets(self):
		tilesets = list()
		folder_path = os.path.dirname(__file__)
		target_path = 'tilesets'
		tilesets_path = os.path.join(folder_path, target_path)

		subfolders = [x[0] for x in os.walk(tilesets_path)]

		for subfolder in subfolders:

			# Skips the current folder
			if subfolder == tilesets_path:
				continue

			tileset = list()

			try:
				with open(os.path.join(subfolder, 'metadata.txt'), 'r') as metadata_file:
					tot_entries = 0

					for line in metadata_file:
						text = line.split()

						# Avoids empty lines
						if text:
							tileset.append(text)
							tot_entries += 1
					
					# Sanity check #1 - numbers of tiles and entries in the metadata file must match
					tot_tiles = len([tile for tile in os.listdir(subfolder) if tile[-4:] == '.jpg'])
					if tot_tiles > tot_entries:
						print('ERROR: not enough metadata entries for tileset {}. Aborting.'.format(subfolder))
						self.quit()
					elif tot_tiles < tot_entries:
						print('ERROR: too many metadata entries for tileset {}. Aborting.'.format(subfolder))
						self.quit()
						
			except IOError:
				print('Error: no metadata file for tileset {}. Aborting.'.format(subfolder))

			# Replaces the file names with the actual images
			for entry in tileset:
				try:
					entry[0] = pygame.image.load(os.path.join(subfolder, entry[0]))
				except pygame.error:
					# Sanity check #2: all entries in the metadata file must correspond to a tile
					print('ERROR: no tile found matching metadata entry {}. Aborting.'.format(entry[0]))
					self.quit()

			tilesets.append(tileset)

		return tilesets

	def initialise_blank_tile(self):
		folder_path = os.path.dirname(__file__)
		img_path = os.path.join(folder_path, "blank.jpg")
		return pygame.image.load(img_path)

	def quit(self):
		pygame.quit()
		sys.exit()

	def is_coord_within_map_bounds(self, coord):
		if coord[0] < MapEditor.MAPWIDTH and coord[1] < MapEditor.MAPHEIGHT:
			return True
		return False


class MapEditor:
	TILESIZE = 32
	SCREENWIDTH = TILESIZE * 20
	SCREENHEIGHT = TILESIZE * 20
	MAPWIDTH = TILESIZE * 20
	MAPHEIGHT = TILESIZE * 20
	FPS = 60

	def __init__(self):
		pygame.init()
		self.screen = pygame.display.set_mode((MapEditor.SCREENWIDTH, MapEditor.SCREENHEIGHT))
		# self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
		
		self.util = Util()
		
		self.my_map = pygame.Surface((MapEditor.MAPWIDTH, MapEditor.MAPHEIGHT))
		self.my_metadata = [[0] * (self.my_map.get_width() / MapEditor.TILESIZE) for i in range(self.my_map.get_height() / MapEditor.TILESIZE)]

		self.tilesets = self.util.initialise_tilesets()
		self.curr_tileset_index = 0
		self.curr_tileset = self.tilesets[self.curr_tileset_index]
		self.curr_tile_index = 0
		self.curr_tile = self.curr_tileset[self.curr_tile_index][0]
		self.random_tile_mode = False
		
		self.blank_tile = self.util.initialise_blank_tile()

		self.camera = Camera(self.screen.get_size(), self.my_map.get_size())
		self.clock = pygame.time.Clock()

	def next_tileset(self):
		self.curr_tileset_index = (self.curr_tileset_index + 1) % len(self.tilesets)
		self.curr_tileset = self.tilesets[self.curr_tileset_index]

		# Reset index to 0 in case new tileset is smaller than previous one - avoids index out of range
		self.curr_tile_index = 0
		self.curr_tile = self.curr_tileset[self.curr_tile_index][0]

	def prev_tileset(self):
		self.curr_tileset_index = (self.curr_tileset_index - 1) % len(self.tilesets)
		self.curr_tileset = self.tilesets[self.curr_tileset_index]

		# Reset index to 0 in case new tileset is smaller than previous one - avoids index out of range
		self.curr_tile_index = 0
		self.curr_tile = self.curr_tileset[self.curr_tile_index][0]

	def next_tile(self):
		self.curr_tile_index = (self.curr_tile_index + 1) % len(self.curr_tileset)
		self.curr_tile = self.curr_tileset[self.curr_tile_index][0]

	def prev_tile(self):
		self.curr_tile_index = (self.curr_tile_index - 1) % len(self.curr_tileset)
		self.curr_tile = self.curr_tileset[self.curr_tile_index][0]

	def random_tile(self):
		self.curr_tile_index = random.randrange(len(self.curr_tileset))
		self.curr_tile = self.curr_tileset[self.curr_tile_index][0]

	def save(self):
		pygame.image.save(self.my_map, os.path.join(os.path.dirname(__file__), 'map.jpeg'))
		with open(os.path.join(os.path.dirname(__file__), 'metadata.p'), 'wb') as out_file:
			pickle.dump(self.my_metadata, out_file)

		print('Map saved successfully.')

	def load(self):
		# Load metadata and adjust to size of loaded map
		with open(os.path.join(os.path.dirname(__file__), 'metadata.p'), 'rb') as in_file:
			old_data = self.my_metadata
			new_data = pickle.load(in_file)

			# Loaded data has more rows than current one: add more rows
			if len(new_data) > len(old_data):
				diff = len(new_data) - len(old_data)
				MapEditor.MAPHEIGHT += diff * MapEditor.TILESIZE

			# Loaded data has more columns than current one: add more columns
			if len(new_data[0]) > len(old_data[0]):
				diff = len(new_data[0]) - len(old_data[0])
				MapEditor.MAPWIDTH += diff * MapEditor.TILESIZE

			# Loaded data has fewer rows than current map: remove rows
			if len(new_data) < len(old_data):
				diff = len(old_data) - len(new_data)
				MapEditor.MAPHEIGHT -= diff * MapEditor.TILESIZE

			# Loaded data has fewer columns than current map: remove columns
			if len(new_data[0]) < len(old_data[0]):
				diff = len(old_data[0]) - len(new_data[0])
				MapEditor.MAPWIDTH -= diff * MapEditor.TILESIZE

			self.my_metadata = new_data

		# Load map and clear screen
		self.my_map = pygame.image.load(os.path.join(os.path.dirname(__file__), 'map.jpeg'))
		self.screen.fill((0, 0, 0))

		# Update camera
		self.camera.setup(self.screen.get_size(), self.my_map.get_size())
		self.camera.reset()

		print('Map loaded successfully.')

	def clear(self):
		self.my_map = pygame.Surface((MapEditor.MAPWIDTH, MapEditor.MAPHEIGHT))
		self.metadata = [[0] * (self.my_map.get_width() / MapEditor.TILESIZE) for i in range(self.my_map.get_height() / MapEditor.TILESIZE)]

	def insert_row(self):
		MapEditor.MAPHEIGHT += MapEditor.TILESIZE

		# Update map
		new_map = pygame.Surface((MapEditor.MAPWIDTH, MapEditor.MAPHEIGHT))
		new_map.blit(self.my_map, (0, 0))
		self.my_map = new_map

		# Update metadata
		new_metadata = [[0] * (self.my_map.get_width() / MapEditor.TILESIZE) for i in range(self.my_map.get_height() / MapEditor.TILESIZE)]

		for i in range(len(self.my_metadata)):
			new_metadata[i] = self.my_metadata[i]
		self.my_metadata = new_metadata

		# Update camera
		self.camera.setup(self.screen.get_size(), self.my_map.get_size())

	def insert_column(self):
		MapEditor.MAPWIDTH += MapEditor.TILESIZE

		# Update map
		new_map = pygame.Surface((MapEditor.MAPWIDTH, MapEditor.MAPHEIGHT))
		new_map.blit(self.my_map, (0, 0))
		self.my_map = new_map

		# Update metadata
		new_metadata = [[0] * (self.my_map.get_width() / MapEditor.TILESIZE) for i in range(self.my_map.get_height() / MapEditor.TILESIZE)]

		for i in range(len(self.my_metadata)):
			for j in range(len(self.my_metadata[i])):	
				new_metadata[i][j] = self.my_metadata[i][j]
		self.my_metadata = new_metadata

		# Update camera
		self.camera.setup(self.screen.get_size(), self.my_map.get_size())

	def delete_row(self):
		MapEditor.MAPHEIGHT -= MapEditor.TILESIZE

		# Update map
		row_to_delete = pygame.Rect(0, MapEditor.MAPHEIGHT, MapEditor.MAPWIDTH, MapEditor.TILESIZE)
		self.my_map.fill((0, 0, 0), row_to_delete)
		self.draw()

		new_map = pygame.Surface((MapEditor.MAPWIDTH, MapEditor.MAPHEIGHT))
		new_map.blit(self.my_map, (0, 0))
		self.my_map = new_map

		# Update metadata
		new_metadata = [[0] * (self.my_map.get_width() / MapEditor.TILESIZE) for i in range(self.my_map.get_height() / MapEditor.TILESIZE)]

		for i in range(len(new_metadata)):
			new_metadata[i] = self.my_metadata[i]
		self.my_metadata = new_metadata

		# Update camera
		self.camera.setup(self.screen.get_size(), self.my_map.get_size())
		self.camera.move(0, -1)

	def delete_column(self):
		MapEditor.MAPWIDTH -= MapEditor.TILESIZE

		# Update map
		column_to_delete = pygame.Rect(MapEditor.MAPWIDTH, 0, MapEditor.TILESIZE, MapEditor.MAPHEIGHT)
		self.my_map.fill((0, 0, 0), column_to_delete)
		self.draw()

		new_map = pygame.Surface((MapEditor.MAPWIDTH, MapEditor.MAPHEIGHT))
		new_map.blit(self.my_map, (0, 0))
		self.my_map = new_map

		# Update metadata
		new_metadata = [[0] * (self.my_map.get_width() / MapEditor.TILESIZE) for i in range(self.my_map.get_height() / MapEditor.TILESIZE)]

		for i in range(len(new_metadata)):
			for j in range(len(new_metadata[i])):
				new_metadata[i][j] = self.my_metadata[i][j]
		self.my_metadata = new_metadata

		# Update camera
		self.camera.setup(self.screen.get_size(), self.my_map.get_size())
		self.camera.move(-1, 0)

	def process_events(self):
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				self.util.quit()

			elif event.type == pygame.KEYDOWN:
				# ESC - exit program
				if event.key == pygame.K_ESCAPE:
					self.util.quit()

				# E - next tileset
				elif event.key == pygame.K_e:
					self.next_tileset()

				# Q - prev tileset
				elif event.key == pygame.K_q:
					self.prev_tileset()

				# F - toggle randomiser
				elif event.key == pygame.K_f:
					self.random_tile_mode = not self.random_tile_mode

				# 9 - insert row
				elif event.key == pygame.K_9:
					self.insert_row()	

				# 7 - insert column
				elif event.key == pygame.K_7:
					self.insert_column()	

				# 0 - delete row
				elif event.key == pygame.K_0:
					self.delete_row()	

				# 8 - delete column
				elif event.key == pygame.K_8:
					self.delete_column()			

				# K - save
				elif event.key == pygame.K_k:
					self.save()

				# L - load
				elif event.key == pygame.K_l:
					self.load()

				# C - clear
				elif event.key == pygame.K_c:
					self.clear()

			# Change tiles with mousewheel
			elif event.type == pygame.MOUSEBUTTONDOWN:
				if event.button == 4:
					self.prev_tile()
				elif event.button == 5:
					self.next_tile()


	def get_camera_movements(self):
		# WASD - move camera
		keys = pygame.key.get_pressed()
		if keys[pygame.K_w]:
			self.camera.move(0, -1)
		if keys[pygame.K_a]:
			self.camera.move(-1, 0)
		if keys[pygame.K_s]:
			self.camera.move(0, 1)
		if keys[pygame.K_d]:
			self.camera.move(1, 0)

	def process_mouse_clicks(self):
		# Left click - draw
		if pygame.mouse.get_pressed()[0]:
			coord = self.util.round_down_coords(self.camera.apply_to_coord(list(pygame.mouse.get_pos())))

			if not self.util.is_coord_within_map_bounds(coord):
				return

			if self.random_tile_mode:
				self.random_tile()

			self.my_map.blit(self.curr_tile, coord)
			x, y = self.util.coord_to_index(coord)
			self.my_metadata[y][x] = self.curr_tileset[self.curr_tile_index][1:]

		# Right click - erase
		elif pygame.mouse.get_pressed()[2]:
			coord = self.util.round_down_coords(self.camera.apply_to_coord(list(pygame.mouse.get_pos())))

			if not self.util.is_coord_within_map_bounds(coord):
				return

			self.my_map.blit(self.blank_tile, coord)
			x, y = self.util.coord_to_index(coord)
			self.my_metadata[y][x] = [0]

	def draw(self):
		# Draw map
		self.screen.blit(self.my_map, self.camera.get_pos())

		# Preview current tile at cursor position
		coord = self.util.round_down_coords(list(pygame.mouse.get_pos()))
		if self.util.is_coord_within_map_bounds(coord) and pygame.mouse.get_focused():
			self.screen.blit(self.curr_tile, coord)

		pygame.display.flip()

	def play(self):
		while True:
			self.process_events()
			self.get_camera_movements()
			self.process_mouse_clicks()				
			self.draw()
			self.clock.tick(MapEditor.FPS)


if __name__ == '__main__':
	MapEditor().play()