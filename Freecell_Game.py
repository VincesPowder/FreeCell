# %%
import random
import copy
import time
# %%
MAX_SEARCH_DEPTH = 5
MAX_SEARCH_NODES = 1000
# %%
POINT = {
    1: "A",
    2: "2",
    3: "3",
    4: "4",
    5: "5",
    6: "6",
    7: "7",
    8: "8",
    9: "9",
    10: "10",
    11: "J",
    12: "Q",
    13: "K",
}
COLOR = ["Heart", "Diamond", "Spade", "Club"]


class Card:
    global point

    def __init__(self, color, num):
        self.color = color
        self.num = num
        self.point = POINT[num]
        self.group_id = -1
        self.group_index = -1
        if color in ["Heart", "Diamond"]:
            self.rb = "r"
        else:
            self.rb = "b"


# %%
OPERATIONS = (
    [(m, n) for m in range(0, 4) for n in range(4, 16)]
    + [(m, n) for m in range(4, 8) for n in list(range(0, 4)) + list(range(8, 16))]
    + [(m, n) if m > n else (m, n + 1) for m in range(8, 16) for n in range(0, 15)]
)


# %%
class PokerHeap:
    def __init__(self, heap_id):
        self.heap_list = []
        self.heap_id = heap_id

    def reset(self, cards):
        self.heap_list = cards

    def GetTop(self):
        if len(self.heap_list) == 0:
            return False
        else:
            return self.heap_list[-1]

    def PopTop(self):
        self.heap_list.pop()

    def PushTop(self, card):
        self.heap_list.append(card)
        card.group_id = self.heap_id
        card.group_index = len(self.heap_list) - 1


class ColorHeap(PokerHeap):
    def __init__(self, color, heap_id):
        super().__init__(heap_id)
        self.color = color

    def CheckMoveInto(self, card):
        if card.color != self.color:
            return False
        if (len(self.heap_list) == 0 and card.num == 1) or (
            len(self.heap_list) != 0 and card.num == self.heap_list[-1].num + 1
        ):
            return True
        else:
            return False


class FreeCell(PokerHeap):
    def __init__(self, heap_id):
        super().__init__(heap_id)

    def CheckMoveInto(self, card):
        if len(self.heap_list) == 0:
            return True
        else:
            return False


class CardHeap(PokerHeap):
    def __init__(self, heap_id):
        super().__init__(heap_id)

    def CheckMoveInto(self, card):
        if (len(self.heap_list) == 0) or (
            card.rb != self.heap_list[-1].rb and card.num == self.heap_list[-1].num - 1
        ):
            return True
        else:
            return False


