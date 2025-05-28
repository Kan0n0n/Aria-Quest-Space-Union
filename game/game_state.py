from enum import Enum


class GameState(Enum):
    START = "START"
    PLAYING = "PLAYING"
    PAUSED = "PAUSED"
    GAME_OVER = "GAME_OVER"


class GameStateManager:
    def __init__(self):
        self.current_state = GameState.START
        self.previous_state = None
        self.state_data = {}

    def change_state(self, new_state, **data):
        self.previous_state = self.current_state
        self.current_state = new_state
        self.state_data.update(data)

    def is_state(self, state):
        return self.current_state == state

    def can_transition_to(self, target_state):
        # Define valid transitions
        valid_transitions = {
            GameState.START: [GameState.PLAYING],
            GameState.PLAYING: [GameState.PAUSED, GameState.GAME_OVER],
            GameState.PAUSED: [GameState.PLAYING, GameState.GAME_OVER],
            GameState.GAME_OVER: [GameState.PLAYING, GameState.START],
        }
        return target_state in valid_transitions.get(self.current_state, [])
