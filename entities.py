import pygame
import os


class Block(pygame.sprite.Sprite):
	def __init__(self, width, height, x=0, y=0, solid=False, name='Block'):
		super().__init__()
		self.x = x
		self.y = y
		self.name = name
		image = pygame.Surface((width, height))
		self.set_image(image)
		self.image.set_colorkey((0,0,0))
		self.solid = solid

	def set_image(self, surface):
		self.image = surface
		self.rect = surface.get_rect()
		self.rect.x = self.x
		self.rect.y = self.y

	@classmethod
	def from_image_file(cls, image_file, x, y, solid=False):
		image = pygame.image.load(image_file)
		image.set_colorkey((255, 255, 255))
		blockclass = cls(image.get_rect().width, image.get_rect().height, x, y, solid=solid, name=os.path.basename(image_file))
		blockclass.set_image(image)
		return blockclass

	def __repr__(self):
		return self.name


class DynamicBlock(Block):
	def set_dynamic_path(self, block_directory, block_name):
		self.sprite_top = pygame.image.load(os.path.join(block_directory, block_name + '.png'))
		self.sprite_left = pygame.image.load(os.path.join(block_directory, block_name + '_side.png'))
		self.sprite_right = pygame.transform.flip(self.sprite_left, True, False)
		self.sprite_center = pygame.image.load(os.path.join(block_directory, block_name + '_center.png'))
		self.sprite_bottom = pygame.image.load(os.path.join(block_directory, block_name + '_bottom.png'))
		self.sprite_floater = pygame.image.load(os.path.join(block_directory, block_name + '_floater.png'))
		self.sprite_floater_right = pygame.image.load(os.path.join(block_directory, block_name + '_floater_side.png'))
		self.sprite_floater_left = pygame.transform.flip(self.sprite_floater_right, True, False)
		self.sprite_single = pygame.image.load(os.path.join(block_directory, block_name + '_single.png'))
		self.sprite_center_left = pygame.image.load(os.path.join(block_directory, block_name + '_center_side.png'))
		self.sprite_center_right = pygame.transform.flip(self.sprite_center_left, True, False)
		self.sprite_bottom_left = pygame.image.load(os.path.join(block_directory, block_name + '_bottom_side.png'))
		self.sprite_bottom_right = pygame.transform.flip(self.sprite_bottom_left, True, False)

	def set_dynamic_sprite(self, grid_layout):
		grid_flattened = [tile for row in grid_layout for tile in row]
		real_index = grid_flattened.index(self)
		col = real_index % len(grid_layout[0])
		row = real_index // len(grid_layout[0])

		if col > 0:
			adjacent_left = type(grid_layout[row][col-1]) == type(self)
		else:
			adjacent_left = False

		try:
			adjacent_right = type(grid_layout[row][col+1]) == type(self)
		except IndexError:
			adjacent_right = False

		if row > 0:
			adjacent_top = type(grid_layout[row-1][col]) == type(self)
		else:
			adjacent_top = False

		try:
			adjacent_bottom = type(grid_layout[row+1][col]) == type(self)
		except IndexError:
			adjacent_bottom = False

		if adjacent_left and adjacent_right and adjacent_bottom and not adjacent_top:
			sprite = self.sprite_top
		elif adjacent_left and adjacent_bottom and not adjacent_right and not adjacent_top:
			sprite = self.sprite_right
		elif adjacent_right and adjacent_bottom and not adjacent_left and not adjacent_top:
			sprite = self.sprite_left
		elif all((adjacent_right, adjacent_left, adjacent_top, adjacent_bottom)):
			sprite = self.sprite_center
		elif adjacent_left and adjacent_right and adjacent_top and not adjacent_bottom:
			sprite = self.sprite_bottom
		elif adjacent_left and adjacent_right and not adjacent_top and not adjacent_bottom:
			sprite = self.sprite_floater
		elif adjacent_left and not adjacent_right and not adjacent_top and not adjacent_bottom:
			sprite = self.sprite_floater_right
		elif adjacent_right and not adjacent_left and not adjacent_top and not adjacent_bottom:
			sprite = self.sprite_floater_left
		elif not adjacent_left and adjacent_right and adjacent_bottom and adjacent_top:
			sprite = self.sprite_center_left
		elif not adjacent_right and adjacent_left and adjacent_bottom and adjacent_top:
			sprite = self.sprite_center_right
		elif not adjacent_bottom and not adjacent_left and adjacent_top and adjacent_right:
			sprite = self.sprite_bottom_left
		elif not adjacent_bottom and adjacent_left and adjacent_top and not adjacent_right:
			sprite = self.sprite_bottom_right
		elif not any((adjacent_right, adjacent_left, adjacent_top, adjacent_bottom)):
			sprite = self.sprite_single

		sprite.set_colorkey((255, 255, 255))
		self.set_image(sprite)


