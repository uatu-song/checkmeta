# CHANGELOG

## v4.2.1 - 2025-04-28

### CRITICAL FIXES

- **PGN Generation**: Fixed a critical compatibility issue where v4.2.0 was only producing aggregated match PGNs instead of individual board PGNs, breaking downstream analysis tools.

### Backward Compatibility

- Added `per_board_pgn` configuration option (default: `true`) to restore the original behavior of generating individual PGN files for each chess board
- Implemented proper validation to ensure at least one PGN format is always enabled
- Maintains backward compatibility with existing analysis pipelines
- Added extensive documentation about PGN generation options

### New Features

- **Stamina System**: Implemented a comprehensive stamina tracking system that:
  - Tracks character stamina across matches with persistent storage
  - Applies stamina decay during matches based on activity
  - Provides recovery between matches and days
  - Implements performance penalties for low stamina (increased damage taken)
  - Integrates with the injury system to trigger injuries at low stamina thresholds

- **Combat Calibration**: Implemented enhanced combat balance parameters:
  - Increased base damage by 25% to make moves more meaningful
  - Increased stamina decay per round by 15% for greater fatigue effects
  - Doubled convergence damage for more decisive board collapses
  - Added extra damage taken (20%) for characters with low stamina
  - Enabled morale collapse chance when morale drops below 30%
  - Set injury trigger threshold at stamina below 35%

- **Enhanced Configuration System**: Improved configuration management with:
  - Dot-notation access to nested configuration values
  - Robust default values with fallbacks
  - Configuration validation and auto-correction
  - Automated backup functionality

### Documentation

- Added explicit documentation about PGN generation modes in README.md
- Added warnings about potential compatibility issues
- Updated file naming conventions documentation
- Added comprehensive implementation guide for developers

### Technical Improvements

- Enhanced error handling and validation throughout all systems
- Improved logging for better diagnostics and monitoring
- Added comprehensive test suite for new functionality
- Updated dependency checking and validation in the Gatekeeper system

## v4.2.0 - 2025-04-14

[Previous version changelog entries...]