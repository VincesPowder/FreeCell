"""
BFS Solver for FreeCell Game
Implement Breadth-First Search algorithm to solve FreeCell
"""

import copy
import time
import tracemalloc
import os
from collections import deque
from Freecell_Game import FreeCellGame


class BFSSolver:
    """BFS Solver for FreeCell Game"""
    
    def __init__(self, game_state):
        """
        Initialize BFS Solver
        
        Args:
            game_state: Initial FreeCellGame instance
        """
        self.initial_game = copy.deepcopy(game_state)
        self.visited_states = set()  # For storing visited state hashes
        self.solutions = []  # Store solution path
        self.expanded_nodes = 0
        self.start_time = None
        self.end_time = None
        self.start_memory = None
        self.end_memory = None
        self.search_length = 0
        
    def _get_game_state_hash(self, game):
        """
        Create a hashable representation of the current game state
        Using card positions (group_id and group_index for each card)
        
        Args:
            game: FreeCellGame instance
            
        Returns:
            str: hash string representing the state
        """
        state = []
        for card in game.CARDS:
            state.append(str(card.group_id))
            state.append(str(card.group_index))
        return "".join(state)
    
    def _check_win(self, game):
        """
        Check if the current game state is a winning state
        (all 52 cards are on foundation piles in order)
        
        Args:
            game: FreeCellGame instance
            
        Returns:
            bool: True if won, False otherwise
        """
        # All cards should be on foundation piles (indices 0-3)
        # Each foundation should have 13 cards
        for i in range(4):
            if len(game.card_heaps[i].heap_list) != 13:
                return False
        # Check that cascades (8-15) and free cells (4-7) are empty
        for i in range(4, 16):
            if len(game.card_heaps[i].heap_list) != 0:
                return False
        return True
    
    def _get_valid_moves(self, game):
        """
        Get all valid moves from the current game state
        
        Args:
            game: FreeCellGame instance
            
        Returns:
            list: List of valid moves as tuples (from_heap_id, to_heap_id)
        """
        valid_moves = []
        
        # Try moving from each heap to every other heap
        for from_id in range(16):
            if len(game.card_heaps[from_id].heap_list) == 0:
                continue
                
            for to_id in range(16):
                if from_id == to_id:
                    continue
                    
                # Check if move is valid
                if game.CheckMove(from_id, to_id):
                    valid_moves.append((from_id, to_id))
        
        return valid_moves
    
    def _apply_move(self, game, from_id, to_id):
        """
        Apply a move to a game copy
        
        Args:
            game: FreeCellGame instance (will be modified)
            from_id: Source heap id
            to_id: Target heap id
        """
        game.Move(from_id, to_id)
    
    def solve(self, max_nodes=100000, timeout=300):
        """
        Solve FreeCell puzzle using BFS Algorithm
        
        Args:
            max_nodes: Maximum nodes to explore (default: 100000)
            timeout: Time limit in seconds (default: 300s)
            
        Returns:
            dict: Result containing:
                - 'solved': bool indicating if puzzle was solved
                - 'solution': list of moves (from_id, to_id) representing the solution
                - 'search_time': time taken for search in seconds
                - 'memory_used': peak memory used in MB
                - 'expanded_nodes': number of nodes expanded
                - 'search_length': number of moves in solution
        """
        # Record start metrics
        self.start_time = time.time()
        tracemalloc.start()
        
        # Initialize queue for BFS
        # Each item: (current_game_state, path=[list of moves])
        queue = deque()
        initial_game = copy.deepcopy(self.initial_game)
        initial_hash = self._get_game_state_hash(initial_game)
        
        # Check if initial state is already a winning state
        if self._check_win(initial_game):
            self.end_time = time.time()
            peak_memory = process.memory_info().rss / (1024 ** 2)
            self.end_memory = peak_memory
            return {
                'solved': True,
                'solution': [],
                'search_time': self.end_time - self.start_time,
                'memory_used': peak_memory - self.start_memory,
                'expanded_nodes': 1,
                'search_length': 0
            }
        
        # Add initial state to queue and visited set
        queue.append((initial_game, []))
        self.visited_states.add(initial_hash)
        
        # BFS main loop
        while queue and self.expanded_nodes < max_nodes:
            # Check timeout
            if time.time() - self.start_time > timeout:
                self.end_time = time.time()
                peak_memory = process.memory_info().rss / (1024 ** 2)
                self.end_memory = peak_memory
                return {
                    'solved': False,
                    'solution': [],
                    'search_time': self.end_time - self.start_time,
                    'memory_used': peak_memory - self.start_memory,
                    'expanded_nodes': self.expanded_nodes,
                    'search_length': 0,
                    'error': 'Timeout exceeded'
                }
            
            # Pop next state from queue
            current_game, path = queue.popleft()
            self.expanded_nodes += 1
            
            # Get valid moves from current state
            valid_moves = self._get_valid_moves(current_game)
            
            # Try each valid move
            for move in valid_moves:
                from_id, to_id = move
                
                # Create new game state with this move
                next_game = copy.deepcopy(current_game)
                self._apply_move(next_game, from_id, to_id)
                
                # Check if this is a winning state
                if self._check_win(next_game):
                    self.end_time = time.time()
                    peak_memory = process.memory_info().rss / (1024 ** 2)
                    self.end_memory = peak_memory
                    
                    solution = path + [move]
                    self.search_length = len(solution)
                    
                    return {
                        'solved': True,
                        'solution': solution,
                        'search_time': self.end_time - self.start_time,
                        'memory_used': peak_memory - self.start_memory,
                        'expanded_nodes': self.expanded_nodes,
                        'search_length': self.search_length
                    }
                
                # Check if state has been visited
                next_hash = self._get_game_state_hash(next_game)
                if next_hash not in self.visited_states:
                    self.visited_states.add(next_hash)
                    new_path = path + [move]
                    queue.append((next_game, new_path))
        
        # No solution found
        self.end_time = time.time()
        peak_memory = process.memory_info().rss / (1024 ** 2)
        self.end_memory = peak_memory
        
        return {
            'solved': False,
            'solution': [],
            'search_time': self.end_time - self.start_time,
            'memory_used': peak_memory - self.start_memory,
            'expanded_nodes': self.expanded_nodes,
            'search_length': 0,
            'error': 'No solution found within node limit'
        }


def test_bfs_solver():
    """Test the BFS Solver with a sample game"""
    print("Creating a new FreeCell game...")
    game = FreeCellGame()
    game.NewGameWithDifficulty("easy")
    
    print("Initial game state:")
    print(game.ObserveForHuman())
    
    print("\nSolving using BFS...")
    solver = BFSSolver(game)
    result = solver.solve(max_nodes=50000, timeout=60)
    
    print(f"\nResults:")
    print(f"  Solved: {result['solved']}")
    print(f"  Solution length: {result['search_length']}")
    print(f"  Expanded nodes: {result['expanded_nodes']}")
    print(f"  Search time: {result['search_time']:.2f}s")
    print(f"  Memory used: {result['memory_used']:.2f}MB")
    
    if result['solved']:
        print(f"\n  Solution moves (first 10):")
        for i, move in enumerate(result['solution'][:10]):
            print(f"    {i+1}. Move from heap {move[0]} to heap {move[1]}")


if __name__ == "__main__":
    test_bfs_solver()
