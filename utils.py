import pygame
from Freecell_Game import FreeCellGame

SCREEN_W = 1280
SCREEN_H = 720
CARD_W = 95     
CARD_H = 135    
GAP = 150       
X_START = 45    

def LoadImages():
    IMAGES = {}
    try:
        bg = pygame.image.load("images/background.png").convert_alpha()
        IMAGES["background"] = pygame.transform.smoothscale(bg, (SCREEN_W, SCREEN_H))
    except:
        IMAGES["background"] = pygame.Surface((SCREEN_W, SCREEN_H))
        IMAGES["background"].fill((0, 100, 0))


    game = FreeCellGame()
    
    # 1. Tạo từ điển (map) để dịch từ tên cũ sang tên file mới
    suit_map = {
        "Heart": "hearts",
        "Club": "clubs",       
        "Diamond": "diamonds",
        "Spade": "spades"
    }
    
    rank_map = {
        "A": "1", "2": "2", "3": "3", "4": "4", "5": "5", 
        "6": "6", "7": "7", "8": "8", "9": "9", "10": "10", 
        "J": "11", "Q": "12", "K": "13"
    }

    for card in game.CARDS:
        mapped_suit = suit_map.get(card.color, "")
        mapped_rank = rank_map.get(card.point, "")
        
        file_name = f"images/{mapped_suit}{mapped_rank}.png"
        
        try:
            card_img = pygame.image.load(file_name).convert_alpha()
            card_img = pygame.transform.smoothscale(card_img, (CARD_W, CARD_H))
            IMAGES[card.color + card.point] = card_img
        except Exception as e:
            print(f"Cảnh báo: Không tìm thấy ảnh {file_name}")
            error_card = pygame.Surface((CARD_W, CARD_H))
            error_card.fill((255, 0, 0))
            IMAGES[card.color + card.point] = error_card
            
    return IMAGES