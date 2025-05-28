import pygame
import random
from collections import deque
from constants import *
from entities.player_base import PlayerBase
import math


class AIPlayer(PlayerBase):
    def __init__(self, player_id, start_x, start_y, sprite_manager, ai_type="simple"):
        super().__init__(player_id, start_x, start_y, sprite_manager)
        self.direction = "LEFT"
        self.next_direction = "LEFT"
        self.speed = AI_SPEED
        self.ai_type = ai_type
        self.path = []
        self.target = None
        self.decision_timer = 0

    def update(self, maze, player_position=None):
        # Use base class methods
        self.update_invincibility()
        self.update_animation()

        self.decision_timer += 1

        # Make decisions every few frames to avoid too frequent changes
        if self.decision_timer >= 10:
            self._make_decision(maze, player_position)
            self.decision_timer = 0

        # Check if we can change direction
        if self.movement_progress <= 0.1:
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
                # Reached next cell
                self.grid_x = target_x
                self.grid_y = target_y
                self.movement_progress = 0.0

                # Collect pellets
                points = maze.collect_pellet(self.grid_x, self.grid_y)
                self.score += points
        else:
            self.moving = False
            self.movement_progress = 0.0
            # If can't move, try a different direction
            self._find_alternative_direction(maze)

        # Update pixel position for smooth movement
        self._update_pixel_position()

    def _make_decision(self, maze, player_position=None):
        # Skip decision making if dead
        if self.is_dead():
            return

        if self.ai_type == "simple":
            self._simple_ai(maze)
        elif self.ai_type == "pellet_hunter":
            self._pellet_hunter_ai(maze)
        elif self.ai_type == "competitive":
            self._competitive_ai(maze, player_position)
        else:
            self._simple_ai(maze)

    def _simple_ai(self, maze):
        # Get valid directions
        valid_directions = []
        for direction, (dx, dy) in DIRECTIONS.items():
            new_x = self.grid_x + dx
            new_y = self.grid_y + dy
            if maze.is_valid_position(new_x, new_y):
                valid_directions.append(direction)

        if valid_directions:
            # Prefer continuing in the same direction if possible
            if self.direction in valid_directions and random.random() < 0.7:
                self.next_direction = self.direction
            else:
                self.next_direction = random.choice(valid_directions)

    def _pellet_hunter_ai(self, maze):
        # Find nearest pellet
        nearest_pellet = self._find_nearest_pellet(maze)
        if nearest_pellet:
            path = self._find_path_to_target(maze, nearest_pellet)
            if path and len(path) > 1:
                next_pos = path[1]  # First step in path
                self._set_direction_to_position(next_pos)
            else:
                self._simple_ai(maze)  # Fallback
        else:
            self._simple_ai(maze)  # No pellets left

    def _competitive_ai(self, maze, player_position):
        if player_position:
            # If close to player, try to move away or compete for pellets
            distance = abs(self.grid_x - player_position[0]) + abs(self.grid_y - player_position[1])
            if distance < 5:
                # Move away from player
                self._move_away_from_position(maze, player_position)
            else:
                # Hunt pellets normally
                self._pellet_hunter_ai(maze)
        else:
            self._pellet_hunter_ai(maze)

    # Find the nearest pellet (regular or power) based on Manhattan distance
    def _find_nearest_pellet(self, maze):
        nearest = None
        min_distance = float("inf")

        # Check regular pellets
        for pellet_pos in maze.pellets:
            distance = abs(self.grid_x - pellet_pos[0]) + abs(self.grid_y - pellet_pos[1])
            if distance < min_distance:
                min_distance = distance
                nearest = pellet_pos

        # Check power pellets (higher priority)
        for pellet_pos in maze.power_pellets:
            distance = abs(self.grid_x - pellet_pos[0]) + abs(self.grid_y - pellet_pos[1])
            if distance < min_distance * 1.5:  # Give power pellets priority
                min_distance = distance
                nearest = pellet_pos

        return nearest

    # Find a path to the target position using BFS
    def _find_path_to_target(self, maze, target):
        start = (self.grid_x, self.grid_y)
        if start == target:
            return [start]

        queue = deque([(start, [start])])
        visited = {start}

        while queue:
            (x, y), path = queue.popleft()

            for new_x, new_y, direction in maze.get_neighbors(x, y):
                if (new_x, new_y) == target:
                    return path + [(new_x, new_y)]

                if (new_x, new_y) not in visited:
                    visited.add((new_x, new_y))
                    queue.append(((new_x, new_y), path + [(new_x, new_y)]))

        return []  # No path found

    def _set_direction_to_position(self, target_pos):
        dx = target_pos[0] - self.grid_x
        dy = target_pos[1] - self.grid_y

        if dx > 0:
            self.next_direction = "RIGHT"
        elif dx < 0:
            self.next_direction = "LEFT"
        elif dy > 0:
            self.next_direction = "DOWN"
        elif dy < 0:
            self.next_direction = "UP"

    def _move_away_from_position(self, maze, position):
        # Calculate opposite direction
        dx = self.grid_x - position[0]
        dy = self.grid_y - position[1]

        # Prefer moving in the direction that increases distance
        preferred_directions = []
        if dx > 0:
            preferred_directions.append("RIGHT")
        elif dx < 0:
            preferred_directions.append("LEFT")

        if dy > 0:
            preferred_directions.append("DOWN")
        elif dy < 0:
            preferred_directions.append("UP")

        # Try preferred directions
        for direction in preferred_directions:
            dx, dy = DIRECTIONS[direction]
            new_x = self.grid_x + dx
            new_y = self.grid_y + dy
            if maze.is_valid_position(new_x, new_y):
                self.next_direction = direction
                return

        # Fallback to simple AI
        self._simple_ai(maze)

    def _find_alternative_direction(self, maze):
        valid_directions = []
        for direction, (dx, dy) in DIRECTIONS.items():
            new_x = self.grid_x + dx
            new_y = self.grid_y + dy
            if maze.is_valid_position(new_x, new_y):
                valid_directions.append(direction)

        if valid_directions:
            # Prefer any direction except the opposite of current
            opposite = {"UP": "DOWN", "DOWN": "UP", "LEFT": "RIGHT", "RIGHT": "LEFT"}
            preferred = [d for d in valid_directions if d != opposite.get(self.direction)]
            if preferred:
                self.next_direction = random.choice(preferred)
            else:
                self.next_direction = random.choice(valid_directions)

    def render(self, screen):
        if self.is_dead():
            return

        sprite = self.sprite_manager.get_sprite(self.player_id, self.direction.lower())

        # Handle blinking effect during invincibility
        should_render = True
        if self.is_invincible:
            # Blink every 10 frames (6 times per second at 60 FPS)
            should_render = (self.invincibility_blink_timer // 10) % 2 == 0

        if should_render:
            if sprite:
                render_y = self.pixel_y + self.bob_offset
                screen.blit(sprite, (self.pixel_x, render_y))
            else:
                # Fallback rendering with invincibility effect
                color = GREEN if self.player_id == "ai1" else ORANGE
                if self.is_invincible:
                    # Make color lighter during invincibility
                    color = tuple(min(255, c + 100) for c in color)
                pygame.draw.circle(screen, color, (int(self.pixel_x + CELL_SIZE // 2), int(self.pixel_y + CELL_SIZE // 2)), CELL_SIZE // 2 - 2)