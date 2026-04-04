import time
import psutil
import os
import copy
from heapq import heappush, heappop

class AStarSolver:
    def __init__(self, game_state):
        self.initial_game_source = game_state
        self.visited_states = {} # Dùng dict lưu {hash: g_score} để cho phép cập nhật đường đi ngắn hơn
        self.expanded_nodes = 0
        self.start_time = None
        self.end_time = None
        self.start_memory = None
        self.end_memory = None

    def _get_game_state_hash(self, game):
        """Hash tối ưu bỏ qua tính đối xứng của FreeCell và Cascade"""
        foundations = tuple(game.card_heaps[i].heap_list[-1].num if game.card_heaps[i].heap_list else 0 for i in range(4))
        
        freecells = []
        for i in range(4, 8):
            if game.card_heaps[i].heap_list:
                c = game.card_heaps[i].heap_list[0]
                freecells.append((c.color, c.num))
        freecells.sort()
        
        cascades = []
        for i in range(8, 16):
            col = tuple((c.color, c.num) for c in game.card_heaps[i].heap_list)
            cascades.append(col)
        cascades.sort()
        
        return (foundations, tuple(freecells), tuple(cascades))

    def _heuristic(self, game):
        score = 0
        # 1. Thưởng điểm khi đưa bài lên Foundation (0-3)
        cards_in_foundation = sum(len(game.card_heaps[i].heap_list) for i in range(4))
        score -= cards_in_foundation * 150

        # 2. Phạt nếu chiếm dụng FreeCell (4-7)
        for i in range(4, 8):
            if len(game.card_heaps[i].heap_list) > 0:
                score += 30

        # 3. Phạt nếu các lá bài nhỏ (A, 2, 3...) bị kẹt sâu trong Cascade
        for i in range(8, 16):
            column = game.card_heaps[i].heap_list
            for idx, card in enumerate(column):
                val = card.num
                if val < 8:
                    score += (len(column) - 1 - idx) * 30
        return score

    def _get_valid_moves(self, game):
        valid_moves = []
        foundation_moves = []

        for from_id in range(4, 16):
            heap_from = game.card_heaps[from_id].heap_list
            if not heap_from: continue

            start_indices = range(len(heap_from)) if from_id >= 8 else [len(heap_from) - 1]

            for card_idx in start_indices:
                num_cards = len(heap_from) - card_idx
                for to_id in range(16):
                    if from_id == to_id: continue

                    can_move, _ = game.CheckMoveSequence(from_id, to_id, card_idx)
                    if can_move:
                        move = (from_id, to_id, card_idx, num_cards)
                        if 0 <= to_id <= 3:
                            foundation_moves.append(move)
                        else:
                            valid_moves.append(move)

        return foundation_moves if foundation_moves else valid_moves

    def _apply_move(self, game, move):
        from_id, to_id, _, num_cards = move
        cards_to_move = game.card_heaps[from_id].heap_list[-num_cards:]
        game.card_heaps[from_id].heap_list = game.card_heaps[from_id].heap_list[:-num_cards]
        game.card_heaps[to_id].heap_list.extend(cards_to_move)
        for i, card in enumerate(game.card_heaps[to_id].heap_list):
            card.group_id, card.group_index = to_id, i

    def _undo_move(self, game, move):
        from_id, to_id, _, num_cards = move
        cards_to_undo = game.card_heaps[to_id].heap_list[-num_cards:]
        game.card_heaps[to_id].heap_list = game.card_heaps[to_id].heap_list[:-num_cards]
        game.card_heaps[from_id].heap_list.extend(cards_to_undo)
        for i, card in enumerate(game.card_heaps[from_id].heap_list):
            card.group_id, card.group_index = from_id, i

    def solve(self, max_nodes=100000, timeout=60, stop_event=None):
        self.start_time = time.time()
        process = psutil.Process(os.getpid())
        self.start_memory = process.memory_info().rss / (1024 ** 2)

        open_set = []
        counter = 0

        current_game = copy.deepcopy(self.initial_game_source)
        current_path = []

        initial_hash = self._get_game_state_hash(current_game)
        initial_h = self._heuristic(current_game)

        # Cấu trúc Hàng đợi ưu tiên: (f_score, counter, g_score, h_score, path)
        heappush(open_set, (initial_h, counter, 0, initial_h, []))
        counter += 1
        self.visited_states[initial_hash] = 0

        while open_set and self.expanded_nodes < max_nodes:
            if stop_event and stop_event.is_set():
                return self._build_result(False, [], 'Solver stopped!')
            if time.time() - self.start_time > timeout:
                self._finalize_metrics(process)
                return self._build_result(False, [], "Timeout exceeded")

            f_score, _, g_score, h_score, path = heappop(open_set)
            self.expanded_nodes += 1

            # Delta Replay để đồng bộ trạng thái game với path hiện tại
            common_len = 0
            for m1, m2 in zip(current_path, path):
                if m1 == m2: common_len += 1
                else: break
            for move in reversed(current_path[common_len:]): self._undo_move(current_game, move)
            for move in path[common_len:]: self._apply_move(current_game, move)
            current_path = path

            # Kiểm tra Goal
            if current_game.CheckWinStrict():
                self._finalize_metrics(process)
                return self._build_result(True, path)

            # Khai triển nhánh mới
            for move in self._get_valid_moves(current_game):
                self._apply_move(current_game, move)
                next_hash = self._get_game_state_hash(current_game)
                new_g = g_score + 1

                # A* check: Cập nhật nếu chưa đi qua hoặc tìm được đường g(n) ngắn hơn
                if next_hash not in self.visited_states or new_g < self.visited_states[next_hash]:
                    self.visited_states[next_hash] = new_g
                    new_h = self._heuristic(current_game)
                    
                    # Hệ số 2.0 cho Heuristic để tăng tốc độ hội tụ (Weighted A*)
                    new_f = new_g + 2.0 * new_h

                    heappush(open_set, (new_f, counter, new_g, new_h, path + [move]))
                    counter += 1

                self._undo_move(current_game, move)

        self._finalize_metrics(process)
        return self._build_result(False, [], "No solution found within node limit")

    def _finalize_metrics(self, process):
        self.end_time = time.time()
        self.end_memory = process.memory_info().rss / (1024 ** 2)

    def _build_result(self, solved, solution, error=None):
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