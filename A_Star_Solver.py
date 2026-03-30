"""
A* Solver for FreeCell Game
Implement A* Search algorithm with highly optimized Single-Object Delta Replay
"""

import time
import tracemalloc
import psutil
import os
import copy
from heapq import heappush, heappop
from Freecell_Game import FreeCellGame

class AStarSolver:
    """A* Solver for FreeCell Game"""
    
    def __init__(self, game_state, on_move_callback=None):
        self.initial_game_source = game_state
        self.visited_states = set()
        self.expanded_nodes = 0
        self.start_time = None
        self.end_time = None
        self.start_memory = None
        self.end_memory = None
        
    def _get_game_state_hash(self, game):
        # TỐI ƯU 1: Dùng Tuple Hash cực nhẹ thay vì String Formatting
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
                
            for to_id in range(16):
                if from_id == to_id:
                    continue
                    
                # Thu thập các bước đưa lên Foundation
                if 0 <= to_id <= 3:
                    if game.CheckMove(from_id, to_id):
                        foundation_moves.append((from_id, to_id))
                    continue
                    
                # LUẬT CẮT TỈA (PRUNING)
                if 4 <= from_id <= 7 and 4 <= to_id <= 7: continue
                if 8 <= from_id <= 15 and len(heap_from) == 1 and 8 <= to_id <= 15 and len(game.card_heaps[to_id].heap_list) == 0: continue
                if 4 <= to_id <= 7 and len(game.card_heaps[to_id].heap_list) == 0 and to_id != first_empty_fc: continue
                if 8 <= to_id <= 15 and len(game.card_heaps[to_id].heap_list) == 0 and to_id != first_empty_cas: continue
                
                if game.CheckMove(from_id, to_id):
                    valid_moves.append((from_id, to_id))
                    
        # TỐI ƯU 2: CHIẾN THUẬT GREEDY FOUNDATION
        # Nếu có bước cờ đẩy được lên nóc, CHỈ trả về bước đó để cắt bớt 99% nhánh vô nghĩa
        if foundation_moves:
            return foundation_moves
            
        return valid_moves
    
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
    
    def solve(self, max_nodes=100000, timeout=300):
        self.start_time = time.time()
        tracemalloc.start()
        process = psutil.Process(os.getpid())
        self.start_memory = process.memory_info().rss / (1024 ** 2)
        
        open_set = []
        counter = 0 
        
        # TỐI ƯU 3: SINGLE-OBJECT DELTA REPLAY
        # Dùng duy nhất 1 object trong suốt vòng đời duyệt, dẹp bỏ hoàn toàn việc Deepcopy!
        current_game = copy.deepcopy(self.initial_game_source)
        current_path = []
        
        initial_hash = self._get_game_state_hash(current_game)
        
        if self._check_win(current_game):
            self._finalize_metrics(process)
            return self._build_result(True, [], 1)
        
        h_initial = self._heuristic(current_game)
        heappush(open_set, (h_initial, counter, [], 0))
        counter += 1
        self.visited_states.add(initial_hash)
        
        while open_set and self.expanded_nodes < max_nodes:
            if time.time() - self.start_time > timeout:
                self._finalize_metrics(process)
                return self._build_result(False, [], self.expanded_nodes, 'Timeout exceeded')
            
            f_score, _, path, g_score = heappop(open_set)
            self.expanded_nodes += 1
            
            # TÁI TẠO TRẠNG THÁI BẰNG DIFF (UNDO/REDO)
            common_len = 0
            for m1, m2 in zip(current_path, path):
                if m1 == m2: common_len += 1
                else: break
                    
            # Undo các nước cờ dư thừa
            for move in reversed(current_path[common_len:]):
                current_game.Move(move[1], move[0]) # Đảo ngược to_id và from_id
                
            # Áp dụng các nước cờ mới
            for move in path[common_len:]:
                current_game.Move(move[0], move[1])
                
            current_path = path
            
            # Sinh nước đi mới
            valid_moves = self._get_valid_moves(current_game)
            
            for move in valid_moves:
                from_id, to_id = move
                
                # Tiến 1 bước
                current_game.Move(from_id, to_id)
                
                if self._check_win(current_game):
                    self._finalize_metrics(process)
                    return self._build_result(True, path + [move], self.expanded_nodes)
                
                next_hash = self._get_game_state_hash(current_game)
                if next_hash not in self.visited_states:
                    self.visited_states.add(next_hash)
                    
                    new_g_score = g_score + 1
                    h_score = self._heuristic(current_game)
                    f_new_score = new_g_score + (3.0 * h_score) # Trọng số A*
                    
                    heappush(open_set, (f_new_score, counter, path + [move], new_g_score))
                    counter += 1
                
                # Lùi 1 bước (Backtrack) để thử nước cờ khác cùng node
                current_game.Move(to_id, from_id)
        
        self._finalize_metrics(process)
        return self._build_result(False, [], self.expanded_nodes, 'No solution found within node limit')

    def _finalize_metrics(self, process):
        self.end_time = time.time()
        self.end_memory = process.memory_info().rss / (1024 ** 2)

    def _build_result(self, solved, solution, nodes, error=None):
        res = {
            'solved': solved,
            'solution': solution,
            'search_time': self.end_time - self.start_time if self.end_time else 0,
            'memory_used': self.end_memory - self.start_memory if self.end_memory else 0,
            'expanded_nodes': nodes,
            'search_length': len(solution)
        }
        if error: res['error'] = error
        return res