class GrassBlock(DynamicBlock):
	def __init__(self, x=0, y=0):
		super().__init__(32, 32, x=x, y=y, solid=True, name='Grass')
		super().set_dynamic_path('sprites/blocks/grass', 'grass')


class Entity(pygame.sprite.Sprite):

	animation_framerate = 120

	def __init__(self, *image_files, solid=True, animation_speed=10):
		super().__init__()

		self._images = self.convert_images_to_sprites(image_files)

		self.solid = solid
		self.animation_speed = animation_speed
		self.animate = True
		self.current_frame = 0
		self.sprite_frame = 0
		self.image = self._images[self.sprite_frame]
		rectangle_width = max(self.images, key=lambda i: i.get_rect().width).get_rect().width
		rectangle_height = max(self.images, key=lambda i: i.get_rect().height).get_rect().height
		self.rect = pygame.Rect(0, 0, rectangle_width, rectangle_height)

	def convert_images_to_sprites(self, image_files, hflip=False, vflip=False):
		images = []
		for image in image_files:
			if not isinstance(image, pygame.Surface):
				image = pygame.image.load(image)
				image = pygame.transform.flip(image, hflip, vflip)
				image.set_colorkey((255, 255, 255))
			images.append(image)
		return images

	def update(self):
		if self.animate:
			self.current_frame += 1
			if self.current_frame % (self.animation_framerate // self.animation_speed) == 0:
				self.sprite_frame += 1
				if self.sprite_frame >= len(self.images):
					self.sprite_frame = 0
					self.current_frame = 0
		self.image = self.images[self.sprite_frame]

	@property
	def images(self):
		return self._images

	@images.setter
	def images(self, images):
		self._images = images
		self.sprite_frame = 0
		self.current_frame = 0


class PhysicsEntity(Entity):

	gravity = 0.1
	terminal_velocity = 15
	inertia = 20

	def __init__(self, *image_files, solid=True, animation_speed=10):
		super().__init__(*image_files, solid=solid, animation_speed=animation_speed)
		self.x_speed = 0
		self.y_speed = 0
		self.max_x_speed = 0

	@property
	def y_velocity(self):
		return self.y_speed

	@y_velocity.setter
	def y_velocity(self, velocity):
		if velocity < -self.terminal_velocity:
			self.y_speed = -self.terminal_velocity
		elif velocity > self.terminal_velocity:
			self.y_speed = self.terminal_velocity
		else:
			self.y_speed = velocity

	@property
	def x_velocity(self):
		return self.x_speed

	@x_velocity.setter
	def x_velocity(self, velocity):
		if velocity < -self.terminal_velocity:
			self.x_speed = -self.terminal_velocity
		elif velocity > self.terminal_velocity:
			self.x_speed = self.terminal_velocity
		if velocity < self.max_x_speed and self.max_x_speed < 0:
			self.x_speed = self.max_x_speed
		elif velocity > self.max_x_speed and self.max_x_speed > 0:
			self.x_speed = self.max_x_speed
		else:
			self.x_speed = velocity

	@property
	def inertia_calc_value(self):
		return 5 / self.inertia

	def jump(self, power):
		if self.on_ground_flag:
			self.y_velocity -= power

	def move_left(self, speed):
		self.max_x_speed = -speed

	def move_right(self, speed):
		self.max_x_speed = speed

	def stop_moving(self):
		self.max_x_speed = 0

	def check_collisions(self, sprites):
		vertical_offset = 4 # how many pixels down a block until it detects collision
		for sprite in sprites:
			if sprite is not self and sprite.solid:
				if sprite.rect.right > self.rect.left and self.rect.right > sprite.rect.left: # Check X boundaries
					## Vertical Collision Testing
					if self.y_velocity > 0 and self.rect.bottom <= sprite.rect.top + vertical_offset: # Check is falling and is above sprite
						next_frame_position = self.rect.y + self.y_velocity
						if next_frame_position > sprite.rect.top - self.rect.height + vertical_offset:
							self.on_ground()
							self.y_velocity = 0
							self.rect.y = sprite.rect.top - self.rect.height + vertical_offset
					elif self.y_velocity < 0 and self.rect.top >= sprite.rect.bottom: # Check is jumping and is below sprite
						next_frame_position = self.rect.y + self.y_velocity
						if next_frame_position < sprite.rect.bottom:
							self.y_velocity = 0
							self.rect.y = sprite.rect.bottom
					## Horizontal Collision Testing

	def update(self):
		super().update()

		if self.y_velocity < 0:
			self.jumping()
		elif self.y_velocity > 0:
			self.falling()

		self.rect.y += self.y_velocity
		self.rect.x += self.x_velocity
		self.y_velocity += self.gravity

		if self.max_x_speed != 0:
			if self.max_x_speed < 0:
				if self.x_velocity - self.inertia_calc_value <= self.max_x_speed:
					self.x_velocity = self.max_x_speed
				else:
					self.x_velocity -= self.inertia_calc_value
			elif self.max_x_speed > 0:
				if self.x_velocity + self.inertia_calc_value >= self.max_x_speed:
					self.x_velocity = self.max_x_speed
				else:
					self.x_velocity += self.inertia_calc_value
		else:
			if self.x_velocity < 0:
				if self.x_velocity + self.inertia_calc_value >= 0:
					self.x_velocity = 0
				else:
					self.x_velocity += self.inertia_calc_value
			elif self.x_velocity > 0:
				if self.x_velocity - self.inertia_calc_value <= 0:
					self.x_velocity = 0
				else:
					self.x_velocity -= self.inertia_calc_value

	def jumping(self):
		pass

	def falling(self):
		pass

	def on_ground(self):
		pass

class PlayerEntity(PhysicsEntity):

	LEFT = -1
	RIGHT = 1
	inertia = 25

	def __init__(self, spawn):
		self.player_move_animation = [os.path.join('sprites', 'player0.png'),
									  os.path.join('sprites', 'player1.png'),
									  os.path.join('sprites', 'player2.png'),
									  os.path.join('sprites', 'player3.png'),
									  os.path.join('sprites', 'player4.png')]
		self.player_jump_animation = [os.path.join('sprites', 'player_jump.png')]
		self.player_fall_animation = [os.path.join('sprites', 'player_fall.png')]
		super().__init__(*self.player_move_animation)
		self.rect.x = spawn[0]
		self.rect.y = spawn[1]
		print(spawn)
		self.falling_threshold = 0
		self.facing = self.RIGHT
		self.last_face = self.RIGHT
		self.animate = False
		self.jumping_flag = False
		self.falling_flag = False
		self.on_ground_flag = False
		self.moving_left_flag = False
		self.moving_right_flag = False

	def move_right(self, speed):
		super().move_right(speed)
		self.facing = self.RIGHT
		self.last_face = self.LEFT

		self.moving_left_flag = False
		if not self.moving_right_flag and not (self.jumping_flag or self.falling_flag):
			self.moving_right_flag = True
			self.images = self.convert_images_to_sprites(self.player_move_animation)

		self.animate = True

	def stop_moving(self):
		super().stop_moving()
		self.animate = False
		self.sprite_frame = 0
		self.current_frame = 0

	def move_left(self, speed):
		super().move_left(speed)
		self.facing = self.LEFT
		self.last_face = self.RIGHT

		self.moving_right_flag = False
		if not self.moving_left_flag and not (self.jumping_flag or self.falling_flag):
			self.moving_left_flag = True
			self.images = self.convert_images_to_sprites(self.player_move_animation, hflip=True)

		self.animate = True

	def jumping(self):
		self.on_ground_flag = False
		self.falling_flag = False
		if not self.jumping_flag:
			self.jumping_flag = True
			if self.facing == self.RIGHT:
				self.images = self.convert_images_to_sprites(self.player_jump_animation)
			else:
				self.images = self.convert_images_to_sprites(self.player_jump_animation, hflip=True)
			self.image = self.images[0]
			self.animate = False

	def falling(self):
		if self.jumping_flag:
			self.jumping_flag = False
			if self.facing == self.RIGHT:
				self.images = self.convert_images_to_sprites(self.player_move_animation)
			else:
				self.images = self.convert_images_to_sprites(self.player_move_animation, hflip=True)
			self.image = self.images[0]
			self.animate = False
			self.falling_threshold = 2
		elif self.y_velocity > self.falling_threshold:
			self.on_ground_flag = False
			self.falling_threshold = 0
			if not self.falling_flag or self.last_face != self.facing:
				self.last_face = self.facing
				self.falling_flag = True
				if self.facing == self.RIGHT:
					self.images = self.convert_images_to_sprites(self.player_fall_animation)
				else:
					self.images = self.convert_images_to_sprites(self.player_fall_animation, hflip=True)
				self.image = self.images[0]
				self.animate = False

	def on_ground(self):
		self.falling_flag = False
		self.jumping_flag = False
		if not self.on_ground_flag:
			self.on_ground_flag = True
			if self.facing == self.RIGHT:
				self.images = self.convert_images_to_sprites(self.player_move_animation)
			else:
				self.images = self.convert_images_to_sprites(self.player_move_animation, hflip=True)
			self.animate = False
