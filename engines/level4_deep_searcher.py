"""Level 4: The Deep Searcher.

Evolutionary Stage: 5 & 6 (Transposition Tables, Null-Move Pruning, & Iterative Deepening)
Capabilities:
  - Transposition Tables (TT): Caches positions via 64-bit Zobrist Hashing so identical board
    states reached via different move orders are never recalculated.
  - Null-Move Pruning (NMP): Passes the turn to the opponent to test if the position is already
    so overwhelmingly won that it refutes the branch without searching 30+ moves (2x-3x speedup).
  - Killer Move Heuristic: Remembers non-capture moves that caused beta cutoffs at each ply.
  - Iterative Deepening with Time Management: Searches Depth 1 -> 2 -> 3 -> 4 -> 5 -> 6+.
    Guarantees optimal move ordering from the previous depth's best move.
  - Stockfish Classical Evaluator at leaf nodes.
Target Elo: ~1900–2200
"""

import time
import chess
import chess.polyglot
from .base import BaseEngine
from .level1_greedy import PIECE_VALUES
from evaluator import StockfishEvaluator

# TT Entry flags
FLAG_EXACT = 0
FLAG_LOWERBOUND = 1
FLAG_UPPERBOUND = 2


class DeepSearcherBot(BaseEngine):
    """Level 4 Bot: Grandmaster Search Acceleration Engine."""

    def __init__(self, max_depth: int = 6, time_limit: float = 2.0):
        super().__init__(
            name="Level 4: The Deep Searcher",
            description=f"Iterative Deepening to Depth {max_depth} using Zobrist Transposition Tables, Null-Move Pruning, and Killer Heuristics."
        )
        self.max_depth = max_depth
        self.time_limit = time_limit
        self.start_time = 0.0
        self.tt = {}  # Zobrist hash table: key -> (depth, flag, score, best_move)
        self.killer_moves = {}  # ply -> [move1, move2]

    def evaluate(self, board: chess.Board) -> int:
        return StockfishEvaluator.evaluate(board)

    def _is_time_up(self) -> bool:
        return (time.time() - self.start_time) >= self.time_limit

    def _mvv_lva_score(self, board: chess.Board, move: chess.Move, tt_move: chess.Move = None, ply: int = 0) -> int:
        """Move ordering priority: TT Best Move > Winning Captures > Killer Moves > Quiet Moves."""
        if tt_move and move == tt_move:
            return 200000  # Highest priority: Previous iteration's best move

        if board.is_capture(move):
            victim = board.piece_at(move.to_square)
            attacker = board.piece_at(move.from_square)
            victim_val = PIECE_VALUES[victim.piece_type] if victim else 100
            attacker_val = PIECE_VALUES[attacker.piece_type] if attacker else 100
            return 100000 + (victim_val * 10) - attacker_val

        # Killer move bonus
        killers = self.killer_moves.get(ply, [])
        if move in killers:
            return 50000

        return 0

    def _order_moves(self, board: chess.Board, moves, tt_move: chess.Move = None, ply: int = 0):
        return sorted(moves, key=lambda m: self._mvv_lva_score(board, m, tt_move, ply), reverse=True)

    def _quiescence(self, board: chess.Board, alpha: int, beta: int, is_maximizing: bool, q_depth: int = 6) -> int:
        self.nodes_evaluated += 1
        stand_pat = self.evaluate(board)

        if q_depth <= 0:
            return stand_pat

        if is_maximizing:
            if stand_pat >= beta:
                return beta
            if stand_pat > alpha:
                alpha = stand_pat

            captures = [m for m in board.legal_moves if board.is_capture(m)]
            ordered = self._order_moves(board, captures)

            for move in ordered:
                board.push(move)
                try:
                    score = self._quiescence(board, alpha, beta, False, q_depth - 1)
                finally:
                    board.pop()

                if score >= beta:
                    return beta
                if score > alpha:
                    alpha = score
            return alpha
        else:
            if stand_pat <= alpha:
                return alpha
            if stand_pat < beta:
                beta = stand_pat

            captures = [m for m in board.legal_moves if board.is_capture(m)]
            ordered = self._order_moves(board, captures)

            for move in ordered:
                board.push(move)
                try:
                    score = self._quiescence(board, alpha, beta, True, q_depth - 1)
                finally:
                    board.pop()

                if score <= alpha:
                    return alpha
                if score < beta:
                    beta = score
            return beta

    def _search(self, board: chess.Board, depth: int, alpha: int, beta: int, is_maximizing: bool, ply: int = 0, allow_null: bool = True) -> int:
        self.nodes_evaluated += 1

        if self._is_time_up():
            raise TimeoutError("Search time exceeded")

        zobrist_key = chess.polyglot.zobrist_hash(board)
        tt_entry = self.tt.get(zobrist_key)
        tt_move = None

        if tt_entry:
            cached_depth, cached_flag, cached_score, cached_move = tt_entry
            tt_move = cached_move
            if cached_depth >= depth:
                if cached_flag == FLAG_EXACT:
                    return cached_score
                elif cached_flag == FLAG_LOWERBOUND and cached_score >= beta:
                    return cached_score
                elif cached_flag == FLAG_UPPERBOUND and cached_score <= alpha:
                    return cached_score

        if depth <= 0:
            return self._quiescence(board, alpha, beta, is_maximizing)

        legal_moves = list(board.legal_moves)
        if not legal_moves:
            if board.is_check():
                return -20000 - depth if is_maximizing else 20000 + depth
            return 0

        # --- Null-Move Pruning (NMP) ---
        has_major_pieces = bool(
            board.pieces(chess.ROOK, board.turn) |
            board.pieces(chess.BISHOP, board.turn) |
            board.pieces(chess.KNIGHT, board.turn) |
            board.pieces(chess.QUEEN, board.turn)
        )
        if allow_null and depth >= 3 and not board.is_check() and has_major_pieces:
            R = 2
            board.push(chess.Move.null())
            try:
                null_score = self._search(board, depth - 1 - R, alpha, beta, not is_maximizing, ply + 1, allow_null=False)
            finally:
                board.pop()

            if is_maximizing and null_score >= beta:
                return beta
            if not is_maximizing and null_score <= alpha:
                return alpha

        ordered_moves = self._order_moves(board, legal_moves, tt_move=tt_move, ply=ply)
        best_move_here = None
        orig_alpha = alpha
        orig_beta = beta

        if is_maximizing:
            max_eval = float('-inf')
            for move in ordered_moves:
                board.push(move)
                try:
                    eval_score = self._search(board, depth - 1, alpha, beta, False, ply + 1, allow_null=True)
                finally:
                    board.pop()

                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move_here = move

                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    if not board.is_capture(move):
                        killers = self.killer_moves.setdefault(ply, [])
                        if move not in killers:
                            killers.insert(0, move)
                            if len(killers) > 2:
                                killers.pop()
                    break

            flag = FLAG_EXACT
            if max_eval <= orig_alpha:
                flag = FLAG_UPPERBOUND
            elif max_eval >= beta:
                flag = FLAG_LOWERBOUND
            self.tt[zobrist_key] = (depth, flag, max_eval, best_move_here)

            return max_eval
        else:
            min_eval = float('inf')
            for move in ordered_moves:
                board.push(move)
                try:
                    eval_score = self._search(board, depth - 1, alpha, beta, True, ply + 1, allow_null=True)
                finally:
                    board.pop()

                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move_here = move

                beta = min(beta, eval_score)
                if beta <= alpha:
                    if not board.is_capture(move):
                        killers = self.killer_moves.setdefault(ply, [])
                        if move not in killers:
                            killers.insert(0, move)
                            if len(killers) > 2:
                                killers.pop()
                    break

            flag = FLAG_EXACT
            if min_eval >= orig_beta:
                flag = FLAG_LOWERBOUND
            elif min_eval <= alpha:
                flag = FLAG_UPPERBOUND
            self.tt[zobrist_key] = (depth, flag, min_eval, best_move_here)

            return min_eval

    def select_move(self, board: chess.Board) -> chess.Move:
        """Select best move using Iterative Deepening with Transposition Table guidance."""
        work_board = board.copy()
        self.nodes_evaluated = 0
        self.start_time = time.time()
        self.killer_moves = {}
        is_white = (work_board.turn == chess.WHITE)

        legal_moves = list(work_board.legal_moves)
        if not legal_moves:
            return None
        if len(legal_moves) == 1:
            return legal_moves[0]

        best_overall_move = legal_moves[0]

        # Iterative Deepening Loop (Depth 1 up to max_depth)
        for depth in range(1, self.max_depth + 1):
            if self._is_time_up():
                break

            current_best_move = None
            alpha = float('-inf')
            beta = float('inf')

            ordered_moves = self._order_moves(work_board, legal_moves, tt_move=best_overall_move, ply=0)

            try:
                if is_white:
                    best_score = float('-inf')
                    for move in ordered_moves:
                        work_board.push(move)
                        try:
                            score = self._search(work_board, depth - 1, alpha, beta, False, ply=1, allow_null=True)
                        finally:
                            work_board.pop()

                        if score > best_score:
                            best_score = score
                            current_best_move = move
                        alpha = max(alpha, best_score)
                else:
                    best_score = float('inf')
                    for move in ordered_moves:
                        work_board.push(move)
                        try:
                            score = self._search(work_board, depth - 1, alpha, beta, True, ply=1, allow_null=True)
                        finally:
                            work_board.pop()

                        if score < best_score:
                            best_score = score
                            current_best_move = move
                        beta = min(beta, best_score)

                if current_best_move:
                    best_overall_move = current_best_move

            except TimeoutError:
                break

        return best_overall_move
