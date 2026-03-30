import pygame
import utils
import copy
import time
from Freecell_Game import FreeCellGame
from BFS_Solver import BFSSolver
from A_Star_Solver import AStarSolver
from UCS_Solver import UCSSolver
import threading

# --- CONFIGURATION ---
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
pygame.display.set_caption("FreeCell")

IMAGES = utils.LoadImages()
FONT = pygame.font.Font(None, 22)
BTN_FONT = pygame.font.Font(None, 26)

class WindowGame:
    def __init__(self):
        self.freecell_game = FreeCellGame()
        # If no difficulty set yet (first time), default to easy
        if not hasattr(self, 'difficulty'):
            self.difficulty = "easy"
        self.freecell_game.NewGameWithDifficulty(self.difficulty)
        
        self.initial_state = copy.deepcopy(self.freecell_game.card_heaps)
        self.undo_stack = []
        
        # Biến kéo thả mới
        self.dragging = False
        self.source_id = -1
        self.drag_start_idx = -1
        self.drag_cards = [] 
        self.mouse_offset_x = 0
        self.mouse_offset_y = 0
        
        self.log = [f"New game started! Difficulty: {self.difficulty.upper()}"]
        self.log_offset = 0  # For log scrolling
        self.button_highlight_time = {}  # Track highlight time for each button
        self.highlight_duration = 0.15  # Show highlight for 0.15 seconds
        
        # Control buttons (right side) - equal sizes
        self.buttons = {
            "New": pygame.Rect(800, PANEL_Y + 20, 90, 35),
            "Restart": pygame.Rect(900, PANEL_Y + 20, 90, 35),
            "Undo": pygame.Rect(1000, PANEL_Y + 20, 90, 35),
            "Mode": pygame.Rect(1100, PANEL_Y + 20, 90, 35),
            "Solver": pygame.Rect(800, PANEL_Y + 60, 90, 35),
            "Stop": pygame.Rect(900, PANEL_Y + 60, 90, 35),
            "Quit": pygame.Rect(1000, PANEL_Y + 60, 90, 35),
        }
        
        # Difficulty menu (upward from Mode button)
        self.mode_menu_open = False
        self.difficulty_menu = {
            "easy": pygame.Rect(1100, PANEL_Y - 120, 90, 30),
            "medium": pygame.Rect(1100, PANEL_Y - 90, 90, 30),
            "hard": pygame.Rect(1100, PANEL_Y - 60, 90, 30),
            "expert": pygame.Rect(1100, PANEL_Y - 30, 90, 30),
        }
        
        # Solver menu (upward from Solver button - same as Mode menu)
        self.solver_menu_open = False
        self.solver_menu = {
            "BFS": pygame.Rect(900, PANEL_Y - 120, 90, 30),
            "DFS": pygame.Rect(900, PANEL_Y - 90, 90, 30),
            "UCS": pygame.Rect(900, PANEL_Y - 60, 90, 30),
            "A*": pygame.Rect(900, PANEL_Y - 30, 90, 30),
        }
        
        # Solver results
        self.solver_running = False
        self.solver_result = None
        self.solver_selected = None
        
        # Animation variables
        self.animation_running = False
        self.animation_moves = []
        self.animation_current_move = 0
        self.animation_start_time = None
        self.move_duration = 0.5  # Duration of each move animation in seconds
        
        self.MainLoop()

    def stop_animation(self):
        """Stop the animation"""
        self.animation_running = False
        self.log.append("Animation stopped")
    
    def update_animation(self):
        """Update animation state and apply moves as needed"""
        if not self.animation_running or not self.animation_moves:
            return
        
        current_time = time.time()
        elapsed = current_time - self.animation_start_time
        
        # Calculate how many moves should have been played
        moves_to_play = int(elapsed / self.move_duration)
        
        # Apply moves that haven't been applied yet
        while self.animation_current_move < moves_to_play and self.animation_current_move < len(self.animation_moves):
            move = self.animation_moves[self.animation_current_move]
            from_id, to_id = move
            
            # Apply the move
            if len(self.freecell_game.card_heaps[from_id].heap_list) > 0:
                card = self.freecell_game.card_heaps[from_id].heap_list.pop()
                self.freecell_game.card_heaps[to_id].PushTop(card)
                self.log.append(f"[Animation] Move {self.animation_current_move + 1}/{len(self.animation_moves)}: Heap {from_id} → {to_id}")
            
            self.animation_current_move += 1
        
        # Check if animation is complete
        if self.animation_current_move >= len(self.animation_moves):
            self.animation_running = False
            self.log.append("Animation complete! All moves played.")

    def GetCardRect(self, pile_id, card_index):
        if pile_id < 8: 
            return pygame.Rect(X_START + GAP * pile_id, 40, CARD_W, CARD_H)
        else: 
            return pygame.Rect(X_START + GAP * (pile_id - 8), 210 + OFFSET_Y * card_index, CARD_W, CARD_H)
    
    def run_solver_thread(self, solver_algo):
        """Run solver in background thread"""
        try:
            if solver_algo == "BFS":
                solver = BFSSolver(self.freecell_game)
                # Note: BFS is slow for FreeCell due to large state space
                # Even solvable games may take 5-10 minutes
                # For faster solving, use A* instead
                self.solver_result = solver.solve(max_nodes=1000000, timeout=600)
                self.solver_selected = "BFS"
                
                if self.solver_result['solved'] and self.solver_result['solution']:
                    self.log.append(f"[BFS] Solved in {self.solver_result['search_length']} moves!")
                    self.log.append(f"Time: {self.solver_result['search_time']:.2f}s, Nodes: {self.solver_result['expanded_nodes']}")
                    self.log.append(f"Memory: {self.solver_result['memory_used']:.2f}MB")
                    # Store solution and auto-start animation
                    self.animation_moves = self.solver_result['solution']
                    self.animation_running = True
                    self.animation_current_move = 0
                    self.animation_start_time = time.time()
                    self.log.append(f"🎬 Playing animation...")
                else:
                    error_msg = self.solver_result.get('error', 'No solution found')
                    self.log.append(f"BFS: {error_msg}")
            elif solver_algo == "A*":
                solver = AStarSolver(self.freecell_game)
                # A* is much faster due to heuristic guidance
                self.solver_result = solver.solve(max_nodes=100000, timeout=300)
                self.solver_selected = "A*"
                
                if self.solver_result['solved'] and self.solver_result['solution']:
                    self.log.append(f"[A*] Solved in {self.solver_result['search_length']} moves!")
                    self.log.append(f"Time: {self.solver_result['search_time']:.2f}s, Nodes: {self.solver_result['expanded_nodes']}")
                    self.log.append(f"Memory: {self.solver_result['memory_used']:.2f}MB")
                    # Store solution and auto-start animation
                    self.animation_moves = self.solver_result['solution']
                    self.animation_running = True
                    self.animation_current_move = 0
                    self.animation_start_time = time.time()
                    self.log.append(f"🎬 Playing animation...")
                else:
                    error_msg = self.solver_result.get('error', 'No solution found')
                    self.log.append(f"A*: {error_msg}")
            elif solver_algo == "UCS":
                solver = UCSSolver(self.freecell_game)
            # UCS tìm kiếm theo chi phí đường đi thấp nhất (g_n)
            # Giới hạn max_nodes để tránh tràn bộ nhớ nếu máy yếu
                self.solver_result = solver.solve(max_nodes=500000, timeout=450)
                self.solver_selected = "UCS"
            
                if self.solver_result['solved'] and self.solver_result['solution']:
                    self.log.append(f"[UCS] Solved in {self.solver_result['search_length']} moves!")
                    self.log.append(f"Time: {self.solver_result['search_time']:.2f}s, Nodes: {self.solver_result['expanded_nodes']}")
                    self.log.append(f"Memory: {self.solver_result['memory_used']:.2f}MB")
                
                # Lưu lời giải và tự động chạy hoạt cảnh (animation)
                    self.animation_moves = self.solver_result['solution']
                    self.animation_running = True
                    self.animation_current_move = 0
                    self.animation_start_time = time.time()
                    self.log.append(f"🎬 Playing animation...")
                else:
                    error_msg = self.solver_result.get('error', 'No solution found')
                    self.log.append(f"UCS: {error_msg}")
            else:
                self.log.append(f"{solver_algo} solver not implemented yet")
                
        except Exception as e:
            self.log.append(f"Error running {solver_algo}: {str(e)}")
        
        self.solver_running = False

    def GetClickedPileAndCard(self, pos):
        """Identify pile_id and index of clicked card"""
        # Check Mode button
        if self.buttons["Mode"].collidepoint(pos):
            return "mode", -1
        
        # Check Solver button
        if self.buttons["Solver"].collidepoint(pos):
            return "solver", -1
        
        # Check Stop button
        if self.buttons["Stop"].collidepoint(pos):
            return "stop", -1
        
        # Check difficulty menu if open
        if self.mode_menu_open:
            for difficulty, rect in self.difficulty_menu.items():
                if rect.collidepoint(pos):
                    return difficulty, -1
        
        # Check solver menu if open
        if self.solver_menu_open:
            for algo, rect in self.solver_menu.items():
                if rect.collidepoint(pos):
                    return algo, -1
        
        # Check other buttons
        for name, rect in self.buttons.items():
            if name not in ["Mode", "Solver", "Stop"] and rect.collidepoint(pos):
                return name, -1

        # Check from bottom to top (to get top card first)
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
                    # Handle mouse scroll
                    if event.button == 4:  # Scroll up (view older logs)
                        self.log_offset = min(self.log_offset + 1, max(0, len(self.log) - 4))
                    elif event.button == 5:  # Scroll down (view newer logs)
                        self.log_offset = max(self.log_offset - 1, 0)
                    
                    p_id, c_idx = self.GetClickedPileAndCard(event.pos)
                    
                    if isinstance(p_id, str): # Click button or menu
                        # Handle Mode button
                        if p_id == "mode":
                            self.mode_menu_open = not self.mode_menu_open
                            self.solver_menu_open = False  # Close solver menu
                        # Handle Solver button
                        elif p_id == "solver":
                            self.solver_menu_open = not self.solver_menu_open
                            self.mode_menu_open = False  # Close mode menu
                        # Handle Stop button
                        elif p_id == "stop":
                            self.stop_animation()
                        # Handle solver selection from menu
                        elif p_id in ["BFS", "DFS", "UCS", "A*"]:
                            if not self.solver_running:
                                self.solver_running = True
                                self.solver_menu_open = False
                                self.log.append(f"Running {p_id} solver...")
                                solver_thread = threading.Thread(target=self.run_solver_thread, args=(p_id,), daemon=True)
                                solver_thread.start()
                            else:
                                self.log.append("Solver already running...")
                        # Handle difficulty selection from menu
                        elif p_id in ["easy", "medium", "hard", "expert"]:
                            self.difficulty = p_id
                            self.freecell_game = FreeCellGame()
                            self.freecell_game.NewGameWithDifficulty(self.difficulty)
                            self.initial_state = copy.deepcopy(self.freecell_game.card_heaps)
                            self.undo_stack = []
                            self.log = [f"New game! Difficulty: {self.difficulty.upper()}"]
                            self.log_offset = 0  # Reset scroll
                            self.mode_menu_open = False
                        # Handle game buttons
                        elif p_id == "New": 
                            # Create new game with random seed but same difficulty
                            self.freecell_game = FreeCellGame()
                            self.freecell_game.NewRandomGameWithDifficulty(self.difficulty)
                            self.initial_state = copy.deepcopy(self.freecell_game.card_heaps)
                            self.undo_stack = []
                            self.animation_moves = []  # Clear any animation
                            self.animation_running = False
                            self.log = [f"New game! Difficulty: {self.difficulty.upper()}"]
                            self.log_offset = 0  # Reset scroll
                            self.mode_menu_open = False
                            self.button_highlight_time["New"] = time.time()  # Highlight New button
                        elif p_id == "Restart":
                            self.freecell_game.card_heaps = copy.deepcopy(self.initial_state)
                            self.undo_stack = []
                            self.animation_moves = []  # Clear animation
                            self.animation_running = False
                            self.log.append("Game restarted.")
                            self.button_highlight_time["Restart"] = time.time()  # Highlight Restart button
                        elif p_id == "Undo" and self.undo_stack:
                            self.freecell_game.card_heaps = self.undo_stack.pop()
                            self.log.append("Move undone.")
                            self.button_highlight_time["Undo"] = time.time()  # Highlight Undo button
                        elif p_id == "Quit":
                            pygame.quit()
                            return
                    
                    elif p_id != -1 and c_idx != -1: # Click on card
                        self.mode_menu_open = False  # Close menu
                        self.solver_menu_open = False  # Close solver menu
                        heap = self.freecell_game.card_heaps[p_id].heap_list
                        self.drag_cards = heap[c_idx:]
                        
                        # Check if this sequence is valid to start dragging
                        if not self.freecell_game.IsValidSequence(self.drag_cards):
                            self.log.append("Invalid sequence!")
                        else:
                            # Check if there are enough free cells
                            max_allowed = self.freecell_game.GetMaxMovable(p_id, len(self.drag_cards))
                            if len(self.drag_cards) > max_allowed:
                                free_cells = sum(1 for i in range(4,8) if not self.freecell_game.card_heaps[i].heap_list)
                                self.log.append(f"Can only move max {max_allowed} cards (free cells: {free_cells})")
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
                            can_move, msg = self.freecell_game.CheckMoveSequence(self.source_id, target_id, self.drag_start_idx)
                            if can_move:
                                self.undo_stack.append(self.pre_move_state)
                                # Move cards one by one
                                for _ in range(len(self.drag_cards)):
                                    card_to_move = self.freecell_game.card_heaps[self.source_id].heap_list.pop(self.drag_start_idx)
                                    self.freecell_game.card_heaps[target_id].PushTop(card_to_move)
                                self.log.append(f"Moved {len(self.drag_cards)} cards.")
                            else:
                                self.log.append(msg)
                        
                        self.dragging = False
                        self.drag_cards = []

            # Update animation
            self.update_animation()

            self.UpdateScreen(mouse_pos)

    def UpdateScreen(self, mouse_pos):
        SCREEN.blit(IMAGES["background"], (0, 0))
        pygame.draw.rect(SCREEN, (30, 65, 70), (0, PANEL_Y, SCREEN_WIDTH, 120))  # Dark cool green background
        
        # Draw 4 control buttons (right side)
        for name, rect in self.buttons.items():
            # Check if button should be highlighted
            is_highlighted = False
            
            # Mode button highlight
            if name == "Mode" and self.mode_menu_open:
                is_highlighted = True
            
            # Other buttons highlight based on recent click
            elif name in self.button_highlight_time:
                elapsed = time.time() - self.button_highlight_time[name]
                if elapsed < self.highlight_duration:
                    is_highlighted = True
                else:
                    del self.button_highlight_time[name]  # Clear old highlight
            
            # Draw button with appropriate color
            color = (200, 230, 150) if is_highlighted else (255, 200, 230)  # Tea Green / Fairy Tale - light colors
            pygame.draw.rect(SCREEN, color, rect, border_radius=5)
            
            text_surf = FONT.render(name, True, (155, 50, 100))  # Quinacridone Magenta - dark text
            SCREEN.blit(text_surf, text_surf.get_rect(center=rect.center))
        
        # Draw difficulty menu (upward from Mode button)
        if self.mode_menu_open:
            for difficulty, rect in self.difficulty_menu.items():
                # Highlight current difficulty
                color = (200, 230, 150) if self.difficulty == difficulty else (255, 200, 230)  # Tea Green / Fairy Tale - light
                pygame.draw.rect(SCREEN, color, rect, border_radius=4)
                pygame.draw.rect(SCREEN, (155, 50, 100), rect, 1, border_radius=4)  # Quinacridone border
                
                text = difficulty.capitalize()
                item_text = FONT.render(text, True, (155, 50, 100))  # Quinacridone Magenta - dark text
                SCREEN.blit(item_text, item_text.get_rect(center=rect.center))

        # Draw solver menu (downward from Solver button)
        if self.solver_menu_open:
            for algo, rect in self.solver_menu.items():
                color = (200, 230, 150) if self.solver_selected == algo else (255, 200, 230)  # Tea Green / Fairy Tale - light
                pygame.draw.rect(SCREEN, color, rect, border_radius=4)
                pygame.draw.rect(SCREEN, (155, 50, 100), rect, 1, border_radius=4)  # Quinacridone border
                
                text = algo
                item_text = FONT.render(text, True, (155, 50, 100))  # Quinacridone Magenta - dark text
                SCREEN.blit(item_text, item_text.get_rect(center=rect.center))

        # Draw Log (with scroll support)
        max_scroll = max(0, len(self.log) - 4)
        display_start = max(0, len(self.log) - 4 - self.log_offset)
        display_logs = self.log[display_start:display_start + 4]
        
        for i, msg in enumerate(display_logs):
            log_text = FONT.render(msg, True, (255, 200, 230))  # Fairy Tale - light text
            SCREEN.blit(log_text, (50, PANEL_Y + 20 + i * 22))
        
        # Draw scroll bar for log
        scroll_bar_x = 640
        scroll_bar_y = PANEL_Y + 10
        scroll_bar_height = 100 
        scroll_bar_width = 8
        
        # Draw scroll bar background
        pygame.draw.rect(SCREEN, (255, 200, 230), pygame.Rect(scroll_bar_x, scroll_bar_y, scroll_bar_width, scroll_bar_height))  # Fairy Tale - light
        
        # Draw scroll bar thumb (indicator)
        if max_scroll > 0:
            thumb_height = max(15, int(scroll_bar_height * 2 / len(self.log)))
            thumb_pos = int(scroll_bar_y + (self.log_offset / max_scroll) * (scroll_bar_height - thumb_height))
            pygame.draw.rect(SCREEN, (155, 50, 100), pygame.Rect(scroll_bar_x, thumb_pos, scroll_bar_width, thumb_height), border_radius=2)  # Quinacridone - dark

        # Draw card columns
        for pile_id in range(16):
            # Draw empty slot
            base_rect = self.GetCardRect(pile_id, 0)
            pygame.draw.rect(SCREEN, (255, 255, 255), base_rect, 1, border_radius=5)
            
            heap = self.freecell_game.card_heaps[pile_id].heap_list
            for i, card in enumerate(heap):
                # Don't draw dragging cards
                if self.dragging and pile_id == self.source_id and i >= self.drag_start_idx:
                    continue
                rect = self.GetCardRect(pile_id, i)
                SCREEN.blit(IMAGES[card.color + card.point], (rect.x, rect.y))

        # Draw dragging cards
        if self.dragging:
            for i, card in enumerate(self.drag_cards):
                drag_x = mouse_pos[0] + self.mouse_offset_x
                drag_y = mouse_pos[1] + self.mouse_offset_y + (i * OFFSET_Y)
                SCREEN.blit(IMAGES[card.color + card.point], (drag_x, drag_y))

        # Draw animation status bar
        if self.animation_running or self.animation_moves:
            status_rect = pygame.Rect(50, 10, 600, 20)
            pygame.draw.rect(SCREEN, (100, 150, 150), status_rect)
            pygame.draw.rect(SCREEN, (255, 255, 255), status_rect, 2)
            
            if self.animation_moves:
                progress = self.animation_current_move / len(self.animation_moves) if self.animation_moves else 0
                progress_width = int(598 * progress)
                progress_rect = pygame.Rect(51, 11, progress_width, 18)
                pygame.draw.rect(SCREEN, (100, 200, 100), progress_rect)
                
                status_text = f"Animation: {self.animation_current_move}/{len(self.animation_moves)} moves"
                status_surf = FONT.render(status_text, True, (255, 255, 255))
                SCREEN.blit(status_surf, (60, 12))

        pygame.display.update()

if __name__ == "__main__":
    WindowGame()