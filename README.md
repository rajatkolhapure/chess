# ♟️ Path to Superhuman: Evolutionary Chess Engine

> A journey from first principles to a superhuman (3500+ Elo) chess engine, focusing purely on **chess logic, evaluation mathematics, and search algorithms**.

---

## 🗺️ The Evolutionary Roadmap

Each stage in this repository represents an evolutionary milestone in computer chess history:

| Level | Engine Name | Key Concepts Introduced | Elo Target | Status |
| :---: | :--- | :--- | :---: | :---: |
| **1** | **The Greedy Bot** | Static Evaluation (Centipawns), Piece-Square Tables, Mobility, Phase Tapering | ~800 |  **Completed** |
| **2** | **The Minimax Bot** | Zero-Sum Game Tree, Adversarial Thinking, Depth 2-4 Lookahead | ~1200 | *Next* |
| **3** | **The Tactician** | Quiescence Search, Forcing-Move Extension, Eliminating the Horizon Effect | ~1500 | *Queued* |
| **4** | **The Deep Searcher** | Alpha-Beta ($\alpha$-$\beta$) Pruning, MVV-LVA Move Ordering, Killer Moves | ~1900 | *Queued* |
| **5** | **The Grandmaster** | Pawn Structure (Isolani, Passed, Doubled), King Safety, Outposts | ~2200 | *Queued* |
| **6** | **The Speed Demon** | Transposition Tables, Zobrist Hashing, Null-Move Pruning, LMR | ~2500 | *Queued* |
| **7** | **The Superhuman** | NNUE (Efficiently Updatable Neural Network), Self-Play Learning | 3500+ | *Queued* |

---

## 🧠 Stage 1: How Level 1 Thinks

Before a computer can calculate future moves, it must answer one fundamental question:
> *"If the game froze right now, who is winning and by how much?"*

### 1. The Centipawn Metric
All chess positions are scored on a numerical centipawn scale ($100 \text{ centipawns} = 1 \text{ pawn}$):
- `+100`: White is ahead by 1 pawn.
- `-320`: Black is ahead by 1 minor piece.
- `0.0`: Completely balanced.

### 2. Piece-Square Tables (PST)
Counting material alone makes a bot place knights on the rim. We map an $8 \times 8$ grid of positional weights to reward central occupation and active outposts:
- Knight on `d5` / `e5`: **$+20\text{ cp}$** bonus.
- Knight on `a1` (corner): **$-50\text{ cp}$** penalty.

### 3. Game Phase Tapering (The King's Split Personality)
- **Middlegame**: The King is penalized for moving into the center; castling and hiding behind pawn shields is heavily rewarded.
- **Endgame**: When queens and major pieces are traded off, the evaluation smoothly flips to the **Endgame King Table**, driving the King into the center to escort passed pawns.

### 4. The Depth-1 Limitation
Level 1 examines all legal moves on the current ply and picks the one yielding the highest immediate static score.
- **Strength**: Snatches undefended pieces instantly; develops pawns and knights to the center; finds 1-move checkmates.
- **Flaw**: Completely blind to opponent counter-attacks (e.g. captures a defended piece because it doesn't see the recapture on ply 2).

---

## 🚀 Quickstart & Testing

### 1. Requirements
```bash
pip install -r requirements.txt
```

### 2. Run the Diagnostic Benchmarks
Run the built-in diagnostic suite to test the bot against tactical benchmark positions:
```bash
python benchmark.py
```

### 3. Play a Sparring Match
Launch the interactive arena to test your skills against any unlocked level:
```bash
python arena.py
```
Type your moves in standard coordinate notation (e.g. `e2e4`, `g1f3`, `e7e5`).

---

## 📊 Benchmark Results

### Level 1: The Greedy Bot
- `[PASS]` **Hanging Piece Snatch**: Spotted undefended knight on `e5` and captured immediately (`Qxe5`).
- `[PASS]` **Checkmate in 1**: Detected instant mate in Scholar's Mate position (`Qxf7#`).
- `[PASS]` **Principled Opening**: Played `1. e2e4` out of the opening due to central piece-square incentives.
- `[EXPECTED FLAW]` **Poisoned Bait**: Captured a defended rook on `d8` because at Depth 1 it cannot foresee the Queen recapture.
