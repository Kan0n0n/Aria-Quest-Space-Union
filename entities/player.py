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

        if self.power_timer > 0:
            self.power_timer -= 1

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
                if points > 0:
                    if points == POWER_PELLET_POINTS:
                        self.is_invincible = True
                        self.invincibility_timer = self.invincibility_duration
                        self.invincibility_blink_timer = 0.0
                        self.power_timer = self.power_up_duration
                    else:
                        self.invincibility_blink_timer = 0.0
                self.score += points
        else:
            self.moving = False
            self.movement_progress = 0.0

        self._update_pixel_position()

    def render(self, screen, debug=False):
        if self.is_dead():
            return

        sprite = self.sprite_manager.get_sprite(self.player_id, self.direction.lower())
        should_render = True

        if self.is_invincible and self.power_timer <= 0:
            self.invincibility_blink_timer += 1
            if (self.invincibility_blink_timer // 10) % 2 == 0:
                should_render = False

        if should_render:
            if sprite:
                render_y = self.pixel_y + self.bob_offset

                # Add power mode visual effect
                if self.power_timer > 0:
                    # Create a glowing effect during power mode
                    glow_surface = pygame.Surface((CELL_SIZE + 4, CELL_SIZE + 4))
                    glow_surface.set_alpha(100)
                    glow_color = YELLOW if self.power_timer > 60 else RED
                    pygame.draw.circle(glow_surface, glow_color, (CELL_SIZE // 2 + 2, CELL_SIZE // 2 + 2), CELL_SIZE // 2 + 2)
                    screen.blit(glow_surface, (self.pixel_x - 2, render_y - 2))

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

    def reset_position_with_score(self, x, y, score):
        self.reset_position(x, y)
        self.score = score
