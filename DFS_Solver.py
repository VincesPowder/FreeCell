import time
import tracemalloc
import psutil
import os
import copy
from Freecell_Game import FreeCellGame

class IDSSolver:
    def __init__(self, game_state):
        self.initial_game_source = game_state
        self.expanded_nodes = 0
        self.start_time = None

    def _get_game_state_hash(self, game):
        return tuple((c.group_id, c.group_index) for c in game.CARDS)
    
    def _get_valid_moves(self, game):
        valid_moves = []
        foundation_moves = []

        first_empty_fc = -1
        for i in range(4, 8):
            if len(game.card_heaps[i].heap_list) == 0:
                first_empty_fc = i
                break

        first_empty_cas = -1
        for i in range(8, 16):
            if len(game.card_heaps[i].heap_list) == 0:
                first_empty_cas = i
                break

        for from_id in range(4, 16):
            heap_from = game.card_heaps[from_id].heap_list
            if len(heap_from) == 0:
                continue

            for to_id in range(16):
                if from_id == to_id:
                    continue

                # Ưu tiên foundation
                if 0 <= to_id <= 3:
                    if game.CheckMove(from_id, to_id):
                        foundation_moves.append((from_id, to_id))
                    continue

                if game.CheckMove(from_id, to_id):
                    valid_moves.append((from_id, to_id))

        if foundation_moves:
            return foundation_moves

        return valid_moves
    
    def _dfs_limited(self, depth_limit, timeout):
        stack = [(
            copy.deepcopy(self.initial_game_source),
            [],
            set()
        )]

        while stack:
            if time.time() - self.start_time > timeout:
                return {'solved': False}

            game, path, visited = stack.pop()
            self.expanded_nodes += 1

            # Check win
            if game.CheckWinStrict():
                return {
                    'solved': True,
                    'solution': path,
                    'expanded_nodes': self.expanded_nodes
                }

            if len(path) >= depth_limit:
                continue

            current_hash = self._get_game_state_hash(game)
            visited.add(current_hash)

            moves = self._get_valid_moves(game)

            for move in reversed(moves):
                new_game = copy.deepcopy(game)
                new_game.Move(move[0], move[1])

                next_hash = self._get_game_state_hash(new_game)

                if next_hash not in visited:
                    stack.append((
                        new_game,
                        path + [move],
                        visited.copy()
                    ))

        return {'solved': False}
    
    def solve(self, max_depth=1000, timeout=300):
        self.start_time = time.time()

        for depth_limit in range(1, max_depth + 1):
            print(f"[IDS] Trying depth = {depth_limit}")

            result = self._dfs_limited(depth_limit, timeout)

            if result['solved']:
                return result

            if time.time() - self.start_time > timeout:
                break

        return {
            'solved': False,
            'solution': [],
            'expanded_nodes': self.expanded_nodes,
            'error': 'Not found (IDS)'
        }