# META Fantasy League Simulator - Modular Architecture

This document describes the modular architecture of the META Fantasy League Simulator, which has been refactored for improved maintainability, flexibility, and fairness.

## Core Architecture

The simulator is organized into multiple modules, each with specific responsibilities:

### Core Simulator

- **meta_simulator.py**: The main simulation engine that coordinates all components and runs the simulation.

### System Modules

1. **systems/initiative_randomizer.py**: Handles randomization of team processing order to prevent first-mover advantage.
2. **systems/buffered_damage.py**: Buffers damage calculations before applying them to ensure fairness.
3. **systems/enhanced_field_leader.py**: Manages Field Leader enhancements and special traits.
4. **systems/loss_conditions.py**: Implements balanced team loss conditions.
5. **systems/convergence_balancer.py**: Ensures fair distribution of convergence targeting.
6. **systems/momentum_system.py**: Handles team momentum and comeback mechanics.

### Utility Modules

1. **utils/pgn_tracker.py**: Records and manages chess games in PGN format.
2. **utils/stat_tracker.py**: Handles tracking, validation, and processing of result statistics.
3. **utils/loaders.py**: Provides functions for loading lineups from various data sources.
4. **utils/match_helpers.py**: Contains utilities for creating and managing matchups.
5. **utils/parity_tester.py**: Tools for testing and validating simulation fairness.

## Directory Structure

```
meta_simulator/
├── meta_simulator.py         # Main simulation engine
├── systems/                  # Core system modules
│   ├── initiative_randomizer.py
│   ├── buffered_damage.py
│   ├── enhanced_field_leader.py
│   ├── loss_conditions.py
│   ├── convergence_balancer.py
│   └── momentum_system.py
├── utils/                    # Utility modules
│   ├── pgn_tracker.py
│   ├── stat_tracker.py
│   ├── loaders.py
│   ├── match_helpers.py
│   └── parity_tester.py
├── data/                     # Data files
│   ├── lineups/              # Team lineup files
│   ├── teams/                # Team metadata
│   └── traits/               # Trait definitions
└── results/                  # Generated output
    ├── pgn/                  # PGN game records
    ├── reports/              # Match reports
    ├── stats/                # Statistics exports
    └── parity_tests/         # Parity test results
```

## Key Improvements

This modular architecture introduces several key improvements over the original design:

1. **Fairness and Parity**:
   - Initiative randomization prevents first-mover advantage
   - Buffered damage calculation prevents processing order bias
   - Enhanced Field Leader resilience prevents overwhelming FL targeting
   - Comprehensive parity testing framework

2. **Better Separation of Concerns**:
   - Each module has a clear, focused responsibility
   - Systems are loosely coupled for easier testing and updating
   - Clean interfaces between components

3. **Improved Maintainability**:
   - Smaller, more focused code files
   - Clear dependency structure
   - Better error handling and fallback mechanisms

4. **Extended Functionality**:
   - Comeback mechanics via the momentum system
   - More sophisticated Field Leader substitution handling
   - Balanced loss conditions with multiple factors
   - Comprehensive statistics tracking and analysis

## Usage Examples

### Basic Simulation

```python
from meta_simulator import MetaLeagueSimulator
from utils.loaders import load_lineups_from_excel

# Initialize simulator
simulator = MetaLeagueSimulator()

# Load teams from Excel
teams = load_lineups_from_excel("data/lineups/All Lineups 1.xlsx")

# Get teams by ID
team_a = teams["tT001"]  # Xavier's School
team_b = teams["tT002"]  # Brotherhood

# Run a simulation
match_result = simulator.simulate_match(team_a, team_b)

# Show results
print(f"Match Winner: {match_result['winning_team']}")
print(f"Score: {match_result['team_a_wins']} - {match_result['team_b_wins']}")
```

### Running a Full Matchday

```python
from meta_simulator import MetaLeagueSimulator

# Initialize simulator
simulator = MetaLeagueSimulator()

# Run all matches for a specific day
results = simulator.run_matchday(
    day_number=3,
    lineup_file="data/lineups/All Lineups 1.xlsx",
    show_details=True
)

# Results contain all match outcomes
print(f"Completed {len(results)} matches for day 3")
```

### Testing Parity

```python
from meta_simulator import MetaLeagueSimulator
from utils.parity_tester import ParityTester
from utils.loaders import load_lineups_from_excel

# Initialize simulator and tester
simulator = MetaLeagueSimulator()
tester = ParityTester(simulator)

# Load teams
teams = load_lineups_from_excel("data/lineups/All Lineups 1.xlsx")
team_a = teams["tT001"]
team_b = teams["tT002"]

# Run mirrored tests
results = tester.run_mirrored_tests(team_a, team_b, iterations=10)

# Show results
print(f"Team A win rate: {results['team_a_win_rate']:.1f}%")
print(f"Team B win rate: {results['team_b_win_rate']:.1f}%")
print(f"Position advantage: {results['position_advantage_pct']:.1f}%")
```

## Implementation Notes

- The modular design allows for incremental testing of each system.
- Components can be modified or replaced individually without affecting the entire system.
- The parity testing framework should be used to validate any changes to game mechanics.
- Default parameter values are designed for balanced gameplay, but can be tuned as needed.

## Future Enhancements

Potential areas for further enhancement:

1. Web interface for simulation visualization
2. Multi-threaded simulation for parallel processing
3. Machine learning-based balance optimization
4. Interactive mode for partial human control
5. Extended narrative generation for match stories