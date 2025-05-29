import pygame
import math
import sys
from core.bg import StarryBackground
import os


class CinematicIntro:
    def __init__(self, screen_width=800, screen_height=600):
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Animation phases
        self.PHASE_SKY_DESCENT = 0
        self.PHASE_NAME_REVEAL = 1
        self.PHASE_STARRY_DISPLAY = 2
        self.PHASE_COMPLETE = 3

        self.current_phase = self.PHASE_SKY_DESCENT
        self.phase_timer = 0

        # Sky descent animation - much slower for cinematic effect
        self.camera_y = 0  # Camera position in the world
        self.descent_speed = 1.5
        self.descent_duration = 240  # 4 seconds at 60fps

        # Logo animation during sky descent
        self.logo_start_y = self.screen_height + 100  # Start below screen
        self.logo_target_y = self.screen_height // 2  # End at center
        self.logo_current_y = self.logo_start_y

        # Logo reveal animation (for alpha and scale refinement)
        self.logo_alpha = 255  # Start visible during descent
        self.logo_scale = 0.8  # Start slightly smaller
        self.logo_reveal_duration = 120  # 2 seconds

        # Starry display duration
        self.starry_display_duration = 300  # 5 seconds

        # Create starry background
        self.starry_bg = StarryBackground(screen_width, screen_height, num_stars=150)

        # Create sky gradient surface (larger for camera movement)
        self.sky_surface = pygame.Surface((screen_width, screen_height * 3))
        self._create_sky_gradient()

        # Load logo image
        try:
            self.logo_image = pygame.image.load(os.path.join("assets", "tsuki_no_tempest.png")).convert_alpha()
            # Scale logo if needed (adjust size as needed)
            logo_width = min(300, self.screen_width // 2)  # Max 300px or half screen width
            logo_height = int(logo_width * self.logo_image.get_height() / self.logo_image.get_width())
            self.logo_image = pygame.transform.scale(self.logo_image, (logo_width, logo_height))
        except pygame.error:
            print("Warning: Could not load logo.png, using text fallback")
            # Fallback to text if image not found
            pygame.font.init()
            font = pygame.font.Font(None, 72)
            self.logo_image = font.render("Tsuki No Tempest", True, (255, 255, 255))

        self.logo_original = self.logo_image.copy()  # Keep original for scaling

    def _create_sky_gradient(self):
        """Create a gradient that matches starry background for seamless transition"""
        total_height = self.screen_height * 3  # Longer gradient for smooth movement

        for y in range(total_height):
            # Calculate gradient factor
            gradient_factor = y / total_height

            if gradient_factor < 0.15:
                # Start with lighter space colors at top
                top_color = (40, 30, 70)  # Deep purple
                bottom_color = (25, 20, 55)  # Darker purple
                local_factor = gradient_factor / 0.15
            elif gradient_factor < 0.35:
                # Transition to night sky
                top_color = (25, 20, 55)  # Darker purple
                bottom_color = (20, 15, 45)  # Even darker
                local_factor = (gradient_factor - 0.15) / 0.2
            elif gradient_factor < 0.6:
                # Deep space transition
                top_color = (20, 15, 45)  # Even darker
                bottom_color = (15, 10, 35)  # Deep space blue
                local_factor = (gradient_factor - 0.35) / 0.25
            elif gradient_factor < 0.8:
                # Approaching starry background colors
                top_color = (15, 10, 35)  # Deep space blue
                bottom_color = (12, 8, 28)  # Almost starry bg
                local_factor = (gradient_factor - 0.6) / 0.2
            else:
                # Final transition to exact starry background color
                top_color = (12, 8, 28)  # Almost starry bg
                bottom_color = (10, 5, 25)  # Exact starry background color
                local_factor = (gradient_factor - 0.8) / 0.2

            # Interpolate colors
            r = int(top_color[0] + (bottom_color[0] - top_color[0]) * local_factor)
            g = int(top_color[1] + (bottom_color[1] - top_color[1]) * local_factor)
            b = int(top_color[2] + (bottom_color[2] - top_color[2]) * local_factor)

            color = (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))
            pygame.draw.line(self.sky_surface, color, (0, y), (self.screen_width, y))

        # The logo should appear when we're at about 70% through the gradient
        self.logo_reveal_position = total_height * 0.7

    def update(self):
        """Update the intro animation"""
        self.phase_timer += 1

        if self.current_phase == self.PHASE_SKY_DESCENT:
            # Camera descending animation with easing
            progress = min(1.0, self.phase_timer / self.descent_duration)
            # Smooth easing - starts fast, slows down as it approaches the target
            eased_progress = 1 - (1 - progress) ** 2

            # Move camera down to reveal the scene
            target_camera_y = self.logo_reveal_position - self.screen_height // 2
            self.camera_y = eased_progress * target_camera_y

            # Logo rises from bottom with the same easing
            logo_progress = min(1.0, self.phase_timer / self.descent_duration)
            logo_eased_progress = 1 - (1 - logo_progress) ** 2

            # Logo moves from bottom to center
            self.logo_current_y = self.logo_start_y - (self.logo_start_y - self.logo_target_y) * logo_eased_progress

            # Gradually scale up the logo during ascent
            self.logo_scale = 0.8 + 0.2 * logo_eased_progress

            # Add subtle floating effect when near the end
            if progress > 0.8:
                float_amplitude = (progress - 0.8) * 5  # Gradually increase floating
                self.logo_current_y += math.sin(self.phase_timer * 0.05) * float_amplitude

            if self.phase_timer >= self.descent_duration:
                self.current_phase = self.PHASE_NAME_REVEAL
                self.phase_timer = 0
                # Ensure logo is at target position
                self.logo_current_y = self.logo_target_y

        elif self.current_phase == self.PHASE_NAME_REVEAL:
            # Logo refinement animation (subtle scale and alpha adjustments)
            progress = min(1.0, self.phase_timer / self.logo_reveal_duration)
            eased_progress = 1 - (1 - progress) ** 3

            # Fine-tune the final scale and add gentle pulsing
            base_scale = 1.0
            pulse = math.sin(self.phase_timer * 0.05) * 0.02
            self.logo_scale = base_scale + pulse

            # Gentle floating motion
            float_offset = math.sin(self.phase_timer * 0.03) * 3
            self.logo_current_y = self.logo_target_y + float_offset

            # Update starry background
            self.starry_bg.update()

            if self.phase_timer >= self.logo_reveal_duration:
                self.current_phase = self.PHASE_STARRY_DISPLAY
                self.phase_timer = 0

        elif self.current_phase == self.PHASE_STARRY_DISPLAY:
            # Display with shooting stars and enhanced logo effects
            self.starry_bg.update()

            # Enhanced pulsing and floating effect
            pulse = math.sin(self.phase_timer * 0.03) * 0.03
            float_offset = math.sin(self.phase_timer * 0.02) * 5

            self.logo_scale = 1.0 + pulse
            self.logo_current_y = self.logo_target_y + float_offset

            if self.phase_timer >= self.starry_display_duration:
                self.current_phase = self.PHASE_COMPLETE

    def render(self, screen):
        """Render the current frame of the intro"""
        if self.current_phase == self.PHASE_SKY_DESCENT:
            # Draw sky with camera movement
            screen.blit(self.sky_surface, (0, -self.camera_y))

            # Add subtle stars that fade in as we approach the bottom
            progress = min(1.0, self.phase_timer / self.descent_duration)
            if progress > 0.6:  # Start showing stars in the last 40% of descent
                star_alpha = int((progress - 0.6) * 2.5 * 255)  # Fade in stars
                star_surface = pygame.Surface((self.screen_width, self.screen_height))
                star_surface.set_alpha(star_alpha)
                self.starry_bg.render(star_surface)
                screen.blit(star_surface, (0, 0))

            # Draw logo during sky descent
            self._render_logo(screen)

        elif self.current_phase in [self.PHASE_NAME_REVEAL, self.PHASE_STARRY_DISPLAY]:
            # Draw starry background
            self.starry_bg.render(screen)

            # Draw logo with enhanced effects
            self._render_logo(screen, add_glow=(self.current_phase == self.PHASE_STARRY_DISPLAY))

    def _render_logo(self, screen, add_glow=False):
        """Render the logo with current transformations"""
        if self.logo_alpha > 0:
            # Apply scaling
            if self.logo_scale != 1.0:
                original_size = self.logo_original.get_size()
                new_size = (int(original_size[0] * self.logo_scale), int(original_size[1] * self.logo_scale))
                scaled_logo = pygame.transform.scale(self.logo_original, new_size)
            else:
                scaled_logo = self.logo_original.copy()

            # Apply alpha
            scaled_logo.set_alpha(self.logo_alpha)

            # Position the logo
            logo_rect = scaled_logo.get_rect(center=(self.screen_width // 2, int(self.logo_current_y)))

            # Add glow effect if requested
            if add_glow:
                glow_logo = scaled_logo.copy()
                glow_logo.set_alpha(30)
                for dx in [-3, -2, -1, 0, 1, 2, 3]:
                    for dy in [-3, -2, -1, 0, 1, 2, 3]:
                        if dx != 0 or dy != 0:
                            glow_rect = glow_logo.get_rect(center=(logo_rect.centerx + dx, logo_rect.centery + dy))
                            screen.blit(glow_logo, glow_rect)

            # Draw the main logo
            screen.blit(scaled_logo, logo_rect)

    def is_complete(self):
        """Check if the intro animation is complete"""
        return self.current_phase == self.PHASE_COMPLETE

    def skip(self):
        """Skip to the end of the intro"""
        self.current_phase = self.PHASE_COMPLETE
