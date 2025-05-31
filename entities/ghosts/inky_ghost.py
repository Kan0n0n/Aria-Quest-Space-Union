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
        self.target_grid_x = (start_x, start_y)  # Target position for movement
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
        self.dead = False
        self.last_grid_pos = None  # Last grid position for movement history

        # Animation properties
        self.animation_timer = 0
        self.bob_offset = 0

        # A* pathfinding variables
        self.current_path = []  # Stores the planned path to destination
        self.path_recalculation_timer = 0  # Timer to periodically recalculate path
        self.path_recalculation_interval = 30  # Recalculate every 0.5 seconds (30 frames at 60 FPS)

        # Grid-based movement history for visual trail
        self.movement_history = []
        self.stuck_counter = 0

        # Catch detection
        self.catch_distance = 0.8  # How close to consider a "catch"

        # Enhanced AI behaviors with food percentage tracking
        self.ai_mode = "CHASE"  # CHASE, SCATTER, or ENRAGED
        self.mode_timer = 0
        self.behavior_switch_interval = 600  # 10 seconds at 60 FPS

        # Food tracking for enraged mode
        self.total_food_count = 0  # Will be set by maze
        self.is_enraged = False  # Triggered when 80% food eaten
        self.enraged_speed_multiplier = 1.5  # 60% speed increase when enraged

        # FRIGHTENED mode properties
        self.first_frightened = True  # First time entering FRIGHTENED mode

    def heuristic(self, a, b):
        return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)

    def choose_greedy_direction(self, maze, target_pos):
        eliminate_directions = {"UP": "DOWN", "DOWN": "UP", "LEFT": "RIGHT", "RIGHT": "LEFT"}
        best_direction = None
        best_distance = float('inf')
        valid_direction = []
        for direction, (dx, dy) in DIRECTIONS.items():
            if direction == eliminate_directions[self.direction]:
                continue
            nx, ny = self.grid_x + dx, self.grid_y + dy

            if not maze.is_valid_position(nx, ny):
                continue
            valid_direction.append(direction)
            distance = self.heuristic((nx, ny), target_pos)
            if distance < best_distance:
                best_distance = distance
                best_direction = direction
        if not valid_direction:
            reverse_dir = eliminate_directions[self.direction]
            dx, dy = DIRECTIONS[reverse_dir]
            nx, ny = self.grid_x + dx, self.grid_y + dy
            if maze.is_valid_position(nx, ny):
                return reverse_dir
        return best_direction or self.direction

    def a_star_pathfind(self, maze, start, goal):
        open_set = []
        heapq.heappush(open_set, (0, start))
        came_from = {}
        g_score = {start: 0}
        f_score = {start: self.heuristic(start, goal)}

        while open_set:
            current = heapq.heappop(open_set)[1]

            if current == goal:
                # Reconstruct path (excluding start position)
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                return path[::-1] if path else []

            for direction, (dx, dy) in DIRECTIONS.items():
                neighbor = (current[0] + dx, current[1] + dy)

                if not maze.is_valid_position(neighbor[0], neighbor[1]):
                    continue

                # Apply no-reverse rule: if this is the first step from start position,
                # don't allow reverse direction
                if current == start:
                    reverse_directions = {"UP": "DOWN", "DOWN": "UP", "LEFT": "RIGHT", "RIGHT": "LEFT"}
                    non_reverse_options = [
                        d
                        for d in DIRECTIONS
                        if d != reverse_directions[self.direction]
                        and maze.is_valid_position(current[0] + DIRECTIONS[d][0], current[1] + DIRECTIONS[d][1])
                    ]
                    if direction == reverse_directions[self.direction] and non_reverse_options:
                        continue  # Skip reverse direction from starting position

                tentative_g_score = g_score[current] + 1

                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = g_score[neighbor] + self.heuristic(neighbor, goal)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))

        return []  # No path found

    def get_direction_to_next_position(self, next_pos):
        dx = next_pos[0] - self.grid_x
        dy = next_pos[1] - self.grid_y

        if dx == 1 and dy == 0:
            return "RIGHT"
        elif dx == -1 and dy == 0:
            return "LEFT"
        elif dx == 0 and dy == 1:
            return "DOWN"
        elif dx == 0 and dy == -1:
            return "UP"
        else:
            return self.direction  # Fallback to current direction

    def random_direction(self, maze):
        eliminate_directions = {"UP": "DOWN", "DOWN": "UP", "LEFT": "RIGHT", "RIGHT": "LEFT"}
        possible_directions = [d for d in DIRECTIONS if d != eliminate_directions[self.direction]]
        if possible_directions:
            new_direction = random.choice(possible_directions)
            nx, ny = self.grid_x + DIRECTIONS[new_direction][0], self.grid_y + DIRECTIONS[new_direction][1]
            if maze.is_valid_position(nx, ny):
                return new_direction
        return self.direction  # Fallback to current direction if no valid move

    def reverse_direction(self):
        reverse_directions = {"UP": "DOWN", "DOWN": "UP", "LEFT": "RIGHT", "RIGHT": "LEFT"}
        return reverse_directions[self.direction]

    def get_closet_player(self, players):
        min_distance = float('inf')
        closest_player = None
        for player_pos in players:
            if player_pos is not None:
                player_grid_x, player_grid_y = player_pos
                distance = self.heuristic((self.grid_x, self.grid_y), (player_grid_x, player_grid_y))
                if distance < min_distance:
                    min_distance = distance
                    closest_player = player_pos
        return closest_player

    def moving_algorithm(self, maze, players):
        # 1) pick target based on mode and determine if we should use A*
        use_astar = False
        target_pos = None

        if self.ai_mode in ("CHASE", "ENRAGED"):
            target_pos = self.get_closet_player(players)
            use_astar = True
        elif self.ai_mode == "SCATTER":
            target_pos = self.get_scatter_point()
            use_astar = False  # Use normal greedy direction for scatter
        elif self.ai_mode == "FRIGHTENED":
            if self.first_frightened:
                self.first_frightened = False
                temp_direction = self.reverse_direction()
                nx, ny = self.grid_x + DIRECTIONS[temp_direction][0], self.grid_y + DIRECTIONS[temp_direction][1]
                if maze.is_valid_position(nx, ny):
                    self.next_direction = temp_direction
                    target_pos = None
                else:
                    # If reverse is blocked, pick a random valid direction
                    valid_dirs = []
                    for d, (dx, dy) in DIRECTIONS.items():
                        tx, ty = self.grid_x + dx, self.grid_y + dy
                        if maze.is_valid_position(tx, ty):
                            valid_dirs.append(d)
                    if valid_dirs:
                        self.next_direction = random.choice(valid_dirs)
                    target_pos = None
            else:
                # In FRIGHTENED mode, choose a random direction
                new_dir = self.random_direction(maze)
                if new_dir != self.direction:
                    self.next_direction = new_dir
                target_pos = None
            use_astar = False
        elif self.ai_mode == "EATEN":
            target_pos = POSITIONS['GHOST_RESPAWN_POINT']['INKY']
            use_astar = True
        else:
            target_pos = None
            use_astar = False

        # 2) adjust speed in ENRAGED
        self.speed = self.base_speed * (self.enraged_speed_multiplier if self.ai_mode == "ENRAGED" else 1)

        # 3) Use A* pathfinding or greedy direction based on mode
        if target_pos:
            if use_astar:
                # Use A* pathfinding for CHASE, ENRAGED, and EATEN modes
                self.path_recalculation_timer += 1
                if not self.current_path or self.path_recalculation_timer >= self.path_recalculation_interval:
                    self.current_path = self.a_star_pathfind(maze, (self.grid_x, self.grid_y), target_pos)
                    self.path_recalculation_timer = 0

                # Follow the calculated path
                if self.current_path:
                    next_position = self.current_path[0]
                    new_dir = self.get_direction_to_next_position(next_position)

                    # Debug print for EATEN mode
                    if self.ai_mode == "EATEN":
                        print(f"EATEN mode: Current pos ({self.grid_x}, {self.grid_y}), Next target: {next_position}, Direction: {new_dir}")

                    self.next_direction = new_dir
                    self.target_grid = next_position

                    # Remove the position we're about to reach from the path
                    if (self.grid_x, self.grid_y) == next_position:
                        self.current_path.pop(0)
                        if self.ai_mode == "EATEN":
                            print(f"Reached waypoint, removing from path. Path length now: {len(self.current_path)}")
            else:
                # Use greedy direction selection for SCATTER mode
                new_dir = self.choose_greedy_direction(maze, target_pos)
                if new_dir != self.direction:
                    self.next_direction = new_dir

                dx, dy = DIRECTIONS[self.next_direction]
                nx, ny = self.grid_x + dx, self.grid_y + dy
                if maze.is_valid_position(nx, ny):
                    self.direction = self.next_direction
                    self.target_grid = (nx, ny)
                else:
                    self.target_grid = (self.grid_x, self.grid_y)

        # 4) FIXED: Ensure we're using the correct target_grid variable
        else:
            dx, dy = DIRECTIONS[self.next_direction]
            nx, ny = self.grid_x + dx, self.grid_y + dy
            if maze.is_valid_position(nx, ny):
                self.direction = self.next_direction
                self.target_grid = (nx, ny)
            else:
                self.target_grid = (self.grid_x, self.grid_y)

    def move_towards_target(self):
        target_px = self.target_grid[0] * CELL_SIZE
        target_py = self.target_grid[1] * CELL_SIZE

        dx = target_px - self.pixel_x
        dy = target_py - self.pixel_y

        dist = math.hypot(dx, dy)
        if dist == 0:
            # Arrived at target cell
            self.grid_x, self.grid_y = self.target_grid
            # Add to movement history
            self.movement_history.append((self.grid_x, self.grid_y))
            if len(self.movement_history) > 10:
                self.movement_history.pop(0)
            return

        move_dist = min(self.speed, dist)
        if dist != 0:
            self.pixel_x += move_dist * dx / dist
            self.pixel_y += move_dist * dy / dist

        # Snap to grid if close enough
        if abs(self.pixel_x - target_px) < 1 and abs(self.pixel_y - target_py) < 1:
            self.pixel_x = target_px
            self.pixel_y = target_py
            self.grid_x, self.grid_y = self.target_grid
            self.movement_history.append((self.grid_x, self.grid_y))
            if len(self.movement_history) > 10:
                self.movement_history.pop(0)

    def get_scatter_point(self):
        # only one scatter point for Inky
        return POSITIONS['INKY_GHOST_SCATTER_POINT']

    def kill(self):
        self.dead = True
        self.ai_mode = "EATEN"

    def is_dead(self):
        return self.dead

    def get_position(self):
        return (self.grid_x, self.grid_y)

    def state_change(self, new_state):
        if new_state == "CHASE" and self.ai_mode != "CHASE":
            self.ai_mode = "CHASE"
            self.mode_timer = 0
            if hasattr(self, 'current_path'):
                self.current_path = []  # Clear path when entering A* mode
        elif new_state == "SCATTER" and self.ai_mode != "SCATTER":
            self.ai_mode = "SCATTER"
            self.mode_timer = 0
            if hasattr(self, 'current_path'):
                self.current_path = []  # Clear path when entering greedy mode
        elif new_state == "ENRAGED" and self.ai_mode != "ENRAGED":
            self.ai_mode = "ENRAGED"
            self.mode_timer = 0
            if hasattr(self, 'current_path'):
                self.current_path = []  # Clear path when entering A* mode
        elif new_state == "FRIGHTENED" and self.ai_mode != "FRIGHTENED":
            self.ai_mode = "FRIGHTENED"
            self.first_frightened = True
            if hasattr(self, 'current_path'):
                self.current_path = []  # Clear path when entering random mode
        elif new_state == "EATEN" and self.ai_mode != "EATEN":
            self.ai_mode = "EATEN"
            if hasattr(self, 'current_path'):
                self.current_path = []  # Clear path when entering A* mode

    def set_total_food_count(self, total_food_count):
        self.total_food_count = total_food_count

    def revive(self):
        self.dead = False
        self.ai_mode = "CHASE"
        self.mode_timer = 0
        self.is_enraged = False
        self.movement_history.clear()

    def draw_debug_walkability(self, screen, maze):
        for y in range(maze.height):
            for x in range(maze.width):
                rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)

                if maze.is_valid_position(x, y):
                    color = (0, 255, 0, 100)  # Green for walkable
                else:
                    color = (255, 0, 0, 100)  # Red for wall

                surface = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
                pygame.draw.rect(surface, color, surface.get_rect())
                screen.blit(surface, rect.topleft)

    def update(self, maze, pos_players, power_up_players):
        # (0) Enter FRIGHTENED mode if a player collects a power pellet
        if self.ai_mode != "EATEN" and self.ai_mode != "FRIGHTENED":
            is_changed = False
            for player in power_up_players:
                if player:
                    is_changed = True
                    break
            if is_changed:
                self.state_change("FRIGHTENED")
                self.mode_timer = 0
        if self.ai_mode == "FRIGHTENED":
            is_changed = False
            for player in power_up_players:
                if player:
                    is_changed = True
                    break
            if not is_changed:
                # If still in FRIGHTENED mode, reset timer
                if self.is_enraged:
                    self.state_change("ENRAGED")
                else:
                    self.state_change("CHASE")

                self.mode_timer = 0

        # (0.5) Check if Inky move to ghost spawn point
        if self.ai_mode == "EATEN":
            now_x, now_y = self.grid_x, self.grid_y
            respawn_x, respawn_y = POSITIONS['GHOST_RESPAWN_POINT']['INKY']
            if (now_x, now_y) == (respawn_x, respawn_y):
                self.revive()
                # Immediately check if Inky should be enraged after revive
                if self.total_food_count > 0:
                    food_percentage = (maze.get_remaining_food_count() / self.total_food_count) * 100
                    if food_percentage <= 20:
                        self.is_enraged = True
                        self.state_change("ENRAGED")

        # (1) Handle state timer for mode switching
        if self.ai_mode in ("CHASE", "SCATTER"):
            self.mode_timer += 1
            if self.mode_timer >= self.behavior_switch_interval:
                if self.ai_mode == "CHASE":
                    self.state_change("SCATTER")
                    self.mode_timer = 0
                elif self.ai_mode == "SCATTER":
                    self.state_change("CHASE")
                    self.mode_timer = 0

        # (2) Check if Inky should enter ENRAGED mode
        if not self.is_enraged and self.total_food_count > 0:
            food_percentage = (maze.get_remaining_food_count() / self.total_food_count) * 100
            if food_percentage <= 20:
                self.is_enraged = True
                self.state_change("ENRAGED")
                print("Inky is enraged! Speed increased.")

        # (3) run the moving algorithm
        if self.pixel_x % CELL_SIZE == 0 and self.pixel_y % CELL_SIZE == 0:
            self.moving_algorithm(maze, pos_players)

        # (4) update pixel position
        self.move_towards_target()

    def render(self, screen, maze=None, debug_mode=False):
        if debug_mode:
            # Draw walkability grid if debug mode is enabled
            self.draw_debug_walkability(screen, maze)

        if debug_mode and self.current_path and self.ai_mode in ("CHASE", "ENRAGED", "EATEN"):
            # Draw A* path as purple squares
            for i, (path_x, path_y) in enumerate(self.current_path):
                alpha = max(50, 200 - i * 15)  # Fade effect along path
                path_rect = pygame.Rect(path_x * CELL_SIZE + CELL_SIZE // 3, path_y * CELL_SIZE + CELL_SIZE // 3, CELL_SIZE // 3, CELL_SIZE // 3)
                pygame.draw.rect(screen, (128, 0, 128), path_rect)  # Purple for A* path

        # Draw scatter points and path in scatter mode (green) if debug mode
        if debug_mode and self.ai_mode == "SCATTER":
            # Draw single scatter point
            scatter_point = self.get_scatter_point()
            scatter_x, scatter_y = scatter_point
            scatter_rect = pygame.Rect(scatter_x * CELL_SIZE + CELL_SIZE // 4, scatter_y * CELL_SIZE + CELL_SIZE // 4, CELL_SIZE // 2, CELL_SIZE // 2)
            pygame.draw.rect(screen, (0, 255, 0), scatter_rect)

        if debug_mode and self.ai_mode == "EATEN":
            target_pos = POSITIONS['GHOST_RESPAWN_POINT']['INKY']
            tx, ty = target_pos
            cx = tx * CELL_SIZE + CELL_SIZE // 2
            cy = ty * CELL_SIZE + CELL_SIZE // 2
            pygame.draw.circle(screen, (0, 255, 255), (cx, cy), 6)  # Cyan dot on target

        # Draw grid-based movement history (red squares) if debug mode
        if debug_mode and self.movement_history:
            for i, (hist_x, hist_y) in enumerate(self.movement_history):
                alpha = int(100 + (155 * i / len(self.movement_history)))  # Fade effect
                base_color = (255, 100, 100) if self.is_enraged else (255, alpha // 2, alpha // 2)

                # Draw small square at grid position
                rect = pygame.Rect(hist_x * CELL_SIZE + CELL_SIZE // 4, hist_y * CELL_SIZE + CELL_SIZE // 4, CELL_SIZE // 2, CELL_SIZE // 2)
                pygame.draw.rect(screen, base_color, rect)

        # Draw next target grid position (blue square) if debug mode
        if debug_mode and self.target_grid:
            target_x, target_y = self.target_grid
            target_rect = pygame.Rect(target_x * CELL_SIZE + CELL_SIZE // 4, target_y * CELL_SIZE + CELL_SIZE // 4, CELL_SIZE // 2, CELL_SIZE // 2)
            pygame.draw.rect(screen, (0, 0, 255), target_rect)

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
        else:
            if self.is_enraged:
                color = (255, 50, 50)  # Bright red for enraged mode
            elif self.ai_mode == "CHASE":
                color = (0, 0, 255)  # Blue for chase mode
            elif self.ai_mode == "SCATTER":
                color = (0, 255, 255)  # Cyan for scatter mode
            elif self.ai_mode == "FRIGHTENED":
                color = (255, 255, 0)  # Yellow for frightened mode
            elif self.ai_mode == "EATEN":
                color = (128, 128, 128)  # Gray for eaten mode
            else:
                color = (255, 255, 255)  # Default white
            pygame.draw.rect(screen, color, (self.pixel_x, self.pixel_y, CELL_SIZE, CELL_SIZE))

        # Debug info
        if debug_mode:
            font = pygame.font.Font(None, 24)
            mode_text = self.ai_mode
            if self.is_enraged:
                mode_text += f" SPD:{self.speed:.1f}"
            timer_text = f"{(self.behavior_switch_interval - self.mode_timer) // 60 + 1}s" if not self.is_enraged else "∞"
            if self.ai_mode != "FRIGHTENED" and self.ai_mode != "EATEN" and self.ai_mode != "ENRAGED":
                debug_text = f"{mode_text} {timer_text}"
            else:
                debug_text = f"{mode_text}"
            text_surface = font.render(debug_text, True, (255, 255, 255))
            screen.blit(text_surface, (self.pixel_x, self.pixel_y - 30))

    def reset_position(self, x, y):
        self.grid_x = x
        self.grid_y = y
        self.pixel_x = x * CELL_SIZE
        self.pixel_y = y * CELL_SIZE
        self.direction = "LEFT"
        self.next_direction = "LEFT"
        self.moving = False
        self.movement_progress = 0.0
        self.dead = False
        self.is_enraged = False
        self.current_path.clear()
        self.movement_history.clear()
        self.animation_timer = 0
        self.bob_offset = 0.0
