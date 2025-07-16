import pygame
pygame.init()

class Button():
	def __init__(self, x, y, image, scale=1.0):
		width = image.get_width()
		height = image.get_height()
		self.image = pygame.transform.scale(image, (int(width * scale), int(height * scale)))
		self.rect = self.image.get_rect()
		self.rect.topleft = (x, y)
		self.clicked = False

	def draw(self, surface, offset=(0, 0)):
		action = False
		# get mouse position and adjust for offset
		pos = pygame.mouse.get_pos()
		pos = (pos[0] - offset[0], pos[1] - offset[1])
		# check mouseover and clicked conditions
		if self.rect.collidepoint(pos):
			if pygame.mouse.get_pressed()[0] == 1 and self.clicked == False:
				action = True
				self.clicked = True
		if pygame.mouse.get_pressed()[0] == 0:
			self.clicked = False
		# draw button
		surface.blit(self.image, (self.rect.x, self.rect.y))
		return action