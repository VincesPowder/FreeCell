import heapq
import time
import psutil
import os
from Freecell_Game import OPERATIONS

class AStarSolver:
    def __init__(self, game_state):
        self.game = game_state
        # Lưu trạng thái bài ban đầu
        self.start_heaps = [h.heap_list[:] for h in game_state.card_heaps]

    def _get_state_tuple(self, heaps):
        # Tạo hash trạng thái để tránh duyệt lặp
        return tuple(tuple((c.color, getattr(c, 'point', getattr(c, 'num', 0))) for c in h) for h in heaps)

    def _heuristic(self, heaps):
        score = 0
        # 1. Ưu tiên bài lên Foundation (0-3)
        cards_in_foundation = sum(len(heaps[i]) for i in range(4))
        score -= cards_in_foundation * 150
        
        # 2. Phạt nếu dùng FreeCell (4-7)
        for i in range(4, 8):
            if len(heaps[i]) > 0:
                score += 30
        
        # 3. Phạt bài nhỏ bị kẹt sâu trong Tableau (8-15)
        for i in range(8, 16):
            column = heaps[i]
            for idx, card in enumerate(column):
                val = 0
                if hasattr(card, 'num'): 
                    val = card.num
                elif hasattr(card, 'point'): 
                    points = {'A':1,'2':2,'3':3,'4':4,'5':5,'6':6,'7':7,'8':8,'9':9,'10':10,'J':11,'Q':12,'K':13}
                    val = points.get(str(card.point), 10)
                
                if val < 8:
                    score += (len(column) - 1 - idx) * 30
        return score

    def solve(self, max_nodes=100000, timeout=60):
        # KHỞI TẠO ĐO RAM CHUẨN
        process = psutil.Process(os.getpid())
        start_mem = process.memory_info().rss
        peak_mem = start_mem # Theo dõi đỉnh để tránh số âm do Garbage Collection
        
        start_time = time.time()
        count = 0
        initial_f = self._heuristic(self.start_heaps)
        # Queue: (f_score, count, heaps, path, g_score)
        queue = [(initial_f, count, self.start_heaps, [], 0)]
        
        visited = {self._get_state_tuple(self.start_heaps): 0}
        expanded_nodes = 0

        while queue:
            # CẬP NHẬT PEAK MEMORY LIÊN TỤC
            curr_mem = process.memory_info().rss
            if curr_mem > peak_mem:
                peak_mem = curr_mem

            if time.time() - start_time > timeout:
                return {"solved": False, "error": "Timeout", "search_time": timeout}

            f, _, current_heaps, path, g_score = heapq.heappop(queue)
            expanded_nodes += 1

            # Kiểm tra điều kiện thắng
            if sum(len(current_heaps[i]) for i in range(4)) == 52:
                actual_used_mb = (peak_mem - start_mem) / (1024 * 1024)
                return {
                    "solved": True, 
                    "solution": path, 
                    "search_length": len(path),
                    "expanded_nodes": expanded_nodes,
                    "search_time": time.time() - start_time,
                    "memory_used": max(0.0, round(actual_used_mb, 4))
                }

            if expanded_nodes > max_nodes:
                return {"solved": False, "error": "Max nodes reached"}

            # TÍNH TOÁN TÀI NGUYÊN TRỐNG HIỆN TẠI
            empty_fc = sum(1 for i in range(4, 8) if not current_heaps[i])
            empty_tab = sum(1 for i in range(8, 16) if not current_heaps[i])

            for from_id, to_id in OPERATIONS:
                heap_from = current_heaps[from_id]
                if not heap_from: continue
                
                # CÔNG THỨC CHUẨN: Tính số lá tối đa có thể move cùng lúc
                # Nếu di chuyển vào cột Tableau trống, nó không được tính là 'cột trống' trong công thức
                is_target_empty_tab = (8 <= to_id <= 15 and not current_heaps[to_id])
                effective_empty_tab = empty_tab - 1 if is_target_empty_tab else empty_tab
                max_allowed = (1 + empty_fc) * (2 ** max(0, effective_empty_tab))

                # GIỚI HẠN RANGE QUÉT: Foundation/Freecell (0-7) chỉ nhận 1 lá
                if to_id < 8:
                    search_range = [len(heap_from) - 1]
                else:
                    # Chỉ quét trong phạm vi số lá luật cho phép di chuyển
                    start_idx = max(0, len(heap_from) - max_allowed)
                    search_range = range(start_idx, len(heap_from))

                for card_idx in search_range:
                    card = heap_from[card_idx]
                    target_logic = self.game.card_heaps[to_id]
                    
                    # Tạm thời gán list để CheckMoveInto
                    old_list = target_logic.heap_list
                    target_logic.heap_list = current_heaps[to_id]
                    
                    if target_logic.CheckMoveInto(card):
                        new_heaps = [h[:] for h in current_heaps]
                        moving_cards = new_heaps[from_id][card_idx:]
                        
                        # Kiểm tra xem chuỗi bài di chuyển có hợp lệ không (nếu là nhiều lá)
                        # Lưu ý: CheckMoveInto thường chỉ check lá đầu tiên của chuỗi
                        new_heaps[from_id] = new_heaps[from_id][:card_idx]
                        new_heaps[to_id].extend(moving_cards)
                        
                        state_hash = self._get_state_tuple(new_heaps)
                        new_g = g_score + 1
                        
                        if state_hash not in visited or new_g < visited[state_hash]:
                            visited[state_hash] = new_g
                            count += 1
                            h_score = self._heuristic(new_heaps)
                            new_path = path + [(from_id, to_id, card_idx)]
                            # Hệ số 2.0 giúp AI quyết đoán hơn để tránh Timeout
                            heapq.heappush(queue, (new_g + (2.0 * h_score), count, new_heaps, new_path, new_g))
                    
                    target_logic.heap_list = old_list

        return {"solved": False, "error": "No solution found"}