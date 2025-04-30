# META Simulator v5.1.0 - Integration Guide

This guide outlines how the newly implemented Guardian-compliant systems work together to create the complete META Simulator experience. Use this as a reference for understanding the system architecture and integration points.

## System Architecture Overview

The META Simulator follows a modular architecture with these key components:

1. **Core Infrastructure**:
   - `system_base.py` - Base class for all systems
   - `system_registry.py` - System registration and dependency management
   - `config_manager.py` - Configuration management

2. **Simulation Core**:
   - `simulate_day.py` - Main simulation orchestration
   - `chess_system.py` - Chess game mechanics
   - `match_simulator.py` - Individual match simulation

3. **Game Mechanics**:
   - `convergence_system.py` - Character interactions ✅
   - `combat_calibration.py` - Damage and modifiers ✅
   - `end_of_round_effects.py` - State progression ✅

4. **Narrative Elements**:
   - `motif_detection_system.py` - Chess pattern identification ✅
   - `trait_system.py` - Character abilities
   - `pgn_tracker.py` - Game recording

5. **Support Systems**:
   - `event_system.py` - Event emission and handling
   - `validation_system.py` - Configuration validation
   - `error_handling.py` - Error management
   - `logging_setup.py` - Logging configuration

## Event Flow Architecture

The system uses an event-driven architecture to connect components:

```
┌────────────────┐     ┌───────────────┐     ┌────────────────┐
│ Day Simulation │────>│ Event System  │<────│ Validation     │
└────┬─────┬─────┘     └───────┬───────┘     └────────────────┘
     │     │                   │
     │     │                   │             ┌────────────────┐
     │     │                   └────────────>│ Error Handler  │
     │     │                                 └────────────────┘
     │     │
     │     │             ┌───────────────┐   ┌────────────────┐
     │     └────────────>│ Match         │──>│ PGN Tracker    │
     │                   │ Simulator     │   └────────────────┘
     │                   └───┬───────┬───┘
     │                       │       │       ┌────────────────┐
     │                       │       └──────>│ Motif Detection│
     │                       │               └────────────────┘
     │                       │
     │                       │       ┌───────────────┐
     └───────────────────────┼──────>│ Combat System │
                             │       └───────────────┘
                             │
                             │       ┌───────────────┐
                             └──────>│ Convergence   │
                                     │ System        │
                                     └───┬───────────┘
                                         │
                                         │       ┌───────────────┐
                                         └──────>│ End-of-Round  │
                                                 │ Effects       │
                                                 └───────────────┘
```

## Integration of Guardian-Compliant Systems

### 1. Convergence System

**Purpose**: Handles character-to-character interactions via chess boards

**Integration Points**:
- Receives characters and boards from `match_simulator`
- Emits events via `event_system`
- Updates character stats in-place
- Inputs into the `combat_system` for damage resolution

**Key Events**:
- `convergence_triggered`
- `assist_given`

### 2. Combat Calibration System

**Purpose**: Manages damage calculations and combat modifiers

**Integration Points**:
- Receives data from `convergence_system` for damage application
- Uses `trait_system` for trait-based modifiers
- Updates character stats and HP
- Tracks combat statistics for reporting

**Key Events**:
- `damage_dealt`
- `injury_taken`
- `combat_modifier_applied`

### 3. End-of-Round Effects System

**Purpose**: Processes all effects that occur at the end of each round

**Integration Points**:
- Called by `match_simulator` at the end of each round
- Integrates with multiple subsystems (stamina, traits, morale)
- Updates character states
- Triggers XP awards and status effects

**Key Events**:
- `stamina_updated`
- `trait_ready`
- `morale_updated`
- `status_effect_expired`
- `xp_awarded`

### 4. Motif Detection System

**Purpose**: Identifies chess patterns and themes for narrative generation

**Integration Points**:
- Called by `match_simulator` or `pgn_tracker` after games
- Analyzes PGNs and board positions
- Updates rStats with detected motifs
- Provides data for narrative generation

**Key Events**:
- `motif_detected`
- `motifs_detected`
- `match_motif_detection_complete`

## Data Flow Example

Here's how a typical match simulation flows through the system:

1. `simulate_day.py` orchestrates the overall simulation
2. `match_simulator` handles individual matches
3. Character moves generate board positions
4. `convergence_system` processes character interactions
5. `combat_system` resolves damage and modifiers
6. `end_of_round_effects` applies state changes after each round
7. `pgn_tracker` records the games
8. `motif_detection_system` analyzes completed games
9. Events flow to the `event_system` throughout the process
10. `rStats` are updated based on events

## Configuration Integration

Each Guardian-compliant system loads configuration from a central configuration manager. Key configuration sections include:

- `combat_calibration` - Combat parameters
- `motif_detection` - Motif patterns and thresholds
- `stamina_settings` - Stamina decay and recovery
- `trait_settings` - Trait mechanics and cooldowns
- `xp_settings` - Experience point awards
- `status_effects` - Status effect handling

## Error Handling Integration

The systems implement consistent error handling:

1. Each method has a try/except block
2. Errors are logged with context
3. Error events are emitted via `event_system`
4. Graceful fallbacks are provided
5. System continues operation where possible

## Using the Systems Together

To use these systems in a simulation:

```python
# Initialize the systems
registry = SystemRegistry()
config = ConfigurationManager("config.json")

# Create core systems
convergence_system = ConvergenceSystem(config, registry)
combat_system = CombatCalibrationSystem(config, registry)
end_of_round_system = EndOfRoundEffectsSystem(config, registry)
motif_detection = MotifDetectionSystem(config, registry)

# Register in the registry
registry.register("convergence_system", convergence_system)
registry.register("combat_system", combat_system)
registry.register("end_of_round_effects", end_of_round_system)
registry.register("motif_detection", motif_detection)

# Activate all systems
registry.activate_all()

# Execute a match simulation
day_simulator = DaySimulationSystem(config, registry)
result = day_simulator.simulate_day(1)
```

## rStats Integration

Each system contributes to rStats tracking:

1. **Convergence System**:
   - `CONVERGENCES_INITIATED`
   - `CONVERGENCES_RECEIVED`
   - `ASSISTS`

2. **Combat System**:
   - `DAMAGE_DEALT`
   - `DAMAGE_TAKEN`
   - `INJURIES_SUSTAINED`

3. **End-of-Round System**:
   - `ROUNDS_SURVIVED`
   - `STAMINA_DEPLETED`
   - `MORALE_COLLAPSED`
   - `XP_EARNED`

4. **Motif Detection System**:
   - `MOTIFS_DETECTED`
   - Category-specific stats (e.g., `TACTICAL_MOTIFS`)

## Summary

With these four Guardian-compliant systems integrated into the META Simulator, you now have a complete, event-driven simulation engine that:

1. Simulates chess-based character interactions
2. Processes combat with calibrated parameters
3. Manages state progression with realistic effects
4. Identifies narrative elements for storytelling
5. Tracks comprehensive statistics for reporting

This foundation provides everything needed for the v5.1.0 rStats-ready edition, allowing you to run simulations that generate both gameplay results and rich narrative fodder.
