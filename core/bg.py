import pygame
import random
import math
from constants import *


class StarryBackground:
    def __init__(self, screen_width=SCREEN_WIDTH, screen_height=SCREEN_HEIGHT, num_stars=100):
        # Handle if a pygame surface is passed instead of dimensions
        if isinstance(screen_width, pygame.Surface):
            surface = screen_width
            self.screen_width = surface.get_width()
            self.screen_height = surface.get_height()
        else:
            self.screen_width = screen_width
            self.screen_height = screen_height

        self.stars = []
        self.shooting_stars = []
        self.shooting_star_timer = 0
        self.shooting_star_spawn_time = random.randint(20, 60)  # Much more frequent: 0.3-1 second at 60fps

        # Create gradient surface for background
        self.gradient_surface = pygame.Surface((self.screen_width, self.screen_height))
        self._create_gradient()

        # Create regular stars
        for _ in range(num_stars):
            star = {
                "x": random.randint(0, self.screen_width),
                "y": random.randint(0, self.screen_height),
                "size": random.randint(2, 4),
                "brightness": random.uniform(0.4, 1.0),
                "twinkle_speed": random.uniform(0.01, 0.05),
                "twinkle_phase": random.uniform(0, 2 * math.pi),
            }
            self.stars.append(star)

    def _create_gradient(self):
        for y in range(self.screen_height):
            # Calculate gradient factor (0 at top, 1 at bottom)
            gradient_factor = y / self.screen_height

            # Define colors with more contrast for better visibility
            top_color = (10, 5, 25)  # Dark purple-black
            bottom_color = (80, 40, 120)  # Bright purple night

            # Interpolate between colors
            r = int(top_color[0] + (bottom_color[0] - top_color[0]) * gradient_factor)
            g = int(top_color[1] + (bottom_color[1] - top_color[1]) * gradient_factor)
            b = int(top_color[2] + (bottom_color[2] - top_color[2]) * gradient_factor)

            # Draw horizontal line with interpolated color
            color = (r, g, b)
            pygame.draw.line(self.gradient_surface, color, (0, y), (self.screen_width, y))

    def create_shooting_star(self):
        """Create a new shooting star"""
        # Start from random edge of screen
        side = random.randint(0, 3)
        if side == 0:  # Top
            start_x = random.randint(0, self.screen_width)
            start_y = 0
        elif side == 1:  # Right
            start_x = self.screen_width
            start_y = random.randint(0, self.screen_height)
        elif side == 2:  # Bottom
            start_x = random.randint(0, self.screen_width)
            start_y = self.screen_height
        else:  # Left
            start_x = 0
            start_y = random.randint(0, self.screen_height)

        # Random direction and speed (faster shooting stars)
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(4, 12)  # Increased speed range

        shooting_star = {
            "x": start_x,
            "y": start_y,
            "dx": math.cos(angle) * speed,
            "dy": math.sin(angle) * speed,
            "trail": [],  # Store trail positions
            "life": random.randint(40, 80),  # Shorter lifetime for more frequent stars
            "max_life": random.randint(40, 80),
            "size": random.randint(2, 8),  # Slightly larger shooting stars
        }

        return shooting_star

    def update(self):
        # Update regular stars
        for star in self.stars:
            star["twinkle_phase"] += star["twinkle_speed"]
            if star["twinkle_phase"] > 2 * math.pi:
                star["twinkle_phase"] -= 2 * math.pi

        # Update shooting star spawn timer (much more frequent spawning)
        self.shooting_star_timer += 1
        if self.shooting_star_timer >= self.shooting_star_spawn_time:
            self.shooting_stars.append(self.create_shooting_star())
            self.shooting_star_timer = 0
            self.shooting_star_spawn_time = random.randint(20, 60)  # 0.3-1 second

        # Update shooting stars
        for shooting_star in self.shooting_stars[:]:
            # Update position
            shooting_star["x"] += shooting_star["dx"]
            shooting_star["y"] += shooting_star["dy"]

            # Add current position to trail
            shooting_star["trail"].append((shooting_star["x"], shooting_star["y"]))

            # Limit trail length
            if len(shooting_star["trail"]) > 20:  # Longer trails
                shooting_star["trail"].pop(0)

            # Decrease life
            shooting_star["life"] -= 1

            # Remove if out of bounds or life expired
            if (
                shooting_star["life"] <= 0
                or shooting_star["x"] < -50
                or shooting_star["x"] > self.screen_width + 50
                or shooting_star["y"] < -50
                or shooting_star["y"] > self.screen_height + 50
            ):
                self.shooting_stars.remove(shooting_star)

    def render(self, screen):
        # Draw gradient background
        screen.blit(self.gradient_surface, (0, 0))

        # Draw regular stars
        for star in self.stars:
            # Calculate twinkling brightness
            twinkle_factor = (math.sin(star["twinkle_phase"]) + 1) / 2
            current_brightness = star["brightness"] * (0.6 + 0.4 * twinkle_factor)

            # Star color (white/yellow with brightness variation)
            color_value = int(255 * current_brightness)
            # Add slight yellow tint to stars
            star_color = (color_value, color_value, max(0, color_value - 20))

            # Draw the star
            pygame.draw.circle(screen, star_color, (int(star["x"]), int(star["y"])), star["size"])

            # Add a subtle glow for larger stars
            if star["size"] >= 4:
                glow_color = (color_value // 3, color_value // 3, color_value // 4)
                pygame.draw.circle(screen, glow_color, (int(star["x"]), int(star["y"])), star["size"] + 2)

        # Draw shooting stars
        for shooting_star in self.shooting_stars:
            # Calculate fade based on remaining life
            fade_factor = max(0, shooting_star["life"] / shooting_star["max_life"])

            # Draw trail with colorful effect
            for i, (trail_x, trail_y) in enumerate(shooting_star["trail"]):
                if len(shooting_star["trail"]) > 0:
                    trail_alpha = (i / len(shooting_star["trail"])) * fade_factor
                    trail_brightness = max(0, min(255, int(255 * trail_alpha)))

                    # Add purple/blue tint to trail
                    trail_color = (trail_brightness, max(0, trail_brightness - 30), min(255, trail_brightness + 40))

                    if trail_brightness > 10:
                        trail_size = max(1, int(shooting_star["size"] * trail_alpha))
                        pygame.draw.circle(screen, trail_color, (int(trail_x), int(trail_y)), trail_size)

            # Draw main shooting star with bright white/yellow color
            main_brightness = max(0, min(255, int(255 * fade_factor)))
            main_color = (main_brightness, main_brightness, max(0, main_brightness - 20))

            if main_brightness > 0:
                pygame.draw.circle(screen, main_color, (int(shooting_star["x"]), int(shooting_star["y"])), shooting_star["size"])
