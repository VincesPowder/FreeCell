import time
import tracemalloc
import copy
from heapq import heappush, heappop
from Freecell_Game import FreeCellGame

class AStarSolver:
    def __init__(self, game_state, on_move_callback=None):
        self.initial_game_source = game_state
        self.visited_states = set()
        self.expanded_nodes = 0
        self.start_time = None
        self.end_time = None
        self.start_memory = None
        self.end_memory = None
        
    def _get_game_state_hash(self, game):
        return tuple((c.group_id, c.group_index) for c in game.CARDS)
    
    def _check_win(self, game):
        return game.CheckWinStrict()
    
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
                
            start_indices = range(len(heap_from)) if from_id >= 8 else [len(heap_from) - 1]
            
            for card_idx in start_indices:
                num_cards = len(heap_from) - card_idx
                for to_id in range(16):
                    if from_id == to_id: continue
                    
                    if 4 <= from_id <= 7 and 4 <= to_id <= 7: continue
                    if 8 <= from_id <= 15 and num_cards == 1 and 8 <= to_id <= 15 and len(game.card_heaps[to_id].heap_list) == 0: continue
                    if 4 <= to_id <= 7 and len(game.card_heaps[to_id].heap_list) == 0 and to_id != first_empty_fc: continue
                    if 8 <= to_id <= 15 and len(game.card_heaps[to_id].heap_list) == 0 and to_id != first_empty_cas: continue
                    
                    can_move, _ = game.CheckMoveSequence(from_id, to_id, card_idx)
                    if can_move:
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
        for i, card in enumerate(game.card_heaps[to_id].heap_list):
            card.group_id = to_id
            card.group_index = i
            
    def _undo_move(self, game, move):
        from_id, to_id, card_idx, num_cards = move
        cards_to_undo = game.card_heaps[to_id].heap_list[-num_cards:]
        game.card_heaps[to_id].heap_list = game.card_heaps[to_id].heap_list[:-num_cards]
        game.card_heaps[from_id].heap_list.extend(cards_to_undo)
        for i, card in enumerate(game.card_heaps[from_id].heap_list):
            card.group_id = from_id
            card.group_index = i

    def _heuristic(self, game):
        h = 0
        cards_in_foundation = sum(len(game.card_heaps[i].heap_list) for i in range(4))
        h += (52 - cards_in_foundation) * 10
        
        for i in range(8, 16):
            heap = game.card_heaps[i].heap_list
            for j, card in enumerate(heap):
                depth = len(heap) - j - 1
                if depth > 0:
                    h += depth * 2
                    
        empty_free_cells = sum(1 for i in range(4, 8) if not game.card_heaps[i].heap_list)
        empty_cascades = sum(1 for i in range(8, 16) if not game.card_heaps[i].heap_list)
        h -= empty_free_cells * 5
        h -= empty_cascades * 10
        
        return max(h, 0)
    
    def solve(self, max_nodes=100000, timeout=60):
        self.start_time = time.time()
        tracemalloc.start()
        
        open_set = []
        counter = 0 
        
        current_game = copy.deepcopy(self.initial_game_source)
        current_path = []
        
        initial_hash = self._get_game_state_hash(current_game)
        
        if self._check_win(current_game):
            return self._build_result(True, [])
        
        h_initial = self._heuristic(current_game)
        heappush(open_set, (h_initial, counter, [], 0))
        counter += 1
        self.visited_states.add(initial_hash)
        
        while open_set and self.expanded_nodes < max_nodes:
            if time.time() - self.start_time > timeout:
                return self._build_result(False, [], 'Timeout exceeded')
            
            f_score, _, path, g_score = heappop(open_set)
            self.expanded_nodes += 1
            
            # Khôi phục trạng thái
            common_len = 0
            for m1, m2 in zip(current_path, path):
                if m1 == m2: common_len += 1
                else: break
                    
            for move in reversed(current_path[common_len:]):
                self._undo_move(current_game, move)
                
            for move in path[common_len:]:
                self._apply_move(current_game, move)
                
            current_path = path
            
            valid_moves = self._get_valid_moves(current_game)
            
            for move in valid_moves:
                self._apply_move(current_game, move)
                
                if self._check_win(current_game):
                    final_path = path + [move]
                    return self._build_result(True, final_path)
                
                next_hash = self._get_game_state_hash(current_game)
                if next_hash not in self.visited_states:
                    self.visited_states.add(next_hash)
                    
                    new_g_score = g_score + 1
                    h_score = self._heuristic(current_game)
                    f_new_score = new_g_score + (3.0 * h_score) 
                    
                    heappush(open_set, (f_new_score, counter, path + [move], new_g_score))
                    counter += 1
                
                self._undo_move(current_game, move)
        
        return self._build_result(False, [], 'No solution found within node limit')

    def _build_result(self, solved, solution, error=None):
        self.end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        self.end_memory = peak / (1024 ** 2)
        
        # Trả về đúng 3 giá trị (from, to, index) để main.py không bị lỗi unpack
        formatted_solution = [(m[0], m[1], m[2]) for m in solution]

        res = {
            'solved': solved,
            'solution': formatted_solution,
            'search_time': self.end_time - self.start_time if self.end_time else 0,
            'memory_used': self.end_memory if self.end_memory else 0,
            'expanded_nodes': self.expanded_nodes,
            'search_length': len(formatted_solution)
        }
        if error: res['error'] = error
        return res