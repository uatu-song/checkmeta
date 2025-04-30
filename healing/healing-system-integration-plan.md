# Healing-Stamina System Integration Implementation Plan

## Overview

This implementation plan outlines the approach for integrating the Healing Mechanics system with the newly developed Stamina System in the META Fantasy League Simulator v5.0. This integration will create a powerful synergy between injuries, healing, and stamina management.

## Integration Components

### 1. Healing-Stamina Relationship

The integration will focus on four key aspects:

- **Stamina Cost for Healing**: Healing attempts will consume stamina based on the severity of injuries and healer traits
- **Stamina-Based Success Rates**: A healer's current stamina level will affect their healing success chances
- **Recovery Modifications**: Healing activities will affect stamina recovery rates for both healers and patients
- **Passive Healing Effects**: Characters with healing abilities will have specialized overnight stamina and injury recovery

### 2. HealingStaminaIntegrator

The core of this integration is the `HealingStaminaIntegrator` class that:

- Interfaces between the Healing Mechanics and Stamina System
- Calculates appropriate stamina costs for healing attempts
- Modifies healing success chances based on stamina levels
- Applies post-healing stamina effects
- Handles overnight recovery for healers and patients

## Implementation Steps

### Phase 1: Core Integration (3 days)

1. Create `HealingStaminaIntegrator` class extending `SystemBase`
2. Modify `healing_mechanics.attempt_healing()` method to be stamina-aware
3. Implement stamina cost calculations based on injury severity
4. Add success chance modifiers based on healer stamina levels

### Phase 2: Recovery Effects (2 days)

1. Implement post-healing stamina effects
2. Create overnight recovery simulation
3. Add passive healing abilities for certain traits
4. Integrate with existing stamina recovery mechanics

### Phase 3: Configuration & Validation (2 days)

1. Add healing section to stamina integration configuration
2. Update schema validator to include healing schemas
3. Implement configuration validation
4. Create default configuration with balanced values

### Phase 4: Testing & Documentation (3 days)

1. Develop integration tests for healing-stamina interactions
2. Test against various injury and stamina scenarios
3. Document integration points and parameters
4. Create usage examples and visualizations

## Key Features

### Stamina Cost Calculation

Healing stamina costs will be calculated based on:

- Base healing cost (configurable, default: 15 stamina points)
- Injury severity multipliers (1.0x for minor injuries, up to 3.0x for severe)
- Healing trait modifiers (regeneration costs more than basic healing)
- Willpower attribute modifier (higher WIL reduces costs)
- Self-healing penalty (healing oneself costs more)

### Success Chance Modifiers

Healing success chances will be modified by:

- Current stamina level thresholds (full effectiveness above 60%, reduced below)
- Different effectiveness levels for minor, moderate, and severe fatigue
- Trait-specific bonuses (regeneration has better chances)
- Willpower and resilience attribute modifiers

### Recovery Effects

The system will apply specialized recovery effects:

- Healers will recover stamina more slowly after performing healing
- Patients will receive a small stamina boost when successfully healed
- Characters with regeneration trait will apply passive healing overnight
- Recovery rates will be configurable through integration settings

## Configuration Parameters

The integration will use the following configuration structure:

```json
{
  "healing": {
    "costs": {
      "base_healing_cost": 15.0,
      "severity_multipliers": {
        "MINOR": 1.0,
        "MODERATE": 1.5,
        "MAJOR": 2.0,
        "SEVERE": 3.0
      }
    },
    "thresholds": {
      "effectiveness": {
        "60": 0.8,
        "40": 0.6,
        "20": 0.4
      }
    },
    "recovery_rates": {
      "healer_penalty": 0.5,
      "patient_bonus": 0.2,
      "self_healing_penalty": 0.3
    },
    "bonus_modifiers": {
      "willpower": 0.2,
      "regeneration_trait": 0.3,
      "healing_trait": 0.2,
      "rapid_healing_trait": 0.25
    }
  }
}
```

## Strategic Impact

This integration will create meaningful strategic decisions around:

1. **Resource Management**: When to use valuable stamina for healing vs. combat
2. **Healer Protection**: Keeping healers at high stamina levels for optimal effectiveness
3. **Recovery Planning**: Balancing immediate healing needs vs. overnight recovery
4. **Character Specialization**: Building team compositions with complementary stamina and healing capabilities

## Integration with Existing Systems

The healing-stamina integration will connect with:

- **Injury System**: For injury severity assessment and recovery tracking
- **Trait System**: For iden