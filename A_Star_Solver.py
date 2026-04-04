import heapq
import time
import psutil
import os
from Freecell_Game import OPERATIONS

class AStarSolver:
    def __init__(self, game_state):
        self.game = game_state
        self.start_heaps = []
        for h in game_state.card_heaps:
            col = []
            for c in h.heap_list:
                v = getattr(c, 'num', 0)
                if v == 0 and hasattr(c, 'point'):
                    pts = {'A':1,'J':11,'Q':12,'K':13}
                    v = pts.get(str(c.point), int(c.point) if str(c.point).isdigit() else 0)
                # Lưu thông tin tối giản: giá trị, màu, và thuộc tính rb (đỏ/đen)
                rb = 'black' if c.color.lower() in ['spade', 'club'] else 'red'
                col.append({'num': v, 'color': c.color, 'rb': rb, 'point': str(c.point)})
            self.start_heaps.append(col)

    def _get_state_tuple(self, heaps):
        """Hàm băm tối ưu: Loại bỏ tính đối xứng để tăng tốc độ giải."""
        fnd = tuple(tuple((c['color'], c['num']) for c in h) for h in heaps[:4])
        f_cells = sorted([(c['color'], c['num']) for h in heaps[4:8] if h for c in h])
        tbl = sorted([tuple((c['color'], c['num']) for c in h) for h in heaps[8:16]])
        return (fnd, tuple(f_cells), tuple(tbl))

    def _check_move_internal(self, card, to_id, target_heap):
        # 1. Foundation (0-3)
        if 0 <= to_id <= 3:
            if not target_heap:
                return card['num'] == 1
            last = target_heap[-1]
            return card['color'] == last['color'] and card['num'] == last['num'] + 1
        
        # 2. FreeCell (4-7)
        if 4 <= to_id <= 7:
            return len(target_heap) == 0
        
        # 3. Tableau (8-15)
        if 8 <= to_id <= 15:
            if not target_heap:
                return True
            last = target_heap[-1]
            return card['rb'] != last['rb'] and card['num'] == last['num'] - 1
        return False

    def _heuristic(self, heaps):
        score = 0
        # Ưu tiên bài lên Foundation
        score -= sum(len(heaps[i]) for i in range(4)) * 150
        # Phạt khi dùng FreeCell
        for i in range(4, 8):
            if heaps[i]: score += 30
        # Phạt bài nhỏ bị kẹt sâu
        for i in range(8, 16):
            for idx, c in enumerate(heaps[i]):
                if c['num'] < 8: 
                    score += (len(heaps[i]) - 1 - idx) * 30
        return score

    def solve(self, max_nodes=100000, timeout=60, stop_event=None):
        process = psutil.Process(os.getpid())
        start_mem = process.memory_info().rss
        peak_mem = start_mem
        start_time = time.time()
        
        count = 0
        initial_hash = self._get_state_tuple(self.start_heaps)
        queue = [(self._heuristic(self.start_heaps), count, self.start_heaps, [], 0)]
        visited = {initial_hash: 0}
        expanded_nodes = 0

        while queue:
            if stop_event and stop_event.is_set():
                return {"solved": False, "error": "Stopped"}

            curr_mem = process.memory_info().rss
            if curr_mem > peak_mem: peak_mem = curr_mem

            if time.time() - start_time > timeout:
                return {"solved": False, "error": "Timeout"}

            f, _, current_heaps, path, g_score = heapq.heappop(queue)
            expanded_nodes += 1

            # Điều kiện thắng
            if sum(len(current_heaps[i]) for i in range(4)) == 52:
                actual_used_mb = (peak_mem - start_mem) / (1024 * 1024)
                return {
                    "solved": True, 
                    "solution": path, 
                    "search_length": len(path),
                    "expanded_nodes": expanded_nodes,
                    "search_time": time.time() - start_time,
                    "memory_used": round(actual_used_mb, 4)
                }

            if expanded_nodes > max_nodes:
                return {"solved": False, "error": "Max nodes reached"}

            # Tính toán tài nguyên trống để xác định max_allowed di chuyển
            empty_fc = sum(1 for i in range(4, 8) if not current_heaps[i])
            empty_tab = sum(1 for i in range(8, 16) if not current_heaps[i])

            for from_id, to_id in OPERATIONS:
                if not current_heaps[from_id]: continue
                
                is_target_empty_tab = (8 <= to_id <= 15 and not current_heaps[to_id])
                effective_empty_tab = empty_tab - 1 if is_target_empty_tab else empty_tab
                max_allowed = (1 + empty_fc) * (2 ** max(0, effective_empty_tab))

                # Chỉ bốc 1 lá nếu vào Foundation/FreeCell, hoặc bốc xấp bài nếu vào Tableau
                if to_id < 8:
                    search_range = [len(current_heaps[from_id]) - 1]
                else:
                    search_range = range(max(0, len(current_heaps[from_id]) - max_allowed), len(current_heaps[from_id]))

                for card_idx in search_range:
                    card = current_heaps[from_id][card_idx]
                    
                    if self._check_move_internal(card, to_id, current_heaps[to_id]):
                        new_heaps = [h[:] for h in current_heaps]
                        moving = new_heaps[from_id][card_idx:]
                        new_heaps[from_id] = new_heaps[from_id][:card_idx]
                        new_heaps[to_id].extend(moving)
                        
                        s_hash = self._get_state_tuple(new_heaps)
                        new_g = g_score + 1
                        
                        if s_hash not in visited or new_g < visited[s_hash]:
                            visited[s_hash] = new_g
                            count += 1
                            h_s = self._heuristic(new_heaps)
                            # Lưu path chuẩn để UI hiển thị sau khi giải xong
                            new_path = path + [(from_id, to_id, card_idx)]
                            heapq.heappush(queue, (new_g + (2.0 * h_s), count, new_heaps, new_path, new_g))

        return {"solved": False, "error": "No solution"}