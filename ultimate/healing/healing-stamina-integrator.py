"""
HealingStaminaIntegrator

This module implements the integration between the Stamina System and the Healing Mechanics
for the META Fantasy League Simulator v5.0.

It provides functions for:
- Managing stamina costs for healing attempts
- Modifying healing success chances based on stamina levels
- Adjusting stamina recovery rates for healers and patients
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from system_base import SystemBase


class HealingStaminaIntegrator(SystemBase):
    """
    Integration class between Healing Mechanics and Stamina System.
    
    This class handles all interactions between healing and stamina:
    - Determining stamina costs for healing attempts
    - Modifying healing success chances based on stamina levels
    - Managing stamina recovery rates for characters with healing abilities
    """
    
    def __init__(self, config, registry):
        """Initialize the healing-stamina integrator"""
        super().__init__("healing_stamina_integrator", registry, config)
        self.logger = logging.getLogger("HEALING_STAMINA_INTEGRATOR")
        self.healing_mechanics = None
        self.stamina_system = None
        
    def _activate_implementation(self):
        """Activate the integrator by connecting to required systems"""
        # Get required systems from registry
        self.healing_mechanics = self.registry.get("healing_mechanics")
        if not self.healing_mechanics:
            raise ValueError("Healing mechanics system is required but not available in the registry")
            
        self.stamina_system = self.registry.get("stamina_system")
        if not self.stamina_system:
            raise ValueError("Stamina system is required but not available in the registry")
            
        # Load healing stamina configuration
        self._load_healing_stamina_config()
        
        # Register with healing mechanics hooks
        self._register_with_healing_mechanics()
        
        self.logger.info("Healing-Stamina integrator activated successfully")
        return True
        
    def _load_healing_stamina_config(self):
        """Load healing stamina configuration"""
        stamina_config_path = self.config.get(
            "paths.stamina_integration_config", 
            "config/stamina_integration_config.json"
        )
        
        try:
            import json
            with open(stamina_config_path, 'r') as f:
                config_data = json.load(f)
                self.stamina_config = config_data.get("healing", {})
                
                if not self.stamina_config:
                    raise ValueError("No healing configuration found in stamina integration config")
        except Exception as e:
            self.logger.warning(f"Failed to load stamina integration config: {e}")
            # Use default configuration
            self.stamina_config = {
                "costs": {
                    "base_healing_cost": 15.0,       # Base stamina cost for healing
                    "severity_multipliers": {
                        "MINOR": 1.0,                # Standard cost for minor injuries
                        "MODERATE": 1.5,             # 50% more for moderate injuries
                        "MAJOR": 2.0,                # Double for major injuries
                        "SEVERE": 3.0                # Triple for severe injuries
                    }
                },
                "thresholds": {
                    "effectiveness": {
                        "60": 0.8,                   # 80% effectiveness at minor fatigue
                        "40": 0.6,                   # 60% effectiveness at moderate fatigue
                        "20": 0.4                    # 40% effectiveness at severe fatigue
                    }
                },
                "recovery_rates": {
                    "healer_penalty": 0.5,           # Reduced recovery for healers
                    "patient_bonus": 0.2,            # Improved recovery for patients
                    "self_healing_penalty": 0.3      # Additional penalty for self-healing
                },
                "bonus_modifiers": {
                    "willpower": 0.2,                # How much willpower affects healing
                    "regeneration_trait": 0.3,       # Bonus for regeneration trait
                    "healing_trait": 0.2,            # Bonus for standard healing
                    "rapid_healing_trait": 0.25      # Bonus for rapid healing
                }
            }
    
    def _register_with_healing_mechanics(self):
        """Register necessary hooks with the healing mechanics system"""
        # Monkey-patch the attempt_healing method to include stamina checks
        original_attempt_healing = self.healing_mechanics.attempt_healing
        
        def stamina_aware_attempt_healing(healer, injured, *args, **kwargs):
            # Calculate stamina cost
            stamina_cost = self.calculate_healing_stamina_cost(healer, injured)
            
            # Check if healer has enough stamina
            if healer.get("stamina", 0) < stamina_cost:
                return {
                    "success": False, 
                    "error": f"Insufficient stamina ({healer.get('stamina', 0):.1f}/{stamina_cost:.1f})"
                }
            
            # Modify success chance based on stamina levels
            original_base_chances = self.healing_mechanics.base_success_chances.copy()
            try:
                # Apply stamina-based modifiers
                self.modify_healing_success_chances(healer)
                
                # Call original method
                result = original_attempt_healing(healer, injured, *args, **kwargs)
                
                # Apply actual stamina cost if not already done
                if result.get("stamina_cost", 0) == 0:
                    # Apply stamina cost to result
                    result["stamina_cost"] = stamina_cost
                    
                    # Apply stamina cost to character if not already done
                    if "stamina" in healer:
                        if abs(healer["stamina"] - (healer.get("original_stamina", 100) - stamina_cost)) > 0.1:
                            # Apply the cost
                            healer["stamina"] = max(0, healer["stamina"] - stamina_cost)
                
                # Process post-healing stamina effects
                if result.get("success", False):
                    self.apply_post_healing_stamina_effects(healer, injured, result)
                
                return result
            finally:
                # Restore original success chances
                self.healing_mechanics.base_success_chances = original_base_chances
        
        # Replace method with stamina-aware version
        self.healing_mechanics.attempt_healing = stamina_aware_attempt_healing
        self.logger.info("Healing mechanics patched with stamina awareness")
    
    def calculate_healing_stamina_cost(self, healer: Dict[str, Any], injured: Dict[str, Any]) -> float:
        """
        Calculate the stamina cost for a healing attempt.
        
        Args:
            healer: Healer character
            injured: Injured character
            
        Returns:
            float: Calculated stamina cost
        """
        # Store original stamina
        if "stamina" in healer:
            healer["original_stamina"] = healer["stamina"]
        
        # Get base cost
        base_cost = self.stamina_config["costs"]["base_healing_cost"]
        
        # Get injury severity if available
        severity = "MINOR"  # Default
        if self.healing_mechanics and self.healing_mechanics.injury_system:
            char_id = injured.get("id", "unknown")
            injury = self.healing_mechanics.injury_system.injured_reserve.get(char_id, {})
            severity = injury.get("severity", "MINOR")
        
        # Apply severity multiplier
        multiplier = self.stamina_config["costs"]["severity_multipliers"].get(severity, 1.0)
        stamina_cost = base_cost * multiplier
        
        # Apply trait modifier
        healing_trait = None
        for trait in healer.get("traits", []):
            if trait in self.healing_mechanics.healing_traits:
                healing_trait = trait
                break
        
        if healing_trait:
            # Apply trait-specific modifiers
            if healing_trait == "regeneration":
                bonus = self.stamina_config["bonus_modifiers"]["regeneration_trait"]
                stamina_cost *= (1.0 + bonus)  # Higher cost for powerful healing
            elif healing_trait == "rapid_healing":
                bonus = self.stamina_config["bonus_modifiers"]["rapid_healing_trait"]
                stamina_cost *= (1.0 + bonus)  # Higher cost for rapid healing
            else:
                bonus = self.stamina_config["bonus_modifiers"]["healing_trait"]
                stamina_cost *= (1.0 + bonus)  # Standard bonus
        
        # Apply willpower modifier
        if "aWIL" in healer:
            willpower_bonus = self.stamina_config["bonus_modifiers"]["willpower"]
            willpower_modifier = 1.0 - ((healer["aWIL"] - 50) / 100.0 * willpower_bonus)
            stamina_cost *= max(0.5, willpower_modifier)  # Cap at 50% reduction
        
        # Self-healing costs more
        if healer.get("id", "") == injured.get("id", ""):
            self_healing_penalty = self.stamina_config["recovery_rates"]["self_healing_penalty"]
            stamina_cost *= (1.0 + self_healing_penalty)
        
        # Round to 1 decimal place
        return round(stamina_cost, 1)
    
    def modify_healing_success_chances(self, healer: Dict[str, Any]):
        """
        Modify healing success chances based on healer's stamina level.
        
        Args:
            healer: Healer character
        """
        # Get current stamina
        current_stamina = healer.get("stamina", 100)
        
        # Apply modifiers based on stamina thresholds
        effectiveness_modifiers = self.stamina_config["thresholds"]["effectiveness"]
        
        # Default modifier (no change)
        modifier = 1.0
        
        # Check each threshold (from lowest to highest)
        thresholds = sorted([int(t) for t in effectiveness_modifiers.keys()], reverse=False)
        
        for threshold in thresholds:
            if current_stamina <= threshold:
                modifier = effectiveness_modifiers[str(threshold)]
                break  # Use the first threshold that applies
        
        # Apply the modifier to base success chances
        for severity, chance in self.healing_mechanics.base_success_chances.items():
            self.healing_mechanics.base_success_chances[severity] = chance * modifier
    
    def apply_post_healing_stamina_effects(self, 
                                          healer: Dict[str, Any], 
                                          injured: Dict[str, Any], 
                                          healing_result: Dict[str, Any]):
        """
        Apply post-healing stamina effects such as recovery modifications.
        
        Args:
            healer: Healer character
            injured: Injured character
            healing_result: Result of healing attempt
        """
        # Store healer's reduced recovery rate (will recover stamina slower)
        healer_penalty = self.stamina_config["recovery_rates"]["healer_penalty"]
        if "stamina_recovery_modifier" not in healer:
            healer["stamina_recovery_modifier"] = 1.0 - healer_penalty
        
        # Patient gets bonus to stamina recovery (if not already at max)
        if "stamina" in injured and injured["stamina"] < 100:
            patient_bonus = self.stamina_config["recovery_rates"]["patient_bonus"]
            recovery_bonus = injured["stamina"] * patient_bonus
            
            # Don't exceed max stamina
            injured["stamina"] = min(100, injured["stamina"] + recovery_bonus)
            
            # Add log entry for stamina bonus
            if "stamina_log" not in injured:
                injured["stamina_log"] = []
                
            injured["stamina_log"].append({
                "bonus": recovery_bonus,
                "reason": "healing_treatment",
                "stamina": injured["stamina"]
            })
    
    def simulate_overnight_healing_recovery(self, team: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Simulate overnight healing and recovery effects.
        
        Args:
            team: List of team characters
            
        Returns:
            dict: Recovery results
        """
        results = {
            "stamina_recovery": [],
            "injury_improvements": []
        }
        
        # Identify healers
        healers = self.healing_mechanics.identify_healers(team)
        healer_ids = [h["character"].get("id", "") for h in healers]
        
        # Apply overnight recovery for each character
        for character in team:
            char_id = character.get("id", "")
            
            # Apply stamina recovery
            if "stamina" in character and character["stamina"] < 100:
                original_stamina = character["stamina"]
                
                # Base recovery rate
                recovery_rate = 0.7  # Default: recover 70% of missing stamina
                
                # Adjust recovery rate for healers
                if char_id in healer_ids:
                    recovery_modifier = self.stamina_config["recovery_rates"]["healer_penalty"]
                    recovery_rate *= (1.0 - recovery_modifier)
                
                # Apply recovery
                missing_stamina = 100 - original_stamina
                recovery = missing_stamina * recovery_rate
                new_stamina = min(100, original_stamina + recovery)
                
                # Update character
                character["stamina"] = new_stamina
                
                # Record recovery
                results["stamina_recovery"].append({
                    "character_id": char_id,
                    "character_name": character.get("name", "Unknown"),
                    "original_stamina": original_stamina,
                    "recovery_amount": new_stamina - original_stamina,
                    "new_stamina": new_stamina
                })
            
            # Apply passive healing effects for healers
            if char_id in healer_ids and self.healing_mechanics.injury_system:
                # Check if character has regeneration trait
                has_regeneration = False
                for trait in character.get("traits", []):
                    if trait == "regeneration":
                        has_regeneration = True
                        break
                
                if has_regeneration:
                    # Apply passive healing to all injured characters
                    for injured in team:
                        if self.healing_mechanics.injury_system.is_character_injured(injured):
                            # Apply minor recovery (reduce by 0.25 matches per night)
                            injured_id = injured.get("id", "")
                            injury = self.healing_mechanics.injury_system.injured_reserve.get(injured_id, {})
                            
                            if injury:
                                # Record original state
                                original_remaining = injury.get("matches_remaining", 0)
                                
                                # Apply reduction
                                new_remaining = max(0, original_remaining - 0.25)
                                injury["matches_remaining"] = new_remaining
                                
                                # Update injury system
                                self.healing_mechanics.injury_system.injured_reserve[injured_id] = injury
                                
                                # Record improvement
                                results["injury_improvements"].append({
                                    "character_id": injured_id,
                                    "character_name": injured.get("name", "Unknown"),
                                    "original_remaining": original_remaining,
                                    "reduction": original_remaining - new_remaining,
                                    "new_remaining": new_remaining,
                                    "healer_id": char_id,
                                    "passive": True
                                })
        
        # Save injury system changes
        if self.healing_mechanics.injury_system:
            self.healing_mechanics.injury_system._save_ir_list()
        
        return results
