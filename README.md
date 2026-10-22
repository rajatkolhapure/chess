# ♟️ Path to Superhuman: Evolutionary Chess Engine

> A journey from first principles to a superhuman (3500+ Elo) chess engine, focusing purely on **chess logic, evaluation mathematics, and search algorithms**.

---

## 🗺️ The Evolutionary Roadmap

Each stage in this repository represents an evolutionary milestone in computer chess history:

| Level | Engine Name | Key Concepts Introduced | Elo Target | Status |
| :---: | :--- | :--- | :---: | :---: |
| **1** | **The Greedy Bot** | Static Evaluation (Centipawns), Piece-Square Tables, Mobility, Phase Tapering | ~800 |  **Completed** |
| **2** | **The Minimax Bot** | Zero-Sum Game Tree, Adversarial Thinking, Depth 3 Lookahead, Refusing Baits | ~1200 |  **Completed** |
| **3** | **The Tactician** | Quiescence Search, MVV-LVA Move Ordering, Alpha-Beta Pruning, Horizon Fix | ~1500 |  **Completed** |
| **4** | **The Deep Searcher** | Transposition Tables, Zobrist Hashing, Killer Moves, Iterative Deepening | ~1900 | *Next* |
| **5** | **The Grandmaster** | Pawn Structure (Isolani, Passed, Doubled), King Safety, Outposts | ~2200 | *Queued* |
| **6** | **The Speed Demon** | Null-Move Pruning, Late Move Reductions (LMR), History Heuristics | ~2500 | *Queued* |
| **7** | **The Superhuman** | NNUE (Efficiently Updatable Neural Network), Self-Play Learning | 3500+ | *Queued* |

---

## 👤 Real-Time Elo Rating Tracker
The engine includes a live FIDE Elo calculation engine ([elo.py](file:///c:/Users/rmk19/OneDrive/Documents/chess/elo.py)) that tracks your performance across games.
- Starts at provisional **1000 Elo**.
- Dynamically calculates $K$-factor adjustments after every checkmate/draw against each bot level.
- Displayed directly inside the Web GUI sidebar.

---

## 🧠 Stage 3: The Tactician (Quiescence & Alpha-Beta)

Why Level 2 fell off in the middlegame:
1. **The Horizon Effect**: An abrupt search depth cut off calculation mid-trade. Level 2 evaluated positions with blood still on the board.
2. **Combinatorial Explosion**: Without pruning, looking 5 moves deep meant exploring over 100,000,000 moves.

How Level 3 solves this:
- **Quiescence Search**: At the leaf nodes, the engine refuses to freeze if there are active captures. It continues calculating all capture sequences until the position is completely calm ("quiescent").
- **Alpha-Beta Pruning**: If a move branch is mathematically proven to be worse than an existing option, the rest of the branch is pruned immediately.
- **MVV-LVA Ordering**: Moves are sorted by **Most Valuable Victim - Least Valuable Attacker** (e.g. Pawn captures Queen tested before Queen captures Pawn) to trigger immediate beta cutoffs.

---

## 🧠 Stage 2: Minimax vs. Greedy (What Changed?)

| Test Scenario | Level 1: Greedy Bot (Depth 1) | Level 2: Minimax Bot (Depth 3) |
| :--- | :--- | :--- |
| **Checkmate in 1** | Can get distracted by high-value piece capture | **Delivers Mate Instantly (`h5f7#`)** |
| **Poisoned Bait Trap** | **Fell for Trap (`d1d8`)** (Snaps defended rook, loses Queen) | **Refused Bait (`d1b1`)** (Sees Queen recapture on ply 2) |
| **Adversarial Logic** | Assumes opponent is passive | Assumes opponent plays the best possible counter-move |
| **Nodes Explored** | ~35 positions | **~21,000 positions** per move |

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

## 🚀 Quickstart & How to Play

### 1. Requirements
```bash
pip install -r requirements.txt
```

### 2. Launch the Interactive Web GUI (Recommended)
Enjoy drag-and-drop gameplay, real-time evaluation bars, and engine analytics right in your browser:
```bash
python server.py
```
This automatically launches your browser at `http://127.0.0.1:8080`.

### 3. Run the Diagnostic Benchmarks
Run the built-in tactical test suite across all engines:
```bash
python benchmark.py
```

### 4. Terminal Arena (Optional)
If you prefer terminal play:
```bash
python arena.py
```

---

## 📊 Benchmark Results

### Level 1: The Greedy Bot
- `[PASS]` **Hanging Piece Snatch**: Spotted undefended knight on `e5` and captured immediately (`Qxe5`).
- `[PASS]` **Checkmate in 1**: Detected instant mate in Scholar's Mate position (`Qxf7#`).
- `[PASS]` **Principled Opening**: Played `1. e2e4` out of the opening due to central piece-square incentives.
- `[EXPECTED FLAW]` **Poisoned Bait**: Captured a defended rook on `d8` because at Depth 1 it cannot foresee the Queen recapture.
