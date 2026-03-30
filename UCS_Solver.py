import time
import psutil
import os
import copy
from heapq import heappush, heappop
from Freecell_Game import FreeCellGame

class UCSSolver:
    """UCS Solver cho game FreeCell - Tìm lời giải ngắn nhất bằng chi phí g(n)"""
    
    def __init__(self, game_state):
        # Lưu lại trạng thái gốc để bắt đầu tìm kiếm
        self.initial_game_source = game_state
        self.visited_states = set()
        self.expanded_nodes = 0
        self.start_time = None
        self.end_time = None
        self.start_memory = None
        self.end_memory = None
        
    def _get_game_state_hash(self, game):
        """Tạo mã hash từ vị trí các lá bài để nhận diện trạng thái lặp [cite: 95]"""
        return tuple((c.group_id, c.group_index) for c in game.CARDS)
    
    def _get_valid_moves(self, game):
        """Lấy danh sách các nước đi hợp lệ từ class FreeCellGame [cite: 52]"""
        return game.ValidOprts()
    
    def solve(self, max_nodes=500000, timeout=450):
        """
        Thực hiện tìm kiếm Uniform-Cost Search.
        max_nodes: Giới hạn số node để tránh tràn RAM[cite: 129].
        timeout: Thời gian tối đa cho phép chạy (giây).
        """
        # Ghi nhận thông số bắt đầu [cite: 85, 127]
        self.start_time = time.time()
        process = psutil.Process(os.getpid())
        self.start_memory = process.memory_info().rss / (1024 ** 2)
        
        # Priority Queue lưu: (g_score, counter, path)
        # Trong UCS, độ ưu tiên duy nhất là g(n) [cite: 98]
        open_set = []
        counter = 0 
        
        # Sử dụng kỹ thuật Delta Replay (giống file A* của bạn) để tối ưu tốc độ
        current_game = copy.deepcopy(self.initial_game_source)
        current_path = []
        
        initial_hash = self._get_game_state_hash(current_game)
        
        # Kiểm tra nếu ván bài đã thắng ngay từ đầu [cite: 63, 64]
        if current_game.CheckWinStrict():
            self._finalize_metrics(process)
            return self._build_result(True, [], 1)
        
        # Push node gốc vào hàng đợi: (cost=0, counter, path=[])
        heappush(open_set, (0, counter, []))
        counter += 1
        self.visited_states.add(initial_hash)
        
        while open_set and self.expanded_nodes < max_nodes:
            # Kiểm tra giới hạn thời gian
            if time.time() - self.start_time > timeout:
                self._finalize_metrics(process)
                return self._build_result(False, [], self.expanded_nodes, 'Timeout exceeded')
            
            # Lấy node có g(n) thấp nhất ra khỏi hàng đợi [cite: 98]
            g_score, _, path = heappop(open_set)
            self.expanded_nodes += 1
            
            # --- DELTA REPLAY: Đưa trạng thái game về đúng node đang xét ---
            common_len = 0
            for m1, m2 in zip(current_path, path):
                if m1 == m2: common_len += 1
                else: break
            # Undo các nước cờ cũ
            for move in reversed(current_path[common_len:]):
                current_game.Move(move[1], move[0]) 
            # Áp dụng các nước cờ của node hiện tại
            for move in path[common_len:]:
                current_game.Move(move[0], move[1])
            current_path = path
            # -----------------------------------------------------------

            # Lấy các nước đi hợp lệ
            valid_moves = self._get_valid_moves(current_game)
            
            for move in valid_moves:
                from_id, to_id = move
                
                # Thử thực hiện nước đi
                current_game.Move(from_id, to_id)
                
                # Kiểm tra trạng thái đích [cite: 63, 64]
                if current_game.CheckWinStrict():
                    self._finalize_metrics(process)
                    return self._build_result(True, path + [move], self.expanded_nodes)
                
                # Kiểm tra trạng thái lặp
                next_hash = self._get_game_state_hash(current_game)
                if next_hash not in self.visited_states:
                    self.visited_states.add(next_hash)
                    
                    # Trong UCS, cost mỗi bước là 1 
                    new_g_score = g_score + 1
                    heappush(open_set, (new_g_score, counter, path + [move]))
                    counter += 1
                
                # Backtrack: Trả lại trạng thái cũ để thử nước đi khác cùng node
                current_game.Move(to_id, from_id)
        
        self._finalize_metrics(process)
        return self._build_result(False, [], self.expanded_nodes, 'No solution found')

    def _finalize_metrics(self, process):
        self.end_time = time.time()
        self.end_memory = process.memory_info().rss / (1024 ** 2)

    def _build_result(self, solved, solution, nodes, error=None):
        """Đóng gói kết quả cho báo cáo [cite: 133]"""
        res = {
            'solved': solved,
            'solution': solution,
            'search_time': self.end_time - self.start_time if self.end_time else 0,
            'memory_used': max(0, self.end_memory - self.start_memory) if self.end_memory else 0,
            'expanded_nodes': nodes,
            'search_length': len(solution)
        }
        if error: res['error'] = error
        return res