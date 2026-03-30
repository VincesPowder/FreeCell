import pygame
import psutil
import os
from Freecell_Game import FreeCellGame

SCREEN_W = 1280
SCREEN_H = 720
CARD_W = 95     # Giảm nhẹ chiều rộng
CARD_H = 135    # Giảm nhẹ chiều cao để tăng khoảng trống dọc
GAP = 150       # Tăng khoảng cách ngang vì màn hình giờ rất rộng (1280px)
X_START = 45    # Căn lề trái rộng hơn cho cân đối

def LoadImages():
    IMAGES = {}
    # 1. Load background và ép về đúng size màn hình 1200x800
    try:
        bg = pygame.image.load("images/background.png").convert_alpha()
        IMAGES["background"] = pygame.transform.smoothscale(bg, (SCREEN_W, SCREEN_H))
    except:
        # Tạo màu xanh lá tạm thời nếu thiếu file ảnh
        IMAGES["background"] = pygame.Surface((SCREEN_W, SCREEN_H))
        IMAGES["background"].fill((0, 100, 0))

    # 2. Load ảnh thắng
    try:
        win = pygame.image.load("images/win.png").convert_alpha()
        IMAGES["win"] = pygame.transform.smoothscale(win, (400, 200))
    except: pass

    game = FreeCellGame()
    # 3. Phôi thẻ bài gốc - cực kỳ quan trọng để chống kéo dãn
    try:
        raw_blank = pygame.image.load("images/blank_card.png").convert_alpha()
    except:
        raw_blank = pygame.Surface((200, 300)) # Tạo phôi tạm nếu thiếu file
        raw_blank.fill((255, 255, 255))

    for card in game.CARDS:
        # ÉP PHÔI VỀ 100x145 (Tỷ lệ chuẩn)
        blank_card = pygame.transform.smoothscale(raw_blank, (CARD_W, CARD_H))
        
        # Load icon màu và số
        try:
            color_icon = pygame.image.load(f"images/{card.color}.png").convert_alpha()
            point_icon = pygame.image.load(f"images/{card.point}-icon.png").convert_alpha()
            
            # Ép icon về size nhỏ để không làm biến dạng bài
            color_icon = pygame.transform.smoothscale(color_icon, (30, 30))
            point_icon = pygame.transform.smoothscale(point_icon, (30, 30))
            
            # Vẽ lên phôi
            blank_card.blit(point_icon, (5, 5))
            blank_card.blit(color_icon, (CARD_W - 35, 5))
        except:
            pass # Bỏ qua nếu thiếu icon, vẫn giữ lại phôi trắng
            
        IMAGES[card.color + card.point] = blank_card
        
    return IMAGES



def LoadRects():
    RECTS = {}
    # Hàng trên (ID: 0-7) - 4 Foundation + 4 FreeCell
    for x in range(8):
        RECTS[x] = pygame.Rect(X_START + GAP * x, 20, CARD_W, CARD_H)
    
    # Hàng dưới (ID: 8-15) - 8 Cascades
    # Dùng chung công thức X_START + GAP * (x - 8) để thẳng hàng tuyệt đối
    for x in range(8, 16):
        RECTS[x] = pygame.Rect(X_START + GAP * (x - 8), 200, CARD_W, 500)
    return RECTS

def get_memory_use():
    """Hàm đo bộ nhớ đang sử dụng (MB) để làm báo cáo đồ án"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024