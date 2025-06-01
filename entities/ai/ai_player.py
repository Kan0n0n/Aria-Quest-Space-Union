import pygame
import random
import math
from constants import *
from entities.player_base import PlayerBase
from entities.ai.ai_state import AIState
from entities.ai.behaviors.behavior_manager import BehaviorManager
from entities.ai.pathfinding import PathfindingManager
from entities.ai.decision_making import DecisionMaker


class AIPlayer(PlayerBase):
    def __init__(self, player_id, start_x, start_y, sprite_manager, ai_type="simple_bfs"):
        super().__init__(player_id, start_x, start_y, sprite_manager)

        # Core AI components
        self.ai_state = AIState(ai_type, start_x, start_y)
        self.pathfinding = PathfindingManager(self)
        self.decision_maker = DecisionMaker(self)
        self.behavior_manager = BehaviorManager(self)

        # Movement properties
        self.direction = "LEFT"
        self.next_direction = "LEFT"
        self.speed = AI_SPEED if 'AI_SPEED' in globals() else PLAYER_SPEED

        self.total_moves_made = 0

    def update(self, maze, player_position=None, ghosts_positions=None):
        # Use base class methods
        self.update_invincibility()
        self.update_animation()

        # Update AI state
        self.ai_state.update()

        # Handle power-up timer
        if self.power_timer > 0:
            self.power_timer -= 1

        # Check for stuck condition
        current_pos = (self.grid_x, self.grid_y)
        if current_pos != self.ai_state.last_position:
            self.ai_state.add_recent_position(self.ai_state.last_position)
            self.ai_state.last_position = current_pos
            self.ai_state.stuck_counter = 0
        else:
            self.ai_state.stuck_counter += 1

        # Handle being stuck
        if self.ai_state.stuck_counter > 30:
            self._handle_stuck_situation(maze)

        # Make decisions periodically
        if self.ai_state.decision_timer >= 8:
            situation = self.decision_maker.analyze_situation(maze, player_position, ghosts_positions)
            self.behavior_manager.execute_behavior(maze, situation)
            self.ai_state.decision_timer = 0

        # Handle movement
        self._handle_movement(maze)

    def _handle_stuck_situation(self, maze):
        """Handle when AI is stuck"""
        valid_directions = []
        for direction, (dx, dy) in DIRECTIONS.items():
            new_x = self.grid_x + dx
            new_y = self.grid_y + dy
            if maze.is_valid_position(new_x, new_y):
                valid_directions.append(direction)

        if valid_directions:
            self.next_direction = random.choice(valid_directions)
            self.ai_state.stuck_counter = 0

    def _handle_movement(self, maze):
        """Handle the actual movement logic"""
        # Allow direction changes early in movement
        if self.movement_progress <= 0.3:
            dx, dy = DIRECTIONS[self.next_direction]
            new_x = self.grid_x + dx
            new_y = self.grid_y + dy
            if maze.is_valid_position(new_x, new_y):
                self.direction = self.next_direction

        # Move in current direction
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
                self.total_moves_made += 1

                if maze.is_corner(self.grid_x, self.grid_y):
                    self.ai_state.add_corner_been_through((self.grid_x, self.grid_y))

                # Collect pellets
                points = maze.collect_pellet(self.grid_x, self.grid_y)
                if points > 0:
                    if points == POWER_PELLET_POINTS:
                        self.is_invincible = True
                        self.invincibility_timer = self.invincibility_duration
                        self.invincibility_blink_timer = 0.0
                        self.power_timer = self.power_up_duration
                    else:
                        self.invincibility_blink_timer = 0.0
                    self.ai_state.pellet_eaten((self.grid_x, self.grid_y))
                self.score += points
        else:
            self.moving = False
            self.movement_progress = 0.0

        # Update pixel position
        self._update_pixel_position()

    def render(self, screen, debug=False):
        """Render the AI player with debug info if needed"""
        if self.is_dead():
            return

        # Render debug path if available
        if debug and hasattr(self.ai_state, 'path') and self.ai_state.path:
            path_points = []
            for x, y in self.ai_state.path:
                path_points.append((x * CELL_SIZE + CELL_SIZE // 2, y * CELL_SIZE + CELL_SIZE // 2))

            if len(path_points) > 1:
                pygame.draw.lines(screen, (0, 255, 0), False, path_points, 2)

        # Get sprite and render
        sprite = self.sprite_manager.get_sprite(self.player_id, self.direction.lower())
        should_render = True

        if self.is_invincible and self.power_timer <= 0:
            self.invincibility_blink_timer += 1
            if (self.invincibility_blink_timer // 10) % 2 == 0:
                should_render = False

        if should_render:
            if sprite:
                render_y = self.pixel_y + self.bob_offset

                if debug:
                    # Draw debug grid position
                    pygame.draw.rect(screen, (255, 0, 0), (self.pixel_x, render_y, CELL_SIZE, CELL_SIZE), 1)
                    # Draw debug pixel position
                    pygame.draw.circle(screen, (0, 0, 255), (int(self.pixel_x + CELL_SIZE // 2), int(self.pixel_y + CELL_SIZE // 2)), 3)
                    # Draw Algorithm name and Power Timer above the player
                    font = pygame.font.Font(None, 24)
                    algorithm_text = font.render(f"AI: {self.get_current_algorithm()}", True, (255, 255, 255))
                    power_text = font.render(f"Power: {self.power_timer}", True, (255, 255, 0))
                    screen.blit(algorithm_text, (self.pixel_x, render_y - 20))
                    screen.blit(power_text, (self.pixel_x, render_y - 40))

                # Add power mode visual effect
                if self.power_timer > 0:
                    glow_surface = pygame.Surface((CELL_SIZE + 4, CELL_SIZE + 4))
                    glow_surface.set_alpha(100)
                    glow_color = YELLOW if self.power_timer > 60 else RED
                    pygame.draw.circle(glow_surface, glow_color, (CELL_SIZE // 2 + 2, CELL_SIZE // 2 + 2), CELL_SIZE // 2 + 2)
                    screen.blit(glow_surface, (self.pixel_x - 2, render_y - 2))

                screen.blit(sprite, (self.pixel_x, render_y))
            else:
                color = GREEN if self.player_id == "ai1" else ORANGE
                if self.is_invincible:
                    color = tuple(min(255, c + 100) for c in color)
                pygame.draw.circle(screen, color, (int(self.pixel_x + CELL_SIZE // 2), int(self.pixel_y + CELL_SIZE // 2)), CELL_SIZE // 2 - 2)

    def change_algorithm(self, new_algorithm):
        if new_algorithm in self.behavior_manager.behaviors:
            self.ai_state.ai_type = new_algorithm
            print(f"AI Player {self.player_id} algorithm changed to: {new_algorithm}")
        else:
            available_algorithms = list(self.behavior_manager.behaviors.keys())
            print(f"Invalid algorithm: {new_algorithm}")
            print(f"Available algorithms: {available_algorithms}")

    def get_current_algorithm(self):
        return self.ai_state.ai_type

    def get_available_algorithms(self):
        return list(self.behavior_manager.behaviors.keys())

    def reset_position(self, x, y):
        """Reset AI player position"""
        self.grid_x = x
        self.grid_y = y
        self.pixel_x = x * CELL_SIZE
        self.pixel_y = y * CELL_SIZE
        self.movement_progress = 0.0
        self.direction = "LEFT"
        self.next_direction = "LEFT"
        self.moving = False
        if self.is_dead():
            self.health = 3
            self.is_invincible = False
            self.invincibility_timer = 0.0
            self.invincibility_blink_timer = 0.0
