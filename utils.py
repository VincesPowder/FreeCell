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
    try:
        win = pygame.image.load("images/win.png").convert_alpha()
        IMAGES["win"] = pygame.transform.smoothscale(win, (400, 200))
    except: pass

    game = FreeCellGame()
    try:
        raw_blank = pygame.image.load("images/blank_card.png").convert_alpha()
    except:
        raw_blank = pygame.Surface((200, 300))
        raw_blank.fill((255, 255, 255))

    for card in game.CARDS:
        blank_card = pygame.transform.smoothscale(raw_blank, (CARD_W, CARD_H))
        try:
            color_icon = pygame.image.load(f"images/{card.color}.png").convert_alpha()
            point_icon = pygame.image.load(f"images/{card.point}-icon.png").convert_alpha()
            
            color_icon = pygame.transform.smoothscale(color_icon, (30, 30))
            point_icon = pygame.transform.smoothscale(point_icon, (30, 30))
            
            blank_card.blit(point_icon, (5, 5))
            blank_card.blit(color_icon, (CARD_W - 35, 5))
        except:
            pass 
            
        IMAGES[card.color + card.point] = blank_card
        
    return IMAGES