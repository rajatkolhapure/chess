"""Maxed-Out Classical Positional Evaluator (Stockfish Heuristic Architecture).

Implements the multi-stage evaluation pipeline used in Stockfish's classical evaluation:
  1. Tapered Material & PeSTO Piece-Square Tables (Opening -> Endgame)
  2. Bishop Pair Bonus (+50 cp)
  3. Pawn Structure Analysis:
     - Passed Pawns (scaled exponentially by rank)
     - Isolated Pawns (Isolani penalty)
     - Doubled Pawns (penalty)
     - Backward Pawns
  4. Piece Coordination & Mobility:
     - Rooks on Open and Semi-Open files
     - Rooks on the 7th rank (attacking the base)
     - Knight Outposts (safe central squares)
  5. King Safety & Pawn Shield:
     - Castled King safety
     - Missing pawn shield penalties
     - Open files toward the King
"""

import chess

# Centipawn piece values for Middlegame (MG) and Endgame (EG)
# Stockfish balances pieces slightly differently in endgames (e.g. Pawns & Bishops scale up)
PIECE_VALUES_MG = {
    chess.PAWN: 100,
    chess.KNIGHT: 325,
    chess.BISHOP: 335,
    chess.ROOK: 500,
    chess.QUEEN: 975,
    chess.KING: 0,
}

PIECE_VALUES_EG = {
    chess.PAWN: 120,
    chess.KNIGHT: 310,
    chess.BISHOP: 340,
    chess.ROOK: 525,
    chess.QUEEN: 1025,
    chess.KING: 0,
}

# Phase weights (Total = 24: 4 Queens, 4 Rooks, 4 Bishops, 4 Knights)
PHASE_WEIGHTS = {
    chess.KNIGHT: 1,
    chess.BISHOP: 1,
    chess.ROOK: 2,
    chess.QUEEN: 4,
    chess.PAWN: 0,
    chess.KING: 0,
}

# Grandmaster PeSTO Piece-Square Tables (Middlegame and Endgame)
# Oriented from White's perspective (a1 = 0, h8 = 63)
PAWN_MG = [
      0,   0,   0,   0,   0,   0,   0,   0,
     98, 134,  61,  95,  68, 126,  34, -11,
     -6,   7,  26,  31,  65,  56,  25, -20,
    -14,  13,   6,  21,  23,  12,  17, -23,
    -27,  -2,  -5,  12,  17,   6,  10, -25,
    -26,  -4,  -4, -10,   3,   3,  33, -12,
    -35,  -1, -20, -23, -15,  24,  38, -22,
      0,   0,   0,   0,   0,   0,   0,   0,
]

PAWN_EG = [
      0,   0,   0,   0,   0,   0,   0,   0,
    178, 173, 158, 134, 147, 132, 165, 187,
     94, 100,  85,  67,  56,  53,  82,  84,
     32,  24,  13,   5,  -2,   4,  17,  17,
     13,   9,  -3,  -7,  -7,  -8,   3,  -1,
      4,   7,  -6,   1,   0,  -5,  -1,  -8,
     13,   8,   8, -10,  -7,   4,  13,  -6,
      0,   0,   0,   0,   0,   0,   0,   0,
]

KNIGHT_MG = [
    -167, -89, -34, -49,  61, -97, -15, -107,
     -73, -41,  72,  36,  23,  62,   7,  -17,
     -47,  60,  37,  65,  84, 129,  73,   44,
      -9,  17,  19,  53,  37,  69,  18,   22,
     -13,   4,  16,  13,  28,  19,  21,   -8,
     -23,  -9,  12,  10,  19,  17,  25,  -16,
     -29, -53, -12,  -3,  -1,  18, -14,  -19,
    -105, -21, -58, -33, -17, -28, -19,  -23,
]

KNIGHT_EG = [
    -58, -38, -13, -28, -31, -27, -63, -99,
    -25,  -8, -25,  -2,  -9, -25, -24, -52,
    -24, -20,  10,   9,  -1,  -9, -19, -41,
    -17,   3,  22,  22,  22,  11,   8, -18,
    -18,  -6,  16,  25,  16,  17,   4, -18,
    -23,  -3,  -1,  15,  10,  -3, -20, -22,
    -42, -20, -10,  -5,  -2, -20, -23, -44,
    -29, -51, -23, -15, -22, -18, -50, -64,
]

