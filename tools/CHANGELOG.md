# 📝 CHANGELOG — Metachess Zero

All significant updates to the tactical simulation engine.

---

## [v1.0.0] — Matchday Sim Kernel

- ✅ Added matchday simulation with 5 pairwise matches
- ✅ Implemented match loop with up to 50 turns per board
- ✅ Integrated Stockfish-based move selection
- ✅ Generated per-match result logs with rStats and move logs

## [v1.1.0] — Depth System

- 🧠 Added tactical depth calculation using aStats (FS, INT, AM, etc.)
- 🧮 Scaled Stockfish move range (top N) by depth
- 📝 Logged per-unit depth and move selection

## [v1.2.0] — Lineup + Attribute Pipeline

- 🧾 Created lineup extractor from Excel sheets
- 💾 Injected `aStats` from attribute_stats_full.json per NBID
- 📂 Exported lineups per team and per date

## [v1.3.0] — Convergence System

- ⚔ Enabled tile-time convergence evaluation
- 🧠 MOTo and AST awarded based on successful stack captures
- 🌀 Introduced cross-board convergence model

## [v1.4.0] — Logging & Visibility

- 📤 Match logs include moves, FEN per turn, final result
- 🔁 Console output shows per-turn progression
- 📊 Results folder auto-populated with one file per match

## [v1.5.0] — Trait System Integration (in progress)

- 🧬 Folded in EventBus and TraitEngine core modules
- 🗂 Traits react to events like 'on_turn_start', 'on_convergence'
- 🌟 Traits influence stats, narrative triggers, and move logic

## [v1.6.0] — Documentation & Cleanup

- 🧾 Generated README.md and LLM_Handbook.md
- 📚 Added match_result.schema.json for structured result validation
- 🔧 Cleaned script interface and runner structure

---

Want to extend? Fork it. Patch it. Rewrite the field.
