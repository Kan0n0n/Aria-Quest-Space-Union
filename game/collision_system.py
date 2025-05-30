class CollisionSystem:
    def __init__(self):
        pass

    def check_ghost_collisions(self, players, ghosts):
        collision_results = []

        if not isinstance(ghosts, list):
            ghosts = [ghosts]

        for ghost in ghosts:
            if ghost.is_dead():
                continue

            ghost_pos = ghost.get_position()

            for player in players:
                if not player.is_dead():
                    if hasattr(player, 'ai_type'):  # This is an AI player
                        collision_result = player.check_ghost_collision(ghost_pos)
                    else:  # This is a regular player
                        collision_result = player.check_ghost_collision(ghost_pos)

                    if collision_result == "caught_ghost":
                        # Player caught the ghost while powered up
                        collision_results.append({'type': 'ghost_caught', 'player': player, 'ghost': ghost, 'ghost_pos': ghost_pos})
                    elif collision_result:
                        # Player took damage (collision_result is True)
                        collision_results.append(
                            {'type': 'player_damaged', 'player': player, 'ghost': ghost, 'ghost_pos': ghost_pos, 'player_died': player.is_dead()}
                        )
        return collision_results

    def handle_collision_results(self, collision_results):
        for result in collision_results:
            if result['type'] == 'ghost_caught':
                player = result['player']
                ghost = result['ghost']
                print(f"{player.player_id} caught a ghost! +200 points! Score: {player.score}")
                ghost.kill()

            elif result['type'] == 'player_damaged':
                player = result['player']
                ghost = result['ghost']
                print(f"{player.player_id} hit by ghost! Health: {player.health}")

                if result['player_died']:
                    print(f"{player.player_id} has died!")
                    self._handle_player_death(player)

    def _handle_player_death(self, player):
        print(f"Handling death for player {player.player_id}")
        # !NOTE: Add stuff later on maybe...
        # Reset player position, score, etc
