"""
Bộ Test Case đo lường hiệu suất BFS - Đầy đủ 52 lá bài.
Mức độ khó tăng dần dựa trên số lượng quân bài còn lại ở cột Cascade.
"""
from Freecell_Game import FreeCellGame

class TestCases:
    @staticmethod
    def _clear_and_prepare(game: FreeCellGame):
        for heap in game.card_heaps:
            heap.heap_list = []
        return game.CARDS # Trả về 52 lá: 0-12 Heart, 13-25 Diamond, 26-38 Spade, 39-51 Club

    @staticmethod
    def setup_test_1_trivial(game: FreeCellGame):
        """Mức 1: 1-2 bước (Trivial) - Kiểm tra logic thắng cơ bản.
        48 lá ở Foundation, 4 lá King nằm ở đầu 4 cột."""
        cards = TestCases._clear_and_prepare(game)
        for s in range(4):
            for r in range(12): # A -> Q vào Foundation
                game.card_heaps[s].PushTop(cards[s * 13 + r])
        # 4 King ở 4 cột khác nhau
        for i in range(4):
            game.card_heaps[8 + i].PushTop(cards[i * 13 + 12])

    @staticmethod
    def setup_test_2_very_easy(game: FreeCellGame):
        """Mức 2: ~4-6 bước - Kiểm tra khả năng di chuyển bài giữa các cột.
        44 lá ở Foundation. Cần xếp lại Q, K rồi mới lên Foundation."""
        cards = TestCases._clear_and_prepare(game)
        for s in range(4):
            for r in range(11): # A -> J vào Foundation
                game.card_heaps[s].PushTop(cards[s * 13 + r])
        # Cột 8: K Cơ, Q Cơ (Sai thứ tự)
        game.card_heaps[8].PushTop(cards[12]) # K Heart
        game.card_heaps[8].PushTop(cards[11]) # Q Heart
        # Cột 9-11: Các cặp Q-K khác đúng thứ tự nhưng chưa lên Foundation
        game.card_heaps[9].PushTop(cards[25])
        game.card_heaps[9].PushTop(cards[24])
        game.card_heaps[10].PushTop(cards[38])
        game.card_heaps[10].PushTop(cards[37])
        game.card_heaps[11].PushTop(cards[51])
        game.card_heaps[11].PushTop(cards[50])

    @staticmethod
    def setup_test_3_easy(game: FreeCellGame):
        """Mức 3: ~8-12 bước - Bắt đầu xuất hiện sự kẹt bài nhẹ.
        40 lá ở Foundation (A-10). Các quân J, Q, K xếp lộn xộn."""
        cards = TestCases._clear_and_prepare(game)
        for s in range(4):
            for r in range(10): # A -> 10 vào Foundation
                game.card_heaps[s].PushTop(cards[s * 13 + r])
        # Xếp lộn xộn J, Q, K ở 4 cột để BFS phải tìm thứ tự đúng
        order = [12, 10, 11] # K, J, Q
        for i in range(4):
            for off in order:
                game.card_heaps[8 + i].PushTop(cards[i * 13 + off])

    @staticmethod
    def setup_test_4_medium(game: FreeCellGame):
        """Mức 4: ~15-20 bước - Yêu cầu dùng FreeCell để giải phóng bài.
        32 lá ở Foundation (A-8). 20 lá còn lại xếp thành các dãy xen kẽ r-b."""
        cards = TestCases._clear_and_prepare(game)
        for s in range(4):
            for r in range(8): # A -> 8 vào Foundation
                game.card_heaps[s].PushTop(cards[s * 13 + r])
        # Cột 8: 10 Rô (r), 9 Bích (b) đè lên 9 Rô (r)
        game.card_heaps[8].PushTop(cards[22]) # 10 Diamond
        game.card_heaps[8].PushTop(cards[34]) # 9 Spade
        game.card_heaps[8].PushTop(cards[21]) # 9 Diamond (Đang bị kẹt)
        # Thêm 9 Cơ và 9 Nhép vào 2 cột riêng (đủ 4 lá 9)
        game.card_heaps[12].PushTop(cards[8])  # 9 Heart
        game.card_heaps[13].PushTop(cards[47]) # 9 Club
        # Các lá còn lại (10, J, Q, K) rải rác
        for i in range(4):
            for r in [12, 11, 10, 9]:
                if cards[i * 13 + r].group_id == -1: # Nếu chưa xếp
                    game.card_heaps[9 + i].PushTop(cards[i * 13 + r])

    @staticmethod
    def setup_test_5_hard(game: FreeCellGame):
        """Mức 5: ~25-35 bước - Thử thách bộ nhớ của BFS.
        24 lá ở Foundation (A-6). Số lượng trạng thái bắt đầu bùng nổ."""
        cards = TestCases._clear_and_prepare(game)
        for s in range(4):
            for r in range(6): game.card_heaps[s].PushTop(cards[s * 13 + r])
        # Xếp 28 lá còn lại vào 8 cột, tạo ra nhiều nước đi giả (nước đi không dẫn tới đích)
        all_remain = [cards[i] for i in range(52) if cards[i].group_id == -1]
        for i, card in enumerate(all_remain):
            game.card_heaps[8 + (i % 8)].PushTop(card)

    @staticmethod
    def setup_test_6_stress(game: FreeCellGame):
        """Mức 6: Giới hạn của BFS - Game nguyên bản (Seed 1).
        Toàn bộ 52 lá ở Cascade. BFS thường sẽ hết RAM hoặc chạy rất lâu."""
        game.NewGameWithNumber(1)

    @staticmethod
    def load_test(test_num: int):
        game = FreeCellGame()
        tests = {
            1: TestCases.setup_test_1_trivial,
            2: TestCases.setup_test_2_very_easy,
            3: TestCases.setup_test_3_easy,
            4: TestCases.setup_test_4_medium,
            5: TestCases.setup_test_5_hard,
            6: TestCases.setup_test_6_stress,
        }
        setup_f = tests.get(test_num, TestCases.setup_test_1_trivial)
        setup_f(game)
        return game