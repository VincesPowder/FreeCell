"""
BFS Solver for FreeCell Game
Implement Breadth-First Search algorithm to solve FreeCell
"""

import copy
import time
import tracemalloc
import psutil
import os
from collections import deque
from Freecell_Game import FreeCellGame


class BFSSolver:
    """BFS Solver for FreeCell Game"""
    
    def __init__(self, game_state, on_move_callback=None):
        """
        Initialize BFS Solver
        
        Args:
            game_state: Initial FreeCellGame instance
            on_move_callback: Optional callback function(move, game_state) for animation
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
        self.on_move_callback = on_move_callback  # Animation callback
        
    def _get_game_state_hash(self, game_or_res):
        """
        Return a fixed-width hash string for a game or a raw observe list.

        Accepts either a `FreeCellGame` instance or the `res` list returned
        by `ObserveForData()`.
        """
        # If a FreeCellGame provided, use its ObserveForData to get canonical string
        if hasattr(game_or_res, "ObserveForData"):
            hash_index, _ = game_or_res.ObserveForData()
            return hash_index

        # Otherwise expect a flat list [group_id, group_index, ...]
        res = game_or_res
        parts = []
        for i in range(0, len(res), 2):
            parts.append("%02d%02d" % (int(res[i]), int(res[i + 1])))
        return "".join(parts)
    
    def _check_win(self, game):
        """
        Check if the current game state is a winning state
        (all 52 cards are on foundation piles in correct order)
        
        Args:
            game: FreeCellGame instance
            
        Returns:
            bool: True if won, False otherwise
        """
        # Use the game's built-in CheckWinStrict method
        # All 4 foundations must have 13 cards each, ending with King
        return game.CheckWinStrict()
    
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
        # we'll use tracemalloc peak for measured memory
        
        # Initialize queue for BFS
        # Each item: (current_game_state, path=[list of moves])
        queue = deque()
        # Use ObserveForData() to get canonical hash and compact representation
        initial_hash, initial_res = self.initial_game.ObserveForData()

        # Check if initial state is already a winning state
        if self._check_win(self.initial_game):
            self.end_time = time.time()
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            return {
                'solved': True,
                'solution': [],
                'search_time': self.end_time - self.start_time,
                'memory_used': peak / (1024 ** 2),
                'expanded_nodes': 1,
                'search_length': 0
            }

        # Add initial state to queue and visited set. Store only compact `res` lists.
        queue.append((initial_res, []))
        self.visited_states.add(initial_hash)
        
        # BFS main loop
        while queue and self.expanded_nodes < max_nodes:
            # Check timeout
            if time.time() - self.start_time > timeout:
                self.end_time = time.time()
                self.end_memory = process.memory_info().rss / (1024 ** 2)
                return {
                    'solved': False,
                    'solution': [],
                    'search_time': self.end_time - self.start_time,
                    'memory_used': self.end_memory - self.start_memory,
                    'expanded_nodes': self.expanded_nodes,
                    'search_length': 0,
                    'error': 'Timeout exceeded'
                }
            
            # Pop next state from queue (we store compact `res` lists, not full game objects)
            current_res, path = queue.popleft()
            self.expanded_nodes += 1

            # Reconstruct a FreeCellGame for move generation from the compact representation
            current_game = FreeCellGame()
            current_game.ParseDataObserve(current_res)

            # Get valid moves from current state
            valid_moves = self._get_valid_moves(current_game)

            # Try each valid move
            for move in valid_moves:
                from_id, to_id = move

                # Reconstruct game for this child move, apply move, then get its compact res
                next_game = FreeCellGame()
                next_game.ParseDataObserve(current_res)
                self._apply_move(next_game, from_id, to_id)

                # Check if this is a winning state
                if self._check_win(next_game):
                    self.end_time = time.time()
                    current, peak = tracemalloc.get_traced_memory()
                    tracemalloc.stop()

                    solution = path + [move]
                    self.search_length = len(solution)

                    return {
                        'solved': True,
                        'solution': solution,
                        'search_time': self.end_time - self.start_time,
                        'memory_used': peak / (1024 ** 2),
                        'expanded_nodes': self.expanded_nodes,
                        'search_length': self.search_length
                    }

                # Get compact representation and check visited
                next_hash, next_res = next_game.ObserveForData()
                if next_hash not in self.visited_states:
                    self.visited_states.add(next_hash)
                    new_path = path + [move]
                    queue.append((next_res, new_path))
        
        # No solution found
        self.end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        return {
            'solved': False,
            'solution': [],
            'search_time': self.end_time - self.start_time,
            'memory_used': peak / (1024 ** 2),
            'expanded_nodes': self.expanded_nodes,
            'search_length': 0,
            'error': 'No solution found within node limit'
        }
    
    def solve_with_animation(self, max_nodes=100000, timeout=300):
        """
        Solve FreeCell puzzle using BFS and yield moves for animation
        
        This is a generator version that yields each move as it's found
        
        Args:
            max_nodes: Maximum nodes to explore
            timeout: Time limit in seconds
            
        Yields:
            dict: Move result containing 'move', 'game_state', 'status', 'progress'
        """
        self.start_time = time.time()
        tracemalloc.start()

        queue = deque()
        initial_hash, initial_res = self.initial_game.ObserveForData()

        if self._check_win(self.initial_game):
            self.end_time = time.time()
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            yield {
                'status': 'solved',
                'solution': [],
                'search_time': self.end_time - self.start_time,
                'memory_used': peak / (1024 ** 2),
                'expanded_nodes': 1,
                'search_length': 0
            }
            return

        queue.append((initial_res, []))
        self.visited_states.add(initial_hash)
        
        while queue and self.expanded_nodes < max_nodes:
            if time.time() - self.start_time > timeout:
                yield {
                    'status': 'timeout',
                    'error': 'Timeout exceeded'
                }
                return
            
            current_res, path = queue.popleft()
            self.expanded_nodes += 1

            current_game = FreeCellGame()
            current_game.ParseDataObserve(current_res)

            valid_moves = self._get_valid_moves(current_game)

            for move in valid_moves:
                from_id, to_id = move
                next_game = FreeCellGame()
                next_game.ParseDataObserve(current_res)
                self._apply_move(next_game, from_id, to_id)

                if self._check_win(next_game):
                    self.end_time = time.time()
                    current, peak = tracemalloc.get_traced_memory()
                    tracemalloc.stop()
                    solution = path + [move]
                    self.search_length = len(solution)

                    yield {
                        'status': 'solved',
                        'solution': solution,
                        'search_time': self.end_time - self.start_time,
                        'memory_used': peak / (1024 ** 2),
                        'expanded_nodes': self.expanded_nodes,
                        'search_length': self.search_length
                    }
                    return

                next_hash, next_res = next_game.ObserveForData()
                if next_hash not in self.visited_states:
                    self.visited_states.add(next_hash)
                    new_path = path + [move]
                    queue.append((next_res, new_path))
        
        self.end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        yield {
            'status': 'failed',
            'error': 'No solution found',
            'expanded_nodes': self.expanded_nodes,
            'search_time': self.end_time - self.start_time,
            'memory_used': peak / (1024 ** 2)
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
