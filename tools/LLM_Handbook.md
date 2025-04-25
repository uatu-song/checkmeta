# LLM Handbook: Lessons from Building Metachess Zero

## 🧠 Overview

Metachess Zero is more than a simulation — it's a tactical-narrative engine with spatial metaphors, modular behavior, and character expression through convergence. These are the key takeaways and system design principles we discovered.

---

## 🔁 Simulation Pitfalls (and Fixes)

### ❌ Problem: Scripts would run silently
✅ Fix: Added explicit `__main__` blocks and per-turn `print()` logs

### ❌ Problem: Only one move pushed per turn
✅ Fix: Adjusted to simulate multiple moves and push key ones (FL, high-depth, etc.)

### ❌ Problem: No resolution even after 50 turns
✅ Fix: Planned material effect simulation and trait-driven disruption to unlock stalemates

---

## 📊 Design Learnings

### Tactical Depth
- Derived from aStats (`FS`, `INT`, `AM`, etc.)
- Controls how many Stockfish options a character evaluates
- Affects risk tolerance and decision variance

### Trait Architecture
- Traits should be decoupled using an EventBus (`on_turn_start`, `on_convergence`)
- TraitEngine listens to events and applies effects to units, stats, morale, etc.

### Convergence as Trigger
- Characters interact not based on board-only logic, but **tile-time convergence**
- Stacked events across boards create meaning and motif resonance

---

## 🔄 Automation Strategy

- Lineups are parsed from Excel sheets by day
- Matchdays automatically assign teams into 5 pairs
- Each match runs for up to 50 turns or until PGN resolves
- Output JSONs log final FEN, all moves, stats, and character state

---

## 🔥 Performance & Efficiency

- Stockfish-based move selection runs ~6s per full turn (16 units)
- Each match averages ~1.5–2 mins for 30+ turns
- System handles batch matchdays with minimal overhead

---

## 📘 Narrative Integration (Planned)

- rStats → Sally Floyd engine for post-match stories
- Trait activation logs used for reflection
- Synergy and ULT triggers will seed rivalries and epilogues

---

## ✅ Design Philosophy

- Every mechanic should reinforce **metaphor** and **narrative arc**
- Efficiency is nothing without expressiveness
- Characters act in context, not isolation

