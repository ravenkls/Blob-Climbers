import pygame
from pygame.locals import *
import os
import entities
import json
import random

pygame.init()

class GridLayout:
	def __init__(self, tile_width, tile_height):
		self.tile_width = tile_width
		self.tile_height = tile_height
		self.window_w, self.window_h = pygame.display.get_surface().get_size()
		self.grid = []
		for y in range(int(self.window_h/self.tile_height)):
			row = []
			for x in range(int(self.window_w/self.tile_width)):
				tile = entities.Block(self.tile_width, self.tile_height, 0, 0)
				row.append(tile)
			self.grid.append(row)
		self.set_grid_positions(self.grid)

	def set_dynamic_sprites(self):
		for block in filter(lambda x: isinstance(x, entities.DynamicBlock), self.blocks):
			block.set_dynamic_sprite(self.grid)

	def add_layer(self):
		row = [entities.Block(self.tile_width, self.tile_height, 0, 0) for b in range(len(self.grid[0]))]
		self.grid.insert(0, row)


	def set_grid_positions(self, grid):
		grid_height = len(grid)
		grid_width = len(grid[0])
		top_most_position = self.window_h - grid_height*self.tile_height
		for y in range(grid_height):
			for x in range(grid_width):
				block = grid[y][x]
				block.rect.x = x*self.tile_width
				block.rect.y = top_most_position + y*self.tile_height

	@property
	def blocks(self):
		return pygame.sprite.Group(*[block for row in self.grid for block in row])

	@classmethod
	def from_json(cls, filename):
		with open(filename, 'r') as json_file:
			level = json.load(json_file)
		width, height = level['width'], level['height']
		references = level['references']
		grid_blueprint = level['blueprint']
		grid = []
		for row_blueprint in grid_blueprint:
			row = []
			for tile_repr in row_blueprint:
				if tile_repr:
					tile_type = references[tile_repr[:-1]]
					solid = tile_repr[-1] == 's'
					row.append(entities.Block.from_image_file(tile_type, 0, 0, solid=solid))
				else:
					row.append(entities.Block(width, height, 0, 0))
			grid.append(row)
		gridclass = cls(width, height)
		gridclass.grid = grid
		gridclass.set_grid_positions(grid)
		return gridclass


WINDOW_WIDTH = 640
WINDOW_HEIGHT = 480

SKY_BLUE = (135,206,235)

game_running = True
window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption('Blob Climbers V2')
clock = pygame.time.Clock()

camera_x = 0
camera_y = 0
camera_sensitivity_x = 150
camera_sensitivity_y = 100

grass_floor_thickness = 10
player = entities.PlayerEntity(spawn=(WINDOW_WIDTH/2, -100))
#grid = GridLayout.from_json('levels/level_1.json')

grid = GridLayout(32, 32)


def generate_platform(block_type, i=0, start_platform_point='auto', max_length=9999):
	row = grid.grid[i]
	if not any(block.solid for block in row):
		if start_platform_point != 'auto':
			platform_length = min(random.randint(2, len(grid.grid[i])//2), 19-start_platform_point, max_length)
			end_platform_point = start_platform_point + platform_length
		else:
			platform_length = min(random.randint(2, len(grid.grid[i])//2), max_length)
			start_platform_point = random.randint(0, len(grid.grid[i]) - 1 - platform_length)
			end_platform_point = start_platform_point + platform_length

		grid.grid[i][start_platform_point:end_platform_point] = [block_type() for _ in range(platform_length)]
		grid.set_dynamic_sprites()
		return start_platform_point, platform_length



next_point = 'auto'
max_next_length = 999
def generate_realistic_platform(i=0):
	global next_point
	global max_next_length
	grid.add_layer()
	grid.add_layer()
	grid.add_layer()
	last_point, length = generate_platform(entities.GrassBlock, i, start_platform_point=next_point, max_length=max_next_length)
	next_point = -1
	while 0 >= next_point or next_point >= len(grid.grid)-1:
		next_point = random.choice([random.randint(last_point-4, last_point-1), random.randint(last_point+1, last_point+4)])
		if next_point < last_point:
			max_next_length = length + next_point
	grid.set_grid_positions(grid.grid)
	return last_point, length


for _ in range(grass_floor_thickness):
	grid.grid.append([entities.GrassBlock() for _ in range(len(grid.grid[0]))])
grid.set_dynamic_sprites()

for i in range(0, len(grid.grid), 3):
	generate_platform(entities.GrassBlock, i)

for _ in range(20):
	generate_realistic_platform()

def load_all_sprites():
	all_entities = pygame.sprite.Group(player)
	blocks = grid.blocks
	all_sprites = pygame.sprite.Group(blocks, all_entities)
	return all_entities, blocks, all_sprites

all_entities, blocks, all_sprites = load_all_sprites()

grid.set_grid_positions(grid.grid)

keys_pressed = []
while game_running:

	for event in pygame.event.get():
		if event.type == QUIT:
			game_running = False
		elif event.type == KEYDOWN:
			keys_pressed.append(event.key)
		elif event.type == KEYUP:
			if event.key == K_RIGHT or event.key == K_LEFT:
				player.stop_moving()
			keys_pressed.remove(event.key)

	for key in keys_pressed:
		if key == K_RIGHT:
			player.move_right(2)
		elif key == K_LEFT:
			player.move_left(2)
		elif key == K_UP:
			player.jump(4)

	pygame.display.update()

	window.fill(SKY_BLUE)


	if player.rect.left < camera_sensitivity_x: # too left
		camera_x += camera_sensitivity_x - player.rect.left
	elif player.rect.right > WINDOW_WIDTH - camera_sensitivity_x: # too right
		camera_x -= camera_sensitivity_x - (WINDOW_WIDTH - player.rect.right)
	else:
		camera_x = 0

	if player.rect.top < camera_sensitivity_y: # too high
		camera_y += camera_sensitivity_y - player.rect.top
	elif player.rect.bottom > WINDOW_HEIGHT -  camera_sensitivity_y: # too low
		camera_y -= camera_sensitivity_y - (WINDOW_HEIGHT - player.rect.bottom)
	else:
		camera_y = 0

	platform_removed = False
	for sprite in all_sprites:
		# Process All sprites
		sprite.rect.x += camera_x
		sprite.rect.y += camera_y

		if sprite.rect.top > WINDOW_HEIGHT:
			sprite.image.fill((0,0,0))
			sprite.image.set_colorkey((0,0,0))
			sprite.solid = False
			all_sprites.remove(sprite)
			platform_removed = True

	if platform_removed:
		generate_realistic_platform()

	blocks.update()
	all_entities.update()
	player.check_collisions(blocks)
	all_entities.draw(window)
	blocks.draw(window)

	clock.tick(120)

pygame.quit()
