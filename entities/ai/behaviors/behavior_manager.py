from .reflex_agent import ReflexAgentBehavior
from .smart_hunter import SmartHunterBehavior
from .competitive import CompetitiveBehavior
from .simple import SimpleBFSBehavior, SimpleDFSBehavior, SimpleUCSBehavior, SimpleAStarBehavior


class BehaviorManager:
    def __init__(self, ai_player):
        self.ai_player = ai_player
        self.behaviors = {
            "reflex_agent": ReflexAgentBehavior(ai_player),
            "smart_hunter": SmartHunterBehavior(ai_player),
            "competitive": CompetitiveBehavior(ai_player),
            "simple_bfs": SimpleBFSBehavior(ai_player),
            "simple_dfs": SimpleDFSBehavior(ai_player),
            "simple_ucs": SimpleUCSBehavior(ai_player),
            "simple_astar": SimpleAStarBehavior(ai_player),
        }

    def execute_behavior(self, maze, situation):
        """Execute the appropriate AI behavior"""
        behavior_type = self.ai_player.ai_state.ai_type
        behavior = self.behaviors.get(behavior_type, self.behaviors["simple_bfs"])
        behavior.execute(maze, situation)
