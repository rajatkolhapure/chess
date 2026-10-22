"""Level 2: The Minimax Bot.

Evolutionary Stage: 2 (Adversarial Lookahead)
Capabilities:
  - Evaluates future game trees using the Minimax theorem (White maximizes, Black minimizes).
  - Search Depth: Fixed 3 plies (I move -> Opponent replies -> I counter-reply).
  - Immunity to naive baits: Refuses to capture defended pieces when the recapture is losing.
  - Tactical vision: Spots 2-ply tactics (forks, pins, hanging piece combinations, forced checkmates in 2).
Limitations:
  - Exhaustive search: Explores every single branch without pruning (evaluates 10,000+ positions per move).
  - Horizon Effect: Volatile trades that conclude on Ply 4 or 5 are cut off prematurely.
"""

import chess
from .base import BaseEngine
from .level1_greedy import GreedyBot


class MinimaxBot(BaseEngine):
    """Level 2 Bot: Fixed-depth Adversarial Minimax Search."""

    def __init__(self, depth: int = 3):
        super().__init__(
            name="Level 2: Minimax Bot",
            description=f"Looks {depth} plies ahead using adversarial Minimax. Never falls for 1-ply traps; plans tactics."
        )
        self.search_depth = depth
        self.evaluator = GreedyBot()  # Uses Level 1's static evaluation as the terminal leaf scorer

    def evaluate(self, board: chess.Board) -> int:
        return self.evaluator.evaluate(board)

    def _minimax(self, board: chess.Board, depth: int, is_maximizing: bool) -> int:
        """Recursive Minimax search algorithm."""
        self.nodes_evaluated += 1

        if depth <= 0:
            return self.evaluate(board)

        # Single legal move generation per node
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            if board.is_check():
                return -20000 - depth if is_maximizing else 20000 + depth
            return 0  # Stalemate

        if is_maximizing:
            max_eval = float('-inf')
            for move in legal_moves:
                board.push(move)
                eval_score = self._minimax(board, depth - 1, False)
                board.pop()
                if eval_score > max_eval:
                    max_eval = eval_score
            return max_eval
        else:
            min_eval = float('inf')
            for move in legal_moves:
                board.push(move)
                eval_score = self._minimax(board, depth - 1, True)
                board.pop()
                if eval_score < min_eval:
                    min_eval = eval_score
            return min_eval

    def select_move(self, board: chess.Board) -> chess.Move:
        """Select best move by analyzing the full minimax game tree to target depth."""
        self.nodes_evaluated = 0
        best_move = None
        is_white = (board.turn == chess.WHITE)

        if is_white:
            best_score = float('-inf')
            for move in board.legal_moves:
                board.push(move)
                # Next turn is Black's (minimizer), search with depth - 1
                score = self._minimax(board, self.search_depth - 1, is_maximizing=False)
                board.pop()
                if score > best_score:
                    best_score = score
                    best_move = move
        else:
            best_score = float('inf')
            for move in board.legal_moves:
                board.push(move)
                # Next turn is White's (maximizer), search with depth - 1
                score = self._minimax(board, self.search_depth - 1, is_maximizing=True)
                board.pop()
                if score < best_score:
                    best_score = score
                    best_move = move

        return best_move
