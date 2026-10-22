"""Level 1: The Greedy Bot.

Evolutionary Stage: 1 (Static Evaluation Only)
Capabilities:
  - Static Evaluation: Material count + Piece-Square Tables (PST) + Mobility.
  - Game-Phase Tapering: Switches King safety to King centralization in endgame.
  - Search: Depth 1 only. Plays the move that produces the highest immediate evaluation.
Limitations:
  - Blind to opponent replies: Falls for simple 1-move traps, sacrifices, and defended pieces.
"""

import chess
from .base import BaseEngine

# Piece base values in centipawns (1 pawn = 100 cp)
PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000,
}

# Piece-Square Tables (oriented for White, from a1 to h8; square index 0 is a1, 63 is h8)
PAWN_TABLE = [
     0,  0,  0,  0,  0,  0,  0,  0,
     5, 10, 10,-20,-20, 10, 10,  5,
     5, -5,-10,  0,  0,-10, -5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5,  5, 10, 25, 25, 10,  5,  5,
    10, 10, 20, 30, 30, 20, 10, 10,
    50, 50, 50, 50, 50, 50, 50, 50,
     0,  0,  0,  0,  0,  0,  0,  0
]

KNIGHT_TABLE = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50
]

BISHOP_TABLE = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -20,-10,-10,-10,-10,-10,-10,-20
]

ROOK_TABLE = [
      0,  0,  0,  5,  5,  0,  0,  0,
     -5,  0,  0,  0,  0,  0,  0, -5,
     -5,  0,  0,  0,  0,  0,  0, -5,
     -5,  0,  0,  0,  0,  0,  0, -5,
     -5,  0,  0,  0,  0,  0,  0, -5,
     -5,  0,  0,  0,  0,  0,  0, -5,
      5, 10, 10, 10, 10, 10, 10,  5,
      0,  0,  0,  0,  0,  0,  0,  0
]

QUEEN_TABLE = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -10,  5,  5,  5,  5,  5,  0,-10,
      0,  0,  5,  5,  5,  5,  0, -5,
     -5,  0,  5,  5,  5,  5,  0, -5,
    -10,  0,  5,  5,  5,  5,  0,-10,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20
]

KING_MIDDLEGAME_TABLE = [
     20, 30, 10,  0,  0, 10, 30, 20,
     20, 20,  0,  0,  0,  0, 20, 20,
    -10,-20,-20,-20,-20,-20,-20,-10,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30
]

KING_ENDGAME_TABLE = [
    -50,-30,-30,-30,-30,-30,-30,-50,
    -30,-10,  0,  0,  0,  0,-10,-30,
    -30, -5, 20, 30, 30, 20, -5,-30,
    -30,  0, 30, 40, 40, 30,  0,-30,
    -30,  0, 30, 40, 40, 30,  0,-30,
    -30, -5, 20, 30, 30, 20, -5,-30,
    -30,-10,  0,  0,  0,  0,-10,-30,
    -50,-30,-30,-30,-30,-30,-30,-50
]

PST = {
    chess.PAWN: PAWN_TABLE,
    chess.KNIGHT: KNIGHT_TABLE,
    chess.BISHOP: BISHOP_TABLE,
    chess.ROOK: ROOK_TABLE,
    chess.QUEEN: QUEEN_TABLE,
}


class GreedyBot(BaseEngine):
    """Level 1 Bot: Pure Static Evaluation with Depth-1 Lookahead."""

    def __init__(self):
        super().__init__(
            name="Level 1: Greedy Bot",
            description="Evaluates frozen positions using Material + PSTs + Mobility. Picks the best single immediate move."
        )

    def _is_endgame(self, board: chess.Board) -> bool:
        """Detect whether game has reached the endgame phase (queens gone or minor material)."""
        white_queens = len(board.pieces(chess.QUEEN, chess.WHITE))
        black_queens = len(board.pieces(chess.QUEEN, chess.BLACK))
        if white_queens == 0 and black_queens == 0:
            return True
        major_pieces = (
            len(board.pieces(chess.ROOK, chess.WHITE)) + len(board.pieces(chess.ROOK, chess.BLACK)) +
            len(board.pieces(chess.KNIGHT, chess.WHITE)) + len(board.pieces(chess.KNIGHT, chess.BLACK)) +
            len(board.pieces(chess.BISHOP, chess.WHITE)) + len(board.pieces(chess.BISHOP, chess.BLACK))
        )
        return major_pieces <= 4

    def evaluate(self, board: chess.Board) -> int:
        """Statically evaluate board position from White's perspective."""
        self.nodes_evaluated += 1

        if board.is_checkmate():
            # If the side to move is checkmated:
            return -20000 if board.turn == chess.WHITE else 20000
        if board.is_stalemate() or board.is_insufficient_material() or board.can_claim_draw():
            return 0

        score = 0
        is_endgame = self._is_endgame(board)

        # 1. Material & Piece-Square Tables
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if not piece:
                continue

            piece_val = PIECE_VALUES[piece.piece_type]

            # PST index calculation (mirror square for black)
            if piece.piece_type == chess.KING:
                table = KING_ENDGAME_TABLE if is_endgame else KING_MIDDLEGAME_TABLE
            else:
                table = PST[piece.piece_type]

            sq_idx = square if piece.color == chess.WHITE else chess.square_mirror(square)
            pst_val = table[sq_idx]

            total_piece_score = piece_val + pst_val
            if piece.color == chess.WHITE:
                score += total_piece_score
            else:
                score -= total_piece_score

        # 2. Mobility Bonus (1 centipawn per legal move)
        # Note: In pure static evaluation, mobility adds subtle activity incentives
        white_mobility = 0
        black_mobility = 0
        current_turn = board.turn

        board.turn = chess.WHITE
        white_mobility = board.legal_moves.count()
        board.turn = chess.BLACK
        black_mobility = board.legal_moves.count()
        board.turn = current_turn

        score += (white_mobility - black_mobility) * 2

        return score

    def select_move(self, board: chess.Board) -> chess.Move:
        """Select the move that yields the best static evaluation on the next ply."""
        best_move = None
        is_white = (board.turn == chess.WHITE)
        best_score = float('-inf') if is_white else float('inf')

        for move in board.legal_moves:
            board.push(move)
            eval_score = self.evaluate(board)
            board.pop()

            if is_white:
                if eval_score > best_score:
                    best_score = eval_score
                    best_move = move
            else:
                if eval_score < best_score:
                    best_score = eval_score
                    best_move = move

        return best_move
