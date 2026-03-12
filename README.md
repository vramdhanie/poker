# ♠ Poker

![Python](https://img.shields.io/badge/python-3.11%2B-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)
![uv](https://img.shields.io/badge/built%20with-uv-7c3aed?logo=python&logoColor=white)
![No Dependencies](https://img.shields.io/badge/dependencies-none-brightgreen)
![Texas Hold'em](https://img.shields.io/badge/variant-Texas%20Hold'em-red)
![CLI](https://img.shields.io/badge/interface-CLI-black)

A fully-featured Texas Hold'em poker game for the terminal. Play against three AI opponents powered by a GTO-inspired Monte Carlo strategy engine, with full save/resume support.

```
 ██████╗  ██████╗ ██╗  ██╗███████╗██████╗
 ██╔══██╗██╔═══██╗██║ ██╔╝██╔════╝██╔══██╗
 ██████╔╝██║   ██║█████╔╝ █████╗  ██████╔╝
 ██╔═══╝ ██║   ██║██╔═██╗ ██╔══╝  ██╔══██╗
 ██║     ╚██████╔╝██║  ██╗███████╗██║  ██║
 ╚═╝      ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
       Texas Hold'em — Command Line Edition
```

---

## Features

- **Texas Hold'em** — full preflop → flop → turn → river flow with proper blind structure
- **Unicode card icons** — colored suits rendered in your terminal: `[A♠]` `[K♥]` `[Q♦]` `[J♣]`
- **4-player table** — you vs. three AI opponents, each with a unique personality
- **GTO-based AI** — Monte Carlo equity simulation (300 runs/decision) combined with pot odds, position weighting, and probabilistic bluffing so the AI never plays robotically
- **Full betting actions** — Check, Call, Raise (you choose the size), All In, Fold
- **Betting between every street** — pre-flop, flop, turn, and river each have their own round
- **Save & resume** — state is saved to `~/.poker_save.json` after every hand; pick up exactly where you left off
- **Game over flow** — when you go broke, you're shown your stats and offered a new game
- **Zero dependencies** — pure Python 3.11 standard library only

---

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (for setup)

---

## Installation

```bash
# Clone or enter the project directory
cd poker

# Create the virtual environment and install
uv venv
uv pip install -e .
```

---

## Running the Game

```bash
# Option 1 — activate the venv first
source .venv/bin/activate
poker

# Option 2 — run directly from the venv
.venv/bin/poker

# Option 3 — via uv
uv run poker
```

---

## How to Play

### Main Menu

```
  [N]  New Game
  [R]  Resume Game     ← only shown if a save exists
  [Q]  Quit
```

### Between Hands

```
  [D]  Deal next hand
  [S]  Save & Quit
  [Q]  Quit without saving
```

### Betting Actions

| Key | Action | Description |
|-----|--------|-------------|
| `C` | Check / Call | Check if no bet to call; otherwise call the current bet |
| `R` | Raise | Enter a raise amount (min and max shown) |
| `A` | All In | Push all your chips into the pot |
| `F` | Fold | Discard your hand and sit out the rest of the hand |

### Rules

- Blinds are **$10 small / $20 big**, fixed for the entire session
- Everyone starts with **$1,000**
- AI opponents **rebuy** for $1,000 if they bust, so the game always has 4 players
- The game ends when **you** run out of money

---

## AI Opponents

Each AI has a distinct personality that shapes their preflop tightness, postflop aggression, and bluff frequency:

| Name  | Style       | Aggression | Bluff Rate | Tightness |
|-------|-------------|-----------|------------|-----------|
| Alice | Balanced    | 65%       | 12%        | 55%       |
| Bob   | Aggressive  | 80%       | 20%        | 40%       |
| Carol | Conservative| 50%       | 8%         | 70%       |

**Strategy engine:**
1. **Hand equity** — Monte Carlo simulation against random opponent ranges (300 iterations per decision)
2. **Pot odds** — folds when equity doesn't justify the call
3. **Position** — late position adds an aggression bonus
4. **Bet sizing** — raises are sized 0.5x–2x pot, scaled by equity and personality
5. **Probabilistic noise** — Gaussian noise on equity estimates prevents perfectly predictable play

---

## Project Structure

```
poker/
├── pyproject.toml
└── src/
    └── poker/
        ├── __init__.py
        ├── main.py          Entry point
        ├── cards.py         Card, Deck, unicode display
        ├── evaluator.py     Hand ranking, Monte Carlo equity, pot odds
        ├── player.py        Player & AIPlayer classes
        ├── game.py          Game engine, betting loop, menus
        ├── display.py       ANSI color terminal helpers
        └── save_load.py     JSON save/load (~/.poker_save.json)
```

---

## Save File

Progress is stored at `~/.poker_save.json`. It is written automatically after every hand. To start fresh, choose **New Game** from the main menu (you'll be asked to confirm before overwriting).

---

## License

MIT License — see [LICENSE](LICENSE).