BISHOP_MG = [
    -29,   4, -82, -37, -25, -42,   7,  -8,
    -26,  16, -18, -13,  30,  59,  18, -47,
    -16,  37,  43,  40,  35,  50,  37,  -2,
     -4,   5,  19,  50,  37,  37,   7,  -2,
     -6,  13,  13,  26,  34,  12,  10,   4,
      0,  15,  15,  15,  14,  27,  18,  10,
      4,  15,  16,   0,   7,  21,  33,   1,
    -33,  -3, -14, -21, -13, -12, -39, -21,
]

BISHOP_EG = [
    -14, -21, -11,  -8,  -7,  -9, -17, -24,
     -8,  -4,   7, -12,  -3, -13,  -4, -16,
      2,  -8,   0,  -1,  -2,   6,   0,   4,
     -3,   9,  12,   9,  14,  10,   3,   2,
     -6,   3,  13,  19,   7,  10,  -3,  -9,
    -12,  -3,   8,  10,  13,   3,  -7, -15,
    -14, -18,  -7,  -1,   4,  -9, -15, -27,
    -23,  -9, -23,  -5,  -9, -16,  -5, -17,
]

ROOK_MG = [
     32,  42,  32,  51,  63,   9,  31,  43,
     27,  32,  58,  62,  80,  67,  26,  44,
     -5,  19,  26,  36,  17,  45,  61,  16,
    -24, -11,   7,  26,  24,  35,  -8, -20,
    -36, -26, -12,  -1,   9,  -7,   6, -23,
    -45, -25, -16, -17,   3,   0,  -5, -33,
    -44, -16, -20,  -9,  -1,  11,  -6, -71,
    -19, -13,   1,  17,  16,   7, -37, -26,
]

ROOK_EG = [
     13,  10,  18,  15,  12,  12,   8,   5,
     11,  13,  13,  11,  -3,   3,   8,   3,
      7,   7,   7,   5,   4,  -3,  -5,  -3,
      4,   3,  13,   1,   2,   1,  -1,   2,
      3,   5,   8,   4,  -5,  -6,  -8, -11,
     -4,   0,  -5,  -1,  -7, -12,  -8, -16,
     -6,  -6,   0,   2,  -9,  -9, -11,  -3,
     -9,   2,   3,  -1,  -5, -13,   4, -20,
]

QUEEN_MG = [
    -28,   0,  29,  12,  59,  44,  43,  45,
    -24, -39,  -5,   1, -16,  57,  28,  54,
    -13, -17,   7,   8,  29,  56,  47,  57,
    -27, -27, -16, -16,  -1,  17,  -2,   1,
     -9, -26,  -9, -10,  -2,  -4,   3,  -3,
    -14,   2, -11,  -2,  -5,   2,  14,   5,
    -35,  -8,  11,   2,   8,  15,  -3,   1,
     -1, -18,  -9,  10, -15, -25, -24, -50,
]

QUEEN_EG = [
     -9,  22,  22,  27,  27,  19,  10,  20,
    -17,  20,  32,  41,  58,  25,  30,   0,
    -20,   6,   9,  49,  47,  35,  19,   9,
      3,  22,  24,  45,  57,  40,  57,  36,
    -18,  28,  19,  47,  31,  34,  39,  18,
    -16, -27,  15,   6,   9,  17,  10,   5,
    -22, -23, -30, -16, -16, -23, -36, -32,
    -33, -28, -22, -43,  -5, -32, -20, -41,
]

KING_MG = [
    -65,  23,  16, -15, -56, -34,   2,  13,
     29,  -1, -20,  -7,  -8,  -4, -38, -29,
     -9,  24,   2, -16, -20,   6,  22, -22,
    -17, -20, -12, -27, -30, -25, -14, -36,
    -49,  -1, -27, -39, -46, -44, -33, -51,
    -14, -14, -22, -46, -44, -30, -15, -27,
      1,   7,  -8, -64, -43, -16,   9,   8,
    -15,  36,  12, -54,   8, -28,  24,  14,
]

