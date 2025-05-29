import pygame
from constants import *
import os
import math


class TopBarUI:
    def __init__(self, font_manager=None, bar_height=60):
        self.bar_height = bar_height
        self.font_manager = font_manager

        if font_manager:
            self.font_large = font_manager.get_font('medium')
            self.font_small = font_manager.get_font('small')
        else:
            self.font_large = pygame.font.Font(None, 24)
            self.font_small = pygame.font.Font(None, 18)

        # Load game icon (optional)
        self.game_icon = None
        try:
            icon_path = os.path.join("assets", "game_icon.png")
            if os.path.exists(icon_path):
                self.game_icon = pygame.image.load(icon_path).convert_alpha()
                self.game_icon = pygame.transform.scale(self.game_icon, (40, 40))
        except:
            pass  # No icon if file doesn't exist

    def render(self, screen, player1, player2, maze):
        # Create top bar background - FIXED: Use full screen width
        bar_surface = pygame.Surface((SCREEN_WIDTH, self.bar_height), pygame.SRCALPHA)
        background_color = (30, 30, 30, 220)  # Semi-transparent dark background
        pygame.draw.rect(bar_surface, background_color, (0, 0, SCREEN_WIDTH, self.bar_height))
        pygame.draw.rect(bar_surface, WHITE, (0, 0, SCREEN_WIDTH, self.bar_height), 2)

        # Player 1 section (left side)
        self._render_player_section(bar_surface, player1, "Ena", 20, YELLOW)

        # Player 2 section (right side) - FIXED: Better positioning
        player2_x = SCREEN_WIDTH - 220  # Adjusted to prevent overflow
        self._render_player_section(bar_surface, player2, "Mizuki", player2_x, GREEN)

        # Center section with game icon and stats
        center_x = SCREEN_WIDTH // 2
        self._render_center_section(bar_surface, center_x, maze)

        # Blit the bar to screen
        screen.blit(bar_surface, (0, 0))

    def _render_player_section(self, surface, player, name, x_pos, color):
        y_padding = 8

        # Player name
        name_text = self.font_large.render(f"{name}:", True, color)
        surface.blit(name_text, (x_pos, y_padding))

        # Score (below name)
        score_text = self.font_small.render(f"Score: {player.score}", True, WHITE)
        surface.blit(score_text, (x_pos, y_padding + 22))

        # Health hearts (inline with score) - FIXED: Better spacing
        heart_x = x_pos + score_text.get_width() + 15
        self._render_hearts(surface, player, heart_x, y_padding + 25)

    def _render_hearts(self, surface, player, start_x, y):
        heart_size = 12
        heart_spacing = 15
        max_health = 3

        for i in range(max_health):
            heart_x = start_x + (i * heart_spacing)

            if i < player.health:
                # Full heart
                pygame.draw.polygon(
                    surface,
                    RED,
                    [
                        (heart_x + heart_size // 2, y + heart_size - 1),
                        (heart_x + 1, y + heart_size // 3),
                        (heart_x + heart_size // 3, y + 1),
                        (heart_x + heart_size // 2, y + heart_size // 4),
                        (heart_x + 2 * heart_size // 3, y + 1),
                        (heart_x + heart_size - 1, y + heart_size // 3),
                    ],
                )
            else:
                # Empty heart
                pygame.draw.polygon(
                    surface,
                    (100, 100, 100),
                    [
                        (heart_x + heart_size // 2, y + heart_size - 1),
                        (heart_x + 1, y + heart_size // 3),
                        (heart_x + heart_size // 3, y + 1),
                        (heart_x + heart_size // 2, y + heart_size // 4),
                        (heart_x + 2 * heart_size // 3, y + 1),
                        (heart_x + heart_size - 1, y + heart_size // 3),
                    ],
                    1,
                )

    def _render_center_section(self, surface, center_x, maze):
        # Game icon
        if self.game_icon:
            icon_rect = self.game_icon.get_rect(center=(center_x, self.bar_height // 2))
            surface.blit(self.game_icon, icon_rect)
            text_x = center_x + 30  # Offset text to right of icon
        else:
            text_x = center_x

        # Pellets remaining
        pellets_remaining = len(maze.pellets) + len(maze.power_pellets)
        pellets_text = self.font_small.render(f"Pellets: {pellets_remaining}", True, WHITE)
        pellets_rect = pellets_text.get_rect(center=(text_x, self.bar_height // 2))
        surface.blit(pellets_text, pellets_rect)


class BottomBarUI:
    def __init__(self, font_manager=None, bar_height=30):
        self.bar_height = bar_height
        self.font_manager = font_manager

        if font_manager:
            self.font = font_manager.get_font('small')
        else:
            self.font = pygame.font.Font(None, 18)

    def render(self, screen, game_state=None):
        # Create bottom bar background
        bar_y = SCREEN_HEIGHT - self.bar_height
        bar_surface = pygame.Surface((SCREEN_WIDTH, self.bar_height), pygame.SRCALPHA)
        background_color = (20, 20, 20, 200)  # Semi-transparent dark background
        pygame.draw.rect(bar_surface, background_color, (0, 0, SCREEN_WIDTH, self.bar_height))
        pygame.draw.rect(bar_surface, WHITE, (0, 0, SCREEN_WIDTH, self.bar_height), 1)

        if game_state is not "START":
            # Context-sensitive instructions
            instructions = self._get_instructions(game_state)

            # Centered text
            instruction_text = self.font.render(instructions, True, WHITE)
            text_rect = instruction_text.get_rect(center=(SCREEN_WIDTH // 2, self.bar_height // 2))
            bar_surface.blit(instruction_text, text_rect)

            # Blit to screen
            screen.blit(bar_surface, (0, bar_y))

    def _get_instructions(self, game_state):
        if game_state == "START":
            return "Press SPACE to start | ESC to quit"
        elif game_state == "PLAYING":
            return "Controls: WASD | P: Pause | R: Restart | ESC: Quit"
        elif game_state == "PAUSED":
            return "Game Paused | P: Resume | R: Restart | ESC: Quit"
        elif game_state == "GAME_OVER":
            return "Game Over | R: Restart | ESC: Quit"
        else:
            return "Controls: WASD | P: Pause | R: Restart | ESC: Quit"


class GameUI:
    def __init__(self, font_path=None, top_bar_height=60, bottom_bar_height=30):
        pygame.font.init()

        # Initialize font manager
        self.font_manager = FontManager(font_path)

        # Get fonts from font manager
        self.font = self.font_manager.get_font('medium')
        self.small_font = self.font_manager.get_font('small')
        self.large_font = self.font_manager.get_font('extra_large')

        # UI Components
        self.top_bar = TopBarUI(self.font_manager, top_bar_height)
        self.bottom_bar = BottomBarUI(self.font_manager, bottom_bar_height)

        # Store bar heights for game area calculation
        self.top_bar_height = top_bar_height
        self.bottom_bar_height = bottom_bar_height
        self.game_area_y = top_bar_height
        self.game_area_height = SCREEN_HEIGHT - top_bar_height - bottom_bar_height

    def get_game_area(self):
        return {'x': 0, 'y': self.top_bar_height, 'width': SCREEN_WIDTH, 'height': self.game_area_height}

    def render_gameplay_ui(self, screen, player1, player2, maze, game_state="PLAYING"):
        self.top_bar.render(screen, player1, player2, maze)
        self.bottom_bar.render(screen, game_state)

    def render_game_over(self, screen, winner, player1_score, player2_score):
        # Semi-transparent overlay over game area only
        game_area = self.get_game_area()
        overlay = pygame.Surface((game_area['width'], game_area['height']))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        screen.blit(overlay, (game_area['x'], game_area['y']))

        # Main game over panel
        panel_width = 500
        panel_height = 280
        panel_x = (SCREEN_WIDTH - panel_width) // 2
        panel_y = game_area['y'] + (game_area['height'] - panel_height) // 2

        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        pygame.draw.rect(screen, (50, 50, 50), panel_rect)
        pygame.draw.rect(screen, WHITE, panel_rect, 3)

        # Game over text
        game_over_text = self.large_font.render("GAME OVER", True, WHITE)
        game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, panel_y + 40))
        screen.blit(game_over_text, game_over_rect)

        # Multi-line winner text
        self._render_multiline_text(screen, winner, SCREEN_WIDTH // 2, panel_y + 100, YELLOW, self.font, panel_width - 40)

        # Score comparison
        score_text = self.font.render(f"Ena: {player1_score} | Mizuki: {player2_score}", True, WHITE)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, panel_y + 200))
        screen.blit(score_text, score_rect)

    def render_pause_screen(self, screen):
        game_area = self.get_game_area()
        overlay = pygame.Surface((game_area['width'], game_area['height']))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        screen.blit(overlay, (game_area['x'], game_area['y']))

        # Pause panel
        panel_width = 300
        panel_height = 120
        panel_x = (SCREEN_WIDTH - panel_width) // 2
        panel_y = game_area['y'] + (game_area['height'] - panel_height) // 2

        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        pygame.draw.rect(screen, (50, 50, 50), panel_rect)
        pygame.draw.rect(screen, WHITE, panel_rect, 3)

        # Pause text
        pause_text = self.large_font.render("PAUSED", True, WHITE)
        pause_rect = pause_text.get_rect(center=(SCREEN_WIDTH // 2, panel_y + 60))
        screen.blit(pause_text, pause_rect)

    def render_start_screen(self, screen):
        # Try to load background image first
        background_image = None
        try:
            # Đường dẫn đến file PNG start screen của bạn
            bg_path = os.path.join("assets", "intro_scene_1.png")
            if os.path.exists(bg_path):
                background_image = pygame.image.load(bg_path).convert()
                # Scale image to fit screen
                background_image = pygame.transform.scale(background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except Exception as e:
            print(f"Could not load start screen image: {e}")
            background_image = None

        if background_image:
            # Use PNG background
            screen.blit(background_image, (0, 0))

            # Add only essential text over the image
            # use normal font for instructions
            instruction_font = self.font  # fallback to default
            try:
                instruction_font_path = os.path.join("fonts", "Orbitron-Regular.ttf")
                if os.path.exists(instruction_font_path):
                    instruction_font = pygame.font.Font(instruction_font_path, 24)  # Adjust size as needed
                else:
                    print("Instruction font not found, using default")
            except Exception as e:
                print(f"Could not load instruction font: {e}")

            current_time = pygame.time.get_ticks()
            pulse_speed = 0.002
            alpha_value = int(155 + 100 * abs(math.sin(current_time * pulse_speed)))

            instructions_text = instruction_font.render("Press SPACE to start", True, BLACK)
            instructions_rect = instructions_text.get_rect(center=(640, 460))

            # Add text shadow for better visibility
            shadow_text = instruction_font.render("Press SPACE to start", True, WHITE)
            shadow_rect = instructions_rect.copy()
            shadow_rect.x += 2
            shadow_rect.y += 2

            # Create a surface for the pulsing effect
            text_surface = pygame.Surface(instructions_text.get_size(), pygame.SRCALPHA)
            text_surface.set_alpha(alpha_value)
            text_surface.blit(instructions_text, (0, 0))

            screen.blit(shadow_text, shadow_rect)
            screen.blit(text_surface, instructions_rect)

    def _render_multiline_text(self, screen, text, center_x, start_y, color, font, max_width):
        lines = text.split('\n')
        all_lines = []

        for line in lines:
            if line.strip() == "":
                all_lines.append("")
                continue
            wrapped_lines = self._wrap_text(line.strip(), font, max_width)
            all_lines.extend(wrapped_lines)

        line_height = font.get_height() + 5
        total_height = len(all_lines) * line_height
        current_y = start_y - (total_height // 2)

        for line in all_lines:
            if line.strip() == "":
                current_y += line_height // 2
                continue
            text_surface = font.render(line, True, color)
            text_rect = text_surface.get_rect(center=(center_x, current_y))
            screen.blit(text_surface, text_rect)
            current_y += line_height

    def _wrap_text(self, text, font, max_width):
        words = text.split(' ')
        lines = []
        current_line = []

        for word in words:
            test_line = ' '.join(current_line + [word])
            test_width = font.size(test_line)[0]

            if test_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    lines.append(word)

        if current_line:
            lines.append(' '.join(current_line))

        return lines

    # Legacy methods for backward compatibility
    def render_player_info(self, screen, player1, player2):
        pass

    def render_game_stats(self, screen, maze):
        pass

    def render_instructions(self, screen):
        pass

    def render_scores(self, screen, player_score, ai_score):
        pass


class FontManager:
    def __init__(self, font_path=None):
        self.fonts = {}
        self.font_path = font_path
        self._load_fonts()

    def _load_fonts(self):
        try:
            if self.font_path and os.path.exists(self.font_path):
                self.fonts = {
                    'extra_large': pygame.font.Font(self.font_path, 36),
                    'large': pygame.font.Font(self.font_path, 28),
                    'medium': pygame.font.Font(self.font_path, 22),
                    'small': pygame.font.Font(self.font_path, 18),
                    'tiny': pygame.font.Font(self.font_path, 14),
                }
                print(f"Custom font loaded: {self.font_path}")
            else:
                self._load_fallback_fonts()
        except Exception as e:
            print(f"Error loading custom font: {e}")
            self._load_fallback_fonts()

    def _load_fallback_fonts(self):
        try:
            system_fonts = ['arial', 'helvetica', 'calibri', 'verdana']
            font_name = None

            for font in system_fonts:
                if font in pygame.font.get_fonts():
                    font_name = font
                    break

            self.fonts = {
                'extra_large': pygame.font.SysFont(font_name, 36) if font_name else pygame.font.Font(None, 36),
                'large': pygame.font.SysFont(font_name, 28) if font_name else pygame.font.Font(None, 28),
                'medium': pygame.font.SysFont(font_name, 22) if font_name else pygame.font.Font(None, 22),
                'small': pygame.font.SysFont(font_name, 18) if font_name else pygame.font.Font(None, 18),
                'tiny': pygame.font.SysFont(font_name, 14) if font_name else pygame.font.Font(None, 14),
            }
            print(f"Using system font: {font_name if font_name else 'default'}")
        except:
            self.fonts = {
                'extra_large': pygame.font.Font(None, 36),
                'large': pygame.font.Font(None, 28),
                'medium': pygame.font.Font(None, 22),
                'small': pygame.font.Font(None, 18),
                'tiny': pygame.font.Font(None, 14),
            }
            print("Using default pygame fonts")

    def get_font(self, size_name):
        return self.fonts.get(size_name, self.fonts['medium'])
