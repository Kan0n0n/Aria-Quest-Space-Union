import pygame
from constants import *
from entities.player_base import PlayerBase


class Player(PlayerBase):
    def __init__(self, player_id, start_x, start_y, key_mapping, sprite_manager):
        super().__init__(player_id, start_x, start_y, sprite_manager)
        self.direction = "RIGHT"
        self.next_direction = "RIGHT"
        self.speed = PLAYER_SPEED
        self.key_mapping = key_mapping

    def handle_input(self, keys):
        for key, direction in self.key_mapping.items():
            if keys[key]:
                self.next_direction = direction
                break

    def update(self, maze):
        self.update_invincibility()
        self.update_animation()

        if self.movement_progress <= 0.1:
            dx, dy = DIRECTIONS[self.next_direction]
            new_x = self.grid_x + dx
            new_y = self.grid_y + dy
            if maze.is_valid_position(new_x, new_y):
                self.direction = self.next_direction

        dx, dy = DIRECTIONS[self.direction]
        target_x = self.grid_x + dx
        target_y = self.grid_y + dy

        if maze.is_valid_position(target_x, target_y):
            self.moving = True
            self.movement_progress += self.speed / CELL_SIZE
            if self.movement_progress >= 1.0:
                self.grid_x = target_x
                self.grid_y = target_y
                self.movement_progress = 0.0
                points = maze.collect_pellet(self.grid_x, self.grid_y)
                self.score += points
        else:
            self.moving = False
            self.movement_progress = 0.0

        self._update_pixel_position()

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

    def render(self, screen):
        if self.is_dead():
            return

        sprite = self.sprite_manager.get_sprite(self.player_id, self.direction.lower())
        should_render = True
        if self.is_invincible:
            should_render = (self.invincibility_blink_timer // 10) % 2 == 0

        if should_render:
            if sprite:
                render_y = self.pixel_y + self.bob_offset
                screen.blit(sprite, (self.pixel_x, render_y))
            else:
                color = YELLOW if self.player_id == "player1" else RED
                if self.is_invincible:
                    color = tuple(min(255, c + 100) for c in color)
                pygame.draw.circle(screen, color, (int(self.pixel_x + CELL_SIZE // 2), int(self.pixel_y + CELL_SIZE // 2)), CELL_SIZE // 2 - 2)

    def reset_position(self, x, y):
        self.grid_x = x
        self.grid_y = y
        self.pixel_x = x * CELL_SIZE
        self.pixel_y = y * CELL_SIZE
        self.direction = "RIGHT"
        self.next_direction = "RIGHT"
        self.moving = False
        self.movement_progress = 0.0
        if self.is_dead():
            self.health = 3
            self.is_invincible = False
            self.invincibility_timer = 0.0
            self.invincibility_blink_timer = 0.0
