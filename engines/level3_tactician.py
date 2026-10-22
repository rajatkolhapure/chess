"""Level 3: The Tactician.

Evolutionary Stage: 3 & 4 (Tactical Immunity & Alpha-Beta Pruning)
Capabilities:
  - Alpha-Beta Pruning: Discards branches proven to be inferior to already-calculated moves.
  - Quiescence Search: Never freezes calculation mid-trade. Continues searching captures
    until the board is calm (immune to Horizon Effect tactical traps).
  - Move Ordering (MVV-LVA): Explores high-reward captures first (e.g. Pawn takes Queen
    before Queen takes Pawn) to trigger instant Alpha-Beta cutoffs.
  - Search Depth: Base Depth 4 + dynamic capture extensions (often reaching depth 8+ in trades).
Target Elo: ~1500
"""

import chess
from .base import BaseEngine
from .level1_greedy import PIECE_VALUES
from evaluator import StockfishEvaluator


class TacticianBot(BaseEngine):
    """Level 3 Bot: Alpha-Beta Search with Quiescence Search and MVV-LVA Move Ordering."""

    def __init__(self, depth: int = 4):
        super().__init__(
            name="Level 3: The Tactician",
            description=f"Searches Depth {depth} + Quiescence. Uses Alpha-Beta pruning & MVV-LVA to eliminate the Horizon Effect."
        )
        self.search_depth = depth

    def evaluate(self, board: chess.Board) -> int:
        return StockfishEvaluator.evaluate(board)

    def _mvv_lva_score(self, board: chess.Board, move: chess.Move) -> int:
        """Score moves to order forcing captures first (Most Valuable Victim - Least Valuable Attacker)."""
        if not board.is_capture(move):
            return 0

        victim = board.piece_at(move.to_square)
        attacker = board.piece_at(move.from_square)

        victim_val = PIECE_VALUES[victim.piece_type] if victim else 100  # 100 for en-passant
        attacker_val = PIECE_VALUES[attacker.piece_type] if attacker else 100

        # High priority: high victim value, low attacker value
        return 10000 + (victim_val * 10) - attacker_val

    def _order_moves(self, board: chess.Board, moves):
        """Sort moves so that highest-threat captures are calculated first."""
        return sorted(moves, key=lambda m: self._mvv_lva_score(board, m), reverse=True)

    def _quiescence(self, board: chess.Board, alpha: int, beta: int, is_maximizing: bool, q_depth: int = 6) -> int:
        """Search capture sequences until the position is quiet (dust has settled)."""
        self.nodes_evaluated += 1

        # Stand-pat score: what is our score if we choose NOT to make any more captures?
        stand_pat = self.evaluate(board)

        if q_depth <= 0:
            return stand_pat

        if is_maximizing:
            if stand_pat >= beta:
                return beta
            if stand_pat > alpha:
                alpha = stand_pat

            # Only examine captures in quiescence
            captures = [m for m in board.legal_moves if board.is_capture(m)]
            ordered_captures = self._order_moves(board, captures)

            for move in ordered_captures:
                board.push(move)
                score = self._quiescence(board, alpha, beta, False, q_depth - 1)
                board.pop()

                if score >= beta:
                    return beta  # Beta cutoff
                if score > alpha:
                    alpha = score
            return alpha
        else:
            if stand_pat <= alpha:
                return alpha
            if stand_pat < beta:
                beta = stand_pat

            captures = [m for m in board.legal_moves if board.is_capture(m)]
            ordered_captures = self._order_moves(board, captures)

            for move in ordered_captures:
                board.push(move)
                score = self._quiescence(board, alpha, beta, True, q_depth - 1)
                board.pop()

                if score <= alpha:
                    return alpha  # Alpha cutoff
                if score < beta:
                    beta = score
            return beta

    def _alpha_beta(self, board: chess.Board, depth: int, alpha: int, beta: int, is_maximizing: bool) -> int:
        """Minimax with Alpha-Beta Pruning and Quiescence search at leaf nodes."""
        self.nodes_evaluated += 1

        # When target depth is reached, transition into Quiescence Search!
        if depth <= 0:
            return self._quiescence(board, alpha, beta, is_maximizing)

        legal_moves = list(board.legal_moves)
        if not legal_moves:
            if board.is_check():
                return -20000 - depth if is_maximizing else 20000 + depth
            return 0  # Stalemate

        ordered_moves = self._order_moves(board, legal_moves)

        if is_maximizing:
            max_eval = float('-inf')
            for move in ordered_moves:
                board.push(move)
                eval_score = self._alpha_beta(board, depth - 1, alpha, beta, False)
                board.pop()

                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break  # Beta cutoff (prune remaining moves)
            return max_eval
        else:
            min_eval = float('inf')
            for move in ordered_moves:
                board.push(move)
                eval_score = self._alpha_beta(board, depth - 1, alpha, beta, True)
                board.pop()

                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break  # Alpha cutoff (prune remaining moves)
            return min_eval

    def select_move(self, board: chess.Board) -> chess.Move:
        """Select best move using Alpha-Beta pruning with move ordering."""
        self.nodes_evaluated = 0
        best_move = None
        is_white = (board.turn == chess.WHITE)
        legal_moves = list(board.legal_moves)
        ordered_moves = self._order_moves(board, legal_moves)

        alpha = float('-inf')
        beta = float('inf')

        if is_white:
            best_score = float('-inf')
            for move in ordered_moves:
                board.push(move)
                score = self._alpha_beta(board, self.search_depth - 1, alpha, beta, False)
                board.pop()

                if score > best_score:
                    best_score = score
                    best_move = move
                alpha = max(alpha, best_score)
        else:
            best_score = float('inf')
            for move in ordered_moves:
                board.push(move)
                score = self._alpha_beta(board, self.search_depth - 1, alpha, beta, True)
                board.pop()

                if score < best_score:
                    best_score = score
                    best_move = move
                beta = min(beta, best_score)

        return best_move
