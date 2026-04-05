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
        """Mức 5: Supermove Tối Giản (Bản chuẩn 52 lá).
        Đã sửa lỗi mất bài: 41 lá được đưa lên Foundation an toàn.
        11 lá còn lại xếp thành thế cờ ép buộc bốc cả chuỗi."""
        cards = TestCases._clear_and_prepare(game)
        
        # Đưa 41 lá lên Foundation để đảm bảo game có thể thắng
        for r in range(8): game.card_heaps[0].PushTop(cards[0 * 13 + r]) # Hearts A->8
        for r in range(13): game.card_heaps[1].PushTop(cards[1 * 13 + r]) # Clubs A->K
        for r in range(13): game.card_heaps[2].PushTop(cards[2 * 13 + r]) # Diamonds A->K
        for r in range(7): game.card_heaps[3].PushTop(cards[3 * 13 + r]) # Spades A->7
        
        # 11 lá mấu chốt còn lại trên bàn
        # Cột 8: 9H bị đè bởi chuỗi JS -> 10H -> 9S
        game.card_heaps[8].PushTop(cards[0 * 13 + 8])  # 9 Heart
        game.card_heaps[8].PushTop(cards[3 * 13 + 10]) # J Spade
        game.card_heaps[8].PushTop(cards[0 * 13 + 9])  # 10 Heart
        game.card_heaps[8].PushTop(cards[3 * 13 + 8])  # 9 Spade
        
        # Cột 9
        game.card_heaps[9].PushTop(cards[0 * 13 + 12]) # K Heart
        game.card_heaps[9].PushTop(cards[3 * 13 + 11]) # Q Spade
        game.card_heaps[9].PushTop(cards[0 * 13 + 10]) # J Heart
        
        # Cột 10
        game.card_heaps[10].PushTop(cards[3 * 13 + 12]) # K Spade
        game.card_heaps[10].PushTop(cards[0 * 13 + 11]) # Q Heart
        
        # Cột 11
        game.card_heaps[11].PushTop(cards[3 * 13 + 9]) # 10 Spade
        
        # Cột 12
        game.card_heaps[12].PushTop(cards[3 * 13 + 7]) # 8 Spade

    @staticmethod
    def setup_test_6_stress_8col(game: FreeCellGame):
        """Mức 6: Nút thắt Supermove 2 tầng.
        Vẫn là 11 lá bài mấu chốt nhưng bị đè chéo lên nhau tạo bẫy sâu hơn."""
        cards = TestCases._clear_and_prepare(game)
        
        for r in range(8): game.card_heaps[0].PushTop(cards[0 * 13 + r]) # Hearts
        for r in range(13): game.card_heaps[1].PushTop(cards[1 * 13 + r]) # Clubs
        for r in range(13): game.card_heaps[2].PushTop(cards[2 * 13 + r]) # Diamonds
        for r in range(7): game.card_heaps[3].PushTop(cards[3 * 13 + r]) # Spades
        
        # Cột 8: 9H bị đè bởi chuỗi dài: KS -> QH -> JS -> 10H -> 9S
        game.card_heaps[8].PushTop(cards[0 * 13 + 8])  # 9H
        game.card_heaps[8].PushTop(cards[3 * 13 + 12]) # KS
        game.card_heaps[8].PushTop(cards[0 * 13 + 11]) # QH
        game.card_heaps[8].PushTop(cards[3 * 13 + 10]) # JS
        game.card_heaps[8].PushTop(cards[0 * 13 + 9])  # 10H
        game.card_heaps[8].PushTop(cards[3 * 13 + 8])  # 9S
        
        # Cột 9: 8S bị đè bởi chuỗi dài: KH -> QS -> JH -> 10S
        game.card_heaps[9].PushTop(cards[3 * 13 + 7])  # 8S
        game.card_heaps[9].PushTop(cards[0 * 13 + 12]) # KH
        game.card_heaps[9].PushTop(cards[3 * 13 + 11]) # QS
        game.card_heaps[9].PushTop(cards[0 * 13 + 10]) # JH
        game.card_heaps[9].PushTop(cards[3 * 13 + 9])  # 10S

    @staticmethod
    def setup_test_7_stress_4col(game: FreeCellGame):
        """Mức 7: Mê cung Đảo Ngược (Tuyệt tác Demo).
        Chuẩn 52 lá. 28 lá đã an toàn trên Foundation.
        24 lá còn lại nằm ở 4 cột, bị lộn ngược thứ tự từ 8 đến K.
        AI phải dùng 4 cột trống để 'lật ngược' các chuỗi bài này lại."""
        cards = TestCases._clear_and_prepare(game)
        
        # 1. Đưa 28 lá lên Foundation (A -> 7 của cả 4 chất)
        for s in range(4):
            for r in range(7):
                game.card_heaps[s].PushTop(cards[s * 13 + r])
                
        # 2. Xếp 24 lá còn lại vào 4 cột (Cột 8 -> 11) theo thứ tự ngược (8 đè lên K)
        # Các chuỗi này đã được tính toán kỹ để so le màu (Đỏ - Đen) hoàn hảo
        col8 = [cards[7], cards[47], cards[35], cards[23], cards[11], cards[51]] # 8H, 9S, 10D, JC, QH, KS
        col9 = [cards[20], cards[8], cards[48], cards[36], cards[24], cards[12]] # 8C, 9H, 10S, JD, QC, KH
        col10 = [cards[46], cards[34], cards[22], cards[10], cards[50], cards[38]] # 8S, 9D, 10C, JH, QS, KD
        col11 = [cards[33], cards[21], cards[9], cards[49], cards[37], cards[25]] # 8D, 9C, 10H, JS, QD, KC
        
        for c in col8: game.card_heaps[8].PushTop(c)
        for c in col9: game.card_heaps[9].PushTop(c)
        for c in col10: game.card_heaps[10].PushTop(c)
        for c in col11: game.card_heaps[11].PushTop(c)
    
    @staticmethod
    def setup_test_8_seed_25904(game: FreeCellGame):
        """Mức 8: Ván chơi thực tế - Seed #25904.
        Toàn bộ 52 lá được chia ngẫu nhiên theo thuật toán của game gốc.
        Dùng để kiểm tra khả năng giải ván thực của 4 thuật toán."""
        game.NewGameWithNumber(25904)

    @staticmethod
    def setup_test_9_seed_1(game: FreeCellGame):
        """Mức 9: Ván chơi thực tế - Seed #1."""
        game.NewGameWithNumber(1)

    @staticmethod
    def setup_test_10_seed_617(game: FreeCellGame):
        """Mức 10: Ván chơi thực tế - Seed #617."""
        game.NewGameWithNumber(617)

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
            9: TestCases.setup_test_9_seed_1,
            10: TestCases.setup_test_10_seed_617,
        }
        setup_f = tests.get(test_num, TestCases.setup_test_1_trivial)
        setup_f(game)
        return game