import pygame
from game.game_state import GameState


class InputHandler:
    def __init__(self):
        self.key_actions = {
            pygame.K_ESCAPE: "quit",
            pygame.K_SPACE: "start_game",
            pygame.K_p: "pause_toggle",
            pygame.K_r: "restart",
            pygame.K_m: "music_toggle",
            pygame.K_EQUALS: "volume_up",
            pygame.K_PLUS: "volume_up",
            pygame.K_MINUS: "volume_down",
            # Add test and algorithm keys
            pygame.K_F1: "test_ghost_flee",
            pygame.K_F2: "test_ghost_hunt",
            pygame.K_F3: "test_ai_hunt",
            pygame.K_F4: "power_player2",
            pygame.K_F5: "reset_positions",
            pygame.K_F6: "toggle_debug",
            pygame.K_F7: "toggle_hide_player1",
            pygame.K_F8: "toggle_hide_ghosts",
            pygame.K_F9: "next_algorithm",
            pygame.K_F10: "prev_algorithm",
            pygame.K_F11: "run_benchmark",
            pygame.K_F12: "save_results",
        }

    def handle_events(self, events, state_manager, callbacks):
        for event in events:
            if event.type == pygame.QUIT:
                return callbacks.get("quit", lambda: None)()

            elif event.type == pygame.KEYDOWN:
                action = self.key_actions.get(event.key)

                if action and action in callbacks:
                    callbacks[action]()

    def handle_player_input(self, keys, player, state_manager):
        """Handle continuous key presses for player movement"""
        if state_manager.is_state(GameState.PLAYING) and not player.is_dead():
            player.handle_input(keys)
