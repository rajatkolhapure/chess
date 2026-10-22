"""Diagnostic and Benchmark Test Suite for Evolutionary Chess Bots."""
import chess
from engines import GreedyBot, MinimaxBot


def run_benchmarks(bot):
    print(f"\n==========================================")
    print(f"Running Diagnostic Suite on: {bot.name}")
    print(f"==========================================")

    tests_passed = 0
    total_tests = 4

    # --- Test 1: Capture Hanging Piece ---
    # White to move: Black knight on e5 is completely undefended. Best move is Qxe5.
    b1 = chess.Board("r1bqkbnr/pppp1ppp/2n5/4n3/4Q3/8/PPPPPPPP/RNB1KBNR w KQkq - 0 1")
    move1 = bot.select_move(b1)
    captured_piece = b1.piece_at(move1.to_square) if move1 else None
    if move1 and captured_piece and captured_piece.piece_type == chess.KNIGHT:
        print(" [PASS] Test 1: Hanging Piece Capture -> Snatched free piece:", move1.uci())
        tests_passed += 1
    else:
        print(" [FAIL] Test 1: Hanging Piece Capture -> Played:", move1)

    # --- Test 2: Checkmate in 1 ---
    # Scholar's mate delivery: Qxf7# is mate.
    b2 = chess.Board("r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4")
    move2 = bot.select_move(b2)
    b2.push(move2)
    if b2.is_checkmate():
        print(" [PASS] Test 2: Checkmate in 1 -> Spotted immediate mate:", move2.uci())
        tests_passed += 1
    else:
        print(" [FAIL] Test 2: Checkmate in 1 -> Failed mate, played:", move2.uci())
    b2.pop()

    # --- Test 3: Opening Central Control ---
    b3 = chess.Board()
    move3 = bot.select_move(b3)
    good_openers = ["e2e4", "d2d4", "g1f3", "b1c3", "c2c4"]
    if move3 and move3.uci() in good_openers:
        print(f" [PASS] Test 3: Central Development -> Chose principled move: {move3.uci()}")
        tests_passed += 1
    else:
        print(f" [WARN] Test 3: Central Development -> Chose: {move3.uci() if move3 else None}")

    # --- Test 4: The Poisoned Bait (Defended Piece Trap) ---
    # White Queen on d1. Black Rook on d8 is defended by Black Queen on a8.
    # Level 1 takes Qxd8 because +500 immediate points.
    # Level 2+ Minimax looks ahead 3 plies, sees Queen recapture, and refuses Qxd8!
    b4 = chess.Board("q2r2k1/5ppp/8/8/8/8/5PPP/3Q2K1 w - - 0 1")
    move4 = bot.select_move(b4)
    if move4 and move4.uci() == "d1d8":
        print(f" [GREEDY FLAW] Test 4: Poisoned Bait Trap -> Fell for trap: {move4.uci()} (Loses Queen).")
    else:
        print(f" [PASS] Test 4: Poisoned Bait Trap -> Refused bait! Played safe move: {move4.uci() if move4 else None}")
        tests_passed += 1

    print(f"Diagnostic summary for {bot.name}: {tests_passed}/{total_tests} tests passed.")


if __name__ == "__main__":
    bot1 = GreedyBot()
    run_benchmarks(bot1)

    bot2 = MinimaxBot(depth=3)
    run_benchmarks(bot2)
