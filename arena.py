"""Interactive Arena for Sparring and Bot vs Bot matches."""
import sys
import chess
from engines import GreedyBot

ENGINES = {
    "1": GreedyBot,
}


def render_board(board: chess.Board, player_is_white: bool = True):
    """Render a clean ASCII chess board with coordinates."""
    ranks = range(7, -1, -1) if player_is_white else range(8)
    files = range(8) if player_is_white else range(7, -1, -1)

    print("\n   +-----------------+")
    for r in ranks:
        row_str = f" {r + 1} |"
        for f in files:
            piece = board.piece_at(chess.square(f, r))
            symbol = piece.symbol() if piece else "."
            row_str += f" {symbol}"
        row_str += " |"
        print(row_str)
    print("   +-----------------+")
    file_labels = "     a b c d e f g h" if player_is_white else "     h g f e d c b a"
    print(file_labels)
    turn_str = "White" if board.turn == chess.WHITE else "Black"
    print(f"\nTurn: {turn_str} | Move #{board.fullmove_number}")


def play_human_vs_bot(bot, human_is_white: bool = True):
    board = chess.Board()
    print(f"\n--- Starting Sparring Match vs {bot.name} ---")
    print("Commands: Enter move in UCI format (e.g., e2e4, g1f3) or type 'quit' / 'resign'.\n")

    while not board.is_game_over():
        render_board(board, player_is_white=human_is_white)
        is_human_turn = (board.turn == chess.WHITE) if human_is_white else (board.turn == chess.BLACK)

        if is_human_turn:
            while True:
                user_input = input("\nYour move > ").strip().lower()
                if user_input in ["quit", "exit", "resign"]:
                    print("Game aborted.")
                    return
                try:
                    move = chess.Move.from_uci(user_input)
                    if move in board.legal_moves:
                        board.push(move)
                        break
                    else:
                        print("Illegal move! Try again. (Legal examples: e2e4, b1c3)")
                except ValueError:
                    print("Invalid notation format! Use standard coordinates like: e2e4, d7d5")
        else:
            print(f"\n{bot.name} is thinking...")
            bot_move = bot.select_move(board)
            print(f"{bot.name} played: {bot_move.uci()}")
            board.push(bot_move)

    render_board(board, player_is_white=human_is_white)
    print("\n=== Game Over ===")
    if board.is_checkmate():
        winner = "Black" if board.turn == chess.WHITE else "White"
        print(f"Checkmate! Winner: {winner}")
    elif board.is_stalemate():
        print("Stalemate! Game is a draw.")
    elif board.is_insufficient_material():
        print("Draw due to insufficient material.")
    else:
        print("Game drawn.")


def main():
    print("==========================================")
    print("        CHESS BOT ARENA                   ")
    print("==========================================")
    print("Available Engines:")
    print("  [1] Level 1: The Greedy Bot (Static Eval & Depth 1)")
    print("\nGame Options:")
    print("  [w] Play as White")
    print("  [b] Play as Black")
    print("  [q] Quit")

    choice = input("\nSelect Engine [1]: ").strip() or "1"
    bot_class = ENGINES.get(choice, GreedyBot)
    bot = bot_class()

    side = input("Play as White (w) or Black (b)? [w]: ").strip().lower() or "w"
    human_is_white = (side != "b")

    play_human_vs_bot(bot, human_is_white=human_is_white)


if __name__ == "__main__":
    main()
