#!/Library/Frameworks/Python.framework/Versions/2.7/bin/python2.7
# coding: utf-8

import pygame
import sys
pygame.init()

width, height = 800, 600

screen = pygame.display.set_mode((width, height))
path = 'assets/pokeballs/pokeball_closed.png'
orig = pygame.image.load(path)
large = pygame.image.load(path)
large = pygame.transform.scale(large, (large.get_width() * 2, large.get_height() * 2))
larger = pygame.image.load(path)
larger = pygame.transform.scale(larger, (larger.get_width() * 3, larger.get_height() * 3))

# print(orig.get_width(), orig.get_height())
# print(large.get_width(), large.get_height())
# print(larger.get_width(), larger.get_height())

# myfont = pygame.font.Font(None, 30)
# myfont = pygame.font.Font('assets/misc/lemonmilk_font.otf', 30)
s = '0123456789'
# s = '0'
size = 16 # 32-> 22 per character, 16-> 11 per character
myfont = pygame.font.Font('assets/misc/manti_sans_fixed.otf', size)
myfontsurf = myfont.render(s, False, (0, 255, 0))
print(myfontsurf.get_rect().width)

while True:
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			pygame.quit()
			sys.exit()

		screen.fill((0, 0, 0))
		centery = height / 2
		left = width - len(s) * 11
		screen.blit(myfontsurf, myfontsurf.get_rect(left=left, centery=centery))
		# screen.blit(orig, (0, 0))
		# screen.blit(large, (0, 64))
		# screen.blit(larger, (0, 256))

	pygame.display.flip()
