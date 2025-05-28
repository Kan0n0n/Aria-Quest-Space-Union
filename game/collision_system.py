class CollisionSystem:
    def __init__(self):
        pass

    def check_ghost_collisions(self, players, ghost):
        ghost_pos = ghost.get_position()
        collision_results = []

        for player in players:
            if not player.is_dead() and player.check_collision_with_ghost(ghost_pos):
                collision_results.append({'player': player, 'ghost_pos': ghost_pos, 'player_died': player.is_dead()})

        return collision_results

    def handle_collision_results(self, collision_results):
        for result in collision_results:
            player = result['player']
            print(f"{player.player_id} hit by ghost! Health: {player.health}")

            if result['player_died']:
                print(f"{player.player_id} has died!")
                self._handle_player_death(player)

    def _handle_player_death(self, player):
        print(f"Handling death for player {player.player_id}")
        # !NOTE: Add stuff later on maybe...
