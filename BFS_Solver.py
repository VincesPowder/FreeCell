import copy
import time
import tracemalloc
from collections import deque
from Freecell_Game import FreeCellGame

class BFSSolver:
    def __init__(self, game_state, on_move_callback=None):
        self.initial_game = copy.deepcopy(game_state)
        self.visited_states = set() 
        self.solutions = [] 
        self.expanded_nodes = 0
        self.start_time = None
        self.end_time = None
        self.start_memory = None
        self.end_memory = None
        self.search_length = 0
        self.on_move_callback = on_move_callback
        
    def _get_game_state_hash(self, game_or_res):
        if hasattr(game_or_res, "CARDS"):
            return tuple((c.group_id, c.group_index) for c in game_or_res.CARDS)

        res = game_or_res
        parts = []
        for i in range(0, len(res), 2):
            parts.append("%02d%02d" % (int(res[i]), int(res[i + 1])))
        return "".join(parts)
    
    def _check_win(self, game):
        return game.CheckWinStrict()
        
    def _get_valid_moves(self, game):
        valid_moves = []
        foundation_moves = []

        for from_id in range(4, 16): 
            heap_from = game.card_heaps[from_id].heap_list
            if len(heap_from) == 0:
                continue
                
            # FreeCell chỉ bốc 1 lá, Cascade bốc được chuỗi
            start_indices = range(len(heap_from)) if from_id >= 8 else [len(heap_from) - 1]
            
            for card_idx in start_indices:
                num_cards = len(heap_from) - card_idx
                for to_id in range(16):
                    if from_id == to_id:
                        continue
                        
                    if 4 <= from_id <= 7 and 4 <= to_id <= 7: 
                        continue
                        
                    can_move, _ = game.CheckMoveSequence(from_id, to_id, card_idx)
                    if can_move:
                        # Lưu thêm num_cards để tiện lợi cho việc apply move
                        move = (from_id, to_id, card_idx, num_cards)
                        if 0 <= to_id <= 3:
                            foundation_moves.append(move)
                        else:
                            valid_moves.append(move)
                            
        if foundation_moves:
            return foundation_moves
        return valid_moves

    def _apply_move(self, game, move):
        from_id, to_id, card_idx, num_cards = move
        cards_to_move = game.card_heaps[from_id].heap_list[-num_cards:]
        game.card_heaps[from_id].heap_list = game.card_heaps[from_id].heap_list[:-num_cards]
        game.card_heaps[to_id].heap_list.extend(cards_to_move)
        
        # Cập nhật group_id và group_index cho UI
        for i, card in enumerate(game.card_heaps[to_id].heap_list):
            card.group_id = to_id
            card.group_index = i

    def solve(self, max_nodes=100000, timeout=180):
        self.start_time = time.time()
        tracemalloc.start()
        
        queue = deque()
        current_game = copy.deepcopy(self.initial_game)
        
        if self._check_win(current_game):
            return self._finalize(True, [])

        initial_hash = self._get_game_state_hash(current_game)
        queue.append((current_game, []))
        self.visited_states.add(initial_hash)
        
        while queue and self.expanded_nodes < max_nodes:
            if time.time() - self.start_time > timeout:
                return self._finalize(False, [], 'Timeout exceeded')
            
            current_game, path = queue.popleft()
            self.expanded_nodes += 1

            for move in self._get_valid_moves(current_game):
                next_game = copy.deepcopy(current_game)
                self._apply_move(next_game, move)

                if self._check_win(next_game):
                    return self._finalize(True, path + [move])

                next_hash = self._get_game_state_hash(next_game)
                if next_hash not in self.visited_states:
                    self.visited_states.add(next_hash)
                    queue.append((next_game, path + [move]))
        
        return self._finalize(False, [], 'No solution found within node limit')

    def _finalize(self, solved, solution, error=None):
        self.end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Trả về đúng 3 giá trị (from, to, index) để main.py không bị lỗi unpack
        formatted_solution = [(m[0], m[1], m[2]) for m in solution]
        
        res = {
            'solved': solved,
            'solution': formatted_solution,
            'search_time': self.end_time - self.start_time,
            'memory_used': peak / (1024 ** 2),
            'expanded_nodes': self.expanded_nodes,
            'search_length': len(formatted_solution)
        }
        if error:
            res['error'] = error
        return res