"""
META Fantasy League Simulator - Stamina System
==============================================

A comprehensive stamina management system for tracking character stamina throughout matches
and across seasons, with proper integration into the META League Simulator architecture.

This module follows the Math Formulas Bible for all calculations and implements the
guardrail requirements for patch-driven configuration.
"""

import os
import json
import logging
import datetime
from typing import Dict, List, Any, Optional, Tuple, Union, Set
from collections import defaultdict

# Import system base classes
from system_base import SystemBase

class StaminaSystem(SystemBase):
    """Manages character stamina throughout matches and across seasons"""
    
    def __init__(self, config, registry):
        """Initialize the stamina system"""
        super().__init__("stamina_system", registry, config)
        self.logger = logging.getLogger("StaminaSystem")
        self.stamina_config = {}
        self.stamina_logs = {}
        self.persistent_stamina = {}
    
    def _activate_implementation(self):
        """Implementation-specific activation logic"""
        self.logger.info("Activating stamina system")
        self.load_stamina_config()
        self.load_persistent_data()
    
    def load_stamina_config(self):
        """Loads stamina configuration from patch file"""
        config_path = self.config.get("paths.stamina_config", "config/stamina_config_v1.json")
        
        # Make sure the config directory exists
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    self.stamina_config = json.load(f)
                    self.logger.info(f"Loaded stamina configuration from {config_path}")
            else:
                # Load default configuration
                self.stamina_config = self._get_default_config()
                
                # Save default configuration
                with open(config_path, 'w') as f:
                    json.dump(self.stamina_config, indent=2, fp=f)
                    self.logger.info(f"Created default stamina configuration at {config_path}")
        except Exception as e:
            self.logger.error(f"Error loading stamina configuration: {e}")
            # Fall back to default configuration
            self.stamina_config = self._get_default_config()
    
    def _get_default_config(self):
        """Get default stamina configuration according to Math Formulas Bible"""
        return {
            "version": "1.0.0",
            "base_stamina": 100,
            "base_decay": 2.0,
            "decay_multiplier": 1.15,
            "base_recovery": 5.0,
            "recovery_multiplier": 1.0,
            "overnight_recovery_percent": 70,
            "thresholds": {
                "60": [
                    {
                        "id": "minor_fatigue",
                        "effect": "accuracy_penalty",
                        "value": 0.05
                    }
                ],
                "40": [
                    {
                        "id": "moderate_fatigue",
                        "effect": "damage_penalty",
                        "value": 0.10
                    },
                    {
                        "id": "trait_restriction",
                        "effect": "trait_chance_penalty",
                        "value": 0.25
                    }
                ],
                "20": [
                    {
                        "id": "severe_fatigue",
                        "effect": "damage_penalty",
                        "value": 0.20
                    },
                    {
                        "id": "trait_lockout",
                        "effect": "high_cost_trait_lockout",
                        "value": 1.0
                    },
                    {
                        "id": "resignation_risk",
                        "effect": "resignation_chance",
                        "value": 0.05
                    }
                ]
            },
            "action_costs": {
                "standard_move": 1.0,
                "trait_activation": 2.0,
                "convergence_assist": 3.0,
                "convergence_target": 5.0
            },
            "trait_cost_multipliers": {
                "low": 0.5,
                "medium": 1.0,
                "high": 2.0,
                "extreme": 3.0
            }
        }
    
    def load_persistent_data(self):
        """Load persistent stamina data from storage"""
        data_path = self.config.get("paths.stamina_data", "data/stamina_data.json")
        
        # Make sure the data directory exists
        os.makedirs(os.path.dirname(data_path), exist_ok=True)
        
        try:
            if os.path.exists(data_path):
                with open(data_path, 'r') as f:
                    self.persistent_stamina = json.load(f)
                    self.logger.info(f"Loaded persistent stamina data from {data_path}")
        except Exception as e:
            self.logger.error(f"Error loading persistent stamina data: {e}")
            # Initialize empty data structure if loading fails
            self.persistent_stamina = {}
    
    def save_persistent_data(self):
        """Save persistent stamina data to storage"""
        data_path = self.config.get("paths.stamina_data", "data/stamina_data.json")
        
        # Make sure the data directory exists
        os.makedirs(os.path.dirname(data_path), exist_ok=True)
        
        try:
            with open(data_path, 'w') as f:
                json.dump(self.persistent_stamina, indent=2, fp=f)
                self.logger.info(f"Saved persistent stamina data to {data_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error saving persistent stamina data: {e}")
            return False
    
    def export_state(self):
        """Export state for backup"""
        return {
            "stamina_config": self.stamina_config,
            "persistent_stamina": self.persistent_stamina
        }
    
    def initialize_character_stamina(self, character):
        """Sets initial stamina for a character based on attributes
        
        This is called at the start of a match to initialize stamina values.
        It uses persistent storage to maintain stamina between matches.
        """
        character_id = character.get("id", "unknown")
        
        # Check if character has persistent stamina data
        if character_id in self.persistent_stamina:
            # Use persistent stamina, but apply overnight recovery if needed
            last_match = self.persistent_stamina[character_id].get("last_match_date")
            current_time = datetime.datetime.now().isoformat()
            
            # If this is a new day, apply overnight recovery
            if last_match and self._is_new_day(last_match, current_time):
                persisted_stamina = self.persistent_stamina[character_id].get("stamina", 0)
                recovery_percent = self.stamina_config.get("overnight_recovery_percent", 70)
                
                # Apply overnight recovery formula
                max_stamina = self._calculate_max_stamina(character)
                recovery_amount = (max_stamina - persisted_stamina) * (recovery_percent / 100)
                new_stamina = min(persisted_stamina + recovery_amount, max_stamina)
                
                character["stamina"] = new_stamina
                self.logger.info(f"Applied overnight recovery for {character_id}: {persisted_stamina} -> {new_stamina}")
            else:
                # Use persisted stamina directly
                character["stamina"] = self.persistent_stamina[character_id].get("stamina", 0)
        else:
            # No persistent data, calculate from scratch
            character["stamina"] = self._calculate_max_stamina(character)
        
        # Initialize empty stamina log
        character["stamina_log"] = []
        
        # Initialize empty effects list if not present
        if "effects" not in character:
            character["effects"] = []
        
        return character["stamina"]
    
    def _calculate_max_stamina(self, character):
        """Calculate maximum stamina based on character attributes"""
        base_stamina = self.stamina_config.get("base_stamina", 100)
        modifier = 0
        
        # Apply attributes-based modifiers (DUR affects stamina capacity)
        if "aDUR" in character:
            modifier += (character["aDUR"] - 50) * 0.5
        
        return min(max(base_stamina + modifier, 50), 150)  # Clamp between 50 and 150
    
    def _is_new_day(self, last_match, current_time):
        """Check if this match is on a new day compared to the last match"""
        try:
            last_date = datetime.datetime.fromisoformat(last_match).date()
            current_date = datetime.datetime.fromisoformat(current_time).date()
            return current_date > last_date
        except:
            # If there's any error parsing dates, assume it's a new day
            return True
    
    def apply_stamina_cost(self, character, cost, reason, match_context):
        """Apply a stamina cost to a character and emit an event
        
        Args:
            character: The character to apply the cost to
            cost: The base stamina cost
            reason: The reason for the stamina cost
            match_context: The current match context
            
        Returns:
            The remaining stamina after the cost is applied
        """
        # Ensure character has stamina initialized
        if "stamina" not in character:
            self.initialize_character_stamina(character)
        
        # Calculate actual cost based on character attributes and reason
        actual_cost = self._calculate_actual_cost(character, cost, reason)
        
        # Apply the cost
        character["stamina"] = max(character["stamina"] - actual_cost, 0)
        
        # Log the stamina change
        log_entry = {
            "turn": match_context.get("round", 0),
            "cost": actual_cost,
            "reason": reason,
            "stamina_remaining": character["stamina"]
        }
        
        character["stamina_log"].append(log_entry)
        
        # Update match context with stamina log
        if "stamina_logs" not in match_context:
            match_context["stamina_logs"] = []
        
        match_context["stamina_logs"].append({
            "character_id": character.get("id", "unknown"),
            "character_name": character.get("name", "Unknown"),
            "team_id": character.get("team_id", "unknown"),
            "turn": match_context.get("round", 0),
            "cost": actual_cost,
            "reason": reason,
            "stamina_remaining": character["stamina"]
        })
        
        # Emit an event
        event_system = self.registry.get("event_system")
        if event_system:
            event_system.emit({
                "type": "stamina_drain",
                "character_id": character.get("id", "unknown"),
                "amount": actual_cost,
                "reason": reason,
                "remaining": character["stamina"],
                "match_id": match_context.get("match_id", "unknown"),
                "turn": match_context.get("round", 0)
            })
        
        # Check for effects based on stamina level
        self.apply_stamina_effects(character, match_context)
        
        return character["stamina"]
    
    def _calculate_actual_cost(self, character, base_cost, reason):
        """Calculate the actual stamina cost based on character attributes and reason"""
        # Get the action type from the reason
        action_type = reason.split(':')[0] if ':' in reason else reason
        
        # Get action cost multiplier
        action_costs = self.stamina_config.get("action_costs", {})
        action_multiplier = action_costs.get(action_type, 1.0)
        
        # Get trait cost multiplier if it's a trait activation
        trait_multiplier = 1.0
        if action_type == "trait_activation" and ':' in reason:
            trait_name = reason.split(':')[1]
            trait_system = self.registry.get("trait_system")
            if trait_system:
                trait_cost_category = trait_system.get_trait_cost_category(trait_name)
                trait_multipliers = self.stamina_config.get("trait_cost_multipliers", {})
                trait_multiplier = trait_multipliers.get(trait_cost_category, 1.0)
        
        # Calculate base cost with action and trait multipliers
        modified_cost = base_cost * action_multiplier * trait_multiplier
        
        # Apply character attribute modifiers (DUR reduces stamina costs)
        durability_factor = 1.0
        if "aDUR" in character:
            durability_factor = max(0.5, 1 - ((character["aDUR"] - 50) / 100))
        
        # Calculate final cost
        actual_cost = modified_cost * durability_factor
        
        # Round to one decimal place as per Math Formulas Bible
        return round(actual_cost, 1)
    
    def apply_stamina_recovery(self, character, match_context):
        """Apply stamina recovery at the end of a round
        
        Args:
            character: The character to apply recovery to
            match_context: The current match context
            
        Returns:
            The amount of stamina recovered
        """
        # Ensure character has stamina initialized
        if "stamina" not in character:
            self.initialize_character_stamina(character)
        
        # Calculate recovery amount
        base_recovery = self.stamina_config.get("base_recovery", 5.0)
        recovery_multiplier = self.stamina_config.get("recovery_multiplier", 1.0)
        
        # Apply character attribute modifiers (DUR increases recovery)
        durability_factor = 1.0
        if "aDUR" in character:
            durability_factor = 1.0 + ((character["aDUR"] - 50) / 100)
        
        recovery_amount = base_recovery * recovery_multiplier * durability_factor
        
        # Check for effects that might affect recovery
        if self._has_effect(character, "stamina:severe_fatigue"):
            recovery_amount *= 0.5  # Severe fatigue halves recovery
        
        # Round to one decimal place
        recovery_amount = round(recovery_amount, 1)
        
        # Apply recovery (can't exceed max stamina)
        max_stamina = self._calculate_max_stamina(character)
        old_stamina = character["stamina"]
        
        # Cap recovery at max stamina
        new_stamina = min(old_stamina + recovery_amount, max_stamina)
        actual_recovery = new_stamina - old_stamina
        
        character["stamina"] = new_stamina
        
        # Log the stamina recovery
        log_entry = {
            "turn": match_context.get("round", 0),
            "recovery": actual_recovery,
            "reason": "end_of_round_recovery",
            "stamina_remaining": character["stamina"]
        }
        
        character["stamina_log"].append(log_entry)
        
        # Update match context with stamina log
        if "stamina_logs" not in match_context:
            match_context["stamina_logs"] = []
        
        match_context["stamina_logs"].append({
            "character_id": character.get("id", "unknown"),
            "character_name": character.get("name", "Unknown"),
            "team_id": character.get("team_id", "unknown"),
            "turn": match_context.get("round", 0),
            "recovery": actual_recovery,
            "reason": "end_of_round_recovery",
            "stamina_remaining": character["stamina"]
        })
        
        # Emit an event
        event_system = self.registry.get("event_system")
        if event_system:
            event_system.emit({
                "type": "stamina_recovery",
                "character_id": character.get("id", "unknown"),
                "amount": actual_recovery,
                "reason": "end_of_round_recovery",
                "remaining": character["stamina"],
                "match_id": match_context.get("match_id", "unknown"),
                "turn": match_context.get("round", 0)
            })
        
        # Check for effects based on new stamina level
        self.apply_stamina_effects(character, match_context)
        
        return actual_recovery
    
    def apply_stamina_effects(self, character, match_context):
        """Apply effects based on current stamina level
        
        Args:
            character: The character to apply effects to
            match_context: The current match context
            
        Returns:
            List of active effect IDs
        """
        stamina = character.get("stamina", 0)
        effects = []
        
        # Ensure character has effects list
        if "effects" not in character:
            character["effects"] = []
            
        # Remove all existing stamina effects
        character["effects"] = [e for e in character["effects"] 
                               if not e.startswith("stamina:")]
        
        # Apply new effects based on thresholds (from lowest to highest)
        thresholds = self.stamina_config.get("thresholds", {})
        
        # Sort thresholds to process from lowest to highest
        sorted_thresholds = sorted(thresholds.items(), key=lambda x: int(x[0]))
        
        for threshold_key, threshold_effects in sorted_thresholds:
            threshold = int(threshold_key)
            if stamina <= threshold:
                for effect in threshold_effects:
                    effect_id = f"stamina:{effect['id']}"
                    
                    # Add effect to character
                    if effect_id not in character["effects"]:
                        character["effects"].append(effect_id)
                        
                        # Log the effect application
                        self._log_effect_application(character, effect, match_context)
                        
                    effects.append(effect_id)
        
        return effects
    
    def _log_effect_application(self, character, effect, match_context):
        """Log the application of a stamina effect"""
        # Update match context with effect log
        if "morale_logs" not in match_context:
            match_context["morale_logs"] = []
        
        match_context["morale_logs"].append({
            "character_id": character.get("id", "unknown"),
            "character_name": character.get("name", "Unknown"),
            "team_id": character.get("team_id", "unknown"),
            "turn": match_context.get("round", 0),
            "effect": effect["id"],
            "effect_type": effect["effect"],
            "value": effect["value"],
            "current_stamina": character.get("stamina", 0)
        })
        
        # Emit an event
        event_system = self.registry.get("event_system")
        if event_system:
            event_system.emit({
                "type": "stamina_effect",
                "character_id": character.get("id", "unknown"),
                "effect_id": effect["id"],
                "effect_type": effect["effect"],
                "value": effect["value"],
                "stamina": character.get("stamina", 0),
                "match_id": match_context.get("match_id", "unknown"),
                "turn": match_context.get("round", 0)
            })
    
    def _has_effect(self, character, effect_id):
        """Check if a character has a specific effect"""
        if "effects" not in character:
            return False
        return effect_id in character["effects"]
    
    def get_low_stamina_penalty(self, character):
        """Get the damage penalty multiplier for low stamina
        
        Based on Math Formulas Bible:
        DamageMultiplier = 1 + ((StaminaThreshold - CurrentStamina) / StaminaThreshold × PenaltyFactor)
        
        Returns:
            The damage multiplier (>1.0 means taking more damage)
        """
        stamina = character.get("stamina", 0)
        stamina_threshold = 30  # Default threshold
        penalty_factor = 0.2    # Default penalty factor (20%)
        
        # Only apply when below threshold
        if stamina >= stamina_threshold:
            return 1.0
        
        # Calculate penalty multiplier
        penalty = 1.0 + ((stamina_threshold - stamina) / stamina_threshold * penalty_factor)
        
        # Round to 2 decimal places
        return round(penalty, 2)
    
    def can_use_trait(self, character, trait_name, trait_cost):
        """Check if a character can use a trait based on their stamina
        
        Args:
            character: The character who wants to use the trait
            trait_name: The name of the trait
            trait_cost: The base stamina cost of the trait
            
        Returns:
            (bool, str): Whether the trait can be used and reason if not
        """
        # Ensure character has stamina initialized
        if "stamina" not in character:
            return False, "No stamina value initialized"
        
        stamina = character.get("stamina", 0)
        
        # Check for severe fatigue effect which locks high-cost traits
        if self._has_effect(character, "stamina:trait_lockout"):
            # Get trait cost category
            trait_system = self.registry.get("trait_system")
            if trait_system:
                trait_cost_category = trait_system.get_trait_cost_category(trait_name)
                # Lock high and extreme cost traits when severely fatigued
                if trait_cost_category in ["high", "extreme"]:
                    return False, "Severe fatigue prevents using high-cost traits"
        
        # Calculate actual trait cost
        actual_cost = self._calculate_actual_cost(
            character, 
            trait_cost, 
            f"trait_activation:{trait_name}"
        )
        
        # Check if character has enough stamina
        if stamina < actual_cost:
            return False, f"Insufficient stamina: {stamina} < {actual_cost}"
        
        return True, "Sufficient stamina"
    
    def calculate_trait_chance_modifier(self, character, base_chance):
        """Calculate modifier to trait activation chance based on stamina
        
        Args:
            character: The character using the trait
            base_chance: The base activation chance
            
        Returns:
            The modified activation chance
        """
        # No modifier if not using moderate fatigue effect
        if not self._has_effect(character, "stamina:trait_restriction"):
            return base_chance
        
        # Get penalty value from effect
        penalty = 0.25  # Default 25% reduction
        for effect in self.stamina_config.get("thresholds", {}).get("40", []):
            if effect["id"] == "trait_restriction":
                penalty = effect["value"]
                break
        
        # Apply penalty to base chance
        modified_chance = base_chance * (1.0 - penalty)
        
        # Ensure chance is still at least 10%
        return max(modified_chance, 0.1)
    
    def calculate_resignation_chance(self, character):
        """Calculate chance of resignation due to extreme fatigue
        
        Returns:
            Chance of resignation (0.0-1.0)
        """
        # No chance if not using severe fatigue effect
        if not self._has_effect(character, "stamina:resignation_risk"):
            return 0.0
        
        # Get base chance from effect
        base_chance = 0.05  # Default 5% chance per turn
        for effect in self.stamina_config.get("thresholds", {}).get("20", []):
            if effect["id"] == "resignation_risk":
                base_chance = effect["value"]
                break
        
        # Lower stamina increases resignation chance
        stamina = character.get("stamina", 0)
        stamina_factor = max(0, 20 - stamina) / 20.0
        
        # Apply willpower to reduce chance (if available)
        will_factor = 1.0
        if "aWIL" in character:
            will_factor = max(0.5, 1.0 - ((character["aWIL"] - 50) / 100))
        
        # Calculate final chance
        resignation_chance = base_chance * (1.0 + stamina_factor) * will_factor
        
        # Cap at 50% per turn maximum
        return min(resignation_chance, 0.5)
    
    def apply_end_of_round_effects(self, characters, match_context):
        """Apply stamina effects at the end of a round
        
        Args:
            characters: List of characters to process
            match_context: The current match context
        """
        for character in characters:
            # Skip knocked out characters
            if character.get("is_ko", False):
                continue
                
            # Apply base stamina decay
            self._apply_base_stamina_decay(character, match_context)
            
            # Apply stamina recovery
            self.apply_stamina_recovery(character, match_context)
    
    def _apply_base_stamina_decay(self, character, match_context):
        """Apply base stamina decay at the end of a round"""
        # Calculate decay amount from Math Formulas Bible:
        # StaminaLoss = BaseDecay × DecayMultiplier × (1 - (aDUR / 200))
        base_decay = self.stamina_config.get("base_decay", 2.0)
        decay_multiplier = self.stamina_config.get("decay_multiplier", 1.15)
        
        durability_factor = 1.0
        if "aDUR" in character:
            durability_factor = 1.0 - (character["aDUR"] / 200)
        
        decay_amount = base_decay * decay_multiplier * durability_factor
        
        # Round to one decimal place
        decay_amount = round(decay_amount, 1)
        
        # Apply the decay
        self.apply_stamina_cost(
            character,
            decay_amount,
            "end_of_round_decay",
            match_context
        )
    
    def process_match_end(self, character, match_result, match_context):
        """Process the end of a match for a character
        
        This persists stamina values for use in future matches.
        
        Args:
            character: The character to process
            match_result: The match result for this character
            match_context: The match context
        """
        character_id = character.get("id", "unknown")
        current_stamina = character.get("stamina", 0)
        
        # Store persistent stamina data
        self.persistent_stamina[character_id] = {
            "stamina": current_stamina,
            "last_match_date": datetime.datetime.now().isoformat(),
            "last_match_id": match_context.get("match_id", "unknown")
        }
        
        # Save persistent data
        self.save_persistent_data()
        
        # Log end of match
        self.logger.info(f"End of match for {character_id}: stamina={current_stamina}")
    
    def process_day_change(self, day_number):
        """Process a day change for all characters
        
        This applies overnight recovery to all characters.
        
        Args:
            day_number: The new day number
            
        Returns:
            Dict with recovery statistics
        """
        recovery_stats = {
            "day": day_number,
            "recovered": [],
            "total_characters": len(self.persistent_stamina)
        }
        
        # Apply overnight recovery to all characters
        recovery_percent = self.stamina_config.get("overnight_recovery_percent", 70)
        
        for character_id, data in self.persistent_stamina.items():
            old_stamina = data.get("stamina", 0)
            
            # Get character data to calculate max stamina
            # In a real implementation, we would retrieve character data from data_loader
            # For now, we'll estimate with a default max stamina
            max_stamina = 100
            
            # Apply overnight recovery formula
            recovery_amount = (max_stamina - old_stamina) * (recovery_percent / 100)
            new_stamina = min(old_stamina + recovery_amount, max_stamina)
            
            # Update persistent data
            self.persistent_stamina[character_id]["stamina"] = new_stamina
            
            # Add to recovery stats
            recovery_stats["recovered"].append({
                "character_id": character_id,
                "old_stamina": old_stamina,
                "new_stamina": new_stamina,
                "recovery_amount": new_stamina - old_stamina
            })
        
        # Save persistent data
        self.save_persistent_data()
        
        return recovery_stats
    
    def set_decay_multiplier(self, multiplier):
        """Set the stamina decay multiplier
        
        Used by combat calibration system to adjust game balance
        
        Args:
            multiplier: The new decay multiplier (1.0 = normal)
        """
        # Validate against Math Formulas Bible allowed range
        if 0.5 <= multiplier <= 2.0:
            self.stamina_config["decay_multiplier"] = multiplier
            self.logger.info(f"Stamina decay multiplier set to {multiplier}")
            return True
        else:
            self.logger.warning(f"Invalid stamina decay multiplier: {multiplier} (must be 0.5-2.0)")
            return False
    
    def set_low_stamina_damage_percent(self, percent):
        """Set the extra damage percent taken at low stamina
        
        Used by combat calibration system to adjust game balance
        
        Args:
            percent: The damage increase percentage (e.g., 20 = 20% more damage)
        """
        # Validate against Math Formulas Bible allowed range
        if 0 <= percent <= 50:
            # Update the effect in thresholds
            for threshold_key, effects in self.stamina_config["thresholds"].items():
                for effect in effects:
                    if effect["id"] == "moderate_fatigue" and effect["effect"] == "damage_penalty":
                        effect["value"] = percent / 100.0
                    elif effect["id"] == "severe_fatigue" and effect["effect"] == "damage_penalty":
                        effect["value"] = percent * 2 / 100.0
            
            self.logger.info(f"Low stamina damage percent set to {percent}%")
            return True
        else:
            self.logger.warning(f"Invalid low stamina damage percent: {percent}% (must be 0-50%)")
            return False

