import pygame
import utils
import copy
from Freecell_Game import FreeCellGame

# --- CẤU HÌNH ---
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
CARD_W = 95
CARD_H = 135
GAP = 150         
X_START = 45      
OFFSET_Y = 25     
PANEL_Y = 600     

pygame.init()
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("FreeCell Pro - Multiple Drag & Drop")

IMAGES = utils.LoadImages()
FONT = pygame.font.Font(None, 22)
BTN_FONT = pygame.font.Font(None, 26)

class WindowGame:
    def __init__(self):
        self.freecell_game = FreeCellGame()
        self.freecell_game.NewGame()
        
        self.initial_state = copy.deepcopy(self.freecell_game.card_heaps)
        self.undo_stack = []
        
        # Biến kéo thả mới
        self.dragging = False
        self.source_id = -1
        self.drag_start_idx = -1
        self.drag_cards = [] 
        self.mouse_offset_x = 0
        self.mouse_offset_y = 0
        
        self.log = ["New game started! Space rule applied."]
        self.buttons = {
            "New": pygame.Rect(750, PANEL_Y + 35, 100, 45),
            "Restart": pygame.Rect(870, PANEL_Y + 35, 100, 45),
            "Undo": pygame.Rect(990, PANEL_Y + 35, 100, 45),
        }
        self.MainLoop()

    def GetCardRect(self, pile_id, card_index):
        if pile_id < 8: 
            return pygame.Rect(X_START + GAP * pile_id, 40, CARD_W, CARD_H)
        else: 
            return pygame.Rect(X_START + GAP * (pile_id - 8), 210 + OFFSET_Y * card_index, CARD_W, CARD_H)

    def GetClickedPileAndCard(self, pos):
        """Xác định pile_id và index của lá bài bị click"""
        # Kiểm tra nút bấm trước
        for name, rect in self.buttons.items():
            if rect.collidepoint(pos): return name, -1

        # Kiểm tra từ dưới lên trên các cột (để lấy lá bài nằm đè lên trước)
        for pile_id in range(15, -1, -1):
            heap = self.freecell_game.card_heaps[pile_id].heap_list
            if not heap:
                if self.GetCardRect(pile_id, 0).collidepoint(pos):
                    return pile_id, -1
            else:
                for i in range(len(heap) - 1, -1, -1):
                    if self.GetCardRect(pile_id, i).collidepoint(pos):
                        return pile_id, i
        return -1, -1

    def MainLoop(self):
        while True:
            mouse_pos = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); return

                if event.type == pygame.MOUSEBUTTONDOWN:
                    p_id, c_idx = self.GetClickedPileAndCard(event.pos)
                    
                    if isinstance(p_id, str): # Click nút
                        if p_id == "New": self.__init__()
                        elif p_id == "Restart":
                            self.freecell_game.card_heaps = copy.deepcopy(self.initial_state)
                            self.undo_stack = []; self.log.append("Game restarted.")
                        elif p_id == "Undo" and self.undo_stack:
                            self.freecell_game.card_heaps = self.undo_stack.pop()
                            self.log.append("Move undone.")
                    
                    elif p_id != -1 and c_idx != -1: # Click vào bài
                        heap = self.freecell_game.card_heaps[p_id].heap_list
                        self.drag_cards = heap[c_idx:]
                        
                        # Kiểm tra xem dây bài này có hợp lệ để bắt đầu kéo không
                        if not self.freecell_game.IsValidSequence(self.drag_cards):
                            self.log.append("Invalid sequence!")
                        else:
                            # Kiểm tra có đủ ô trống để kéo dây bài này không
                            max_allowed = self.freecell_game.GetMaxMovable(p_id, len(self.drag_cards))
                            if len(self.drag_cards) > max_allowed:
                                self.log.append(f"Chỉ được kéo tối đa {max_allowed} lá (còn {sum(1 for i in range(4,8) if not self.freecell_game.card_heaps[i].heap_list)} ô trống)")
                            else:
                                self.dragging = True
                                self.source_id = p_id
                                self.drag_start_idx = c_idx
                                self.pre_move_state = copy.deepcopy(self.freecell_game.card_heaps)
                                
                                card_rect = self.GetCardRect(p_id, c_idx)
                                self.mouse_offset_x = card_rect.x - event.pos[0]
                                self.mouse_offset_y = card_rect.y - event.pos[1]

                elif event.type == pygame.MOUSEBUTTONUP:
                    if self.dragging:
                        target_id, _ = self.GetClickedPileAndCard(event.pos)
                        if isinstance(target_id, int) and target_id != -1:
                            # Sử dụng hàm CheckMoveSequence mới tạo ở trên
                            can_move, msg = self.freecell_game.CheckMoveSequence(self.source_id, target_id, self.drag_start_idx)
                            if can_move:
                                self.undo_stack.append(self.pre_move_state)
                                # Di chuyển từng lá một trong dây bài
                                for _ in range(len(self.drag_cards)):
                                    # Cần viết logic lấy đúng lá bài đó. 
                                    # Ở đây đơn giản là bốc từ vị trí drag_start_idx của source
                                    card_to_move = self.freecell_game.card_heaps[self.source_id].heap_list.pop(self.drag_start_idx)
                                    self.freecell_game.card_heaps[target_id].PushTop(card_to_move)
                                self.log.append(f"Moved {len(self.drag_cards)} cards.")
                            else:
                                self.log.append(msg)
                        
                        self.dragging = False
                        self.drag_cards = []

            self.UpdateScreen(mouse_pos)

    def UpdateScreen(self, mouse_pos):
        SCREEN.blit(IMAGES["background"], (0, 0))
        pygame.draw.rect(SCREEN, (35, 35, 35), (0, PANEL_Y, SCREEN_WIDTH, 120))
        
        # Vẽ nút
        for name, rect in self.buttons.items():
            pygame.draw.rect(SCREEN, (90, 90, 90), rect, border_radius=8)
            text_surf = BTN_FONT.render(name, True, (255, 255, 255))
            SCREEN.blit(text_surf, text_surf.get_rect(center=rect.center))

        # Vẽ Log
        for i, msg in enumerate(self.log[-4:]):
            log_text = FONT.render(msg, True, (220, 220, 220))
            SCREEN.blit(log_text, (50, PANEL_Y + 30 + i * 22))

        # Vẽ các cột bài
        for pile_id in range(16):
            # Vẽ ô trống
            base_rect = self.GetCardRect(pile_id, 0)
            pygame.draw.rect(SCREEN, (255, 255, 255), base_rect, 1, border_radius=5)
            
            heap = self.freecell_game.card_heaps[pile_id].heap_list
            for i, card in enumerate(heap):
                # Không vẽ những lá đang bị kéo
                if self.dragging and pile_id == self.source_id and i >= self.drag_start_idx:
                    continue
                rect = self.GetCardRect(pile_id, i)
                SCREEN.blit(IMAGES[card.color + card.point], (rect.x, rect.y))

        # Vẽ chùm bài đang kéo
        if self.dragging:
            for i, card in enumerate(self.drag_cards):
                drag_x = mouse_pos[0] + self.mouse_offset_x
                drag_y = mouse_pos[1] + self.mouse_offset_y + (i * OFFSET_Y)
                SCREEN.blit(IMAGES[card.color + card.point], (drag_x, drag_y))

        pygame.display.update()

if __name__ == "__main__":
    WindowGame()