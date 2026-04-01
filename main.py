import pygame
import utils
import copy
import time
from Freecell_Game import FreeCellGame
from BFS_Solver import BFSSolver
from A_Star_Solver import AStarSolver
from test_cases import TestCases
import threading
import random

# Cấu hình hằng số
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
CARD_W = 95
CARD_H = 135
GAP = 150         
X_START = 68      
OFFSET_Y = 25     
PANEL_Y = 600     

pygame.init()
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("FreeCell & Solver")

IMAGES = utils.LoadImages()
FONT = pygame.font.SysFont('arial', 16)
BTN_FONT = pygame.font.SysFont('arial', 16)

class WindowGame:
    def __init__(self):
        self.freecell_game = FreeCellGame()
        if not hasattr(self, 'seed'):
            self.seed = random.randint(0, 32000)
        self.freecell_game.NewGameWithNumber(self.seed)

        self.initial_state = copy.deepcopy(self.freecell_game.card_heaps)
        self.undo_stack = []
        
        self.dragging = False
        self.source_id = -1
        self.drag_start_idx = -1
        self.drag_cards = [] 
        self.mouse_offset_x = 0
        self.mouse_offset_y = 0
        
        self.log = [f"New game started! Seed: {self.seed}"]
        self.log_offset = 0  
        self.button_highlight_time = {}  
        self.highlight_duration = 0.15  
        
        # Cập nhật vị trí các nút: Test nằm dưới Seed
        self.buttons = {
            "New": pygame.Rect(800, PANEL_Y + 20, 90, 35),
            "Restart": pygame.Rect(900, PANEL_Y + 20, 90, 35),
            "Undo": pygame.Rect(1000, PANEL_Y + 20, 90, 35),
            "Seed": pygame.Rect(1100, PANEL_Y + 20, 90, 35),
            "Test": pygame.Rect(1100, PANEL_Y + 60, 90, 35),
            "Solver": pygame.Rect(900, PANEL_Y + 60, 90, 35),
            "Quit": pygame.Rect(1000, PANEL_Y + 60, 90, 35),
        }
        
        self.seed_input_open = False
        self.seed_text = str(self.seed)
        
        self.solver_menu_open = False
        self.solver_menu = {
            "BFS": pygame.Rect(900, PANEL_Y - 120, 90, 30),
            "DFS": pygame.Rect(900, PANEL_Y - 90, 90, 30),
            "UCS": pygame.Rect(900, PANEL_Y - 60, 90, 30),
            "A*": pygame.Rect(900, PANEL_Y - 30, 90, 30),
        }
        
        self.test_menu_open = False
        self.test_menu = {}
        for i in range(1, 17):
            self.test_menu[f"Test {i}"] = i
        self.test_menu_scroll_offset = 0
        self.max_visible_tests = 4
        
        self.solver_running = False
        self.solver_result = None
        self.solver_selected = None
        self.pending_solver_results = []  
        
        self.animation_running = False
        self.animation_moves = []
        self.animation_current_move = 0
        self.animation_start_time = None
        self.move_duration = 0.5  
        
        self.MainLoop()

    def stop_animation(self):
        self.animation_running = False
        self.log.append("Animation stopped")
        self.log_offset = 0
    
    def update_animation(self):
        if not self.animation_running or not self.animation_moves or self.animation_start_time is None:
            return
        
        current_time = time.time()
        elapsed = current_time - self.animation_start_time
        moves_to_play = int(elapsed / self.move_duration)
        
        while self.animation_current_move < moves_to_play and self.animation_current_move < len(self.animation_moves):
            # --- CHỈ CHỈNH SỬA TỪ ĐÂY ---
            move = self.animation_moves[self.animation_current_move]
            from_id, to_id, card_idx = move # Lấy 3 giá trị
            
            # Thực hiện bốc cả chuỗi (từ card_idx đến hết)
            heap_from = self.freecell_game.card_heaps[from_id].heap_list
            num_to_move = len(heap_from) - card_idx
            
            for _ in range(num_to_move):
                card = self.freecell_game.card_heaps[from_id].heap_list.pop(card_idx)
                self.freecell_game.card_heaps[to_id].PushTop(card)
                
            self.log.append(f"[Animation] Move {self.animation_current_move + 1}/{len(self.animation_moves)}: Heap {from_id} → {to_id}")
            # --- ĐẾN ĐÂY ---

            self.log_offset = 0
            self.animation_current_move += 1
        
        if self.animation_current_move >= len(self.animation_moves):
            self.animation_running = False
            self.log.append("Animation complete! All moves played.")
            self.log_offset = 0
            
            if self.pending_solver_results:
                self.log.extend(self.pending_solver_results)
                self.pending_solver_results = []
                self.log_offset = 0
    def GetCardRect(self, pile_id, card_index):
        if pile_id < 8: 
            return pygame.Rect(X_START + GAP * pile_id, 40, CARD_W, CARD_H)
        else: 
            return pygame.Rect(X_START + GAP * (pile_id - 8), 210 + OFFSET_Y * card_index, CARD_W, CARD_H)
    
    def run_solver_thread(self, solver_algo):
        try:
            if solver_algo == "BFS":
                solver = BFSSolver(self.freecell_game)
                self.solver_result = solver.solve(max_nodes=1000000, timeout=180)
                self.solver_selected = "BFS"
            elif solver_algo == "A*":
                solver = AStarSolver(self.freecell_game)
                self.solver_result = solver.solve(max_nodes=100000, timeout=60)
                self.solver_selected = "A*"
            else:
                self.log.append(f"{solver_algo} solver not implemented yet")
                self.log_offset = 0
                self.solver_running = False
                return

            results_log = [
                "Results:",
                f"  Solved: {self.solver_result.get('solved', False)}",
                f"  Solution length: {self.solver_result.get('search_length', 0)}",
                f"  Expanded nodes: {self.solver_result.get('expanded_nodes', 0)}",
                f"  Search time: {self.solver_result.get('search_time', 0):.2f}s",
                f"  Memory used: {self.solver_result.get('memory_used', 0):.2f}MB"
            ]
            
            # --- ĐOẠN CODE MỚI: GHI LOG VÀO FILE log.txt ---
            try:
                import datetime
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with open("log.txt", "a", encoding="utf-8") as log_file:
                    log_file.write(f"[{current_time}] Game Seed: {self.seed} | Solver: {solver_algo}\n")
                    if not self.solver_result.get('solved'):
                        error_msg = self.solver_result.get('error', 'No solution found')
                        log_file.write(f"  Error: {error_msg}\n")
                    for line in results_log:
                        log_file.write(f"{line}\n")
                    log_file.write("-" * 40 + "\n")
            except Exception as file_err:
                self.log.append(f"Warning: Cannot write to log.txt ({file_err})")
                self.log_offset = 0

            if self.solver_result.get('solved') and self.solver_result.get('solution'):
                self.pending_solver_results = results_log
                self.animation_moves = self.solver_result['solution']
                self.animation_current_move = 0
                self.animation_start_time = time.time()
                self.animation_running = True
                self.log.append(f"Playing animation...")
                self.log_offset = 0
            else:
                error_msg = self.solver_result.get('error', 'No solution found')
                self.log.append(f"{solver_algo}: {error_msg}")
                self.log.extend(results_log)
                self.log_offset = 0
                
        except Exception as e:
            self.log.append(f"Error running {solver_algo}: {str(e)}")
            self.log_offset = 0
        
        self.solver_running = False

    def GetClickedPileAndCard(self, pos):
        if self.buttons["Seed"].collidepoint(pos):
            return "seed", -1
        
        if self.buttons["Test"].collidepoint(pos):
            return "test", -1
        
        if self.buttons["Solver"].collidepoint(pos):
            return "solver", -1
        
        if self.test_menu_open:
            visible_tests = list(self.test_menu.keys())[self.test_menu_scroll_offset:self.test_menu_scroll_offset + self.max_visible_tests]
            for idx, test_name in enumerate(visible_tests):
                # Đã chỉnh về x=1100 để khớp với giao diện vẽ
                test_rect = pygame.Rect(1100, PANEL_Y - 30 - idx * 30, 90, 30)
                if test_rect.collidepoint(pos):
                    return test_name, -1
        
        if self.solver_menu_open:
            for algo, rect in self.solver_menu.items():
                if rect.collidepoint(pos):
                    return algo, -1
        
        for name, rect in self.buttons.items():
            if name not in ["Seed", "Test", "Solver"] and rect.collidepoint(pos):
                return name, -1

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

                if event.type == pygame.KEYDOWN:
                    if self.seed_input_open:
                        if event.key == pygame.K_RETURN:
                            try:
                                val = int(self.seed_text)
                                if val < 0 or val > 32000:
                                    self.log.append("Seed must be between 0 and 32000")
                                    self.log_offset = 0
                                else:
                                    self.seed = val
                                    self.freecell_game = FreeCellGame()
                                    self.freecell_game.NewGameWithNumber(self.seed)
                                    self.initial_state = copy.deepcopy(self.freecell_game.card_heaps)
                                    self.undo_stack = []
                                    self.animation_moves = []
                                    self.animation_running = False
                                    self.pending_solver_results = []
                                    self.log = [f"New game! Seed: {self.seed}"]
                                    self.seed_input_open = False
                            except Exception:
                                self.log.append("Invalid seed input")
                                self.log_offset = 0
                        elif event.key == pygame.K_BACKSPACE:
                            self.seed_text = self.seed_text[:-1]
                        elif event.key == pygame.K_ESCAPE:
                            self.seed_input_open = False
                        else:
                            if event.unicode.isdigit():
                                self.seed_text += event.unicode

                if event.type == pygame.MOUSEBUTTONDOWN:
                    # Phân biệt nút cuộn và nút click
                    if event.button == 4:  # Scroll up
                        # Nếu chuột đang ở vùng menu Test thì cuộn Test
                        test_menu_area = pygame.Rect(1100, PANEL_Y - 150, 110, 150)
                        if self.test_menu_open and test_menu_area.collidepoint(event.pos):
                            self.test_menu_scroll_offset = max(0, self.test_menu_scroll_offset - 1)
                        else:
                            self.log_offset = min(self.log_offset + 1, max(0, len(self.log) - 4))
                            
                    elif event.button == 5:  # Scroll down
                        test_menu_area = pygame.Rect(1100, PANEL_Y - 150, 110, 150)
                        if self.test_menu_open and test_menu_area.collidepoint(event.pos):
                            max_offset = max(0, len(self.test_menu) - self.max_visible_tests)
                            self.test_menu_scroll_offset = min(self.test_menu_scroll_offset + 1, max_offset)
                        else:
                            self.log_offset = max(self.log_offset - 1, 0)
                    
                    elif event.button == 1: # CHỈ XỬ LÝ CLICK KHI LÀ CHUỘT TRÁI
                        p_id, c_idx = self.GetClickedPileAndCard(event.pos)
                        
                        if isinstance(p_id, str):
                            if p_id == "seed":
                                self.seed_input_open = not self.seed_input_open
                                self.solver_menu_open = False
                                self.test_menu_open = False
                            elif p_id == "test":
                                self.test_menu_open = not self.test_menu_open
                                self.test_menu_scroll_offset = 0 
                                self.seed_input_open = False
                                self.solver_menu_open = False
                            elif p_id.startswith("Test "):
                                test_num = int(p_id.split()[1])
                                self.freecell_game = TestCases.load_test(test_num)
                                self.seed = -test_num  
                                self.initial_state = copy.deepcopy(self.freecell_game.card_heaps)
                                self.undo_stack = []
                                self.animation_moves = []
                                self.animation_running = False
                                self.pending_solver_results = []
                                self.log.append(f"Test {test_num} loaded!")
                                self.log_offset = 0
                                self.test_menu_open = False
                                self.button_highlight_time["Test"] = time.time()
                            elif p_id == "solver":
                                self.solver_menu_open = not self.solver_menu_open
                                self.seed_input_open = False
                                self.test_menu_open = False
                            elif p_id in ["BFS", "DFS", "UCS", "A*"]:
                                if not self.solver_running:
                                    self.solver_running = True
                                    self.solver_menu_open = False
                                    self.log.append(f"Running {p_id} solver...")
                                    self.log_offset = 0
                                    solver_thread = threading.Thread(target=self.run_solver_thread, args=(p_id,), daemon=True)
                                    solver_thread.start()
                                else:
                                    self.log.append("Solver already running...")
                                    self.log_offset = 0
                            elif p_id == "New": 
                                self.seed = random.randint(0, 32000)
                                self.freecell_game = FreeCellGame()
                                self.freecell_game.NewGameWithNumber(self.seed)
                                self.initial_state = copy.deepcopy(self.freecell_game.card_heaps)
                                self.undo_stack = []
                                self.animation_moves = []
                                self.animation_running = False
                                self.pending_solver_results = []
                                self.log = [f"New game! Seed: {self.seed}"]
                                self.log_offset = 0
                                self.seed_input_open = False
                                self.button_highlight_time["New"] = time.time()
                            elif p_id == "Restart":
                                self.freecell_game.card_heaps = copy.deepcopy(self.initial_state)
                                self.undo_stack = []
                                self.animation_moves = []
                                self.animation_running = False
                                self.pending_solver_results = []
                                self.log.append("Game restarted.")
                                self.log_offset = 0
                                self.button_highlight_time["Restart"] = time.time()
                            elif p_id == "Undo" and self.undo_stack:
                                self.freecell_game.card_heaps = self.undo_stack.pop()
                                self.log.append("Move undone.")
                                self.log_offset = 0
                                self.button_highlight_time["Undo"] = time.time()
                            elif p_id == "Quit":
                                pygame.quit()
                                return
                        
                        elif p_id != -1 and c_idx != -1: 
                            self.seed_input_open = False
                            self.solver_menu_open = False
                            heap = self.freecell_game.card_heaps[p_id].heap_list
                            self.drag_cards = heap[c_idx:]
                            
                            can_drag, error_msg = self.freecell_game.CheckMoveSequence(p_id, p_id, c_idx)
                            
                            if not self.freecell_game.IsValidSequence(self.drag_cards):
                                self.log.append("Invalid sequence!")
                                self.log_offset = 0
                            else:
                                max_allowed = self.freecell_game.GetMaxMovable(p_id, len(self.drag_cards))
                                if len(self.drag_cards) > max_allowed:
                                    free_cells = sum(1 for i in range(4,8) if not self.freecell_game.card_heaps[i].heap_list)
                                    self.log.append(f"Can only move max {max_allowed} cards (free cells: {free_cells})")
                                    self.log_offset = 0
                                else:
                                    self.dragging = True
                                    self.source_id = p_id
                                    self.drag_start_idx = c_idx
                                    self.pre_move_state = copy.deepcopy(self.freecell_game.card_heaps)
                                    
                                    card_rect = self.GetCardRect(p_id, c_idx)
                                    self.mouse_offset_x = card_rect.x - event.pos[0]
                                    self.mouse_offset_y = card_rect.y - event.pos[1]

                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1 and self.dragging:
                        target_id, _ = self.GetClickedPileAndCard(event.pos)
                        if isinstance(target_id, int) and target_id != -1:
                            can_move, msg = self.freecell_game.CheckMoveSequence(self.source_id, target_id, self.drag_start_idx)
                            if can_move:
                                self.undo_stack.append(self.pre_move_state)
                                for _ in range(len(self.drag_cards)):
                                    card_to_move = self.freecell_game.card_heaps[self.source_id].heap_list.pop(self.drag_start_idx)
                                    self.freecell_game.card_heaps[target_id].PushTop(card_to_move)
                                self.log.append(f"Moved {len(self.drag_cards)} cards.")
                                self.log_offset = 0
                            else:
                                self.log.append(msg)
                                self.log_offset = 0
                        
                        self.dragging = False
                        self.drag_cards = []

            self.update_animation()
            self.UpdateScreen(mouse_pos)

    def UpdateScreen(self, mouse_pos):
        SCREEN.blit(IMAGES["background"], (0, 0))
        pygame.draw.rect(SCREEN, (30, 65, 70), (0, PANEL_Y, SCREEN_WIDTH, 120))
        
        for name, rect in self.buttons.items():
            is_highlighted = False
            if name == "Seed" and self.seed_input_open:
                is_highlighted = True
            elif name in self.button_highlight_time:
                elapsed = time.time() - self.button_highlight_time[name]
                if elapsed < self.highlight_duration:
                    is_highlighted = True
                else:
                    del self.button_highlight_time[name]
            
            color = (200, 230, 150) if is_highlighted else (255, 200, 230)
            pygame.draw.rect(SCREEN, color, rect, border_radius=5)
            
            text_surf = FONT.render(name, True, (155, 50, 100))
            SCREEN.blit(text_surf, text_surf.get_rect(center=rect.center))
        
        if self.seed_input_open:
            seed_rect = pygame.Rect(1100, PANEL_Y - 40, 140, 30)
            pygame.draw.rect(SCREEN, (255, 255, 255), seed_rect, border_radius=4)
            pygame.draw.rect(SCREEN, (155,50,100), seed_rect, 2, border_radius=4)
            prompt = FONT.render("Enter seed (0-32000):", True, (255,255,255))
            SCREEN.blit(prompt, (1100, PANEL_Y - 68))
            seed_text_surf = FONT.render(self.seed_text, True, (155,50,100))
            SCREEN.blit(seed_text_surf, (seed_rect.x + 6, seed_rect.y + 6))

        if self.solver_menu_open:
            for algo, rect in self.solver_menu.items():
                color = (200, 230, 150) if self.solver_selected == algo else (255, 200, 230)
                pygame.draw.rect(SCREEN, color, rect, border_radius=4)
                pygame.draw.rect(SCREEN, (155, 50, 100), rect, 1, border_radius=4)
                
                text = algo
                item_text = FONT.render(text, True, (155, 50, 100))
                SCREEN.blit(item_text, item_text.get_rect(center=rect.center))

        # --- PHẦN VẼ MENU TEST VÀ THANH CUỘN ĐÃ CHỈNH SỬA ---
        if self.test_menu_open:
            visible_tests = list(self.test_menu.keys())[self.test_menu_scroll_offset:self.test_menu_scroll_offset + self.max_visible_tests]
            for idx, test_name in enumerate(visible_tests):
                # Menu hiện phía trên nút Test
                test_rect = pygame.Rect(1100, PANEL_Y - 30 - idx * 30, 90, 30)
                test_num = self.test_menu[test_name]
                color = (200, 230, 150) if self.seed == -test_num else (255, 200, 230)
                pygame.draw.rect(SCREEN, color, test_rect, border_radius=4)
                pygame.draw.rect(SCREEN, (155, 50, 100), test_rect, 1, border_radius=4)
                
                item_text = FONT.render(test_name, True, (155, 50, 100))
                SCREEN.blit(item_text, item_text.get_rect(center=test_rect.center))
            
            # Vẽ thanh cuộn khớp với các nút Test
            if len(self.test_menu) > self.max_visible_tests:
                scroll_bar_width = 8
                scroll_bar_x = 1100 + 90 + 2 # Sát bên phải menu
                total_menu_h = self.max_visible_tests * 30
                scroll_bar_y = PANEL_Y - total_menu_h
                
                # Nền thanh cuộn
                pygame.draw.rect(SCREEN, (255, 200, 230), pygame.Rect(scroll_bar_x, scroll_bar_y, scroll_bar_width, total_menu_h))
                
                # Cục trượt
                max_offset = len(self.test_menu) - self.max_visible_tests
                thumb_h = max(10, int(total_menu_h * self.max_visible_tests / len(self.test_menu)))
                # Đảo ngược tỷ lệ vì menu vẽ từ dưới lên
                scroll_ratio = (max_offset - self.test_menu_scroll_offset) / max_offset if max_offset > 0 else 0
                thumb_pos = int(scroll_bar_y + scroll_ratio * (total_menu_h - thumb_h))
                pygame.draw.rect(SCREEN, (155, 50, 100), pygame.Rect(scroll_bar_x, thumb_pos, scroll_bar_width, thumb_h), border_radius=2)

        # Log ở dưới panel
        max_scroll = max(0, len(self.log) - 4)
        display_start = max(0, len(self.log) - 4 - self.log_offset)
        display_logs = self.log[display_start:display_start + 4]
        
        for i, msg in enumerate(display_logs):
            log_text = FONT.render(msg, True, (255, 200, 230))
            SCREEN.blit(log_text, (50, PANEL_Y + 20 + i * 22))
        
        # Thanh cuộn log chính
        scroll_bar_x = 640
        scroll_bar_y = PANEL_Y + 10
        scroll_bar_height = 100 
        scroll_bar_width = 8
        pygame.draw.rect(SCREEN, (255, 200, 230), pygame.Rect(scroll_bar_x, scroll_bar_y, scroll_bar_width, scroll_bar_height))
        
        if max_scroll > 0:
            thumb_height = max(15, int(scroll_bar_height * 2 / len(self.log)))
            scroll_ratio = (max_scroll - self.log_offset) / max_scroll
            thumb_pos = int(scroll_bar_y + scroll_ratio * (scroll_bar_height - thumb_height))
            pygame.draw.rect(SCREEN, (155, 50, 100), pygame.Rect(scroll_bar_x, thumb_pos, scroll_bar_width, thumb_height), border_radius=2)

        # Vẽ bài
        for pile_id in range(16):
            base_rect = self.GetCardRect(pile_id, 0)
            pygame.draw.rect(SCREEN, (255, 255, 255), base_rect, 1, border_radius=5)
            
            heap = self.freecell_game.card_heaps[pile_id].heap_list
            for i, card in enumerate(heap):
                if self.dragging and pile_id == self.source_id and i >= self.drag_start_idx:
                    continue
                rect = self.GetCardRect(pile_id, i)
                SCREEN.blit(IMAGES[card.color + card.point], (rect.x, rect.y))

        if self.dragging:
            for i, card in enumerate(self.drag_cards):
                drag_x = mouse_pos[0] + self.mouse_offset_x
                drag_y = mouse_pos[1] + self.mouse_offset_y + (i * OFFSET_Y)
                SCREEN.blit(IMAGES[card.color + card.point], (drag_x, drag_y))

        # Thanh tiến trình animation
        if self.animation_running or self.animation_moves:
            bar_x = X_START + GAP*2
            bar_y = 12
            bar_w = GAP * 3 + CARD_W
            bar_h = 20
            
            status_rect = pygame.Rect(bar_x, bar_y, bar_w, bar_h)
            pygame.draw.rect(SCREEN, (255, 200, 230), status_rect, border_radius=5)
            pygame.draw.rect(SCREEN, (155, 50, 100), status_rect, 1, border_radius=5)
            if self.animation_moves:
                progress = self.animation_current_move / len(self.animation_moves) if self.animation_moves else 0
                progress_width = int((bar_w - 2) * progress)                
                if progress_width > 0:
                    progress_rect = pygame.Rect(bar_x + 1, bar_y + 1, progress_width, bar_h - 2)
                    pygame.draw.rect(SCREEN, (200, 230, 150), progress_rect, border_radius=4)               
                status_text = f"Animation: {self.animation_current_move}/{len(self.animation_moves)} moves"
                status_surf = FONT.render(status_text, True, (155, 50, 100))
                SCREEN.blit(status_surf, status_surf.get_rect(center=status_rect.center))

        pygame.display.update()

if __name__ == "__main__":
    WindowGame()