# Helper functions for unit testing
def test_stamina_system():
    """Run unit tests for the stamina system"""
    from unittest.mock import MagicMock
    
    # Mock config and registry
    config = {
        "paths": {
            "stamina_config": "tests/stamina_config_test.json",
            "stamina_data": "tests/stamina_data_test.json"
        }
    }
    
    registry = MagicMock()
    
    # Create stamina system
    stamina_system = StaminaSystem(config, registry)
    
    # Initialize config
    stamina_system.stamina_config = stamina_system._get_default_config()
    
    # Test character
    character = {
        "id": "test_char_1",
        "name": "Test Character",
        "team_id": "team_1",
        "aDUR": 60  # Above average durability
    }
    
    # Test match context
    match_context = {
        "match_id": "test_match_1",
        "round": 1
    }
    
    # Test initialization
    stamina = stamina_system.initialize_character_stamina(character)
    assert 100 < stamina <= 105, f"Initial stamina should be slightly above 100 due to DUR, got {stamina}"
    
    # Test stamina cost
    stamina_system.apply_stamina_cost(character, 10, "trait_activation:test_trait", match_context)
    assert character["stamina"] < stamina, "Stamina should decrease after cost"
    
    # Test effects
    character["stamina"] = 30  # Set to trigger moderate fatigue
    effects = stamina_system.apply_stamina_effects(character, match_context)
    assert len(effects) > 0, "Should have at least one effect at low stamina"
    assert character["effects"], "Character should have effects applied"
    
    # Test recovery
    old_stamina = character["stamina"]
    recovery = stamina_system.apply_stamina_recovery(character, match_context)
    assert character["stamina"] > old_stamina, "Stamina should increase after recovery"
    assert recovery > 0, "Recovery amount should be positive"
    
    # Test end of round effects
    stamina_system.apply_end_of_round_effects([character], match_context)
    
    # Test persistence
    stamina_system.process_match_end(character, "win", match_context)
    assert character["id"] in stamina_system.persistent_stamina, "Character should be in persistent data"
    
    print("All stamina system tests passed!")

if __name__ == "__main__":
    # Run tests if executed directly
    test_stamina_system()