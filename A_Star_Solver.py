import heapq
import time
import psutil
import os
from Freecell_Game import OPERATIONS

class AStarSolver:
    def __init__(self, game_state):
        self.game = game_state
        # Lưu trạng thái bài ban đầu dưới dạng list đơn giản
        self.start_heaps = [h.heap_list[:] for h in game_state.card_heaps]

    def _get_state_tuple(self, heaps):
        # Tạo hash duy nhất để nhận diện trạng thái (tránh lặp lại)
        return tuple(tuple((c.color, getattr(c, 'point', getattr(c, 'num', 0))) for c in h) for h in heaps)

    def _heuristic(self, heaps):
        score = 0
        # 1. Ưu tiên bài lên Foundation (0-3) - Tăng giá trị ưu tiên
        cards_in_foundation = sum(len(heaps[i]) for i in range(4))
        score -= cards_in_foundation * 150
        
        # 2. Phạt nếu dùng FreeCell (4-7) - giữ FreeCell trống càng tốt
        for i in range(4, 8):
            if len(heaps[i]) > 0:
                score += 30
        
        # 3. Phạt bài bị kẹt trong Tableau (8-15)
        for i in range(8, 16):
            column = heaps[i]
            for idx, card in enumerate(column):
                val = 0
                if hasattr(card, 'num'): 
                    val = card.num
                elif hasattr(card, 'point'): 
                    points = {'A':1,'2':2,'3':3,'4':4,'5':5,'6':6,'7':7,'8':8,'9':9,'10':10,'J':11,'Q':12,'K':13}
                    val = points.get(str(card.point), 10)
                
                if val < 8: # Các quân bài chiến lược cần được giải phóng
                    score += (len(column) - 1 - idx) * 30
        return score

    def solve(self, max_nodes=100000, timeout=60):
        process = psutil.Process(os.getpid())
        start_mem = process.memory_info().rss
        start_time = time.time()
        
        count = 0
        initial_f = self._heuristic(self.start_heaps)
        queue = [(initial_f, count, self.start_heaps, [], 0)]
        
        visited = {self._get_state_tuple(self.start_heaps): 0}
        expanded_nodes = 0

        while queue:
            if time.time() - start_time > timeout:
                return {"solved": False, "error": "Timeout", "search_time": timeout}

            f, _, current_heaps, path, g_score = heapq.heappop(queue)
            expanded_nodes += 1

            # Kiểm tra điều kiện thắng (52 lá trên Foundation)
            if sum(len(current_heaps[i]) for i in range(4)) == 52:
                end_mem = process.memory_info().rss
                actual_used_mb = abs(end_mem - start_mem) / (1024 * 1024)

                return {
                    "solved": True, 
                    "solution": path, 
                    "search_length": len(path),
                    "expanded_nodes": expanded_nodes,
                    "search_time": time.time() - start_time,
                    "memory_used": round(actual_used_mb, 2)
                }

            if expanded_nodes > max_nodes:
                return {"solved": False, "error": "Max nodes reached"}

            # Sắp xếp nước đi để ưu tiên Foundation
            valid_moves = []
            for come_idx, to_idx in OPERATIONS:
                if not current_heaps[come_idx]:
                    continue
                
                card = current_heaps[come_idx][-1]
                target_logic = self.game.card_heaps[to_idx]
                
                old_list = target_logic.heap_list
                target_logic.heap_list = current_heaps[to_idx]
                
                if target_logic.CheckMoveInto(card):
                    # Nếu lên Foundation, đưa lên đầu danh sách xét trước
                    if 0 <= to_idx <= 3:
                        valid_moves.insert(0, (come_idx, to_idx))
                    else:
                        valid_moves.append((come_idx, to_idx))
                
                target_logic.heap_list = old_list

            # Duyệt các nước đi đã được ưu tiên
            for come_idx, to_idx in valid_moves:
                new_heaps = [h[:] for h in current_heaps]
                moving_card = new_heaps[come_idx].pop()
                new_heaps[to_idx].append(moving_card)
                
                state_hash = self._get_state_tuple(new_heaps)
                new_g = g_score + 1
                
                if state_hash not in visited or new_g < visited[state_hash]:
                    visited[state_hash] = new_g
                    count += 1
                    h_score = self._heuristic(new_heaps)
                    
                    new_path = path + [(come_idx, to_idx, len(current_heaps[come_idx])-1)]
                    
                    heapq.heappush(queue, (new_g + (2.0 * h_score), count, new_heaps, new_path, new_g))

        return {"solved": False, "error": "No solution found"}