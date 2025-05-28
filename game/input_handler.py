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
        }

    def handle_events(self, events, state_manager, callbacks):
        for event in events:
            if event.type == pygame.QUIT:
                return callbacks.get("quit", lambda: None)()

            elif event.type == pygame.KEYDOWN:
                action = self.key_actions.get(event.key)

                if action == "quit":
                    return callbacks.get("quit", lambda: None)()

                elif action == "start_game":
                    callbacks.get("start_game", lambda: None)()

                elif action == "pause_toggle":
                    callbacks.get("pause_toggle", lambda: None)()

                elif action == "restart":
                    callbacks.get("restart", lambda: None)()

                elif action in ["music_toggle", "volume_up", "volume_down"]:
                    callbacks.get(action, lambda: None)()

    def handle_player_input(self, keys, player, state_manager):
        if state_manager.is_state(GameState.PLAYING) and not player.is_dead():
            player.handle_input(keys)
