import time
import psutil
import os
import copy
from collections import deque
from Freecell_Game import FreeCellGame

class BFSSolver:
    def __init__(self, game_state, on_move_callback=None):
        self.initial_game = copy.deepcopy(game_state)
        self.visited_states = set() 
        self.solutions = [] 
        self.expanded_nodes = 0
        self.start_time = None
        self.end_time = None
        self.start_memory = None
        self.end_memory = None
        self.search_length = 0
        self.on_move_callback = on_move_callback
        
    def _get_game_state_hash(self, game):
        """Tạo mã hash tối ưu, loại bỏ tính đối xứng của FreeCell và Cascade"""
        # 1. Foundations (0-3): Đã cố định chất bài, chỉ cần lưu giá trị (num) lớn nhất
        foundations = tuple(
            game.card_heaps[i].heap_list[-1].num if game.card_heaps[i].heap_list else 0 
            for i in range(4)
        )
        
        # 2. Freecells (4-7): Sort để đồng nhất các ô Freecell (bỏ vào ô nào cũng giống nhau)
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
                        # Lưu thêm num_cards để tiện lợi cho việc apply move
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
        """Hoàn tác nước đi để đưa bàn cờ về trạng thái trước đó."""
        from_id, to_id, card_idx, num_cards = move
        cards_to_undo = game.card_heaps[to_id].heap_list[-num_cards:]
        game.card_heaps[to_id].heap_list = game.card_heaps[to_id].heap_list[:-num_cards]
        game.card_heaps[from_id].heap_list.extend(cards_to_undo)
        
        # Cập nhật lại group_id và group_index
        for i, card in enumerate(game.card_heaps[from_id].heap_list):
            card.group_id = from_id
            card.group_index = i

    def solve(self, max_nodes=100000, timeout=300, stop_event=None):
        self.start_time = time.time()
        process = psutil.Process(os.getpid())
        self.start_memory = process.memory_info().rss / (1024 ** 2)
        
        queue = deque()
        current_game = copy.deepcopy(self.initial_game)
        current_path = []
        
        if self._check_win(current_game):
            return self._finalize(True, [])

        initial_hash = self._get_game_state_hash(current_game)
        queue.append([]) 
        self.visited_states.add(initial_hash)
        
        while queue and self.expanded_nodes < max_nodes:
            if stop_event and stop_event.is_set():
                return self._finalize(False, [], 'Solver stopped!')
            if time.time() - self.start_time > timeout:
                return self._finalize(False, [], 'Timeout exceeded')
            
            path = queue.popleft()
            self.expanded_nodes += 1

            common_len = 0
            for m1, m2 in zip(current_path, path):
                if m1 == m2: common_len += 1
                else: break
                
            for move in reversed(current_path[common_len:]): 
                self._undo_move(current_game, move)
            for move in path[common_len:]: 
                self._apply_move(current_game, move)
                
            current_path = path

            for move in self._get_valid_moves(current_game):
                self._apply_move(current_game, move)
                if self._check_win(current_game): 
                    return self._finalize(True, path + [move])

                next_hash = self._get_game_state_hash(current_game)
                if next_hash not in self.visited_states:
                    self.visited_states.add(next_hash)
                    queue.append(path + [move]) 
                self._undo_move(current_game, move)
        
        return self._finalize(False, [], 'No solution found within node limit')

    def _finalize(self, solved, solution, error=None):
        self.end_time = time.time()
        process = psutil.Process(os.getpid())
        self.end_memory = process.memory_info().rss / (1024 ** 2)
        
        # Trả về đúng 3 giá trị (from, to, index) để main.py không bị lỗi unpack
        formatted_solution = [(m[0], m[1], m[2]) for m in solution]
        
        res = {
            'solved': solved,
            'solution': formatted_solution,
            'search_time': self.end_time - self.start_time,
            'memory_used': max(0, self.end_memory - self.start_memory) if self.end_memory else 0,
            'expanded_nodes': self.expanded_nodes,
            'search_length': len(formatted_solution)
        }
        if error:
            res['error'] = error
        return res