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
    @staticmethod
    def setup_test_4_medium(game: FreeCellGame):
        """Mức 4: ~15-20 bước - Yêu cầu dùng FreeCell để giải phóng bài.
        28 lá ở Foundation (A-7). 24 lá còn lại gồm đủ 4 lá 9 xếp lộn xộn."""
        cards = TestCases._clear_and_prepare(game)
        for s in range(4):
            for r in range(7): # A -> 7 vào Foundation (chỉ đến 7 để giữ 4 lá 9 ngoài)
                game.card_heaps[s].PushTop(cards[s * 13 + r])
        # Cột 8: 10 Rô (r), 9 Bích (b) đè lên 9 Rô (r) — 2 lá 9 bị kẹt
        game.card_heaps[8].PushTop(cards[22]) # 10 Diamond
        game.card_heaps[8].PushTop(cards[34]) # 9 Spade (b)
        game.card_heaps[8].PushTop(cards[21]) # 9 Diamond (r) — bị kẹt dưới
        # Cột 9: 10 Cơ (r), 9 Tép (b) đè lên 9 Cơ (r) — 2 lá 9 còn lại bị kẹt
        game.card_heaps[9].PushTop(cards[9])  # 10 Heart (r)
        game.card_heaps[9].PushTop(cards[47]) # 9 Club (b)
        game.card_heaps[9].PushTop(cards[8])  # 9 Heart (r) — bị kẹt dưới
        # Các lá còn lại (8, J, Q, K) rải rác ở cột 10-13
        for i in range(4):
            for r in [12, 11, 10]:
                if cards[i * 13 + r].group_id == -1:
                    game.card_heaps[10 + i].PushTop(cards[i * 13 + r])

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
            7: TestCases.setup_test_7_screenshot,
        }
        setup_f = tests.get(test_num, TestCases.setup_test_1_trivial)
        setup_f(game)
        return game
    
    @staticmethod
    def setup_test_7_screenshot(game: FreeCellGame):
        """Mức 7: Trạng thái thực từ ảnh chụp màn hình.
        Foundation: He(A-4), Di(A-2), Sp(A-4), Cl(A-3).
        FreeCells: 5H, 3D, 5S, 4C.
        8 cột cascade với K Bích nằm trên J Nhép ở cột 2."""
        cards = TestCases._clear_and_prepare(game)

        # Foundation
        for i in range(5):     game.card_heaps[0].PushTop(cards[i])      # HeA-He4
        for i in range(13,16): game.card_heaps[1].PushTop(cards[i])      # DiA-Di2
        for i in range(26,31): game.card_heaps[2].PushTop(cards[i])      # SpA-Sp4
        for i in range(39,43): game.card_heaps[3].PushTop(cards[i])      # ClA-Cl3

        # Col 1: DiQ SpJ He10 Sp9 Di8 Sp7 He6 Cl5 Di4
        for i in [24,36,9,34,20,32,5,43,16]:
            game.card_heaps[8].PushTop(cards[i])

        # Col 2: Sp8 ClJ SpK  (K Bich de len J Nhep)
        for i in [33,49,38]:
            game.card_heaps[9].PushTop(cards[i])

        # Col 3: DiK Cl8 Di7 Cl6
        for i in [25,46,19,44]:
            game.card_heaps[10].PushTop(cards[i])

        # Col 4: Di10 Cl9 He8 Cl7
        for i in [22,47,7,45]:
            game.card_heaps[11].PushTop(cards[i])

        # Col 5: ClK HeQ
        for i in [51,11]:
            game.card_heaps[12].PushTop(cards[i])

        # Col 6: SpQ HeJ Cl10 He9
        for i in [37,10,48,8]:
            game.card_heaps[13].PushTop(cards[i])

        # Col 7: HeK Di9 Di6 He7 Sp6 Di5
        for i in [12,21,18,6,31,17]:
            game.card_heaps[14].PushTop(cards[i])

        # Col 8: ClQ DiJ Sp10
        for i in [50,23,35]:
            game.card_heaps[15].PushTop(cards[i])