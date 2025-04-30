"""
META Fantasy League Simulator - Stamina-Trait System Integration
==============================================================

This module implements the bidirectional integration between the Stamina System
and the Trait System, ensuring that traits affect stamina and stamina affects
trait activation in a balanced way.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple, Union
import random
import math

# Import required system components
from system_base import SystemBase

class StaminaTraitIntegration:
    """Integrates stamina system with trait system for bidirectional effects"""
    
    def __init__(self, registry):
        """Initialize the integration"""
        self.registry = registry
        self.logger = logging.getLogger("StaminaTraitIntegration")
        
        # Get required systems
        self.stamina_system = registry.get("stamina_system")
        if not self.stamina_system:
            raise ValueError("Stamina system not available in registry")
        
        self.trait_system = registry.get("trait_system")
        if not self.trait_system:
            raise ValueError("Trait system not available in registry")
        
        # Get event system if available
        self.event_system = registry.get("event_system")
        if not self.event_system:
            self.logger.warning("Event system not available, event emission disabled")
    
    def integrate_systems(self):
        """Integrate the systems by registering hooks and callbacks"""
        self.logger.info("Integrating stamina and trait systems")
        
        # Register activation check in trait system
        if hasattr(self.trait_system, "register_activation_check"):
            self.trait_system.register_activation_check(self.check_trait_activation)
            self.logger.info("Registered stamina-based activation check with trait system")
        else:
            self.logger.warning("Trait system does not support activation check registration")
        
        # Register cost calculation in trait system
        if hasattr(self.trait_system, "register_cost_calculator"):
            self.trait_system.register_cost_calculator(self.calculate_trait_cost)
            self.logger.info("Registered stamina cost calculator with trait system")
        else:
            self.logger.warning("Trait system does not support cost calculator registration")
        
        # Register trait effect on stamina
        if hasattr(self.trait_system, "register_effect_handler"):
            self.trait_system.register_effect_handler("stamina", self.apply_trait_stamina_effect)
            self.logger.info("Registered stamina effect handler with trait system")
        else:
            self.logger.warning("Trait system does not support effect handler registration")
        
        return True
    
    def check_trait_activation(self, character: Dict[str, Any], trait: Dict[str, Any], 
                               match_context: Dict[str, Any]) -> Tuple[bool, str]:
        """Check if a character can activate a trait based on stamina
        
        Args:
            character: The character attempting to activate the trait
            trait: The trait being activated
            match_context: The current match context
            
        Returns:
            (bool, str): Whether activation is allowed and reason if not
        """
        # Get trait cost
        trait_name = trait.get("name", "unknown_trait")
        trait_cost = self.calculate_trait_cost(character, trait, match_context)
        
        # Check with stamina system
        can_use, reason = self.stamina_system.can_use_trait(character, trait_name, trait_cost)
        
        if not can_use:
            self.logger.info(f"Trait activation blocked due to stamina: {reason}")
            
            # Emit event if event system available
            if self.event_system:
                self.event_system.emit({
                    "type": "trait_activation_blocked",
                    "character_id": character.get("id", "unknown"),
                    "trait_name": trait_name,
                    "reason": reason,
                    "stamina": character.get("stamina", 0),
                    "required_stamina": trait_cost,
                    "match_id": match_context.get("match_id", "unknown"),
                    "turn": match_context.get("round", 0)
                })
            
        return can_use, reason
    
    def calculate_trait_cost(self, character: Dict[str, Any], trait: Dict[str, Any], 
                            match_context: Dict[str, Any]) -> float:
        """Calculate the stamina cost for a trait activation
        
        Args:
            character: The character activating the trait
            trait: The trait being activated
            match_context: The current match context
            
        Returns:
            The stamina cost
        """
        # Get base cost from trait
        base_cost = trait.get("stamina_cost", 5.0)
        
        # Get cost category
        cost_category = trait.get("cost_category", "medium")
        
        # Get trait system's trait cost category if not specified in trait
        if not cost_category and hasattr(self.trait_system, "get_trait_cost_category"):
            cost_category = self.trait_system.get_trait_cost_category(trait.get("name", "unknown_trait"))
        
        # Get cost multiplier from stamina system based on category
        trait_cost_multipliers = self.stamina_system.stamina_config.get("trait_cost_multipliers", {
            "low": 0.5,
            "medium": 1.0,
            "high": 2.0,
            "extreme": 3.0
        })
        
        category_multiplier = trait_cost_multipliers.get(cost_category, 1.0)
        
        # Apply character attribute modifiers
        # Characters with high WIL can use traits more efficiently
        attribute_modifier = 1.0
        if "aWIL" in character:
            # 10% reduction per 10 points of WIL above 50
            will_bonus = max(0, (character["aWIL"] - 50) / 100)
            attribute_modifier = max(0.5, 1.0 - will_bonus)  # Cap at 50% reduction
        
        # Calculate round-based scaling (traits get more costly in later rounds)
        round_number = match_context.get("round", 1)
        round_scaling = min(1.0 + ((round_number - 1) * 0.02), 1.2)  # Max 20% increase
        
        # Calculate final cost
        final_cost = base_cost * category_multiplier * attribute_modifier * round_scaling
        
        # Round to one decimal place
        return round(final_cost, 1)
    
    def apply_trait_stamina_effect(self, character: Dict[str, Any], effect: Dict[str, Any], 
                                  match_context: Dict[str, Any]) -> bool:
        """Apply a trait's effect on stamina
        
        Args:
            character: The character to apply the effect to
            effect: The effect details
            match_context: The current match context
            
        Returns:
            True if effect was applied, False otherwise
        """
        effect_type = effect.get("type", "unknown")
        value = effect.get("value", 0)
        
        if effect_type == "stamina_drain":
            # Apply stamina drain
            self.stamina_system.apply_stamina_cost(
                character,
                value,
                f"trait_effect:{effect.get('source_trait', 'unknown')}",
                match_context
            )
            return True
            
        elif effect_type == "stamina_recovery":
            # Apply stamina recovery
            old_stamina = character.get("stamina", 0)
            
            # Calculate recovery amount
            recovery_amount = value
            if effect.get("is_percentage", False):
                # If value is a percentage, calculate based on max stamina
                max_stamina = self.stamina_system._calculate_max_stamina(character)
                recovery_amount = max_stamina * (value / 100)
            
            # Apply recovery
            new_stamina = min(character.get("stamina", 0) + recovery_amount, 
                             self.stamina_system._calculate_max_stamina(character))
            character["stamina"] = new_stamina
            
            # Log recovery
            log_entry = {
                "turn": match_context.get("round", 0),
                "recovery": new_stamina - old_stamina,
                "reason": f"trait_effect:{effect.get('source_trait', 'unknown')}",
                "stamina_remaining": new_stamina
            }
            
            # Add to character's stamina log
            if "stamina_log" not in character:
                character["stamina_log"] = []
            character["stamina_log"].append(log_entry)
            
            # Update match context stamina logs
            if "stamina_logs" not in match_context:
                match_context["stamina_logs"] = []
                
            match_context["stamina_logs"].append({
                "character_id": character.get("id", "unknown"),
                "character_name": character.get("name", "Unknown"),
                "team_id": character.get("team_id", "unknown"),
                "turn": match_context.get("round", 0),
                "recovery": new_stamina - old_stamina,
                "reason": f"trait_effect:{effect.get('source_trait', 'unknown')}",
                "stamina_remaining": new_stamina
            })
            
            # Emit event
            if self.event_system:
                self.event_system.emit({
                    "type": "stamina_recovery",
                    "character_id": character.get("id", "unknown"),
                    "amount": new_stamina - old_stamina,
                    "reason": f"trait_effect:{effect.get('source_trait', 'unknown')}",
                    "remaining": new_stamina,
                    "match_id": match_context.get("match_id", "unknown"),
                    "turn": match_context.get("round", 0)
                })
                
            return True
            
        elif effect_type == "stamina_efficiency":
            # Apply a temporary modifier to stamina costs
            # This is a percentage reduction in stamina costs for a specified duration
            if "stamina_cost_modifier" not in character:
                character["stamina_cost_modifier"] = {}
                
            duration = effect.get("duration", 1)  # Default 1 round
            modifier_id = f"trait_{effect.get('source_trait', 'unknown')}"
            
            character["stamina_cost_modifier"][modifier_id] = {
                "value": value,  # Percent reduction
                "remaining_rounds": duration,
                "source": effect.get("source_trait", "unknown")
            }
            
            # Emit event
            if self.event_system:
                self.event_system.emit({
                    "type": "stamina_modifier_applied",
                    "character_id": character.get("id", "unknown"),
                    "modifier_id": modifier_id,
                    "value": value,
                    "duration": duration,
                    "source": effect.get("source_trait", "unknown"),
                    "match_id": match_context.get("match_id", "unknown"),
                    "turn": match_context.get("round", 0)
                })
                
            return True
            
        return False
    
    def modify_trait_activation_chance(self, character: Dict[str, Any], trait: Dict[str, Any], 
                                      base_chance: float) -> float:
        """Modify trait activation chance based on stamina levels
        
        Args:
            character: The character activating the trait
            trait: The trait being activated
            base_chance: The base activation chance
            
        Returns:
            Modified activation chance
        """
        # Use stamina system's calculation
        return self.stamina_system.calculate_trait_chance_modifier(character, base_chance)
    
    def register_with_combat_system(self):
        """Register with the combat system for stamina-driven combat effects"""
        combat_system = self.registry.get("combat_system")
        if not combat_system:
            self.logger.warning("Combat system not available, skipping registration")
            return False
        
        # Register damage modifier based on stamina
        if hasattr(combat_system, "register_damage_modifier"):
            combat_system.register_damage_modifier(
                "stamina_low_stamina_penalty",
                self._calculate_damage_modifier
            )
            self.logger.info("Registered stamina damage modifier with combat system")
        else:
            self.logger.warning("Combat system does not support damage modifier registration")
        
        return True
    
    def _calculate_damage_modifier(self, target_character: Dict[str, Any], 
                                 damage_amount: float, source: str) -> float:
        """Calculate damage modifier based on stamina
        
        Args:
            target_character: The character taking damage
            damage_amount: The base damage amount
            source: The source of the damage
            
        Returns:
            Modified damage amount
        """
        # Use stamina system's calculation
        modifier = self.stamina_system.get_low_stamina_penalty(target_character)
        return damage_amount * modifier
    
    def update_stamina_modifiers(self, character: Dict[str, Any], match_context: Dict[str, Any]):
        """Update stamina cost modifiers, reducing duration and removing expired ones
        
        Args:
            character: The character to update
            match_context: The current match context
        """
        if "stamina_cost_modifier" not in character:
            return
        
        # Track expired modifiers
        expired = []
        
        # Update duration
        for modifier_id, modifier in character["stamina_cost_modifier"].items():
            modifier["remaining_rounds"] -= 1
            
            if modifier["remaining_rounds"] <= 0:
                expired.append(modifier_id)
                
                # Emit event for expiration
                if self.event_system:
                    self.event_system.emit({
                        "type": "stamina_modifier_expired",
                        "character_id": character.get("id", "unknown"),
                        "modifier_id": modifier_id,
                        "source": modifier["source"],
                        "match_id": match_context.get("match_id", "unknown"),
                        "turn": match_context.get("round", 0)
                    })
        
        # Remove expired modifiers
        for modifier_id in expired:
            del character["stamina_cost_modifier"][modifier_id]
    
    def get_stamina_cost_modifier(self, character: Dict[str, Any]) -> float:
        """Get the combined stamina cost modifier for a character
        
        Args:
            character: The character to get modifiers for
            
        Returns:
            Combined modifier (as a multiplier, e.g., 0.8 for 20% reduction)
        """
        if "stamina_cost_modifier" not in character:
            return 1.0
        
        # Start with no reduction
        total_reduction = 0.0
        
        # Sum all reductions
        for modifier in character["stamina_cost_modifier"].values():
            total_reduction += modifier["value"] / 100.0  # Convert percentage to decimal
        
        # Cap reduction at 75%
        total_reduction = min(total_reduction, 0.75)
        
        # Convert to multiplier
        return 1.0 - total_reduction
    
    def process_end_of_round(self, character: Dict[str, Any], match_context: Dict[str, Any]):
        """Process end of round effects for stamina-trait integration
        
        Args:
            character: The character to process
            match_context: The current match context
        """
        # Update stamina modifiers
        self.update_stamina_modifiers(character, match_context)
    
    def apply_trait_on_threshold_crossing(self, character: Dict[str, Any], threshold: int, 
                                         direction: str, match_context: Dict[str, Any]):
        """Apply traits that trigger when crossing stamina thresholds
        
        Args:
            character: The character crossing a threshold
            threshold: The threshold being crossed
            direction: 'up' or 'down'
            match_context: The current match context
        """
        # Skip if trait system doesn't support the needed interface
        if not hasattr(self.trait_system, "get_character_traits"):
            return
        
        # Get character's traits
        traits = self.trait_system.get_character_traits(character)
        
        # Find traits that trigger on threshold crossings
        for trait in traits:
            # Skip if not a threshold trigger trait
            if trait.get("trigger_type") != "stamina_threshold":
                continue
                
            # Check if trait triggers on this threshold and direction
            if trait.get("trigger_threshold") == threshold and trait.get("trigger_direction") == direction:
                # Attempt to activate the trait
                if hasattr(self.trait_system, "activate_trait"):
                    # Bypass normal stamina cost for threshold-triggered traits
                    result, message = self.trait_system.activate_trait(
                        character, 
                        trait.get("name", "unknown_trait"), 
                        match_context,
                        bypass_checks=True
                    )
                    
                    if result:
                        self.logger.info(
                            f"Automatically activated trait {trait.get('name')} due to "
                            f"stamina threshold {threshold} crossing ({direction})"
                        )
                    else:
                        self.logger.warning(
                            f"Failed to activate threshold trait {trait.get('name')}: {message}"
                        )


# Example integration usage
def integrate_stamina_trait_systems(registry):
    """Example of integrating stamina and trait systems"""
    integration = StaminaTraitIntegration(registry)
    
    # Perform the integration
    integration.integrate_systems()
    
    # Also register with combat system
    integration.register_with_combat_system()
    
    return integration
