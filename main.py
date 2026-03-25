import pygame
import utils
import copy
from Freecell_Game import FreeCellGame

# --- CẤU HÌNH HỆ THỐNG (1280x720) ---
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
CARD_W = 95
CARD_H = 135
GAP = 150         
X_START = 45      
OFFSET_Y = 25     
PANEL_Y = 600     # Vị trí bảng điều khiển phía dưới

pygame.init()
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("FreeCell")

IMAGES = utils.LoadImages()
FONT = pygame.font.Font(None, 22)
BTN_FONT = pygame.font.Font(None, 26)

class WindowGame:
    def __init__(self):
        self.freecell_game = FreeCellGame()
        self.freecell_game.NewGame()
        
        self.initial_state = copy.deepcopy(self.freecell_game.card_heaps)
        self.undo_stack = []
        
        self.dragging = False
        self.source_id = -1
        self.mouse_offset_x = 0
        self.mouse_offset_y = 0
        
        self.log = ["New game started! Welcome to FreeCell."]

        # --- ĐỔI TỌA ĐỘ NÚT SANG BÊN PHẢI ---
        # Tính toán: Màn hình 1280, các nút bắt đầu từ khoảng x=750 trở đi
        self.buttons = {
            "New": pygame.Rect(750, PANEL_Y + 35, 100, 45),
            "Restart": pygame.Rect(870, PANEL_Y + 35, 100, 45),
            "Undo": pygame.Rect(990, PANEL_Y + 35, 100, 45),
            "A* Solver": pygame.Rect(1110, PANEL_Y + 35, 120, 45),
        }

        self.MainLoop()

    def GetCardRect(self, pile_id, card_index):
        if pile_id < 8: 
            return pygame.Rect(X_START + GAP * pile_id, 40, CARD_W, CARD_H)
        else: 
            return pygame.Rect(X_START + GAP * (pile_id - 8), 210 + OFFSET_Y * card_index, CARD_W, CARD_H)

    def GetButtonArea(self, pos):
        for name, rect in self.buttons.items():
            if rect.collidepoint(pos):
                return name

        for pile_id in range(15, -1, -1):
            heap = self.freecell_game.card_heaps[pile_id].heap_list
            if not heap:
                if self.GetCardRect(pile_id, 0).collidepoint(pos):
                    return pile_id
            else:
                top_idx = len(heap) - 1
                if self.GetCardRect(pile_id, top_idx).collidepoint(pos):
                    return pile_id
        return -1

    def MainLoop(self):
        while True:
            mouse_pos = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); return

                if event.type == pygame.MOUSEBUTTONDOWN:
                    clicked = self.GetButtonArea(event.pos)
                    
                    if isinstance(clicked, str): 
                        if clicked == "New": self.__init__()
                        elif clicked == "Restart":
                            self.freecell_game.card_heaps = copy.deepcopy(self.initial_state)
                            self.undo_stack = []; self.log.append("Game restarted.")
                        elif clicked == "Undo" and self.undo_stack:
                            self.freecell_game.card_heaps = self.undo_stack.pop()
                            self.log.append("Move undone.")
                    
                    elif clicked != -1: 
                        heap = self.freecell_game.card_heaps[clicked].heap_list
                        if heap:
                            self.dragging = True
                            self.source_id = clicked
                            self.pre_move_state = copy.deepcopy(self.freecell_game.card_heaps)
                            card_rect = self.GetCardRect(clicked, len(heap) - 1)
                            self.mouse_offset_x = card_rect.x - event.pos[0]
                            self.mouse_offset_y = card_rect.y - event.pos[1]

                elif event.type == pygame.MOUSEBUTTONUP:
                    if self.dragging:
                        target_id = self.GetButtonArea(event.pos)
                        if isinstance(target_id, int) and target_id != -1:
                            if self.freecell_game.CheckMove(self.source_id, target_id):
                                self.undo_stack.append(self.pre_move_state)
                                self.freecell_game.Move(self.source_id, target_id)
                            else: self.log.append("Cannot place card!")
                        self.dragging = False

            self.UpdateScreen(mouse_pos)

    def UpdateScreen(self, mouse_pos):
        SCREEN.blit(IMAGES["background"], (0, 0))
        
        # 1. Vẽ Bảng điều khiển (Control Panel)
        pygame.draw.rect(SCREEN, (35, 35, 35), (0, PANEL_Y, SCREEN_WIDTH, 120))
        
        # Vẽ nút bấm (Bên phải)
        for name, rect in self.buttons.items():
            pygame.draw.rect(SCREEN, (50, 50, 50), (rect.x+3, rect.y+3, rect.width, rect.height), border_radius=8)
            pygame.draw.rect(SCREEN, (90, 90, 90), rect, border_radius=8)
            text_surf = BTN_FONT.render(name, True, (255, 255, 255))
            text_rect = text_surf.get_rect(center=rect.center)
            SCREEN.blit(text_surf, text_rect)

        # --- ĐỔI BẢNG THÔNG SỐ (LOG) SANG BÊN TRÁI ---
        # Tọa độ X=50 cho cân đối với lề trái
        for i, msg in enumerate(self.log[-4:]):
            log_text = FONT.render(msg, True, (220, 220, 220))
            SCREEN.blit(log_text, (50, PANEL_Y + 30 + i * 22))

        # 2. Vẽ các ô Slot và bài
        for pile_id in range(16):
            base_rect = self.GetCardRect(pile_id, 0)
            pygame.draw.rect(SCREEN, (255, 255, 255), base_rect, 1, border_radius=5)
            heap = self.freecell_game.card_heaps[pile_id].heap_list
            for i, card in enumerate(heap):
                if self.dragging and pile_id == self.source_id and i == len(heap) - 1:
                    continue
                rect = self.GetCardRect(pile_id, i)
                SCREEN.blit(IMAGES[card.color + card.point], (rect.x, rect.y))

        # 3. Vẽ quân bài đang kéo
        if self.dragging:
            card = self.freecell_game.card_heaps[self.source_id].heap_list[-1]
            SCREEN.blit(IMAGES[card.color + card.point], (mouse_pos[0] + self.mouse_offset_x, mouse_pos[1] + self.mouse_offset_y))

        pygame.display.update()

if __name__ == "__main__":
    WindowGame()