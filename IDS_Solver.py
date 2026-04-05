import time
import psutil
import os
import copy

class IDSSolver:
    def __init__(self, game_state, on_move_callback=None):
        self.initial_game = copy.deepcopy(game_state)
        self.expanded_nodes = 0
        self.start_time = None
        self.end_time = None
        self.start_memory = None
        self.end_memory = None
        self.search_length = 0
        self.on_move_callback = on_move_callback
        
        # Khởi tạo process một lần duy nhất để tối ưu hiệu năng gọi hàm
        self.process = psutil.Process(os.getpid())

    def _get_game_state_hash(self, game):
        """Tạo mã hash tối ưu, loại bỏ tính đối xứng của FreeCell và Cascade"""
        # 1. Foundations (0-3): Chỉ lưu giá trị (num) lớn nhất của mỗi chất
        foundations = tuple(
            game.card_heaps[i].heap_list[-1].num if game.card_heaps[i].heap_list else 0
            for i in range(4)
        )

        # 2. Freecells (4-7): Sort để đồng nhất các ô Freecell
        freecells = []
        for i in range(4, 8):
            if game.card_heaps[i].heap_list:
                c = game.card_heaps[i].heap_list[0]
                freecells.append((c.color, c.num))
        freecells.sort()

        # 3. Cascades (8-15): Sort các cột để đồng nhất việc dùng các cột rỗng
        cascades = []
        for i in range(8, 16):
            col = tuple((c.color, c.num) for c in game.card_heaps[i].heap_list)
            cascades.append(col)
        cascades.sort()

        return (foundations, tuple(freecells), tuple(cascades))

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

    def _undo_move(self, game, move):
        """Hoàn tác nước đi để đưa bàn cờ về trạng thái trước đó."""
        from_id, to_id, card_idx, num_cards = move
        cards_to_undo = game.card_heaps[to_id].heap_list[-num_cards:]
        game.card_heaps[to_id].heap_list = game.card_heaps[to_id].heap_list[:-num_cards]
        game.card_heaps[from_id].heap_list.extend(cards_to_undo)

        # Cập nhật lại group_id và group_index
        for i, card in enumerate(game.card_heaps[from_id].heap_list):
            card.group_id = from_id
            card.group_index = i

    def _dfs_limited(self, game, path, ancestors, visited_global, depth_limit, timeout):
        """
        DFS giới hạn độ sâu với visited 2 tầng.
        """
        if self.stop_event and self.stop_event.is_set():
            return "STOPPED"

        self.expanded_nodes += 1

        if self._check_win(game):
            return True

        current_depth = len(path)
        if current_depth >= depth_limit:
            return None

        if time.time() - self.start_time > timeout:
            return "TIMEOUT"

        for move in self._get_valid_moves(game):
            self._apply_move(game, move)
            child_hash = self._get_game_state_hash(game)
            child_depth = current_depth + 1

            # Tầng 1: bỏ qua nếu trạng thái đang trên đường đi (tránh vòng lặp)
            skip = child_hash in ancestors

            # Tầng 2: bỏ qua nếu đã thăm trạng thái này ở độ sâu <= child_depth
            if not skip:
                prev_depth = visited_global.get(child_hash, None)
                if prev_depth is not None and prev_depth <= child_depth:
                    skip = True

            if not skip:
                visited_global[child_hash] = child_depth
                ancestors.add(child_hash)
                path.append(move)

                result = self._dfs_limited(game, path, ancestors, visited_global, depth_limit, timeout)

                if result == "TIMEOUT":
                    self._undo_move(game, move)
                    return "TIMEOUT"

                if result is True:
                    self._undo_move(game, move)
                    return True

                path.pop()
                ancestors.discard(child_hash)  # Backtrack: xóa khỏi ancestors

            self._undo_move(game, move)

        return None

    def solve(self, max_depth=100, timeout=300, stop_event=None):
        self.stop_event = stop_event
        self.start_time = time.time()
        
        # Đọc RSS memory trước khi bắt đầu giải
        self.start_memory = self.process.memory_info().rss / (1024 ** 2)
        self.expanded_nodes = 0

        current_game = copy.deepcopy(self.initial_game)

        if self._check_win(current_game):
            return self._finalize(True, [])

        initial_hash = self._get_game_state_hash(current_game)

        # IDS: Chạy DFS lặp lại với độ sâu tăng dần
        for depth in range(1, max_depth + 1):
            ancestors = {initial_hash}
            visited_global = {initial_hash: 0}
            solution_path = []

            result = self._dfs_limited(
                current_game, solution_path,
                ancestors, visited_global,
                depth, timeout
            )

            if result == "STOPPED":
                return self._finalize(False, [], "Solver stopped!")
            if result == "TIMEOUT":
                break
            if result is True:
                return self._finalize(True, solution_path)

        return self._finalize(False, [], "No solution found within node limit")

    def _finalize(self, solved, solution, error=None):
        self.end_time = time.time()
        
        # Đọc RSS memory ngay sau khi kết thúc vòng lặp để lấy đỉnh bộ nhớ
        self.end_memory = self.process.memory_info().rss / (1024 ** 2)

        # Trả về đúng 3 giá trị (from, to, index) để main.py không bị lỗi unpack
        formatted_solution = [(m[0], m[1], m[2]) for m in solution]

        res = {
            'solved': solved,
            'solution': formatted_solution,
            'search_time': self.end_time - self.start_time,
            # Dùng max(0, ...) để tránh âm nếu OS hoặc Garbage Collector dọn dẹp RAM của process
            'memory_used': max(0, self.end_memory - self.start_memory) if self.start_memory and self.end_memory else 0,
            'expanded_nodes': self.expanded_nodes,
            'search_length': len(formatted_solution)
        }
        if error:
            res['error'] = error
            
        return res