import pygame
import os
from constants import *


class SpriteManager:
    def __init__(self):
        self.sprites = {}
        self.default_sprites = {}
        self._create_default_sprites()

    def _create_default_sprites(self):
        size = CELL_SIZE

        # Player 1 default sprites (Yellow Pacman)
        for direction in ["up", "down", "left", "right"]:
            surf = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.circle(surf, YELLOW, (size // 2, size // 2), size // 2 - 2)

            # Add direction indicator (small notch)
            if direction == "up":
                pygame.draw.polygon(surf, BLACK, [(size // 2, 2), (size // 2 - 4, size // 2), (size // 2 + 4, size // 2)])
            elif direction == "down":
                pygame.draw.polygon(surf, BLACK, [(size // 2, size - 2), (size // 2 - 4, size // 2), (size // 2 + 4, size // 2)])
            elif direction == "left":
                pygame.draw.polygon(surf, BLACK, [(2, size // 2), (size // 2, size // 2 - 4), (size // 2, size // 2 + 4)])
            elif direction == "right":
                pygame.draw.polygon(surf, BLACK, [(size - 2, size // 2), (size // 2, size // 2 - 4), (size // 2, size // 2 + 4)])

            self.default_sprites[f"player1_{direction}"] = surf

        # Player 2 default sprites (Red Pacman)
        for direction in ["up", "down", "left", "right"]:
            surf = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.circle(surf, RED, (size // 2, size // 2), size // 2 - 2)

            # Add direction indicator (small notch)
            if direction == "up":
                pygame.draw.polygon(surf, BLACK, [(size // 2, 2), (size // 2 - 4, size // 2), (size // 2 + 4, size // 2)])
            elif direction == "down":
                pygame.draw.polygon(surf, BLACK, [(size // 2, size - 2), (size // 2 - 4, size // 2), (size // 2 + 4, size // 2)])
            elif direction == "left":
                pygame.draw.polygon(surf, BLACK, [(2, size // 2), (size // 2, size // 2 - 4), (size // 2, size // 2 + 4)])
            elif direction == "right":
                pygame.draw.polygon(surf, BLACK, [(size - 2, size // 2), (size // 2, size // 2 - 4), (size // 2, size // 2 + 4)])

            self.default_sprites[f"player2_{direction}"] = surf

    def load_custom_sprites(self, player_id, sprite_paths):
        for direction, path in sprite_paths.items():
            if os.path.exists(path):
                try:
                    sprite = pygame.image.load(path)
                    sprite = pygame.transform.scale(sprite, (CELL_SIZE, CELL_SIZE))
                    self.sprites[f"{player_id}_{direction}"] = sprite
                    print(f"Loaded custom sprite: {player_id}_{direction}")
                except pygame.error as e:
                    print(f"Error loading sprite {path}: {e}")
            else:
                print(f"Sprite file not found: {path}")

    def get_sprite(self, player_id, direction):
        key = f"{player_id}_{direction}"
        return self.sprites.get(key, self.default_sprites.get(key))

    def auto_load_from_assets(self):
        assets_path = "assets"
        if not os.path.exists(assets_path):
            return

        # Try to load ena sprites (assuming they're for player1)
        ena_sprites = {
            "up": os.path.join(assets_path, "ena_up.png"),
            "down": os.path.join(assets_path, "ena_down.png"),
            "left": os.path.join(assets_path, "ena_left.png"),
            "right": os.path.join(assets_path, "ena_right.png"),
        }

        mizuki_sprites = {
            "up": os.path.join(assets_path, "mizuki_up.png"),
            "down": os.path.join(assets_path, "mizuki_down.png"),
            "left": os.path.join(assets_path, "mizuki_left.png"),
            "right": os.path.join(assets_path, "mizuki_right.png"),
        }

        self.load_custom_sprites("player1", ena_sprites)
        self.load_custom_sprites("ai1", mizuki_sprites)

        # Look for other sprite patterns
        files = os.listdir(assets_path)
        for file in files:
            if file.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
                print(f"Found asset: {file}")
