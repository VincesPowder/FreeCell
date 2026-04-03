"""
Bộ Test Case đo lường hiệu suất Search Algorithms.
Độ khó tăng dần từ việc chỉ còn 4 lá bài (Test 1) cho tới toàn bộ 52 lá nguyên bản (Test 13-16).
Đảm bảo đánh giá rõ được Search Time, Memory Usage, và Expanded Nodes.
"""
import random
from Freecell_Game import FreeCellGame

class TestCases:
    @staticmethod
    def _clear_and_prepare(game: FreeCellGame):
        """Xóa trắng bàn chơi và lấy lại 52 lá bài."""
        for heap in game.card_heaps:
            heap.heap_list = []
        return game.CARDS # Trả về 52 lá: 0-12 Heart, 13-25 Diamond, 26-38 Spade, 39-51 Club

    @staticmethod
    def _setup_partial_game(game: FreeCellGame, max_foundation_rank: int, seed: int):
        """Hàm hỗ trợ sinh test case ngẫu nhiên nhưng cố định (dựa vào seed) cho độ khó tăng dần."""
        cards = TestCases._clear_and_prepare(game)
        
        # 1. Đưa các lá bài đến max_foundation_rank vào Foundation an toàn
        for s in range(4):
            for r in range(max_foundation_rank):
                game.card_heaps[s].PushTop(cards[s * 13 + r])

        # 2. Thu thập các lá bài còn lại
        remaining_cards = []
        for s in range(4):
            for r in range(max_foundation_rank, 13):
                remaining_cards.append(cards[s * 13 + r])

        # 3. Trộn ngẫu nhiên với seed cố định để đảm bảo test case không đổi mỗi lần chạy
        rng = random.Random(seed)
        rng.shuffle(remaining_cards)

        # 4. Rải đều vào 8 cột Cascade
        for i, card in enumerate(remaining_cards):
            game.card_heaps[8 + (i % 8)].PushTop(card)

    # ==========================================
    # PHASE 1: MANUAL SETUP (Rèn luyện thuật toán)
    # ==========================================

    @staticmethod
    def setup_test_1(game: FreeCellGame):
        """Mức 1: Trivial (4 lá) - 4 lá King nằm trên đỉnh 4 cột."""
        cards = TestCases._clear_and_prepare(game)
        for s in range(4):
            for r in range(12): # A -> Q vào Foundation
                game.card_heaps[s].PushTop(cards[s * 13 + r])
        for s in range(4):
            game.card_heaps[8 + s].PushTop(cards[s * 13 + 12]) # K vào 4 cột

    @staticmethod
    def setup_test_2(game: FreeCellGame):
        """Mức 2: Very Easy (8 lá) - Q và K kẹt chéo nhau, cần 1 nhịp dùng FreeCell."""
        cards = TestCases._clear_and_prepare(game)
        for s in range(4):
            for r in range(11): # A -> J
                game.card_heaps[s].PushTop(cards[s * 13 + r])
        # Cột 8: K Heart đè bởi Q Spade
        game.card_heaps[8].PushTop(cards[12]); game.card_heaps[8].PushTop(cards[37])
        # Cột 9: K Spade đè bởi Q Heart
        game.card_heaps[9].PushTop(cards[38]); game.card_heaps[9].PushTop(cards[11])
        # Cột 10: K Diamond đè bởi Q Club
        game.card_heaps[10].PushTop(cards[25]); game.card_heaps[10].PushTop(cards[50])
        # Cột 11: K Club đè bởi Q Diamond
        game.card_heaps[11].PushTop(cards[51]); game.card_heaps[11].PushTop(cards[24])

    @staticmethod
    def setup_test_3(game: FreeCellGame):
        """Mức 3: Easy (12 lá) - J, Q, K ngược thứ tự."""
        cards = TestCases._clear_and_prepare(game)
        for s in range(4):
            for r in range(10): # A -> 10
                game.card_heaps[s].PushTop(cards[s * 13 + r])
        suits = [0, 13, 26, 39]
        for i in range(4):
            game.card_heaps[8 + i].PushTop(cards[suits[i] + 10]) # J
            game.card_heaps[8 + i].PushTop(cards[suits[i] + 11]) # Q
            game.card_heaps[8 + i].PushTop(cards[suits[i] + 12]) # K

    @staticmethod
    def setup_test_4(game: FreeCellGame):
        """Mức 4: Medium (16 lá) - Sửa lỗi kẹt bài logic. Yêu cầu gỡ rối sâu.
        Lá 10 nằm dưới cùng, bị chặn bởi J, Q, K chặn bên trên."""
        cards = TestCases._clear_and_prepare(game)
        for s in range(4):
            for r in range(9): # A -> 9
                game.card_heaps[s].PushTop(cards[s * 13 + r])

        # Col 8: 10 Club (dưới), J Heart, Q Club, K Heart (trên)
        game.card_heaps[8].PushTop(cards[39 + 9]); game.card_heaps[8].PushTop(cards[0 + 10])
        game.card_heaps[8].PushTop(cards[39 + 11]); game.card_heaps[8].PushTop(cards[0 + 12])
        # Col 9: 10 Diamond, J Spade, Q Diamond, K Spade
        game.card_heaps[9].PushTop(cards[13 + 9]); game.card_heaps[9].PushTop(cards[26 + 10])
        game.card_heaps[9].PushTop(cards[13 + 11]); game.card_heaps[9].PushTop(cards[26 + 12])
        # Col 10: 10 Spade, J Diamond, Q Spade, K Diamond
        game.card_heaps[10].PushTop(cards[26 + 9]); game.card_heaps[10].PushTop(cards[13 + 10])
        game.card_heaps[10].PushTop(cards[26 + 11]); game.card_heaps[10].PushTop(cards[13 + 12])
        # Col 11: 10 Heart, J Club, Q Heart, K Club
        game.card_heaps[11].PushTop(cards[0 + 9]); game.card_heaps[11].PushTop(cards[39 + 10])
        game.card_heaps[11].PushTop(cards[0 + 11]); game.card_heaps[11].PushTop(cards[39 + 12])

    # ==========================================
    # PHASE 2: GENERATED PARTIAL GAMES
    # ==========================================

    @staticmethod
    def setup_test_5(game: FreeCellGame):
        TestCases._setup_partial_game(game, max_foundation_rank=8, seed=5) # 20 lá còn lại (9-K)

    @staticmethod
    def setup_test_6(game: FreeCellGame):
        TestCases._setup_partial_game(game, max_foundation_rank=7, seed=6) # 24 lá còn lại (8-K)

    @staticmethod
    def setup_test_7(game: FreeCellGame):
        TestCases._setup_partial_game(game, max_foundation_rank=6, seed=7) # 28 lá còn lại (7-K)

    @staticmethod
    def setup_test_8(game: FreeCellGame):
        TestCases._setup_partial_game(game, max_foundation_rank=5, seed=8) # 32 lá còn lại (6-K)

    @staticmethod
    def setup_test_9(game: FreeCellGame):
        TestCases._setup_partial_game(game, max_foundation_rank=4, seed=9) # 36 lá còn lại (5-K)

    @staticmethod
    def setup_test_10(game: FreeCellGame):
        TestCases._setup_partial_game(game, max_foundation_rank=3, seed=10) # 40 lá còn lại (4-K)

    @staticmethod
    def setup_test_11(game: FreeCellGame):
        TestCases._setup_partial_game(game, max_foundation_rank=2, seed=11) # 44 lá còn lại (3-K)

    @staticmethod
    def setup_test_12(game: FreeCellGame):
        TestCases._setup_partial_game(game, max_foundation_rank=1, seed=12) # 48 lá còn lại (2-K)

    # ==========================================
    # PHASE 3: FULL GAMES (52 lá bài)
    # ==========================================

    @staticmethod
    def setup_test_13(game: FreeCellGame):
        """Mức 13: Full Game - Easy (Seed 25904)"""
        game.NewGameWithNumber(25904)

    @staticmethod
    def setup_test_14(game: FreeCellGame):
        """Mức 14: Full Game - Medium (Seed 1)"""
        game.NewGameWithNumber(1)

    @staticmethod
    def setup_test_15(game: FreeCellGame):
        """Mức 15: Full Game - Hard (Seed 617)"""
        game.NewGameWithNumber(617)

    @staticmethod
    def setup_test_16(game: FreeCellGame):
        """Mức 16: Full Game - Expert (Seed 11982)"""
        game.NewGameWithNumber(11982)

    @staticmethod
    def load_test(test_num: int):
        game = FreeCellGame()
        tests = {
            1: TestCases.setup_test_1,
            2: TestCases.setup_test_2,
            3: TestCases.setup_test_3,
            4: TestCases.setup_test_4,
            5: TestCases.setup_test_5,
            6: TestCases.setup_test_6,
            7: TestCases.setup_test_7,
            8: TestCases.setup_test_8,
            9: TestCases.setup_test_9,
            10: TestCases.setup_test_10,
            11: TestCases.setup_test_11,
            12: TestCases.setup_test_12,
            13: TestCases.setup_test_13,
            14: TestCases.setup_test_14,
            15: TestCases.setup_test_15,
            16: TestCases.setup_test_16,
        }
        setup_f = tests.get(test_num, TestCases.setup_test_1)
        setup_f(game)
        return game