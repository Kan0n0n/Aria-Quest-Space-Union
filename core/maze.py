import pygame
from constants import *
from core.bg import StarryBackground
from maze_layout import MAZE_LAYOUT
import math


class Maze:
    def __init__(self):
        self.layout = MAZE_LAYOUT
        self.width = len(self.layout[0])
        self.height = len(self.layout)
        self.pellets = set()
        self.power_pellets = set()
        self.total_pellets = 0
        self.wall_image = pygame.image.load("assets/Dungeon_brick_wall_grey.png.png").convert_alpha()
        self.wall_image = pygame.transform.scale(self.wall_image, (CELL_SIZE, CELL_SIZE))
        self.background = StarryBackground()
        self.pellet_image = pygame.image.load("assets/rubber_duck.png").convert_alpha()
        self.pellet_image = pygame.transform.scale(self.pellet_image, (32, 32))
        self.power_pellet_image = pygame.image.load("assets/rubber_ducktopus.png").convert_alpha()
        self.power_pellet_image = pygame.transform.scale(self.power_pellet_image, (32, 32))
        self.initial_pellets_set = set()  # Mới
        self.initial_power_pellets_set = set()

        # Animation variables
        self.animation_timer = 0
        self.pellet_bob_offset = 0
        self.pellet_rotation = 0
        self.power_pellet_scale = 1.0
        self.power_pellet_glow_alpha = 0
        self.power_pellet_glow_direction = 1

        self._initialize_collectibles()

    def _initialize_collectibles(self):
        for y in range(self.height):
            for x in range(self.width):
                if self.layout[y][x] == 1:  # small food
                    self.pellets.add((x, y))
                elif self.layout[y][x] == 2:  # big food
                    self.power_pellets.add((x, y))

        self.total_pellets = len(self.pellets) + len(self.power_pellets)
        self.initial_pellets_set = set(self.pellets)  # Mới
        self.initial_power_pellets_set = set(self.power_pellets)

    def update_animations(self):
        self.animation_timer += 1

        self.pellet_bob_offset = math.sin(self.animation_timer * 0.08) * 3

        self.pellet_rotation = math.sin(self.animation_timer * 0.05)

        self.power_pellet_scale = 1.0 + math.sin(self.animation_timer * 0.15) * 0.2

        self.power_pellet_glow_alpha += self.power_pellet_glow_direction * 5
        if self.power_pellet_glow_alpha >= 100:
            self.power_pellet_glow_alpha = 100
            self.power_pellet_glow_direction = -1
        elif self.power_pellet_glow_alpha <= 20:
            self.power_pellet_glow_alpha = 20
            self.power_pellet_glow_direction = 1

    def _rotate_image(self, image, angle):
        rotated_image = pygame.transform.rotate(image, angle)
        return rotated_image

    def _scale_image(self, image, scale):
        new_width = int(image.get_width() * scale)
        new_height = int(image.get_height() * scale)
        scaled_image = pygame.transform.scale(image, (new_width, new_height))
        return scaled_image

    def _draw_glow_effect(self, screen, x, y, size, color, alpha):
        glow_surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        glow_color = (*color, alpha)
        pygame.draw.circle(glow_surface, glow_color, (size, size), size)
        screen.blit(glow_surface, (x - size, y - size))

    def _flip_image(self, image, flip_factor):
        # Scale the image horizontally - negative values flip it
        scaled_width = int(image.get_width() * abs(flip_factor))
        scaled_height = image.get_height()

        # Flip horizontally if flip_factor is negative
        if flip_factor < 0:
            return pygame.transform.flip(image, True, False)
        else:
            return image

    def is_wall(self, x, y):
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return True
        # Walls are types 3, 4, 5, 6, 7, 8
        return self.layout[y][x] in [3]

    def is_valid_position(self, x, y):
        return not self.is_wall(x, y)

    def grid_to_pixel(self, grid_x, grid_y):
        pixel_x = grid_x * CELL_SIZE
        pixel_y = grid_y * CELL_SIZE
        return pixel_x, pixel_y

    def pixel_to_grid(self, pixel_x, pixel_y):
        grid_x = pixel_x // CELL_SIZE
        grid_y = pixel_y // CELL_SIZE
        return grid_x, grid_y

    def collect_pellet(self, x, y):
        if (x, y) in self.pellets:
            self.pellets.remove((x, y))
            return PELLET_POINTS
        elif (x, y) in self.power_pellets:
            self.power_pellets.remove((x, y))
            return POWER_PELLET_POINTS
        return 0

    def is_pellet(self, x, y):
        return (x, y) in self.pellets or (x, y) in self.power_pellets

    def all_pellets_collected(self):
        return len(self.pellets) == 0 and len(self.power_pellets) == 0

    def get_neighbors(self, x, y):
        neighbors = []
        for direction, (dx, dy) in DIRECTIONS.items():
            new_x, new_y = x + dx, y + dy
            if self.is_valid_position(new_x, new_y):
                neighbors.append((new_x, new_y, direction))
        return neighbors

    def get_unexplored_positions(self, current_x, current_y):
        unexplored = []
        for y in range(self.height):
            for x in range(self.width):
                if (
                    self.is_valid_position(x, y)
                    and (x, y) not in self.pellets
                    and (x, y) not in self.power_pellets
                    and (x, y) != (current_x, current_y)
                ):
                    unexplored.append((x, y))
        return unexplored

    def render(self, screen):
        self.update_animations()

        # Render the maze background
        self.background.update()
        self.background.render(screen)

        # Render the maze layout
        for y in range(self.height):
            for x in range(self.width):
                cell_type = self.layout[y][x]
                pixel_x, pixel_y = self.grid_to_pixel(x, y)

                if cell_type == 3:
                    # Cell size wall
                    screen.blit(self.wall_image, (pixel_x, pixel_y))

        # Render pellets
        for px, py in self.pellets:
            pixel_x, pixel_y = self.grid_to_pixel(px, py)
            center_x = pixel_x + CELL_SIZE // 2
            center_y = pixel_y + CELL_SIZE // 2

            # Apply bobbing animation
            animated_y = center_y + self.pellet_bob_offset

            # Apply flipping animation instead of rotation
            flipped_pellet = self._flip_image(self.pellet_image, self.pellet_rotation)

            # Center the flipped image
            flipped_rect = flipped_pellet.get_rect(center=(center_x, animated_y))
            screen.blit(flipped_pellet, flipped_rect)

        for px, py in self.power_pellets:
            pixel_x, pixel_y = self.grid_to_pixel(px, py)
            center_x = pixel_x + CELL_SIZE // 2
            center_y = pixel_y + CELL_SIZE // 2

            # Draw glow effect first (behind the pellet)
            self._draw_glow_effect(screen, center_x, center_y, 25, (55, 255, 255), self.power_pellet_glow_alpha)

            # Apply scaling animation
            scaled_power_pellet = self._scale_image(self.power_pellet_image, self.power_pellet_scale)

            # Center the scaled image
            scaled_rect = scaled_power_pellet.get_rect(center=(center_x, center_y))
            screen.blit(scaled_power_pellet, scaled_rect)

    def get_remaining_food_count(self):
        return len(self.pellets) + len(self.power_pellets)

    def is_corner(self, x, y):
        # Check if the position is a corner based on the layout
        if (x, y) in [(0, 0), (self.width - 1, 0), (0, self.height - 1), (self.width - 1, self.height - 1)]:
            return True
        return False
