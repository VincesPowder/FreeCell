"""
Bộ Test Case đo lường hiệu suất BFS/IDS/UCS - Đầy đủ 52 lá bài.
Mức độ khó được tinh chỉnh để thấy rõ sự khác biệt về thuật toán.
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
        """Mức 1: 12 bước - Tuyến tính (Dễ nhất).
        Foundation: Đã có từ A -> 10 (40 lá).
        Cascade: 4 cột, mỗi cột chứa K, Q, J xếp đúng thứ tự.
        Thuật toán chỉ cần bốc J, sau đó Q, cuối cùng là K của 4 chất."""
        cards = TestCases._clear_and_prepare(game)
        for s in range(4):
            for r in range(10): # A -> 10 vào Foundation
                game.card_heaps[s].PushTop(cards[s * 13 + r])
        
        # Xếp J, Q, K vào 4 cột (Cột 8-11)
        for i in range(4):
            game.card_heaps[8 + i].PushTop(cards[i * 13 + 12]) # King nằm dưới
            game.card_heaps[8 + i].PushTop(cards[i * 13 + 11]) # Queen nằm giữa
            game.card_heaps[8 + i].PushTop(cards[i * 13 + 10]) # Jack nằm trên cùng
    @staticmethod
    def setup_test_2_very_easy(game: FreeCellGame):
        """Mức 2: ~18 bước - Dễ nhưng có chút thử thách.
        36 lá ở Foundation (A -> 9). Còn lại 10, J, Q, K.
        - Phân bố 16 quân bài còn lại trên 6 cột đầu (8-13).
        - Giữ nguyên logic kẹt bài (10 nằm TRÊN Jack) cho 2 chất."""
        cards = TestCases._clear_and_prepare(game)
        for s in range(4):
            for r in range(9): # A -> 9 vào Foundation (Cards 0-8, 13-21, 26-34, 39-47)
                game.card_heaps[s].PushTop(cards[s * 13 + r])
        
        # Danh sách quân bài cascade mục tiêu dựa trên bố cục (với kẹt bài được điều chỉnh)
        cascade_cards = [
            # Heart K, Q, J, 10
            cards[12], cards[11], cards[10], cards[9],
            # Diamond K, Q, J, 10
            cards[25], cards[24], cards[23], cards[22],
            # Spade K, Q, J, 10 (thứ tự J trước 10 để xếp 10 trên J)
            cards[38], cards[37], cards[36], cards[35],  # 10 Sp trên J Sp
            # Club K, Q, J, 10 (thứ tự J trước 10 để xếp 10 trên J)
            cards[51], cards[50], cards[49], cards[48]   # 10 Cl trên J Cl
        ]
        
        # Phân bố trên 6 cột đầu (game.card_heaps[8] đến game.card_heaps[13])
        # Phân bố mục tiêu: 3, 3, 3, 3, 2, 2 quân bài
        
        col_counts = [3, 3, 3, 3, 2, 2]
        current_card_index = 0
        for i, count in enumerate(col_counts):
            for _ in range(count):
                game.card_heaps[8 + i].PushTop(cascade_cards[current_card_index])
                current_card_index += 1

    @staticmethod
    def setup_test_3_easy(game: FreeCellGame):
        """Mức 3: Dễ (Logic 1 nút thắt).
        Foundation: Đã ăn đến 9 (36 lá).
        Cascade: Chỉ kẹt duy nhất 1 quân King trên quân 10 ở cột 8.
        Các cột khác xếp hoàn hảo để tạo hiệu ứng domino khi gỡ được King."""
        cards = TestCases._clear_and_prepare(game)
        for s in range(4):
            for r in range(9): game.card_heaps[s].PushTop(cards[s * 13 + r])
        
        # Cột 8: 10 Heart bị King Heart chặn
        game.card_heaps[8].PushTop(cards[9])   # 10 H
        game.card_heaps[8].PushTop(cards[12])  # King H

        # Các cột còn lại xếp thuận thứ tự
        for r in [25, 24, 23, 22]: game.card_heaps[9].PushTop(cards[r])  # Diamond
        for r in [38, 37, 36, 35]: game.card_heaps[10].PushTop(cards[r]) # Spade
        for r in [51, 50, 49, 48]: game.card_heaps[11].PushTop(cards[r]) # Club
        game.card_heaps[12].PushTop(cards[11]) # Queen H
        game.card_heaps[12].PushTop(cards[10]) # Jack H

    @staticmethod
    def setup_test_4_medium(game: FreeCellGame):
        """Mức 4: Trung bình (Logic đa điểm kẹt).
        Foundation: Đã ăn đến 10 (40 lá).
        Cascade: 4 cột đều bị kẹt (King đè lên Queen/Jack).
        Thuật toán phải xử lý việc dọn dẹp nhiều cột cùng lúc."""
        cards = TestCases._clear_and_prepare(game)
        for s in range(4):
            for r in range(10): 
                game.card_heaps[s].PushTop(cards[s * 13 + r])
        for i in range(4):
            game.card_heaps[8 + i].PushTop(cards[i * 13 + 11]) # Q nằm dưới
            game.card_heaps[8 + i].PushTop(cards[i * 13 + 10]) # J nằm dưới
            game.card_heaps[8 + i].PushTop(cards[i * 13 + 12]) # King chặn trên cùng

    @staticmethod
    def setup_test_5_hard(game: FreeCellGame):
        """Mức 5: ~25-35 bước - Thử thách bộ nhớ."""
        cards = TestCases._clear_and_prepare(game)
        for s in range(4):
            for r in range(6): game.card_heaps[s].PushTop(cards[s * 13 + r])
        all_remain = [cards[i] for i in range(52) if cards[i].group_id == -1]
        for i, card in enumerate(all_remain):
            game.card_heaps[8 + (i % 8)].PushTop(card)

    @staticmethod
    def setup_test_6_stress_8col(game: FreeCellGame):
        """Mức 6: 44 bước - Tuyến tính (Rải trên 8 cột).
        Foundation: A, 2. Cascade: 8 cột xếp từ K -> 3 chồng lên nhau.
        Branching factor lớn do có nhiều cột để chọn."""
        cards = TestCases._clear_and_prepare(game)
        for s in range(4):
            game.card_heaps[s].PushTop(cards[s * 13 + 0]) # Ace
            game.card_heaps[s].PushTop(cards[s * 13 + 1]) # 2
        
        remaining_cards = []
        for s in range(4):
            for r in range(12, 1, -1): # K -> 3
                remaining_cards.append(cards[s * 13 + r])
        
        for i, card in enumerate(remaining_cards):
            game.card_heaps[8 + (i % 8)].PushTop(card)

    @staticmethod
    def setup_test_7_stress_4col(game: FreeCellGame):
        """Mức 7: 44 bước - Tuyến tính (Chỉ 4 cột).
        Foundation: A, 2. Cascade: 4 cột xếp đè từ K -> 3.
        Mỗi cột cao 11 lá. Ít lựa chọn cột hơn nhưng chiều sâu mỗi cột lớn."""
        cards = TestCases._clear_and_prepare(game)
        for s in range(4):
            game.card_heaps[s].PushTop(cards[s * 13 + 0]) # Ace
            game.card_heaps[s].PushTop(cards[s * 13 + 1]) # 2
        
        for s in range(4):
            for r in range(12, 1, -1): # King (dưới) -> 3 (trên)
                game.card_heaps[8 + s].PushTop(cards[s * 13 + r])
    
    @staticmethod
    def setup_test_8_seed_25904(game: FreeCellGame):
        """Mức 8: Ván chơi thực tế - Seed #25904.
        Toàn bộ 52 lá được chia ngẫu nhiên theo thuật toán của game gốc.
        Dùng để kiểm tra khả năng giải ván thực của 4 thuật toán."""
        game.NewGameWithNumber(25904)

    @staticmethod
    def setup_test_9_seed_27121(game: FreeCellGame):
        """Mức 9: Ván chơi thực tế - Seed #27121."""
        game.NewGameWithNumber(27121)

    @staticmethod
    def setup_test_10_seed_24176(game: FreeCellGame):
        """Mức 10: Ván chơi thực tế - Seed #24176."""
        game.NewGameWithNumber(24176)

    @staticmethod
    def load_test(test_num: int):
        game = FreeCellGame()
        tests = {
            1: TestCases.setup_test_1_trivial,
            2: TestCases.setup_test_2_very_easy,
            3: TestCases.setup_test_3_easy,
            4: TestCases.setup_test_4_medium,
            5: TestCases.setup_test_5_hard,
            6: TestCases.setup_test_6_stress_8col,
            7: TestCases.setup_test_7_stress_4col,
            8: TestCases.setup_test_8_seed_25904,
            9: TestCases.setup_test_9_seed_27121,
            10: TestCases.setup_test_10_seed_24176,
        }
        setup_f = tests.get(test_num, TestCases.setup_test_1_trivial)
        setup_f(game)
        return game