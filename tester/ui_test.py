import pygame
import sys
import os

# Add the main directory to path so we can import game modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from constants import *
from ui.game_ui import GameUI
from core.maze import Maze
from entities.player import Player
from entities.ai_player import AIPlayer
from core.sprite_manager import SpriteManager
from game.game_state import GameState, GameStateManager


class UITester:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("UI Test - Aria Quest")
        self.clock = pygame.time.Clock()

        # Initialize UI
        font_path = os.path.join("fonts", "pixelFont-7-8x14-sproutLands.ttf")
        self.ui = GameUI(font_path=font_path)

        # Create mock game objects for testing
        self.create_mock_objects()

        # Test scenarios
        self.scenarios = {
            "start": self.test_start_screen,
            "gameplay": self.test_gameplay_ui,
            "pause": self.test_pause_screen,
            "game_over_p1": self.test_game_over_player1_wins,
            "game_over_p2": self.test_game_over_player2_wins,
            "game_over_tie": self.test_game_over_tie,
            "game_over_both_dead": self.test_game_over_both_dead,
        }

        self.current_scenario = "start"
        self.running = True

    def create_mock_objects(self):
        """Create mock game objects for testing"""
        # Mock sprite manager
        sprite_manager = SpriteManager()

        # Mock players with test data
        self.player1 = Player("player1", 5, 5, {}, sprite_manager)
        self.player1.score = 150
        self.player1.health = 2

        self.player2 = AIPlayer("ai1", 10, 10, sprite_manager, "pellet_hunter")
        self.player2.score = 120
        self.player2.health = 3

        # Mock maze
        self.maze = Maze()

    def test_start_screen(self):
        self.ui.render_start_screen(self.screen)

    def test_gameplay_ui(self):
        self.screen.fill(BLACK)
        # Mock maze rendering (just draw a black background)
        self.ui.render_player_info(self.screen, self.player1, self.player2)
        self.ui.render_game_stats(self.screen, self.maze)
        self.ui.render_instructions(self.screen)

    def test_pause_screen(self):
        self.test_gameplay_ui()  # Draw game background first
        self.ui.render_pause_screen(self.screen)

    def test_game_over_player1_wins(self):
        self.player1.score = 200
        self.player2.score = 150
        self.test_gameplay_ui()
        winner = "Ena catch up to Mizuki then they... they...\nI will leave that to your imagination!"
        self.ui.render_game_over(self.screen, winner, self.player1.score, self.player2.score)

    def test_game_over_player2_wins(self):
        self.player1.score = 100
        self.player2.score = 180
        self.test_gameplay_ui()
        winner = "You know what! maybe it's not that bad at all!\nFor Mizuki to be top... The game i mean!!!"
        self.ui.render_game_over(self.screen, winner, self.player1.score, self.player2.score)

    def test_game_over_tie(self):
        self.player1.score = 150
        self.player2.score = 150
        self.test_gameplay_ui()
        winner = "This is kinda boring!\nBut well, it not necessarily that someone has to be top right... Right?"
        self.ui.render_game_over(self.screen, winner, self.player1.score, self.player2.score)

    def test_game_over_both_dead(self):
        self.player1.health = 0
        self.player2.health = 0
        self.test_gameplay_ui()
        winner = "Wacky Wacky Ducky Dinners!"
        self.ui.render_game_over(self.screen, winner, self.player1.score, self.player2.score)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_1:
                    self.current_scenario = "start"
                elif event.key == pygame.K_2:
                    self.current_scenario = "gameplay"
                elif event.key == pygame.K_3:
                    self.current_scenario = "pause"
                elif event.key == pygame.K_4:
                    self.current_scenario = "game_over_p1"
                elif event.key == pygame.K_5:
                    self.current_scenario = "game_over_p2"
                elif event.key == pygame.K_6:
                    self.current_scenario = "game_over_tie"
                elif event.key == pygame.K_7:
                    self.current_scenario = "game_over_both_dead"

    def render_instructions(self):
        """Show test instructions"""
        instructions = [
            "UI TESTER - Press keys to test different screens:",
            "1: Start Screen | 2: Gameplay UI | 3: Pause Screen",
            "4: Player 1 Wins | 5: Player 2 Wins | 6: Tie Game | 7: Both Dead",
            "ESC: Quit",
        ]

        y_start = 10
        font = pygame.font.Font(None, 24)

        for i, instruction in enumerate(instructions):
            color = YELLOW if i == 0 else WHITE
            text = font.render(instruction, True, color)
            self.screen.blit(text, (10, y_start + i * 25))

    def run(self):
        while self.running:
            self.handle_events()

            # Render current scenario
            if self.current_scenario in self.scenarios:
                self.scenarios[self.current_scenario]()

            # Show instructions on top
            self.render_instructions()

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    tester = UITester()
    tester.run()
