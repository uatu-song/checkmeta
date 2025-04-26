# META Fantasy League Simulator

A simulation system for superhero team battles using chess as the underlying mechanic.

## Overview

The META Fantasy League Simulator is a comprehensive system for simulating battles between superhero teams. It uses chess as the underlying mechanic, with each character's abilities, traits, and stats influencing how they perform in battle.

## Key Features

- **Role-Based Chess Openings**: Characters use different chess openings based on their role (Field Leader, Vanguard, etc.)
- **Trait System**: Characters have special traits that provide bonuses in specific situations
- **Team Synergy**: Teams develop synergy over time, providing bonuses to all members
- **Leadership Effects**: Field Leaders provide team-wide bonuses based on their Leadership stat
- **Morale System**: Character morale affects performance and changes based on battle outcomes
- **Convergence Mechanics**: When pieces from different boards occupy the same space, characters battle directly
- **Progressive Growth**: Characters gain XP and improve over time

## Modular Architecture

The simulator has been designed with a modular architecture for easy maintenance and extension:

```
meta_simulator/
├── __init__.py
├── main.py                  # Entry point
├── config/                  # Configuration files
├── models/                  # Data models
├── systems/                 # Core game systems
├── simulation/              # Simulation logic
├── data/                    # Data loading/saving
└── utils/                   # Utility functions
```

## Getting Started

1. Ensure you have Python 3.6+ installed
2. Install required packages: `pip install -r requirements.txt`
3. Install Stockfish chess engine (optional but recommended)
4. Prepare a lineup Excel file with your teams
5. Run the simulator: `python -m meta_simulator.main --lineup-file lineups.xlsx --day 1`

## Lineup File Format

The simulator accepts Excel files with the following columns:
- Team ID/Team: Team identifier
- Name/Nexus Being: Character name
- Position/Role: Character role (FL, VG, EN, RG, GO, PO, SV)
- Primary Type: Character type (tech, energy, cosmic, mutant, bio, mystic, skill)
- Traits: Custom traits (comma-separated)
- Various attribute columns for stats

## Detailed Systems

### Traits

Characters can have up to 3 traits that provide special abilities:
- **Genius Intellect**: Bonus to combat rolls in convergences
- **Power Armor**: Reduces damage taken
- **Tactical Mastery**: Improves team coordination
- **Vibranium Shield**: Strong defense in convergences
- **Enhanced Agility**: Improved positioning and evasion
- **Spider Sense**: Anticipates and avoids danger
- **Polymorphic Body**: Adaptable positioning
- **Rapid Healing**: Regenerates HP over time
- **Extraordinary Luck**: Chance to reroll poor combat results
- **Telekinesis**: Bonus to board control
- And many more...

Traits can be assigned based on high attribute values or manually specified in the lineup file.

### Team Synergy

Teams develop synergy based on:
- Average team morale
- Number of games played together
- Leadership quality

Team affiliations (Avengers, X-Men, etc.) provide additional bonuses and special abilities that reflect their unique dynamics.

### Morale System

Character morale (0-100) affects:
- Attribute bonuses
- Stamina regeneration
- Combat bonuses
- Damage reduction
- Healing effectiveness

Morale changes based on match results, teammate performance, and leadership.

## Extending the Simulator

The modular design makes it easy to extend functionality:
- Add new traits in `systems/traits.py`
- Create new team affiliations in `systems/synergy.py`
- Modify chess mechanics in `systems/chess_engine.py`
- Add new character stats in `models/character.py`

## License

This project is open source and available under the MIT License.