# %%
class FreeCellGame:
    def __init__(self, game=None):
        self.CARDS = [Card(c, n) for c in COLOR for n in range(1, 14)]
        self.card_heaps = (
            [ColorHeap(COLOR[x], x) for x in range(4)]
            + [FreeCell(x + 4) for x in range(4)]
            + [CardHeap(x + 8) for x in range(8)]
        )

    def CheckMove(self, come, to):
        move_card = self.card_heaps[come].GetTop()
        if move_card != False:
            if self.card_heaps[to].CheckMoveInto(move_card):
                return True
            else:
                return False
        else:
            return False

    def CheckReverse(self, come, to):
        move_card = self.card_heaps[come].GetTop()
        if move_card != False:
            # check reverse
            come_flag = False
            self.card_heaps[come].PopTop()
            if self.card_heaps[come].CheckMoveInto(move_card):
                come_flag = True
            self.card_heaps[come].PushTop(move_card)
            to_flag = False
            if to < 8:
                if self.card_heaps[to].CheckMoveInto(move_card):
                    to_flag = True
            else:
                to_flag = True
            if come_flag and to_flag:
                return True
            else:
                return False
        else:
            return False

    # if move for search, don't not change card attr.
    def Move(self, come, to):
        move_card = self.card_heaps[come].GetTop()
        self.card_heaps[come].PopTop()
        self.card_heaps[to].PushTop(move_card)

    def ObserveForNet(self):
        """
        Returns:
            observe = list of group_id, group_index.
        """
        res = []
        for x in range(52):
            res.append(self.CARDS[x].group_id / 16.0)
            res.append(self.CARDS[x].group_index / 20.0)
        return res

    def ObserveForData(self):
        """
        Returns:
            hash_index str.

            observe = list of group_id, group_index.
        """
        res = []
        hash_index = ""
        for x in range(52):
            res.append(self.CARDS[x].group_id)
            res.append(self.CARDS[x].group_index)
            hash_index = (
                hash_index
                + ("%02d" % self.CARDS[x].group_id)
                + ("%02d" % self.CARDS[x].group_index)
            )
        return hash_index, res

    def ParseDataObserve(self, res):
        """
        Useless.
        """
        # clear all heap.
        # no need
        # for poker_heap in self.card_heaps:
        #     poker_heap.reset([])
        # no need to clear cards.
        heap_size = [0 for x in range(16)]
        for i in range(len(res) // 2):
            self.CARDS[i].group_id = res[2 * i]
            self.CARDS[i].group_index = res[2 * i + 1]
            if heap_size[self.CARDS[i].group_id] < self.CARDS[i].group_index + 1:
                heap_size[self.CARDS[i].group_id] = self.CARDS[i].group_index + 1
        for i in range(16):
            self.card_heaps[i].heap_list = [0 for x in range(heap_size[i])]
        for card in self.CARDS:
            self.card_heaps[card.group_id].heap_list[card.group_index] = card

    def ObserveForHuman(self):
        res = []
        for group in self.card_heaps:
            tmp = [
                "ID:"
                + (
                    str(group.heap_id)
                    if (group.heap_id > 9)
                    else (str(group.heap_id) + " ")
                )
            ]
            if hasattr(group, "color"):
                tmp.append("color:" + group.color[0])
            for card in group.heap_list:
                tmp.append(
                    card.color[0]
                    + (card.point if card.point == "10" else card.point + " ")
                )
            res.append(tmp)
        return res

    def CheckWin(self):
        for x in range(8, 16):
            heap_l = self.card_heaps[x].heap_list
            if len(heap_l) == 0:
                continue
            else:
                for i in range(len(heap_l)):
                    if i > 0 and heap_l[i].num > heap_l[i - 1].num:
                        return False
        return True

    def CheckWinStrict(self):
        for x in range(0, 4):
            if (
                len(self.card_heaps[x].heap_list) == 0
                or self.card_heaps[x].heap_list[-1].point != "K"
            ):
                return False
        return True

    def NewGameOld(self):
        # clear all heap
        for x in self.card_heaps:
            x.reset([])
        # init color heap
        for card in self.CARDS:
            group_id = COLOR.index(card.color)
            self.card_heaps[group_id].PushTop(card)
        # use reverse method to generate new game
        while 1:
            init_flag = True
            for x in range(8):
                if self.card_heaps[x].heap_list:
                    init_flag = False
                    break
            for x in range(8, 16):
                if len(self.card_heaps[x].heap_list) < 5:
                    init_flag = False
                    break
            if init_flag:
                break
            oprts = self.ValidReverseOprts()
            if not oprts:
                return False
            index = random.randint(0, len(oprts) - 1)
            oprt = oprts[index]
            self.Move(oprt[0], oprt[1])
        return True

    def NewGame(self, seed=None):
        """
        Tạo game mới với lá bài được xáo trộn.
        
        Args:
            seed: Seed cho random. Nếu None, dùng seed ngẫu nhiên từ thời gian.
        """
        # clear cards and heaps
        for x in self.card_heaps:
            x.reset([])
        # no need to clear cards
        deck = [i for i in range(52)]
        card_left = 52
        
        # Nếu không có seed, tạo seed ngẫu nhiên từ thời gian
        if seed is None:
            seed = int(time.time() * 1000) % 2**32
        
        random.seed(seed)
        for i in range(52):
            card_pick_i = random.randint(0, 10000) % card_left
            self.card_heaps[i % 8 + 8].PushTop(self.CARDS[deck[card_pick_i]])
            card_left -= 1
            deck[card_pick_i] = deck[card_left]
        return seed

    def NewRandomGameWithDifficulty(self, difficulty="medium"):
        """
        Tạo game mới với độ khó cụ thể và seed NGẪU NHIÊN.
        Mỗi lần gọi sẽ tạo game khác nhau (seed khác) nhưng cùng level khó.
        
        Args:
            difficulty: "easy", "medium", "hard", "expert"
            
        Returns:
            seed: Seed được dùng cho game
        """
        # Phạm vi seed cho từng độ khó
        # Càng cao là càng khó
        difficulty_ranges = {
            "easy": (1, 1000),           # Easy: seed 1-1000
            "medium": (1000, 10000),     # Medium: seed 1000-10000
            "hard": (10000, 20000),      # Hard: seed 10000-20000
            "expert": (20000, 32000)     # Expert: seed 20000-32000
        }
        
        # Lấy phạm vi seed, mặc định medium nếu invalid
        min_seed, max_seed = difficulty_ranges.get(difficulty, (1000, 10000))
        
        # Generate seed ngẫu nhiên trong phạm vi
        random_seed = random.randint(min_seed, max_seed)
        return self.NewGame(random_seed)

    def NewGameWithDifficulty(self, difficulty="medium"):
        """
        Tạo game mới với độ khó cụ thể (giống FreeCell Solitaire).
        Mỗi độ khó dùng seed cố định, nên game giống nhau mỗi lần chọn cùng độ khó.
        
        Args:
            difficulty: "easy", "medium", "hard", "expert"
            
        Returns:
            seed: Seed được dùng cho game
        """
        # Các seed cố định cho từng độ khó
        # FreeCell Solitaire truyền thống dùng game numbering 1-32000+
        difficulty_seeds = {
            "easy": 1,           # Seed dễ
            "medium": 100,       # Seed trung bình  
            "hard": 1000,        # Seed khó
            "expert": 10000       # Seed rất khó
        }
        
        # Lấy seed tương ứng, mặc định "medium" nếu invalid
        seed = difficulty_seeds.get(difficulty, 100)
        return self.NewGame(seed)
    
    def NewGameWithNumber(self, game_number):
        """
        Tạo game với game number cố định (giống FreeCell Solitaire chính thức).
        Mỗi game number cho một cấu hình lá bài nhất định.
        
        Args:
            game_number: Số game (1-32000+)
            
        Returns:
            seed: Seed được dùng
        """
        seed = game_number % 2**32
        return self.NewGame(seed)

    def RandomNewGameAndRecordCost(self, train_data, mode):
        """
        use random reverse operations to generate game and record cost.

        Param:
            mode:
                big_cost: only record cost bigger than 20.
                small_cost: only record cost smaller than 25.
        """
        # output string + cost
        # string: (group_id + index) *52
        # clear all heap
        for x in self.card_heaps:
            x.reset([])
        # init color heap
        for card in self.CARDS:  # card from Ace to King.
            group_id = COLOR.index(card.color)
            self.card_heaps[group_id].PushTop(card)
        # use reverse method to generate new game
        # check oscillation.
        step_cost = 0
        oscillate_count = 0
        last_oprt = None
        llast_oprt = None
        while 1:
            oprts = self.ValidReverseOprts()
            if not oprts:
                break
            index = random.randint(0, len(oprts) - 1)
            oprt = oprts[index]
            self.Move(oprt[0], oprt[1])
            # check oscillate
            if oprt == llast_oprt:
                oscillate_count = oscillate_count + 1
                if oscillate_count == 5:
                    break
            llast_oprt = last_oprt
            last_oprt = oprt
            # record data.
            step_cost = step_cost + 1
            if mode == "big_cost":
                if step_cost > 20:
                    train_data.Add(*self.ObserveForData(), step_cost)
            elif mode == "small_cost":
                if step_cost < 25:
                    train_data.Add(*self.ObserveForData(), step_cost)
        return

    def ValidOprts(self):
        res = []
        for op in OPERATIONS:
            if self.CheckMove(op[0], op[1]):
                res.append(op)
        return res

    def ValidReverseOprts(self):
        res = []
        for op in OPERATIONS:
            if self.CheckReverse(op[0], op[1]):
                res.append(op)
        return res
    
    # --- Thêm/Sửa các hàm sau vào class FreeCellGame trong Freecell_Game.py ---

    def IsValidSequence(self, cards):
        """Kiểm tra một danh sách bài có tạo thành chuỗi giảm dần, xen kẽ màu không"""
        if not cards: return False
        for i in range(len(cards) - 1):
            curr_card = cards[i]
            next_card = cards[i+1]
            # Phải khác màu (Red/Black) và giảm đúng 1 đơn vị
            if curr_card.rb == next_card.rb or curr_card.num != next_card.num + 1:
                return False
        return True

    def GetMaxMovable(self, from_pile_id, num_cards_to_move):
        """
        Tính số lá bài tối đa có thể di chuyển theo luật chuẩn.
        
        Công thức: (free_cells + 1) * 2^empty_tableau_columns
        Lưu ý: Nếu kéo hết tất cả bài từ cột nguồn, cột đó sẽ trở nên trống
        nên được tính vào empty_tableau_columns
        """
        # Đếm các ô Free Cell (4-7) đang trống
        empty_free_cells = sum(1 for i in range(4, 8) if len(self.card_heaps[i].heap_list) == 0)
        
        # Đếm các cột Tableau (8-15) đang trống
        empty_columns = sum(1 for i in range(8, 16) if len(self.card_heaps[i].heap_list) == 0)
        
        # QUAN TRỌNG: Nếu kéo TOÀN BỘ bài từ cột nguồn, cột đó sẽ trở nên trống
        # Nên cần cộng thêm nó vào empty_columns để tính toán đúng
        if 8 <= from_pile_id <= 15:
            source_heap_size = len(self.card_heaps[from_pile_id].heap_list)
            if source_heap_size == num_cards_to_move:
                # Kéo hết bài từ cột này = cột này sẽ trở nên trống
                empty_columns += 1
        
        return (1 + empty_free_cells) * (2 ** empty_columns)

    # Cập nhật CheckMove để hỗ trợ kiểm tra cả dây bài
    def CheckMoveSequence(self, come_id, to_id, card_index):
        heap_from = self.card_heaps[come_id].heap_list
        sub_stack = heap_from[card_index:]
        
        # 1. Kiểm tra dây bài định kéo có đúng quy tắc (giảm dần, khác màu) không
        if not self.IsValidSequence(sub_stack):
            return False, "Dây bài không hợp lệ (phải khác màu và giảm dần)!"
            
        # 2. Check if there are enough free cells to move
        max_allowed = self.GetMaxMovable(come_id, len(sub_stack))
        if len(sub_stack) > max_allowed:
            return False, f"Not enough free cells! Can only move max {max_allowed} cards."

        # 3. Check if the first card of the sequence can be placed to target column
        first_card = sub_stack[0]
        if self.card_heaps[to_id].CheckMoveInto(first_card):
            return True, ""
        
        return False, "Card does not fit the target column!"


# %%


class SearchNode:
    def __init__(self, oprt, game):
        self.oprt = oprt
        self.child = []
        # attention! game: FreecellGame
        self.state = game


class SearchTree:
    def __init__(self, node):
        self.root = node
        self.depth = 1
        self.nodes = 1
        self.max_depth = MAX_SEARCH_DEPTH
        self.max_nodes = MAX_SEARCH_NODES

    def reset(self, node):
        self.depth = 1
        self.root = node

    def GenerateChild(self, node):
        oprts = node.state.ValidOprts()
        if not oprts:
            return False
        for oprt in oprts:
            game = FreeCellGame(node.state)
            game.Move(oprt[0], oprt[1], True)
            node.child.append(SearchNode(oprt, game))
            self.nodes = self.nodes + 1
        return True

    # need to be rewrite.
    # think about how to design return.
    def Traversal(self, node, func):
        if not node.child:
            return func(node)
        else:
            for n in node.child:
                self.Traversal(n, func)
            return True  # how to return.

    # attention. Grow doesn't always success.
    def TreeGrow(self):
        if self.Traversal(self.root, self.GenerateChild):
            self.depth = self.depth + 1
            return True
        else:
            # root has no child and generate failed.
            return False

    def TreeUpdate(self):
        while self.depth < self.max_depth and self.nodes < self.max_nodes:
            if not self.TreeGrow():
                return False  # TreeGrow fail.

    def RootDeep(self, oprt):
        for n in self.root.child:
            if n.oprt == oprt:
                self.nodes = self.nodes // len(self.root.child)
                self.depth = self.depth - 1
                self.root = n
                return True
        return False

    def Score(self, node):
        return node.state.Score()

    def MaxScore(self, node):
        max_score = 0

        def Score(node):
            nonlocal max_score
            score = node.state.Score()
            if score > max_score:
                max_score = score

        self.Traversal(node, Score)
        return max_score


# %%
if __name__ == "__main__":
    pass
# %%
game = FreeCellGame()
# %%
game.NewGame()
# %%
observe = game.ObserveForHuman()
observe
# %%
game.Move(8, 2)

# observe = game.ObserveForHuman()
# observe
# # %%
# tmp = game.card_heaps[10].heap_list.pop(0)
# game.card_heaps[2].MoveInto(tmp)
# # %%
# game.CheckWin()

# %%
# game = FreeCellGame()
# while not game.NewGame():
#     pass
# print(*game.ObserveForHuman(), sep='\n')
# print("\n\n")
# new_game = FreeCellGame(game)
# print(*new_game.ObserveForHuman(), sep='\n')
# print("\n\n")
# st = SearchTree(SearchNode(None, new_game))
# st.TreeUpdate()
# # %%
# res = []
# for x in st.root.child:
#     res.append(st.MaxScore(x))
# print(*res)
# st.RootDeep(st.root.child[res.index(max(res))].oprt)
# st.TreeUpdate()
# # %%
# st.root.state.CheckWin()
# # %%
# st.root.state.ObserveForHuman()
#
# # %%
