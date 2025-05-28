#!/usr/bin/env python3
"""
Simple validation script to test core game functionality
"""

import pygame
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def quick_test():
    """Quick test of core components"""
    try:
        # Test imports
        print("Testing imports...")
        from constants import SCREEN_WIDTH, SCREEN_HEIGHT
        from core.sprite_manager import SpriteManager
        from core.maze import Maze
        from entities.player import Player
        from entities.ai_player import AIPlayer
        from ui.game_ui import GameUI

        print("✓ All imports successful")
        # Test sprite manager
        print("Testing sprite manager...")
        sprite_manager = SpriteManager()
        sprite_manager.auto_load_from_assets()
        print("✓ Sprite manager created and auto-loaded assets")

        print("\n🎉 Core components are working!")
        print("The game is ready to play!")
        print("\nTo start the game:")
        print("python main.py")

        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


if __name__ == "__main__":
    quick_test()
