import pygame
import sys
import os

# Game components
from constants import *
from core.sprite_manager import SpriteManager
from core.maze import Maze
from core.intro import CinematicIntro
from ui.game_ui import GameUI
from core.music import OneShotMusicManager
from maze_layout import POSITIONS, MAZE_INFO  # Import position definitions

# Entities
from entities.player import Player
from entities.ai_player import AIPlayer
from entities.inky_ghost import InkyGhost

# Game handler
from game.game_state import GameState, GameStateManager
from game.input_handler import InputHandler
from game.collision_system import CollisionSystem


class PacmanGame:
    def __init__(self, music_file=None, volume=0.5, font_path=None):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Aria Quest: Space Union")
        self.clock = pygame.time.Clock()

        # Initialize systems
        self.state_manager = GameStateManager()
        self.input_handler = InputHandler()
        self.collision_system = CollisionSystem()

        # Initialize components
        self.sprite_manager = SpriteManager()
        self.sprite_manager.auto_load_from_assets()
        self.maze = Maze()
        self.ui = GameUI(font_path=font_path)
        self.music = self._initialize_music(music_file, volume)
        self.intro = CinematicIntro(SCREEN_WIDTH, SCREEN_HEIGHT)

        # Game state
        self.running = True
        self.music_started = False
        self.game_over_timer = 0

        # Initialize players
        self._initialize_players()

    def _initialize_music(self, music_file, volume):
        if music_file and os.path.exists(music_file):
            return OneShotMusicManager(music_file, volume=volume)
        else:
            # !NOTE: Set default music later
            default_file = os.path.join("music", "background.wav")
            return OneShotMusicManager(default_file, volume=volume)

    def _initialize_players(self):
        # Use defined positions from maze_layout
        player1_pos = POSITIONS['PLAYER1_START']
        player2_pos = POSITIONS['PLAYER2_START']
        ghost_pos = POSITIONS['INKY_GHOST_START']

        print(f"Initializing players at defined positions:")
        print(f"Player 1: {player1_pos}")
        print(f"Player 2: {player2_pos}")
        print(f"Ghost: {ghost_pos}")

        # Player 1
        self.player1 = Player(
            player_id="player1", start_x=player1_pos[0], start_y=player1_pos[1], key_mapping=PLAYER1_KEYS, sprite_manager=self.sprite_manager
        )

        # Player 2 (AI)
        self.player2 = AIPlayer(
            player_id="ai1", start_x=player2_pos[0], start_y=player2_pos[1], sprite_manager=self.sprite_manager, ai_type="smart_hunter"
        )

        # Inky Ghost
        self.inky_ghost = InkyGhost(player_id="inky", start_x=ghost_pos[0], start_y=ghost_pos[1], sprite_manager=self.sprite_manager)

        total_food = len(self.maze.pellets) + len(self.maze.power_pellets)
        self.inky_ghost.set_total_food_count(total_food)
        self.inky_ghost.set_target(self.player1.get_position(), self.player2.get_position())

    def handle_events(self):
        events = pygame.event.get()

        # Define callback functions for input handler
        callbacks = {
            "quit": lambda: setattr(self, 'running', False),
            "start_game": self._start_game,
            "pause_toggle": self._toggle_pause,
            "restart": self.restart_game,
            "music_toggle": self._toggle_music,
            "volume_up": self._volume_up,
            "volume_down": self._volume_down,
        }

        self.input_handler.handle_events(events, self.state_manager, callbacks)

        # Handle player input
        keys = pygame.key.get_pressed()
        self.input_handler.handle_player_input(keys, self.player1, self.state_manager)

    def _start_game(self):
        self.state_manager.change_state(GameState.PLAYING)
        self._start_music()

    def _toggle_pause(self):
        if self.state_manager.is_state(GameState.PLAYING):
            self.state_manager.change_state(GameState.PAUSED)
            self.music.stop_temporarily()
        elif self.state_manager.is_state(GameState.PAUSED):
            self.state_manager.change_state(GameState.PLAYING)
            self.music.resume()

    def _toggle_music(self):
        if self.music_started:
            self.music.stop()
            self.music_started = False
        else:
            self._start_music()

    def _volume_up(self):
        vol = self.music.sound.get_volume()
        self.music.set_volume(min(vol + 0.1, 1.0))

    def _volume_down(self):
        vol = self.music.sound.get_volume()
        self.music.set_volume(max(vol - 0.1, 0.0))

    def _start_music(self):
        if not self.music_started:
            self.music.start()
            self.music_started = True
            self.music.is_playing = True
            print("Music started.")

    def update(self):
        if not self.state_manager.is_state(GameState.PLAYING):
            if self.state_manager.is_state(GameState.GAME_OVER):
                self.game_over_timer += 1
                if self.music_started and self.music.is_playing:
                    self.music.stop()
                    self.music_started = False
                self.inky_ghost.can_chase = False
            return

        # Update players
        players = [self.player1, self.player2]
        for player in players:
            if not player.is_dead():
                if player == self.player1:
                    player.update(self.maze)
                else:
                    human_pos = self.player1.get_position() if not self.player1.is_dead() else None
                    ghost_pos = [self.inky_ghost.get_position()] if not self.inky_ghost.is_dead() else []
                    player.update(self.maze, human_pos, ghost_pos)

        # Update Inky Ghost
        alive_positions = [p.get_position() if not p.is_dead() else None for p in players]
        self.inky_ghost.update(self.maze, *alive_positions[:2])

        # Handle collisions
        collision_results = self.collision_system.check_ghost_collisions(players, self.inky_ghost)
        self.collision_system.handle_collision_results(collision_results)

        # Check win conditions
        self._check_win_conditions()

    def _check_win_conditions(self):
        if self.maze.all_pellets_collected():
            self.state_manager.change_state(GameState.GAME_OVER)
            return

        if self.player1.is_dead() and self.player2.is_dead():
            print("Both players died! Game Over!")
            self.state_manager.change_state(GameState.GAME_OVER)
            return

    def _render_gameplay(self):
        # Get game area for maze rendering
        game_area = self.ui.get_game_area()

        # Calculate maze dimensions using new layout
        maze_width = MAZE_INFO['width'] * CELL_SIZE
        maze_height = MAZE_INFO['height'] * CELL_SIZE

        # Calculate scaling to fit the maze in the game area
        scale_x = game_area['width'] / maze_width
        scale_y = game_area['height'] / maze_height
        scale = min(scale_x, scale_y, 1.0)  # Don't scale up, only down if needed

        # Calculate centered position for the maze
        scaled_width = int(maze_width * scale)
        scaled_height = int(maze_height * scale)
        maze_x = (game_area['width'] - scaled_width) // 2
        maze_y = (game_area['height'] - scaled_height) // 2

        # Create a surface for the entire game area
        game_surface = pygame.Surface((game_area['width'], game_area['height']))
        game_surface.fill(BLACK)  # Fill with black background

        # Create a surface for the maze at original size
        maze_surface = pygame.Surface((maze_width, maze_height))

        # Render maze on the maze surface
        self.maze.render(maze_surface)

        # Render players on the maze surface
        if not self.player1.is_dead():
            self.player1.render(maze_surface)
        if not self.player2.is_dead():
            self.player2.render(maze_surface, True)

        # Render ghost on the maze surface
        self.inky_ghost.render(maze_surface, self.maze, True)

        # Scale and center the maze surface if needed
        if scale < 1.0:
            scaled_maze_surface = pygame.transform.scale(maze_surface, (scaled_width, scaled_height))
            game_surface.blit(scaled_maze_surface, (maze_x, maze_y))
        else:
            game_surface.blit(maze_surface, (maze_x, maze_y))

        # Blit game surface to main screen at the correct position
        self.screen.blit(game_surface, (game_area['x'], game_area['y']))

        # FIXED: Always render UI bars for gameplay
        self.ui.render_gameplay_ui(self.screen, self.player1, self.player2, self.maze, "PLAYING")

    def render(self):
        self.screen.fill(BLACK)

        if self.state_manager.is_state(GameState.START):
            self.ui.render_start_screen(self.screen)
            # Show bottom bar on start screen too
            self.ui.bottom_bar.render(self.screen, "START")

        elif self.state_manager.current_state in [GameState.PLAYING, GameState.PAUSED]:
            self._render_gameplay()

            if self.state_manager.is_state(GameState.PAUSED):
                self.ui.render_pause_screen(self.screen)
                # FIXED: Update bottom bar for paused state
                self.ui.bottom_bar.render(self.screen, "PAUSED")

        elif self.state_manager.is_state(GameState.GAME_OVER):
            self._render_gameplay()
            winner = self._determine_winner()
            self.ui.render_game_over(self.screen, winner, self.player1.score, self.player2.score)
            # FIXED: Show bottom bar in game over state
            self.ui.bottom_bar.render(self.screen, "GAME_OVER")

        pygame.display.flip()

    def _determine_winner(self):
        if self.player1.is_dead() and self.player2.is_dead():
            return "Wacky Wacky Ducky Dinners!"
        elif self.player1.is_dead():
            return "All you have to do is wak wak Dza damn Ducky Ena!"
        elif self.player2.is_dead():
            return "Plus 1 student A!\nMizuki enters depression mode!"
        elif self.maze.all_pellets_collected():
            if self.player1.score > self.player2.score:
                return "Ena catch up to Mizuki then they... they...\nI will leave that to your imagination!"
            elif self.player1.score < self.player2.score:
                return "You know what! maybe it's not that bad at all!\nFor Mizuki to be top... The game i mean!!!"
            else:
                return "This is kinda boring!\nBut well, it not necessarily that someone has to be top right... Right?"
        return None

    def restart_game(self):
        self.music.stop()
        self.music_started = False

        self.maze = Maze()

        # Use defined positions for restart
        player1_pos = POSITIONS['PLAYER1_START']
        player2_pos = POSITIONS['PLAYER2_START']
        ghost_pos = POSITIONS['INKY_GHOST_START']

        # Reset Player 1
        self.player1.reset_position(player1_pos[0], player1_pos[1])
        self.player1.score = 0
        self.player1.health = 3
        self.player1.is_invincible = False
        self.player1.invincibility_timer = 0
        self.player1.invincibility_blink_timer = 0

        # Reset Player 2
        self.player2.reset_position(player2_pos[0], player2_pos[1])
        self.player2.score = 0
        self.player2.health = 3
        self.player2.is_invincible = False
        self.player2.invincibility_timer = 0
        self.player2.invincibility_blink_timer = 0

        # Reset Ghost
        self.inky_ghost.reset_position(ghost_pos[0], ghost_pos[1])
        self.inky_ghost.can_chase = True
        total_food = len(self.maze.pellets) + len(self.maze.power_pellets)
        self.inky_ghost.set_total_food_count(total_food)

        self.state_manager.change_state(GameState.PLAYING)
        self.game_over_timer = 0
        self._start_music()

    def run(self):
        # -- Intro scene --
        intro_done = False
        while not intro_done:
            dt = self.clock.tick(FPS) / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            self.intro.update()
            self.intro.render(self.screen)
            pygame.display.flip()
            intro_done = self.intro.is_complete()

        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(FPS)

        self.music.stop()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    music_file = os.path.join("music", "Control_wishes.mp3")
    font_path = os.path.join("fonts", "pixelFont-7-8x14-sproutLands.ttf")
    game = PacmanGame(music_file=music_file, volume=0.5, font_path=font_path)
    game.run()
