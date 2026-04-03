import time
import tracemalloc
import psutil
import os
import copy

class IDSSolver:
    def __init__(self, game_state):
        self.initial_game_source = game_state
        self.expanded_nodes = 0
        self.start_time = None
        self.start_memory = None

    def _get_game_state_hash(self, game):
        # Dùng bytes thay vì tuple → hash nhanh hơn đáng kể
        # & 0xFF để xử lý giá trị âm (-1 → 255), tránh lỗi range(0,256)
        return bytes(
            b & 0xFF
            for c in game.CARDS
            for b in (c.group_id, c.group_index)
        )

    def _get_valid_moves(self, game):
        valid_moves = []
        foundation_moves = []

        for from_id in range(4, 16):
            heap_from = game.card_heaps[from_id].heap_list
            if not heap_from:
                continue

            # Lấy chỉ số của quân bài trên cùng (Top card index)
            card_idx = len(heap_from) - 1

            for to_id in range(16):
                if from_id == to_id:
                    continue

                if game.CheckMove(from_id, to_id):
                    # TRẢ VỀ 3 GIÁ TRỊ: (từ đâu, đến đâu, chỉ số nào)
                    if 0 <= to_id <= 3:
                        foundation_moves.append((from_id, to_id, card_idx))
                    else:
                        valid_moves.append((from_id, to_id, card_idx))

        return foundation_moves if foundation_moves else valid_moves

    def _dfs_limited(self, game, path, visited, depth_limit, timeout):
        self.expanded_nodes += 1

        # Check Win
        if game.CheckWinStrict():
            return True  # path đã chứa đủ nước đi, signal thành công

        if len(path) >= depth_limit:
            return None

        if time.time() - self.start_time > timeout:
            return "TIMEOUT"

        moves = self._get_valid_moves(game)
        for move in moves:
            from_id, to_id, _ = move

            # Tiến 1 bước
            game.Move(from_id, to_id)
            current_hash = self._get_game_state_hash(game)

            if current_hash not in visited:
                visited.add(current_hash)
                path.append(move)  # Dùng append/pop thay vì path + [move] → tránh tạo list mới mỗi bước

                result = self._dfs_limited(game, path, visited, depth_limit, timeout)

                if result == "TIMEOUT":
                    game.Move(to_id, from_id)
                    return "TIMEOUT"

                if result is True:
                    game.Move(to_id, from_id)
                    return True

                path.pop()
                # KHÔNG xóa khỏi visited → tránh thăm lại trạng thái trong cùng iteration
                # Đây là tối ưu quan trọng: giữ visited giúp cắt tỉa mạnh hơn

            # Lùi 1 bước (Undo)
            game.Move(to_id, from_id)

        return None

    def solve(self, max_depth=100, timeout=300):
        self.start_time = time.time()
        tracemalloc.start()
        process = psutil.Process(os.getpid())
        self.start_memory = process.memory_info().rss / (1024 ** 2)

        initial_hash = self._get_game_state_hash(self.initial_game_source)

        # Chỉ deepcopy 1 lần duy nhất (thay vì deepcopy mỗi iteration IDS)
        # Game state được khôi phục bằng Undo moves sau mỗi bước DFS
        current_game = copy.deepcopy(self.initial_game_source)

        solution_path = []

        # IDS: Chạy DFS lặp lại với độ sâu tăng dần
        for depth in range(1, max_depth + 1):
            visited = {initial_hash}
            solution_path = []

            result = self._dfs_limited(current_game, solution_path, visited, depth, timeout)

            if result == "TIMEOUT":
                break

            if result is True:
                return self._build_result(True, solution_path, process)

        return self._build_result(False, [], process, "Not found")

    def _build_result(self, solved, solution, process, error=None):
        end_time = time.time()
        end_mem = process.memory_info().rss / (1024 ** 2)
        res = {
            'solved': solved,
            'solution': solution,
            'search_time': end_time - self.start_time,
            'memory_used': max(0, end_mem - self.start_memory),
            'expanded_nodes': self.expanded_nodes,
            'search_length': len(solution)
        }
        if error:
            res['error'] = error
        return res