import random
import copy
import time

POINT = {
    1: "A", 2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7",
    8: "8", 9: "9", 10: "10", 11: "J", 12: "Q", 13: "K",
}
COLOR = ["Heart", "Club", "Diamond", "Spade"]

class Card:
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

OPERATIONS = (
    [(m, n) for m in range(0, 4) for n in range(4, 16)]
    + [(m, n) for m in range(4, 8) for n in list(range(0, 4)) + list(range(8, 16))]
    + [(m, n) if m > n else (m, n + 1) for m in range(8, 16) for n in range(0, 15)]
)

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
            return False
        return False

    def Move(self, come, to):
        move_card = self.card_heaps[come].GetTop()
        self.card_heaps[come].PopTop()
        self.card_heaps[to].PushTop(move_card)

    def ObserveForData(self):
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
                + (str(group.heap_id) if (group.heap_id > 9) else (str(group.heap_id) + " "))
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

    def CheckWinStrict(self):
        for x in range(0, 4):
            if (
                len(self.card_heaps[x].heap_list) == 0
                or self.card_heaps[x].heap_list[-1].point != "K"
            ):
                return False
        return True

    def NewGame(self, seed=None):
        for x in self.card_heaps:
            x.reset([])
        
        if seed is None:
            seed = int(time.time() * 1000) % 2**32
            
        ms_suits = ["Club", "Diamond", "Heart", "Spade"]
        deck = []
        for i in range(52):
            rank = (i // 4) + 1
            suit = ms_suits[i % 4]
            user_idx = COLOR.index(suit) * 13 + (rank - 1)
            deck.append(user_idx)
            
        state = seed
        for i in range(52):
            state = (state * 214013 + 2531011) & 0xffffffff
            card_pick_i = ((state >> 16) & 0x7fff) % (52 - i)
            self.card_heaps[i % 8 + 8].PushTop(self.CARDS[deck[card_pick_i]])
            deck[card_pick_i] = deck[52 - i - 1]
            
        return seed

    def NewRandomGameWithDifficulty(self, difficulty="medium"):
        difficulty_ranges = {
            "easy": (1, 8000),             
            "medium": (8001, 16000),       
            "hard": (16001, 24000),        
            "expert": (24001, 32000)       
        }
        min_game, max_game = difficulty_ranges.get(difficulty, (8001, 16000))
        game_number = random.randint(min_game, max_game)
        return self.NewGame(game_number)

    def NewGameWithDifficulty(self, difficulty="medium"):
        difficulty_games = {
            "easy": 25904,      
            "medium": 1,        
            "hard": 617,        
            "expert": 11982     
        }   
        game_number = difficulty_games.get(difficulty, 1)
        return self.NewGame(game_number)
    
    def NewGameWithNumber(self, game_number):
        seed = game_number % 2**32
        return self.NewGame(seed)

    def ValidOprts(self):
        res = []
        for op in OPERATIONS:
            if self.CheckMove(op[0], op[1]):
                res.append(op)
        return res

    def IsValidSequence(self, cards):
        if not cards: return False
        for i in range(len(cards) - 1):
            curr_card = cards[i]
            next_card = cards[i+1]
            if curr_card.rb == next_card.rb or curr_card.num != next_card.num + 1:
                return False
        return True

    def GetMaxMovable(self, from_pile_id, num_cards_to_move):
        empty_free_cells = sum(1 for i in range(4, 8) if len(self.card_heaps[i].heap_list) == 0)
        empty_columns = sum(1 for i in range(8, 16) if len(self.card_heaps[i].heap_list) == 0)
        
        if 8 <= from_pile_id <= 15:
            source_heap_size = len(self.card_heaps[from_pile_id].heap_list)
            if source_heap_size == num_cards_to_move:
                empty_columns += 1
        
        return (1 + empty_free_cells) * (2 ** empty_columns)

    def CheckMoveSequence(self, come_id, to_id, card_index):
        heap_from = self.card_heaps[come_id].heap_list
        sub_stack = heap_from[card_index:]
        
        if to_id < 8 and len(sub_stack) > 1:
            return False, "Can only move 1 card to Foundation or FreeCell!"

        if not self.IsValidSequence(sub_stack):
            return False, "Invalid sequence (must be alternating colors and decreasing)!"
            
        max_allowed = self.GetMaxMovable(come_id, len(sub_stack))
        if len(sub_stack) > max_allowed:
            return False, f"Not enough free cells! Can only move max {max_allowed} cards."

        first_card = sub_stack[0]
        if self.card_heaps[to_id].CheckMoveInto(first_card):
            return True, ""
        
        return False, "Card does not fit the target column!"