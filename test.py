#!/Library/Frameworks/Python.framework/Versions/2.7/bin/python2.7
# coding: utf-8

import pygame
pygame.init()

class Test(pygame.sprite.Sprite):
	def __init__(self):
		self.groups = allplayers
		pygame.sprite.Sprite.__init__(self, self.groups)
		print('created')

allplayers = pygame.sprite.Group()
Test()