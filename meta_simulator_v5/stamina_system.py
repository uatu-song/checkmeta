"""
Stamina System for META League Simulator v4.2.1
Implements robust stamina tracking, recovery, and effects
"""

import os
import json
import datetime
import logging
import math
from typing import Dict, List, Any, Optional, Tuple, Union
from system_base import SystemBase

class StaminaSystem(SystemBase):
    """System for tracking and managing character stamina with persistence"""
    
    def __init__(self, config):
        """Initialize the stamina system"""
        super().__init__("stamina_system", None)
        self.config = config
        
        # Initialize stamina persistence
        self.persistence_dir = config.get("paths.persistence_dir")
        os.makedirs(self.persistence_dir, exist_ok=True)
        
        # Track active character stamina values
        self.active_stamina = {}
        
        # Load existing stamina data
        self._load_persistent_data()
        
        # Get configuration values with defaults
        self.base_stamina = config.get("stamina_settings.base_stamina_value", 100)
        self.stamina_decay_per_round = config.get("stamina_settings.base_stamina_decay_per_round", 5)
        self.stamina_decay_per_round_multiplier = config.get("stamina_settings.stamina_decay_per_round_multiplier", 1.15)
        self.low_stamina_threshold = config.get("stamina_settings.low_stamina_threshold", 35)
        self.low_stamina_extra_damage_taken_percent = config.get("stamina_settings.low_stamina_extra_damage_taken_percent", 20)
        self.stamina_regen_rate = config.get("simulation.stamina_regen_rate", 5)
        self.base_stamina_recovery_per_day = config.get("stamina_settings.base_stamina_recovery_per_day", 15)
        
        self.logger.info(f"Stamina system initialized with base:{self.base_stamina}, " 
                        f"decay:{self.stamina_decay_per_round}*{self.stamina_decay_per_round_multiplier}, " 
                        f"threshold:{self.low_stamina_threshold}")
    
    def _activate_implementation(self) -> bool:
        """Implementation-specific activation logic"""
        self.logger.info("Activating Stamina System")
        return True
    
    def _load_persistent_data(self) -> None:
        """Load persistent stamina data from file"""
        stamina_file = os.path.join(self.persistence_dir, "stamina_data.json")
        
        if os.path.exists(stamina_file):
            try:
                with open(stamina_file, 'r') as f:
                    data = json.load(f)
                    
                    if "active_stamina" in data:
                        self.active_stamina = data["active_stamina"]
                    
                    self.logger.info(f"Loaded stamina data for {len(self.active_stamina)} characters")
            except Exception as e:
                self.logger.error(f"Error loading stamina data: {e}")
                self.active_stamina = {}
        else:
            self.logger.info("No stamina data file found, starting with default values")
            self.active_stamina = {}
    
    def save_stamina_data(self) -> None:
        """Save stamina data to persistence file"""
        stamina_file = os.path.join(self.persistence_dir, "stamina_data.json")
        
        try:
            # Create data to save
            data = {
                "active_stamina": self.active_stamina,
                "last_updated": datetime.datetime.now().isoformat()
            }
            
            # Save to file
            with open(stamina_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            self.logger.info(f"Saved stamina data for {len(self.active_stamina)} characters")
        except Exception as e:
            self.logger.error(f"Error saving stamina data: {e}")
    
    def initialize_character_stamina(self, character: Dict[str, Any]) -> None:
        """Initialize stamina for a character, respecting persistent values"""
        # Get character ID
        char_id = character.get("id", "unknown")
        
        # Check if we have persistent data for this character
        if char_id in self.active_stamina:
            # Use persistent value
            character["stamina"] = self.active_stamina[char_id]
            self.logger.debug(f"Loaded persistent stamina for {char_id}: {character['stamina']}")
        else:
            # Start with base stamina value
            character["stamina"] = self.base_stamina
            self.active_stamina[char_id] = self.base_stamina
            self.logger.debug(f"Initialized new stamina for {char_id}: {self.base_stamina}")
        
        # Store initial stamina for this round/match
        character["initial_stamina"] = character["stamina"]
        
        # Add stamina state flags
        character["is_stamina_low"] = character["stamina"] <= self.low_stamina_threshold
    
    def update_stamina(self, character: Dict[str, Any], 
                      change_amount: float, 
                      reason: str,
                      match_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Update character stamina with bounds checking and logging"""
        if "stamina" not in character:
            self.initialize_character_stamina(character)
        
        # Get current stamina
        current_stamina = character["stamina"]
        
        # Calculate new stamina value with bounds checking
        new_stamina = max(0, min(self.base_stamina, current_stamina + change_amount))
        
        # Update character and persistence
        character["stamina"] = new_stamina
        
        # Update persistence
        char_id = character.get("id", "unknown")
        self.active_stamina[char_id] = new_stamina
        
        # Get character details for logging
        char_name = character.get("name", "Unknown")
        
        # Log significant changes
        if abs(change_amount) >= 10:
            log_message = (f"Character {char_name} stamina changed by {change_amount:.1f} "
                         f"({current_stamina:.1f} → {new_stamina:.1f}): {reason}")
            
            if change_amount < 0:
                self.logger.info(log_message)
            else:
                self.logger.debug(log_message)
        
        # Update stamina state flags
        previous_low = character.get("is_stamina_low", False)
        
        character["is_stamina_low"] = new_stamina <= self.low_stamina_threshold
        
        # Log state transitions
        if not previous_low and character["is_stamina_low"]:
            self.logger.info(f"Character {char_name} stamina is now LOW: {new_stamina:.1f}")
        elif previous_low and not character["is_stamina_low"]:
            self.logger.info(f"Character {char_name} stamina recovered from LOW: {new_stamina:.1f}")
        
        # Add to stamina change log if match context provided
        if match_context is not None:
            self._log_stamina_change(character, current_stamina, new_stamina, change_amount, reason, match_context)
        
        return character
    
    def _log_stamina_change(self, character: Dict[str, Any], 
                          old_value: float, new_value: float, 
                          change_amount: float, reason: str,
                          match_context: Dict[str, Any]) -> None:
        """Log a stamina change to match context for reporting"""
        # Create stamina log if not present
        if "stamina_logs" not in match_context:
            match_context["stamina_logs"] = []
        
        # Create log entry
        log_entry = {
            "character_id": character.get("id", "unknown"),
            "character_name": character.get("name", "Unknown"),
            "team_id": character.get("team_id", "unknown"),
            "round": match_context.get("round", 0),
            "old_value": old_value,
            "new_value": new_value,
            "change": change_amount,
            "reason": reason,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        # Add to match context
        match_context["stamina_logs"].append(log_entry)
    
    def apply_stamina_decay(self, character: Dict[str, Any], 
                           decay_amount: Optional[float] = None,
                           match_context: Optional[Dict[str, Any]] = None) -> None:
        """Apply stamina decay to a character"""
        char_id = character.get("id", "unknown")
        
        # Skip if knocked out or inactive
        if character.get("is_ko", False) or not character.get("is_active", True):
            return
        
        # Verify character in stamina data
        if "stamina" not in character:
            self.initialize_character_stamina(character)
        
        # Calculate decay amount
        if decay_amount is None:
            # Calculate from base rates and multipliers
            decay_amount = self.stamina_decay_per_round * self.stamina_decay_per_round_multiplier
            
            # Apply trait modifiers if character has relevant traits
            if "traits" in character:
                for trait in character.get("traits", []):
                    if isinstance(trait, dict) and trait.get("type") == "stamina":
                        if trait.get("effect_type") == "decay_reduction":
                            reduction = trait.get("effect_value", 0)
                            decay_amount *= (1.0 - reduction)
        
        # Apply decay (ensure it doesn't go below 0)
        self.update_stamina(
            character, 
            -decay_amount, 
            "Stamina decay per round",
            match_context
        )
    
    def apply_action_cost(self, character: Dict[str, Any], 
                         action_type: str, success: bool,
                         match_context: Dict[str, Any]) -> None:
        """Apply stamina cost for various actions"""
        # Base costs for different actions
        costs = {
            "movement": 2,
            "attack": 5,
            "special_attack": 8,
            "dodge": 3,
            "block": 4,
            "heal": 6,
            "buff": 7,
            "debuff": 7
        }
        
        # Get base cost for this action type
        base_cost = costs.get(action_type, 3)  # Default cost for unknown actions
        
        # Apply refund if successful
        if success:
            base_cost *= 0.7  # 30% refund for successful actions
        
        # Apply modifiers based on attributes
        if action_type in ["movement", "dodge"]:
            # Speed-based actions
            attr_value = character.get("aSPD", 5)
        elif action_type in ["attack", "special_attack"]:
            # Strength-based actions
            attr_value = character.get("aSTR", 5)
        elif action_type in ["block"]:
            # Durability-based actions
            attr_value = character.get("aDUR", 5)
        elif action_type in ["heal", "buff", "debuff"]:
            # Finesse-based actions
            attr_value = character.get("aFS", 5)
        else:
            # Default to willpower
            attr_value = character.get("aWIL", 5)
        
        # Calculate attribute modifier
        attr_modifier = 1.0 - ((attr_value - 5) * 0.05)  # 5% reduction per point above 5
        attr_modifier = max(0.7, min(1.3, attr_modifier))  # Limit to 70-130% range
        
        # Calculate final cost
        final_cost = base_cost * attr_modifier
        
        # Update stamina
        reason = f"{action_type.replace('_', ' ').capitalize()} {'success' if success else 'failure'}"
        self.update_stamina(
            character, 
            -final_cost,
            reason,
            match_context
        )
    
    def apply_end_of_round_recovery(self, characters: List[Dict[str, Any]], 
                                   match_context: Dict[str, Any]) -> None:
        """Apply end of round stamina effects to all characters"""
        for character in characters:
            # Skip knocked out or inactive characters
            if character.get("is_ko", False) or not character.get("is_active", True):
                continue
            
            # Apply stamina decay first
            self.apply_stamina_decay(character, match_context=match_context)
            
            # Apply attribute-based regeneration
            dur_value = character.get("aDUR", 5)
            will_value = character.get("aWIL", 5)
            
            # Calculate regen amount
            base_regen = self.stamina_regen_rate
            
            # Durability bonus
            if dur_value > 5:
                dur_bonus = (dur_value - 5) * 0.2  # 0.2 per point above 5
                base_regen += dur_bonus
            
            # Willpower bonus
            if will_value > 5:
                will_bonus = (will_value - 5) * 0.1  # 0.1 per point above 5
                base_regen += will_bonus
            
            # Apply regeneration if needed
            if base_regen > 0 and character["stamina"] < self.base_stamina:
                self.update_stamina(
                    character,
                    base_regen,
                    "End of round recovery",
                    match_context
                )
    
    def calculate_stamina_damage_modifier(self, character: Dict[str, Any]) -> float:
        """Calculate damage modifier based on stamina level"""
        # Skip if not tracking stamina
        if "stamina" not in character:
            return 1.0
        
        current_stamina = character["stamina"]
        
        # Check if below low stamina threshold
        if current_stamina < self.low_stamina_threshold:
            # Calculate how far below threshold (as percentage)
            threshold_diff = self.low_stamina_threshold - current_stamina
            threshold_pct = threshold_diff / self.low_stamina_threshold
            
            # Apply damage increase (up to low_stamina_extra_damage_taken_percent)
            extra_damage_pct = threshold_pct * self.low_stamina_extra_damage_taken_percent / 100.0
            
            return 1.0 + extra_damage_pct
        
        return 1.0
    
    def process_day_change(self, day_number: int) -> Dict[str, Any]:
        """Process day change stamina recovery for all tracked characters"""
        self.logger.info(f"Processing day change stamina recovery for day {day_number}")
        
        # Track characters processed
        characters_processed = []
        
        # Process each character
        for char_id, current_stamina in self.active_stamina.items():
            # Calculate recovery amount
            recovery_amount = self.base_stamina_recovery_per_day
            
            # Only recover if current stamina is below maximum
            if current_stamina < self.base_stamina:
                new_stamina = min(self.base_stamina, current_stamina + recovery_amount)
                
                # Update stamina value
                self.active_stamina[char_id] = new_stamina
                
                # Add to processed list
                characters_processed.append({
                    "character_id": char_id,
                    "old_stamina": current_stamina,
                    "new_stamina": new_stamina,
                    "recovery_amount": recovery_amount
                })
                
                self.logger.info(f"Overnight recovery for {char_id}: {current_stamina:.1f} → {new_stamina:.1f} (+{recovery_amount:.1f})")
        
        # Save updated data
        self.save_stamina_data()
        
        return {
            "day_number": day_number,
            "recovery_amount": self.base_stamina_recovery_per_day,
            "characters_processed": characters_processed,
            "total_characters": len(self.active_stamina),
            "date": datetime.datetime.now().isoformat()
        }
    
    def get_character_stamina_report(self, character_id: str) -> Dict[str, Any]:
        """Generate a detailed stamina report for a character"""
        if character_id not in self.active_stamina:
            return {
                "character_id": character_id,
                "error": "Character not found in stamina system"
            }
        
        current_stamina = self.active_stamina[character_id]
        
        # Create report
        report = {
            "character_id": character_id,
            "current_stamina": current_stamina,
            "max_stamina": self.base_stamina,
            "stamina_percent": (current_stamina / self.base_stamina) * 100,
            "is_stamina_low": current_stamina < self.low_stamina_threshold,
            "low_stamina_threshold": self.low_stamina_threshold,
            "damage_modifier": self.calculate_stamina_damage_modifier({"id": character_id, "stamina": current_stamina}),
            "last_updated": datetime.datetime.now().isoformat()
        }
        
        return report