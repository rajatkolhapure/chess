"""Lightweight Web GUI Server for Chess Bot Arena."""
import json
import os
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse
import chess
from engines import GreedyBot

ENGINES = {
    "1": GreedyBot(),
}

CURRENT_BOARD = chess.Board()
CURRENT_BOT = ENGINES["1"]


class ChessRequestHandler(SimpleHTTPRequestHandler):
    """Custom HTTP Handler to serve Web GUI and handle Chess Engine API."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.join(os.path.dirname(__file__), "web"), **kwargs)

    def do_POST(self):
        parsed = urlparse(self.path)
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        data = json.loads(body) if body else {}

        global CURRENT_BOARD, CURRENT_BOT

        if parsed.path == "/api/reset":
            bot_level = str(data.get("bot_level", "1"))
            CURRENT_BOT = ENGINES.get(bot_level, ENGINES["1"])
            CURRENT_BOARD = chess.Board()
            self._send_json(self._get_game_state())

        elif parsed.path == "/api/move":
            move_uci = data.get("move")
            try:
                move = chess.Move.from_uci(move_uci)
                if move in CURRENT_BOARD.legal_moves:
                    CURRENT_BOARD.push(move)
                    self._send_json(self._get_game_state())
                else:
                    self._send_json({"error": "Illegal move"}, status=400)
            except Exception as e:
                self._send_json({"error": str(e)}, status=400)

        elif parsed.path == "/api/bot_move":
            bot_level = str(data.get("bot_level", "1"))
            bot = ENGINES.get(bot_level, ENGINES["1"])
            if CURRENT_BOARD.is_game_over():
                self._send_json(self._get_game_state())
                return

            bot.nodes_evaluated = 0
            best_move = bot.select_move(CURRENT_BOARD)
            if best_move and best_move in CURRENT_BOARD.legal_moves:
                CURRENT_BOARD.push(best_move)
                state = self._get_game_state()
                state["bot_move"] = best_move.uci()
                state["nodes_evaluated"] = bot.nodes_evaluated
                self._send_json(state)
            else:
                self._send_json({"error": "No move found"}, status=500)
        else:
            self._send_json({"error": "Not found"}, status=404)

    def _get_game_state(self):
        eval_score = CURRENT_BOT.evaluate(CURRENT_BOARD)
        return {
            "fen": CURRENT_BOARD.fen(),
            "turn": "white" if CURRENT_BOARD.turn == chess.WHITE else "black",
            "is_game_over": CURRENT_BOARD.is_game_over(),
            "is_check": CURRENT_BOARD.is_check(),
            "is_checkmate": CURRENT_BOARD.is_checkmate(),
            "is_stalemate": CURRENT_BOARD.is_stalemate(),
            "eval_score": eval_score,
            "legal_moves": [m.uci() for m in CURRENT_BOARD.legal_moves],
        }

    def _send_json(self, data, status=200):
        response = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)


def start_server(port=8080):
    server = HTTPServer(("127.0.0.1", port), ChessRequestHandler)
    print(f"\n=======================================================")
    print(f"  Chess Bot GUI is running at: http://127.0.0.1:{port}")
    print(f"  Opening in your default web browser...")
    print(f"  Press Ctrl+C to stop the server.")
    print(f"=======================================================\n")
    try:
        webbrowser.open(f"http://127.0.0.1:{port}")
    except Exception:
        pass
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        server.server_close()


if __name__ == "__main__":
    start_server()