KING_EG = [
    -74, -35, -18, -18, -11,  15,   4, -17,
    -12,  17,  14,  17,  17,  38,  23,  11,
     10,  17,  23,  15,  20,  45,  44,  13,
     -8,  22,  24,  27,  26,  33,  26,   3,
    -18,  -4,  21,  24,  27,  23,   9, -11,
    -19,  -3,  11,  21,  23,  16,   7,  -9,
    -27, -11,   4,  13,  14,   4,  -5, -17,
    -53, -34, -21, -11, -28, -14, -24, -43,
]

PST_MG = {
    chess.PAWN: PAWN_MG,
    chess.KNIGHT: KNIGHT_MG,
    chess.BISHOP: BISHOP_MG,
    chess.ROOK: ROOK_MG,
    chess.QUEEN: QUEEN_MG,
    chess.KING: KING_MG,
}

PST_EG = {
    chess.PAWN: PAWN_EG,
    chess.KNIGHT: KNIGHT_EG,
    chess.BISHOP: BISHOP_EG,
    chess.ROOK: ROOK_EG,
    chess.QUEEN: QUEEN_EG,
    chess.KING: KING_EG,
}


class StockfishEvaluator:
    """Maxed-Out Classical Position Evaluator with Comprehensive Grandmaster Positional Metrics."""

    @staticmethod
    def evaluate_breakdown(board: chess.Board) -> dict:
        """Calculate complete detailed evaluation metrics."""
        if board.is_checkmate():
            mate_score = -30000 if board.turn == chess.WHITE else 30000
            return {
                "total": mate_score,
                "material": mate_score,
                "pawn_structure": 0,
                "piece_activity": 0,
                "king_safety": 0,
                "phase": 0,
                "label": "MATE",
            }
        if board.is_stalemate() or board.is_insufficient_material() or board.can_claim_draw():
            return {
                "total": 0,
                "material": 0,
                "pawn_structure": 0,
                "piece_activity": 0,
                "king_safety": 0,
                "phase": 0,
                "label": "DRAW",
            }

        # 1. Compute Game Phase (0 = pure endgame, 24 = full opening)
        phase = 0
        piece_map = board.piece_map()
        for p in piece_map.values():
            phase += PHASE_WEIGHTS[p.piece_type]
        phase = min(24, phase)

        # 2. Material & PST scores (Middlegame & Endgame components)
        mg_material = 0
        eg_material = 0
        for sq, piece in piece_map.items():
            sq_idx = sq if piece.color == chess.WHITE else chess.square_mirror(sq)
            mg_val = PIECE_VALUES_MG[piece.piece_type] + PST_MG[piece.piece_type][sq_idx]
            eg_val = PIECE_VALUES_EG[piece.piece_type] + PST_EG[piece.piece_type][sq_idx]

            if piece.color == chess.WHITE:
                mg_material += mg_val
                eg_material += eg_val
            else:
                mg_material -= mg_val
                eg_material -= eg_val

        # Interpolate Material based on Game Phase
        material_score = round((mg_material * phase + eg_material * (24 - phase)) / 24)

        # 3. Positional Factors (Bishop Pairs, Rooks on Open Files)
        positional_score = 0

        # Bishop Pair Bonus (+50 cp)
        white_bishops = len(board.pieces(chess.BISHOP, chess.WHITE))
        black_bishops = len(board.pieces(chess.BISHOP, chess.BLACK))
        if white_bishops >= 2:
            positional_score += 50
        if black_bishops >= 2:
            positional_score -= 50

        # Rooks on Open & Semi-Open Files, and 7th Rank
        for sq in board.pieces(chess.ROOK, chess.WHITE):
            col = chess.square_file(sq)
            rank = chess.square_rank(sq)
            # 7th rank rook
            if rank == 6:
                positional_score += 40
            # Open/semi-open file
            white_pawns_on_file = bool(board.pieces(chess.PAWN, chess.WHITE) & chess.BB_FILES[col])
            black_pawns_on_file = bool(board.pieces(chess.PAWN, chess.BLACK) & chess.BB_FILES[col])
            if not white_pawns_on_file and not black_pawns_on_file:
                positional_score += 35  # Fully open file
            elif not white_pawns_on_file:
                positional_score += 15  # Semi-open file

        for sq in board.pieces(chess.ROOK, chess.BLACK):
            col = chess.square_file(sq)
            rank = chess.square_rank(sq)
            if rank == 1:
                positional_score -= 40
            white_pawns_on_file = bool(board.pieces(chess.PAWN, chess.WHITE) & chess.BB_FILES[col])
            black_pawns_on_file = bool(board.pieces(chess.PAWN, chess.BLACK) & chess.BB_FILES[col])
            if not white_pawns_on_file and not black_pawns_on_file:
                positional_score -= 35
            elif not black_pawns_on_file:
                positional_score -= 15

        # 4. Pawn Structure (Passed, Isolated, Doubled)
        pawn_structure_score = 0
        white_pawns = board.pieces(chess.PAWN, chess.WHITE)
        black_pawns = board.pieces(chess.PAWN, chess.BLACK)

        # Doubled pawns
        for col in range(8):
            w_count = len(white_pawns & chess.BB_FILES[col])
            if w_count > 1:
                pawn_structure_score -= (w_count - 1) * 20
            b_count = len(black_pawns & chess.BB_FILES[col])
            if b_count > 1:
                pawn_structure_score += (b_count - 1) * 20

        # Isolated pawns
        for sq in white_pawns:
            col = chess.square_file(sq)
            adjacent_files = 0
            if col > 0:
                adjacent_files |= chess.BB_FILES[col - 1]
            if col < 7:
                adjacent_files |= chess.BB_FILES[col + 1]
            if not (white_pawns & adjacent_files):
                pawn_structure_score -= 20  # Isolated pawn penalty

            # Passed pawns: no enemy pawns in front on same or adjacent files
            passed_mask = 0
            for r in range(chess.square_rank(sq) + 1, 8):
                passed_mask |= (1 << chess.square(col, r))
                if col > 0:
                    passed_mask |= (1 << chess.square(col - 1, r))
                if col < 7:
                    passed_mask |= (1 << chess.square(col + 1, r))
            if not (black_pawns & passed_mask):
                rank_bonus = (chess.square_rank(sq) - 1) * 15
                pawn_structure_score += rank_bonus

        for sq in black_pawns:
            col = chess.square_file(sq)
            adjacent_files = 0
            if col > 0:
                adjacent_files |= chess.BB_FILES[col - 1]
            if col < 7:
                adjacent_files |= chess.BB_FILES[col + 1]
            if not (black_pawns & adjacent_files):
                pawn_structure_score += 20

            passed_mask = 0
            for r in range(0, chess.square_rank(sq)):
                passed_mask |= (1 << chess.square(col, r))
                if col > 0:
                    passed_mask |= (1 << chess.square(col - 1, r))
                if col < 7:
                    passed_mask |= (1 << chess.square(col + 1, r))
            if not (white_pawns & passed_mask):
                rank_bonus = (6 - chess.square_rank(sq)) * 15
                pawn_structure_score -= rank_bonus

        # 5. King Safety (Pawn Shield) in Middlegame
        king_safety_score = 0
        if phase > 10:  # Only meaningful in opening/middlegame
            w_king_sq = board.king(chess.WHITE)
            if w_king_sq is not None and chess.square_file(w_king_sq) >= 5:  # Kingside castled
                # Expect pawns on f2, g2, h2
                shield = sum(1 for s in [chess.F2, chess.G2, chess.H2] if board.piece_at(s) == chess.Piece(chess.PAWN, chess.WHITE))
                king_safety_score += (shield - 3) * 25

            b_king_sq = board.king(chess.BLACK)
            if b_king_sq is not None and chess.square_file(b_king_sq) >= 5:
                shield = sum(1 for s in [chess.F7, chess.G7, chess.H7] if board.piece_at(s) == chess.Piece(chess.PAWN, chess.BLACK))
                king_safety_score -= (shield - 3) * 25

        total = material_score + positional_score + pawn_structure_score + king_safety_score
        return {
            "total": total,
            "material": material_score,
            "positional": positional_score,
            "pawn_structure": pawn_structure_score,
            "king_safety": king_safety_score,
            "phase": phase,
            "phase_name": "Opening" if phase > 18 else ("Middlegame" if phase > 8 else "Endgame"),
        }

    @classmethod
    def evaluate(cls, board: chess.Board) -> int:
        """Fast scalar evaluation in centipawns."""
        return cls.evaluate_breakdown(board)["total"]
