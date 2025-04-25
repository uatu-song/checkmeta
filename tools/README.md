# Metachess Zero

Welcome to **Metachess Zero**, a modular narrative-tactical simulation engine for running multi-board, character-driven, convergence-based chess encounters.

## 💡 What It Does

- Simulates 8-board synchronous matchdays across 10 teams
- Processes real characters with trait-driven behavior
- Uses Stockfish to evaluate moves based on tactical depth
- Tracks stats (`rStats`) like assists, takedowns, synergies, mindbreaks
- Resolves matches turn-by-turn with PGN board state
- Supports narrative trait systems and convergence motifs

## 🔧 Features

- ✅ Full attribute injection from `attribute_stats_full.json`
- ✅ Role profiles influence move selection logic
- ✅ Tactical depth system modifies decision options
- ✅ Convergence system tracks tile-time overlaps
- ✅ PGN purge protocol removes completed boards
- ✅ Match logging per team and per matchup

## 📂 Project Structure

```
metachess_zero/
├── core/                  # Simulation and trait logic
├── tools/                 # Lineup extraction and utility scripts
├── data/lineups/          # JSON lineups generated from Excel
├── results/               # Per-match outputs after simulation
├── attribute_stats_full.json
├── main.py
```

## 🚀 Running a Matchday

```bash
python3 matchday_runner_full_pgntier_verbose.py
```

Runs 5 full matches using Stockfish, traits, depth, and convergence logic.

## 📈 Output

Each match logs a full JSON:
- Moves per turn
- PGN FEN state
- Unit rStats and depth
- Tactical motifs and convergence triggers

## 🧠 Contributions

This engine is modular. Traits, missions, motif maps, and narrative output are pluggable.

