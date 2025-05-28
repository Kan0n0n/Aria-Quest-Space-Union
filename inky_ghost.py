from constants import *
from maze_layout import POSITIONS  # Import positions from maze layout
import pygame
import math
import random
import heapq


class InkyGhost:
    def __init__(self, player_id, start_x, start_y, sprite_manager):
        self.grid_x = start_x
        self.grid_y = start_y
        self.pixel_x = start_x * CELL_SIZE
        self.pixel_y = start_y * CELL_SIZE
        self.direction = "LEFT"
        self.next_direction = "LEFT"
        self.speed = GHOST_SPEED
        self.base_speed = GHOST_SPEED  # Store original speed
        self.sprite_manager = sprite_manager
        self.moving = False
        self.movement_progress = 0.0
        self.target = None
        self.player_id = player_id
        self.can_chase = True

        # Animation properties
        self.animation_timer = 0
        self.bob_offset = 0

        # A* pathfinding
        self.path = []
        self.current_path_index = 0

        # Grid-based movement history for visual trail
        self.movement_history = []
        self.stuck_counter = 0

        # Random movement after catching player
        self.random_mode = False
        self.random_timer = 0
        self.random_duration = 180  # 3 seconds at 60 FPS

        # Catch detection
        self.catch_distance = 0.8  # How close to consider a "catch"

        # Enhanced AI behaviors with food percentage tracking
        self.ai_mode = "CHASE"  # CHASE, SCATTER, or ENRAGED
        self.mode_timer = 0
        self.behavior_switch_interval = 600  # 10 seconds at 60 FPS

        # Food tracking for enraged mode
        self.total_food_count = 0  # Will be set by maze
        self.is_enraged = False  # Triggered when 80% food eaten
        self.enraged_speed_multiplier = 1.6  # 60% speed increase when enraged

        # Improved scatter behavior using maze layout positions
        self.scatter_points = self._get_scatter_points_from_maze()
        self.current_scatter_index = 0
        self.scatter_direction = 1  # 1 for forward, -1 for backward

        print(f"Inky Ghost initialized with {len(self.scatter_points)} scatter points from maze layout")

    def _get_scatter_points_from_maze(self):
        try:
            scatter_points = POSITIONS.get('INKY_SCATTER_POINTS', [])
            if scatter_points:
                print(f"Loaded {len(scatter_points)} scatter points from maze layout: {scatter_points}")
                return scatter_points
            else:
                print("No scatter points found in maze layout, using fallback")
                return self._create_fallback_scatter_points()
        except Exception as e:
            print(f"Error loading scatter points from maze: {e}")
            return self._create_fallback_scatter_points()

    def _create_fallback_scatter_points(self):
        """Create fallback scatter points if maze layout doesn't have them"""
        # Simple corner-based scatter pattern
        return [(1, 1), (17, 1), (17, 9), (1, 9)]  # Top-left  # Top-right  # Bottom-right  # Bottom-left

    def set_total_food_count(self, total_count):
        """Set the total food count from maze initialization"""
        self.total_food_count = total_count

    def check_food_percentage(self, maze):
        """Check if 80% of food has been eaten and trigger enraged mode"""
        if self.total_food_count == 0:
            return

        current_food = len(maze.pellets) + len(maze.power_pellets)
        eaten_percentage = (self.total_food_count - current_food) / self.total_food_count

        if eaten_percentage >= 0.8 and not self.is_enraged:
            # Trigger enraged mode
            self.is_enraged = True
            self.ai_mode = "ENRAGED"
            self.speed = self.base_speed * self.enraged_speed_multiplier
            print(f"Ghost is now ENRAGED! Speed increased to {self.speed:.2f}")
            print(f"Food eaten: {eaten_percentage * 100:.1f}%")

    def heuristic(self, a, b):
        """Manhattan distance heuristic for A*"""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def get_neighbors(self, maze, pos):
        """Get valid neighboring positions"""
        neighbors = []
        x, y = pos
        for direction in ["UP", "DOWN", "LEFT", "RIGHT"]:
            dx, dy = DIRECTIONS[direction]
            new_x, new_y = x + dx, y + dy
            if maze.is_valid_position(new_x, new_y):
                neighbors.append((new_x, new_y))
        return neighbors

    def a_star_pathfinding(self, maze, start, goal):
        """A* pathfinding algorithm"""
        if not goal or start == goal:
            return []

        # Priority queue: (f_score, g_score, position, path)
        open_set = [(0, 0, start, [])]
        closed_set = set()

        while open_set:
            f_score, g_score, current, path = heapq.heappop(open_set)

            if current in closed_set:
                continue

            closed_set.add(current)
            new_path = path + [current]

            # Found goal
            if current == goal:
                return new_path[1:]  # Exclude starting position

            # Explore neighbors
            for neighbor in self.get_neighbors(maze, current):
                if neighbor in closed_set:
                    continue

                new_g_score = g_score + 1
                h_score = self.heuristic(neighbor, goal)
                new_f_score = new_g_score + h_score

                heapq.heappush(open_set, (new_f_score, new_g_score, neighbor, new_path))

        return []  # No path found

    def check_player_catch(self, player_positions):
        """Check if ghost caught any player"""
        ghost_pos = (self.grid_x, self.grid_y)

        for player_pos in player_positions:
            if player_pos:
                player_x, player_y = player_pos
                distance = math.sqrt((ghost_pos[0] - player_x) ** 2 + (ghost_pos[1] - player_y) ** 2)

                if distance <= self.catch_distance:
                    # Player caught! Enter random mode
                    self.random_mode = True
                    self.random_timer = self.random_duration
                    self.path = []  # Clear current path
                    print(f"Ghost caught player at {player_pos}! Entering random mode.")
                    return True
        return False

    def update_random_mode(self, maze):
        """Handle random movement mode"""
        if self.random_timer > 0:
            self.random_timer -= 1

            # Change direction randomly every 30 frames (0.5 seconds)
            if self.random_timer % 30 == 0:
                valid_directions = []
                for direction in ["UP", "DOWN", "LEFT", "RIGHT"]:
                    dx, dy = DIRECTIONS[direction]
                    new_x = self.grid_x + dx
                    new_y = self.grid_y + dy
                    if maze.is_valid_position(new_x, new_y):
                        valid_directions.append(direction)

                if valid_directions:
                    self.next_direction = random.choice(valid_directions)
        else:
            # Exit random mode
            self.random_mode = False
            print("Ghost exiting random mode, resuming AI behavior.")

    def update_ai_mode(self):
        """Switch between CHASE and SCATTER modes (unless enraged)"""
        # Don't switch modes if enraged - stay in ENRAGED mode
        if self.is_enraged:
            self.ai_mode = "ENRAGED"
            return

        self.mode_timer += 1

        if self.mode_timer >= self.behavior_switch_interval:
            # Switch modes
            if self.ai_mode == "CHASE":
                self.ai_mode = "SCATTER"
                print(f"Ghost switching to SCATTER mode - targeting point {self.current_scatter_index}")
            else:
                self.ai_mode = "CHASE"
                print("Ghost switching to CHASE mode")

            self.mode_timer = 0
            self.path = []  # Clear current path when switching modes

    def get_closest_player(self, player_a_pos, player_b_pos):
        """Get position of closest player"""
        if player_a_pos and player_b_pos:
            dist_a = abs(self.grid_x - player_a_pos[0]) + abs(self.grid_y - player_a_pos[1])
            dist_b = abs(self.grid_x - player_b_pos[0]) + abs(self.grid_y - player_b_pos[1])
            return player_a_pos if dist_a < dist_b else player_b_pos
        return player_a_pos or player_b_pos

    def get_scatter_target(self, maze):
        """Get next target from maze-defined scatter points"""
        if not self.scatter_points:
            return (self.grid_x, self.grid_y)

        # Get current target
        target = self.scatter_points[self.current_scatter_index]
        target_x, target_y = target

        # Check if we've reached the current target (within 1 cell)
        current_distance = self.heuristic((self.grid_x, self.grid_y), target)
        if current_distance <= 1:
            # Move to next scatter point
            self.current_scatter_index += self.scatter_direction

            # Check if we need to reverse direction (ping-pong behavior)
            if self.current_scatter_index >= len(self.scatter_points):
                self.current_scatter_index = len(self.scatter_points) - 2
                self.scatter_direction = -1
                print("Ghost reached end of scatter points, reversing direction")
            elif self.current_scatter_index < 0:
                self.current_scatter_index = 1
                self.scatter_direction = 1
                print("Ghost reached start of scatter points, moving forward")

            # Get new target
            if 0 <= self.current_scatter_index < len(self.scatter_points):
                target = self.scatter_points[self.current_scatter_index]
                target_x, target_y = target
                print(f"Ghost new scatter target: {target}")

        # Validate target position
        if maze.is_valid_position(target_x, target_y):
            return target
        else:
            # Find nearest valid position to target
            print(f"Invalid scatter target {target}, finding nearest valid position")
            for radius in range(1, 4):
                for dx in range(-radius, radius + 1):
                    for dy in range(-radius, radius + 1):
                        test_x, test_y = target_x + dx, target_y + dy
                        if maze.is_valid_position(test_x, test_y):
                            print(f"Found valid position {(test_x, test_y)} near target {target}")
                            return (test_x, test_y)

            # Fallback to current position
            print(f"No valid position found near {target}, staying at current position")
            return (self.grid_x, self.grid_y)

    def moving_algorithm(self, maze, player_a_position, player_b_position):
        """Main movement algorithm - CHASE, SCATTER, or ENRAGED mode"""
        if self.random_mode:
            return

        # Check food percentage to trigger enraged mode
        self.check_food_percentage(maze)

        # Update AI mode timer (unless enraged)
        self.update_ai_mode()

        target = None

        if self.ai_mode in ["CHASE", "ENRAGED"]:
            # Chase closest player (more aggressively in enraged mode)
            target = self.get_closest_player(player_a_position, player_b_position)
            if target and self.ai_mode == "CHASE":
                print(f"Ghost chasing player at {target}")
        elif self.ai_mode == "SCATTER":
            # Move to scatter target from maze layout
            target = self.get_scatter_target(maze)

        if target:
            # Use A* pathfinding to reach target
            target_path = self.a_star_pathfinding(maze, (self.grid_x, self.grid_y), target)

            if target_path:
                self.path = target_path
                self.current_path_index = 0

            # Follow the path
            if self.path and self.current_path_index < len(self.path):
                next_pos = self.path[self.current_path_index]
                next_x, next_y = next_pos

                # Determine direction to next position
                dx = next_x - self.grid_x
                dy = next_y - self.grid_y

                if dx > 0:
                    self.next_direction = "RIGHT"
                elif dx < 0:
                    self.next_direction = "LEFT"
                elif dy > 0:
                    self.next_direction = "DOWN"
                elif dy < 0:
                    self.next_direction = "UP"
        else:
            # No target - random movement
            valid_directions = []
            for direction in ["UP", "DOWN", "LEFT", "RIGHT"]:
                dx, dy = DIRECTIONS[direction]
                new_x = self.grid_x + dx
                new_y = self.grid_y + dy
                if maze.is_valid_position(new_x, new_y):
                    valid_directions.append(direction)

            if valid_directions:
                self.next_direction = random.choice(valid_directions)

    def update(self, maze, player_a_position=None, player_b_position=None):
        if not self.can_chase:
            return

        # Check if we caught a player
        player_positions = [pos for pos in [player_a_position, player_b_position] if pos]
        self.check_player_catch(player_positions)

        # Handle random mode
        if self.random_mode:
            self.update_random_mode(maze)
        else:
            # Use movement algorithm
            self.moving_algorithm(maze, player_a_position, player_b_position)

        # Update animation timer for bobbing effect (faster when enraged)
        animation_speed = 0.8 if self.is_enraged else 0.5
        if self.moving:
            self.animation_timer += animation_speed
            self.bob_offset = math.sin(self.animation_timer) * (6 if self.is_enraged else 4)
        else:
            self.animation_timer = 0
            self.bob_offset = 0

        # Check if we can change direction
        if self.movement_progress <= 0.2:
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
            self.stuck_counter = 0

            if self.movement_progress >= 1.0:
                # Reached next cell
                old_pos = (self.grid_x, self.grid_y)
                self.grid_x = target_x
                self.grid_y = target_y
                self.movement_progress = 0.0

                # Update path index if following A* path
                if not self.random_mode and self.path and self.current_path_index < len(self.path):
                    if (self.grid_x, self.grid_y) == self.path[self.current_path_index]:
                        self.current_path_index += 1

                # Add to movement history for grid-based trail
                self.movement_history.append(old_pos)
                max_history = 12 if self.is_enraged else 8  # Longer trail when enraged
                if len(self.movement_history) > max_history:
                    self.movement_history.pop(0)
        else:
            # Can't move in current direction
            self.moving = False
            self.movement_progress = 0.0
            self.stuck_counter += 1

            # Clear path if stuck (will recalculate)
            if self.stuck_counter > 5:
                self.path = []
                self.stuck_counter = 0

        # Update pixel position for smooth movement
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

    def render(self, screen, maze=None, debug_mode=False):
        # Draw A* path (blue line) if debug mode
        if debug_mode and self.path and not self.random_mode:
            path_points = []
            # Add current position
            path_points.append((self.grid_x * CELL_SIZE + CELL_SIZE // 2, self.grid_y * CELL_SIZE + CELL_SIZE // 2))

            # Add remaining path points
            for i in range(self.current_path_index, len(self.path)):
                x, y = self.path[i]
                path_points.append((x * CELL_SIZE + CELL_SIZE // 2, y * CELL_SIZE + CELL_SIZE // 2))

            if len(path_points) > 1:
                line_color = (255, 0, 255) if self.is_enraged else (0, 150, 255)  # Purple if enraged
                line_width = 4 if self.is_enraged else 3
                pygame.draw.lines(screen, line_color, False, path_points, line_width)

        # Draw scatter points and path in scatter mode (green) if debug mode
        if debug_mode and self.ai_mode == "SCATTER" and not self.random_mode and self.scatter_points:
            # Draw all scatter points
            for i, (px, py) in enumerate(self.scatter_points):
                point = (px * CELL_SIZE + CELL_SIZE // 2, py * CELL_SIZE + CELL_SIZE // 2)

                # Highlight current target
                color = (255, 255, 0) if i == self.current_scatter_index else (100, 255, 100)
                radius = 12 if i == self.current_scatter_index else 8
                pygame.draw.circle(screen, color, point, radius)

                # Draw index number
                font = pygame.font.Font(None, 20)
                text = font.render(str(i), True, (0, 0, 0))
                text_rect = text.get_rect(center=point)
                screen.blit(text, text_rect)

            # Draw path between scatter points
            if len(self.scatter_points) > 1:
                scatter_path_points = []
                for px, py in self.scatter_points:
                    scatter_path_points.append((px * CELL_SIZE + CELL_SIZE // 2, py * CELL_SIZE + CELL_SIZE // 2))
                pygame.draw.lines(screen, (0, 255, 0), False, scatter_path_points, 2)

        # Draw grid-based movement history (red squares) if debug mode
        if debug_mode and self.movement_history:
            for i, (hist_x, hist_y) in enumerate(self.movement_history):
                alpha = int(100 + (155 * i / len(self.movement_history)))  # Fade effect
                base_color = (255, 100, 100) if self.is_enraged else (255, alpha // 2, alpha // 2)

                # Draw small square at grid position
                rect = pygame.Rect(hist_x * CELL_SIZE + CELL_SIZE // 4, hist_y * CELL_SIZE + CELL_SIZE // 4, CELL_SIZE // 2, CELL_SIZE // 2)
                pygame.draw.rect(screen, base_color, rect)

        # Try to get ghost sprite - use fallback sprite names
        sprite = None
        sprite_names_to_try = ["inky", "ghost", "ghost1", self.player_id]

        for sprite_name in sprite_names_to_try:
            sprite = self.sprite_manager.get_sprite(sprite_name, self.direction.lower())
            if sprite:
                break

        if sprite:
            bobbed_y = self.pixel_y + self.bob_offset

            # Add red tint when enraged
            if self.is_enraged:
                # Create a red-tinted version of the sprite
                tinted_sprite = sprite.copy()
                red_overlay = pygame.Surface(sprite.get_size())
                red_overlay.fill((255, 0, 0))
                red_overlay.set_alpha(100)  # Semi-transparent red
                tinted_sprite.blit(red_overlay, (0, 0), special_flags=pygame.BLEND_MULT)
                screen.blit(tinted_sprite, (self.pixel_x, bobbed_y))

                # Add pulsing red glow around enraged ghost
                glow_radius = int(CELL_SIZE // 2 + math.sin(self.animation_timer * 0.3) * 5)
                glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surface, (255, 0, 0, 50), (glow_radius, glow_radius), glow_radius)
                screen.blit(glow_surface, (self.pixel_x + CELL_SIZE // 2 - glow_radius, bobbed_y + CELL_SIZE // 2 - glow_radius))
            else:
                screen.blit(sprite, (self.pixel_x, bobbed_y))

            if self.random_mode:
                # Add random mode indicator
                pygame.draw.circle(screen, (255, 0, 255), (int(self.pixel_x + CELL_SIZE // 2), int(bobbed_y - 5)), 3)
        else:
            # Fallback rectangle with enhanced colors
            if self.random_mode:
                color = (255, 0, 255)  # Purple for random mode
            elif self.is_enraged:
                color = (255, 50, 50)  # Bright red for enraged mode
            elif self.ai_mode == "CHASE":
                color = (255, 0, 0)  # Red for chase mode
            else:  # SCATTER
                color = (0, 255, 255)  # Cyan for scatter mode
            pygame.draw.rect(screen, color, (self.pixel_x, self.pixel_y, CELL_SIZE, CELL_SIZE))

        # Debug info
        if debug_mode:
            font = pygame.font.Font(None, 24)
            if self.random_mode:
                mode_text = "RANDOM"
                timer_text = f"{self.random_timer // 60 + 1}s"
            else:
                mode_text = self.ai_mode
                if self.ai_mode == "SCATTER":
                    mode_text += f" ({self.current_scatter_index})"
                elif self.is_enraged:
                    mode_text += f" SPD:{self.speed:.1f}"
                timer_text = f"{(self.behavior_switch_interval - self.mode_timer) // 60 + 1}s" if not self.is_enraged else "∞"
            debug_text = f"{mode_text} {timer_text}"
            text_surface = font.render(debug_text, True, (255, 255, 255))
            screen.blit(text_surface, (self.pixel_x, self.pixel_y - 30))

    def reset_position(self, start_x, start_y):
        self.grid_x = start_x
        self.grid_y = start_y
        self.pixel_x = start_x * CELL_SIZE
        self.pixel_y = start_y * CELL_SIZE
        self.direction = "LEFT"
        self.next_direction = "LEFT"
        self.moving = False
        self.movement_progress = 0.0
        self.animation_timer = 0
        self.bob_offset = 0
        self.movement_history = []
        self.stuck_counter = 0
        self.path = []
        self.current_path_index = 0
        self.random_mode = False
        self.random_timer = 0
        self.ai_mode = "CHASE"
        self.mode_timer = 0

        # Reset enraged state
        self.is_enraged = False
        self.speed = self.base_speed

        # Reset scatter system - reload from maze layout
        self.scatter_points = self._get_scatter_points_from_maze()
        self.current_scatter_index = 0
        self.scatter_direction = 1

    def get_position(self):
        return self.grid_x, self.grid_y

    def set_target(self, target_a_pos, target_b_pos):
        """Set target to closest player"""
        target = self.get_closest_player(target_a_pos, target_b_pos)
        self.target = target
