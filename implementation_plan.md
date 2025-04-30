# Meta Simulator rStats Integration Plan

## Overview

This implementation plan outlines how to properly integrate the new convergence event emission system with the rStats tracking framework in the Meta Simulator.

## Components Created

1. **Convergence System Event Emitter Patch**
   - Enhances the process_convergences method to emit key events:
     - `convergence_triggered`: When a character initiates a convergence
     - `assist_given`: When a character assists another character
   - Adds detailed event metadata for stat tracking

2. **Event System Implementation**
   - Complete pub/sub system for event management
   - Support for event filtering and logging
   - Special handling for rStats-related events
   - Persistence mechanism for event statistics

3. **rStats System Constants**
   - Comprehensive definition of all trackable stats
   - Categorization for UI representation
   - Default values for initialization
   - Event-to-stat mapping for automated tracking

## Implementation Steps

### 1. Core System Files Integration

1. Add the Event System to System Registry initialization:
```python
# In _initialize_subsystems() method
from event_system import EventSystem
event_system = EventSystem(self.config)
self.registry.register("event_system", event_system)
self.logger.info("Event system initialized")
```

2. Update the enhanced_stats_system.py to subscribe to events:
```python
# In EnhancedStatTracker.__init__() method
event_system = self.registry.get("event_system")
if event_system:
    event_system.register_handler("convergence_triggered", self._handle_convergence_event)
    event_system.register_handler("assist_given", self._handle_assist_event)
```

3. Add event handlers to EnhancedStatTracker:
```python
def _handle_convergence_event(self, event_data):
    """Process convergence events for stat tracking"""
    character = event_data.get("character")
    if not character:
        return
        
    # Update convergence initiated stat
    self.update_character_stat(character, "CONVERGENCES_INITIATED", 1, "add")
    
    # Update team stat
    team_id = character.get("team_id")
    if team_id:
        self.update_team_stat(team_id, "CONVERGENCES", 1, "add")
        
def _handle_assist_event(self, event_data):
    """Process assist events for stat tracking"""
    character = event_data.get("character")
    if not character:
        return
        
    # Update assist stat
    self.update_character_stat(character, "ASSISTS", 1, "add")
```

### 2. Modify Existing Systems

1. Update convergence_system.py to include the patched process_convergences method
2. Add the EVENT_TO_STAT_MAP to the stat_tracker.py file
3. Ensure proper imports in all affected files

### 3. Feature Flags 

Add the following to configuration management:

```json
{
  "features": {
    "event_system_enabled": true,
    "event_detailed_logging": true,
    "rstats_tracking": true
  }
}
```

### 4. Testing Plan

1. **Unit Tests**:
   - Test event emission from convergence system
   - Verify event handlers are called correctly
   - Validate stat updates occur properly

2. **Integration Tests**:
   - Run a full match simulation
   - Verify convergence events are emitted
   - Check that character and team stats are updated correctly
   - Validate persistence of stats between simulator runs

3. **Performance Tests**:
   - Measure event system overhead
   - Ensure minimal impact on simulation speed

## Expected Outcomes

1. Character and team convergence statistics will be automatically tracked
2. Support roles will gain XP from assist actions
3. The system will have improved visibility into teamwork-driven gameplay
4. Reports will be enhanced with convergence and assist statistics

## Next Steps

After implementing this system:

1. Similar event emission for trait activations
2. UI enhancements to display convergence and assist statistics
3. Integration with narrative generation system for match reports

---

This plan completes the convergence event emission system and provides the foundation for continuing development of the rStats tracking framework, bringing us closer to finalization of the live event wiring phase.
