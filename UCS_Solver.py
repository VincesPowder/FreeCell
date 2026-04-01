import time
import psutil
import os
import copy
from heapq import heappush, heappop

class UCSSolver:
    """
    UCS Solver cho FreeCell tuân thủ lý thuyết Global Search Strategies.
    Sử dụng hàm đánh giá f(n) = g(n).
    Áp dụng Late Goal Test: kiểm tra đích khi mở rộng nút.
    """
    
    def __init__(self, game_state):
        self.initial_game_source = game_state
        self.visited_states = set()
        self.expanded_nodes = 0
        self.start_time = None
        self.end_time = None
        self.start_memory = None
        self.end_memory = None
        
    def _get_game_state_hash(self, game):
        """Tạo mã hash đại diện cho trạng thái bàn cờ."""
        return tuple((c.group_id, c.group_index) for c in game.CARDS)
    
    def _get_valid_moves(self, game):
        """
        Lấy danh sách các nước đi hợp lệ (di chuyển cả chuỗi bài).
        Trả về format: (from_id, to_id, card_idx, num_cards)
        """
        valid_moves = []
        foundation_moves = []
        
        for from_id in range(4, 16): 
            heap_from = game.card_heaps[from_id].heap_list
            if not heap_from: continue
            
            # Chỉ bốc 1 lá nếu là FreeCell (4-7), bốc cả chuỗi nếu là Cascade (8-15)
            start_indices = range(len(heap_from)) if from_id >= 8 else [len(heap_from) - 1]
            
            for card_idx in start_indices:
                num_cards = len(heap_from) - card_idx
                for to_id in range(16):
                    if from_id == to_id: continue
                    
                    can_move, _ = game.CheckMoveSequence(from_id, to_id, card_idx)
                    if can_move:
                        move = (from_id, to_id, card_idx, num_cards)
                        if 0 <= to_id <= 3: # Ưu tiên nước đi lên Foundation
                            foundation_moves.append(move)
                        else:
                            valid_moves.append(move)
                            
        return foundation_moves if foundation_moves else valid_moves
    
    def _apply_move(self, game, move):
        """Thực hiện nước đi trên trạng thái game hiện tại."""
        from_id, to_id, _, num_cards = move
        cards_to_move = game.card_heaps[from_id].heap_list[-num_cards:]
        game.card_heaps[from_id].heap_list = game.card_heaps[from_id].heap_list[:-num_cards]
        game.card_heaps[to_id].heap_list.extend(cards_to_move)
        for i, card in enumerate(game.card_heaps[to_id].heap_list):
            card.group_id, card.group_index = to_id, i

    def _undo_move(self, game, move):
        """Hoàn tác nước đi để quay lại trạng thái trước đó."""
        from_id, to_id, _, num_cards = move
        cards_to_undo = game.card_heaps[to_id].heap_list[-num_cards:]
        game.card_heaps[to_id].heap_list = game.card_heaps[to_id].heap_list[:-num_cards]
        game.card_heaps[from_id].heap_list.extend(cards_to_undo)
        for i, card in enumerate(game.card_heaps[from_id].heap_list):
            card.group_id, card.group_index = from_id, i

    def solve(self, max_nodes=500000, timeout=450):
        """
        Thực hiện giải thuật Uniform-Cost Search.
        """
        self.start_time = time.time()
        process = psutil.Process(os.getpid())
        self.start_memory = process.memory_info().rss / (1024 ** 2)
        
        # Priority Queue lưu: (path_cost, counter, path)
        open_set = []
        counter = 0 
        
        current_game = copy.deepcopy(self.initial_game_source)
        current_path = []
        
        initial_hash = self._get_game_state_hash(current_game)
        
        # Đưa nút gốc vào Frontier
        heappush(open_set, (0, counter, []))
        counter += 1
        self.visited_states.add(initial_hash)
        
        while open_set and self.expanded_nodes < max_nodes:
            if time.time() - self.start_time > timeout:
                self._finalize_metrics(process)
                return self._build_result(False, [], "Timeout exceeded")
            
            # 1. Lấy nút có g(n) thấp nhất từ Frontier (Expansion)
            g_score, _, path = heappop(open_set)
            self.expanded_nodes += 1
            
            # --- Đưa trạng thái game về đúng node đang xét (Delta Replay) ---
            common_len = 0
            for m1, m2 in zip(current_path, path):
                if m1 == m2: common_len += 1
                else: break
            for move in reversed(current_path[common_len:]): self._undo_move(current_game, move)
            for move in path[common_len:]: self._apply_move(current_game, move)
            current_path = path
            
            # 2. LATE GOAL TEST: Kiểm tra đích khi nút được lấy ra khỏi PQ
            if current_game.CheckWinStrict():
                self._finalize_metrics(process)
                return self._build_result(True, path)

            # 3. Tạo các nút con và thêm vào Frontier (Generation)
            for move in self._get_valid_moves(current_game):
                self._apply_move(current_game, move)
                
                next_hash = self._get_game_state_hash(current_game)
                if next_hash not in self.visited_states:
                    self.visited_states.add(next_hash)
                    
                    # UCS: Chi phí tích lũy g(n)
                    # Ở đây mỗi bước đi có cost = 1
                    heappush(open_set, (g_score + 1, counter, path + [move]))
                    counter += 1
                
                self._undo_move(current_game, move)
        
        self._finalize_metrics(process)
        return self._build_result(False, [], "No solution found or node limit reached")

    def _finalize_metrics(self, process):
        self.end_time = time.time()
        self.end_memory = process.memory_info().rss / (1024 ** 2)

    def _build_result(self, solved, solution, error=None):
        # Format lại solution để UI chính (main.py) có thể chạy animation
        formatted_sol = [(m[0], m[1], m[2]) for m in solution]
        
        return {
            'solved': solved,
            'solution': formatted_sol,
            'search_time': self.end_time - self.start_time if self.end_time else 0,
            'memory_used': max(0, self.end_memory - self.start_memory) if self.end_memory else 0,
            'expanded_nodes': self.expanded_nodes,
            'search_length': len(formatted_sol),
            'error': error
        }