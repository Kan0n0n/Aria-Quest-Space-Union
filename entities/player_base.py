import pygame
import math
from constants import *


class PlayerBase:
    def __init__(self, player_id, start_x, start_y, sprite_manager):
        self.player_id = player_id
        self.grid_x = start_x
        self.grid_y = start_y
        self.pixel_x = start_x * CELL_SIZE
        self.pixel_y = start_y * CELL_SIZE
        self.sprite_manager = sprite_manager
        self.score = 0
        self.moving = False
        self.movement_progress = 0.0

        # Health system
        self.health = 3
        self.is_invincible = False
        self.invincibility_timer = 0.0
        self.invincibility_duration = 180
        self.invincibility_blink_timer = 0.0

        self.power_timer = 0.0
        self.power_up_duration = 1000

        # animations
        self.animation_timer = 0.0
        self.bob_offset = 0.0

    def take_damage(self):
        if not self.is_invincible and self.health > 0:
            self.health -= 1
            if self.health > 0:
                self.is_invincible = True
                self.invincibility_timer = self.invincibility_duration
                self.invincibility_blink_timer = 0.0
            return True
        return False

    def is_powered_up(self):
        return self.power_timer > 0

    def is_dead(self):
        return self.health <= 0

    def check_collision_with_ghost(self, ghost_position):
        if not ghost_position:
            return False
        ghost_x, ghost_y = ghost_position
        distance = math.sqrt((self.grid_x - ghost_x) ** 2 + (self.grid_y - ghost_y) ** 2)
        if distance <= 0.8:
            return self.take_damage()
        return False

    def update_invincibility(self):
        if self.is_invincible:
            self.invincibility_timer -= 1
            self.invincibility_blink_timer += 1
            if self.invincibility_timer <= 0:
                self.is_invincible = False
                self.invincibility_timer = 0
                self.invincibility_blink_timer = 0

    def update_animation(self):
        if self.moving:
            self.animation_timer += 0.5
            self.bob_offset = math.sin(self.animation_timer) * 4
        else:
            self.bob_offset = 0.0

    def render_health_bar(self, screen, x, y, _heart_size=20, _heart_spacing=3):
        heart_size = _heart_size
        heart_spacing = _heart_spacing

        for i in range(3):
            heart_x = x + (i * heart_spacing)
            heart_y = y

            if i < self.health:
                color = (255, 0, 0)  # Red for health
            else:
                color = (100, 100, 100)

            # Draw heart shape
            pygame.draw.circle(screen, color, (heart_x + 5, heart_y + 5), 5)
            pygame.draw.circle(screen, color, (heart_x + 15, heart_y + 5), 5)
            pygame.draw.rect(screen, color, (heart_x, heart_y + 5, 20, 15))
            points = [(heart_x + 10, heart_y + 25), (heart_x, heart_y + 15), (heart_x + 20, heart_y + 15)]
            pygame.draw.polygon(screen, color, points)

    def get_position(self):
        return self.grid_x, self.grid_y

    def get_pixel_position(self):
        return self.pixel_x, self.pixel_y

    def _update_pixel_position(self):
        base_x = self.grid_x * CELL_SIZE
        base_y = self.grid_y * CELL_SIZE
        if self.moving:
            dx, dy = DIRECTIONS[self.direction]
            offset_x = dx * CELL_SIZE * self.movement_progress
            offset_y = dy * CELL_SIZE * self.movement_progress
            self.pixel_x = base_x + offset_x
            self.pixel_y = base_y + offset_y
        else:
            self.pixel_x = base_x
            self.pixel_y = base_y

    def check_ghost_collision(self, ghost_position):
        if not ghost_position:
            return False

        ghost_x, ghost_y = ghost_position
        distance = ((self.grid_x - ghost_x) ** 2 + (self.grid_y - ghost_y) ** 2) ** 0.5

        if distance <= 0.8:  # Close enough for collision
            if self.power_timer > 0:
                # Player is powered up - hunt the ghost
                self.score += 200
                print(f"Player {self.player_id} caught a ghost! +200 points")
                return "caught_ghost"  # Return special value to indicate ghost was caught
            else:
                # Player is not powered up - take damage
                return self.take_damage()
        return False
