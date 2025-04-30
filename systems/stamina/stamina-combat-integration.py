"""
META Fantasy League Simulator - Stamina-Combat System Integration
================================================================

This module implements the integration between the Stamina System
and the Combat System, ensuring that stamina levels affect combat
effectiveness and combat actions impact stamina.
"""

import logging
import random
import math
from typing import Dict, List, Any, Optional, Tuple, Union

# Import required system components
from system_base import SystemBase

class StaminaCombatIntegration:
    """Integrates stamina system with combat system"""
    
    def __init__(self, registry):
        """Initialize the integration"""
        self.registry = registry
        self.logger = logging.getLogger("StaminaCombatIntegration")
        
        # Get required systems
        self.stamina_system = registry.get("stamina_system")
        if not self.stamina_system:
            raise ValueError("Stamina system not available in registry")
        
        self.combat_system = registry.get("combat_system")
        if not self.combat_system:
            raise ValueError("Combat system not available in registry")
        
        # Get event system if available
        self.event_system = registry.get("event_system")
        if not self.event_system:
            self.logger.warning("Event system not available, event emission disabled")
    
    def integrate_systems(self):
        """Integrate the systems by registering hooks and callbacks"""
        self.logger.info("Integrating stamina and combat systems")
        
        # Register damage modifier in combat system
        if hasattr(self.combat_system, "register_damage_modifier"):
            self.combat_system.register_damage_modifier(
                "stamina_fatigue_modifier",
                self.calculate_damage_modifier
            )
            self.logger.info("Registered stamina-based damage modifier")
        else:
            self.logger.warning("Combat system does not support damage modifier registration")
        
        # Register accuracy modifier in combat system
        if hasattr(self.combat_system, "register_accuracy_modifier"):
            self.combat_system.register_accuracy_modifier(
                "stamina_accuracy_modifier",
                self.calculate_accuracy_modifier
            )
            self.logger.info("Registered stamina-based accuracy modifier")
        else:
            self.logger.warning("Combat system does not support accuracy modifier registration")
        
        # Register defense modifier in combat system
        if hasattr(self.combat_system, "register_defense_modifier"):
            self.combat_system.register_defense_modifier(
                "stamina_defense_modifier",
                self.calculate_defense_modifier
            )
            self.logger.info("Registered stamina-based defense modifier")
        else:
            self.logger.warning("Combat system does not support defense modifier registration")
        
        # Register post-action handler in combat system
        if hasattr(self.combat_system, "register_post_action_handler"):
            self.combat_system.register_post_action_handler(
                "stamina_cost_handler",
                self.handle_action_stamina_cost
            )
            self.logger.info("Registered stamina cost handler for combat actions")
        else:
            self.logger.warning("Combat system does not support post-action handler registration")
        
        # Register stamina-based resignation check
        if hasattr(self.combat_system, "register_resignation_check"):
            self.combat_system.register_resignation_check(
                "stamina_exhaustion_check",
                self.check_stamina_resignation
            )
            self.logger.info("Registered stamina-based resignation check")
        else:
            self.logger.warning("Combat system does not support resignation check registration")
        
        return True
    
    def calculate_damage_modifier(self, target_character: Dict[str, Any], 
                                damage_amount: float, source: str,
                                match_context: Dict[str, Any]) -> float:
        """Calculate damage modifier based on stamina
        
        Args:
            target_character: The character receiving damage
            damage_amount: The original damage amount
            source: The source of the damage
            match_context: The current match context
            
        Returns:
            Modified damage amount
        """
        # Get damage multiplier from stamina system
        stamina_multiplier = self.stamina_system.get_low_stamina_penalty(target_character)
        
        # Apply multiplier
        modified_damage = damage_amount * stamina_multiplier
        
        # Log significant modifications
        if stamina_multiplier > 1.05:  # Only log if there's a meaningful increase
            self.logger.info(
                f"Character {target_character.get('name')} takes {((stamina_multiplier - 1) * 100):.1f}% "
                f"more damage due to low stamina: {damage_amount} → {modified_damage}"
            )
            
            # Emit event for significant modifications
            if self.event_system:
                self.event_system.emit({
                    "type": "stamina_damage_modifier",
                    "character_id": target_character.get("id", "unknown"),
                    "original_damage": damage_amount,
                    "modified_damage": modified_damage,
                    "modifier": stamina_multiplier,
                    "stamina": target_character.get("stamina", 0),
                    "source": source,
                    "match_id": match_context.get("match_id", "unknown"),
                    "turn": match_context.get("round", 0)
                })
        
        return modified_damage
    
    def calculate_accuracy_modifier(self, character: Dict[str, Any], 
                                  base_accuracy: float, target: Dict[str, Any],
                                  match_context: Dict[str, Any]) -> float:
        """Calculate accuracy modifier based on stamina
        
        Args:
            character: The character performing the action
            base_accuracy: The base accuracy value
            target: The target character
            match_context: The current match context
            
        Returns:
            Modified accuracy value
        """
        # Get character's stamina
        stamina = character.get("stamina", 0)
        
        # Calculate modifier based on stamina thresholds
        modifier = 1.0
        
        if stamina <= 20:
            # Severe fatigue: -15% accuracy
            modifier = 0.85
        elif stamina <= 40:
            # Moderate fatigue: -10% accuracy
            modifier = 0.9
        elif stamina <= 60:
            # Minor fatigue: -5% accuracy
            modifier = 0.95
        
        # Apply modifier
        modified_accuracy = base_accuracy * modifier
        
        # Log significant modifications
        if modifier < 0.95:  # Only log if there's a meaningful decrease
            self.logger.info(
                f"Character {character.get('name')} has {((1 - modifier) * 100):.1f}% "
                f"reduced accuracy due to fatigue: {base_accuracy} → {modified_accuracy}"
            )
            
            # Emit event for significant modifications
            if self.event_system:
                self.event_system.emit({
                    "type": "stamina_accuracy_modifier",
                    "character_id": character.get("id", "unknown"),
                    "original_accuracy": base_accuracy,
                    "modified_accuracy": modified_accuracy,
                    "modifier": modifier,
                    "stamina": stamina,
                    "match_id": match_context.get("match_id", "unknown"),
                    "turn": match_context.get("round", 0)
                })
        
        return modified_accuracy
    
    def calculate_defense_modifier(self, character: Dict[str, Any], 
                                 base_defense: float, attacker: Dict[str, Any],
                                 match_context: Dict[str, Any]) -> float:
        """Calculate defense modifier based on stamina
        
        Args:
            character: The character defending
            base_defense: The base defense value
            attacker: The attacking character
            match_context: The current match context
            
        Returns:
            Modified defense value
        """
        # Get character's stamina
        stamina = character.get("stamina", 0)
        
        # Calculate modifier based on stamina thresholds
        modifier = 1.0
        
        if stamina <= 20:
            # Severe fatigue: -20% defense
            modifier = 0.8
        elif stamina <= 40:
            # Moderate fatigue: -12% defense
            modifier = 0.88
        elif stamina <= 60:
            # Minor fatigue: -6% defense
            modifier = 0.94
        
        # Apply modifier
        modified_defense = base_defense * modifier
        
        # Log significant modifications
        if modifier < 0.95:  # Only log if there's a meaningful decrease
            self.logger.info(
                f"Character {character.get('name')} has {((1 - modifier) * 100):.1f}% "
                f"reduced defense due to fatigue: {base_defense} → {modified_defense}"
            )
            
            # Emit event for significant modifications
            if self.event_system:
                self.event_system.emit({
                    "type": "stamina_defense_modifier",
                    "character_id": character.get("id", "unknown"),
                    "original_defense": base_defense,
                    "modified_defense": modified_defense,
                    "modifier": modifier,
                    "stamina": stamina,
                    "match_id": match_context.get("match_id", "unknown"),
                    "turn": match_context.get("round", 0)
                })
        
        return modified_defense
    
    def handle_action_stamina_cost(self, action: Dict[str, Any], character: Dict[str, Any],
                                 result: Dict[str, Any], match_context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply stamina costs for combat actions
        
        Args:
            action: The combat action
            character: The character performing the action
            result: The result of the action
            match_context: The current match context
            
        Returns:
            Updated result with stamina costs
        """
        # Get action type
        action_type = action.get("type", "standard_move")
        
        # Get base cost from stamina config
        action_costs = self.stamina_system.stamina_config.get("action_costs", {})
        base_cost = action_costs.get(action_type, 1.0)
        
        # Apply modifiers based on action result
        if result.get("hit", False):
            # Successful hits cost a bit more stamina
            base_cost *= 1.2
        
        if result.get("critical", False):
            # Critical hits cost even more stamina
            base_cost *= 1.3
        
        if not result.get("hit", True):
            # Misses cost less stamina
            base_cost *= 0.8
        
        # Apply material change modifier
        material_change = result.get("material_change", 0)
        if material_change > 0:
            # Capturing pieces costs extra stamina based on material value
            material_cost = material_change * 0.5  # 0.5 stamina per material point
            base_cost += material_cost
        
        # Apply the cost
        self.stamina_system.apply_stamina_cost(
            character,
            base_cost,
            f"combat_action:{action_type}",
            match_context
        )
        
        # Update result with stamina cost
        result["stamina_cost"] = base_cost
        
        return result
    
    def check_stamina_resignation(self, character: Dict[str, Any], match_context: Dict[str, Any]) -> Tuple[bool, str]:
        """Check if a character should resign due to stamina exhaustion
        
        Args:
            character: The character to check
            match_context: The current match context
            
        Returns:
            (bool, str): Whether the character should resign and reason
        """
        # Calculate resignation chance from stamina system
        resignation_chance = self.stamina_system.calculate_resignation_chance(character)
        
        if resignation_chance <= 0:
            return False, "No resignation risk"
        
        # Roll for resignation
        roll = random.random()
        should_resign = roll < resignation_chance
        
        if should_resign:
            reason = f"Character exhausted - resigned due to severe fatigue (stamina: {character.get('stamina', 0)})"
            
            # Emit event
            if self.event_system:
                self.event_system.emit({
                    "type": "stamina_resignation",
                    "character_id": character.get("id", "unknown"),
                    "character_name": character.get("name", "Unknown"),
                    "stamina": character.get("stamina", 0),
                    "resignation_chance": resignation_chance,
                    "reason": reason,
                    "match_id": match_context.get("match_id", "unknown"),
                    "turn": match_context.get("round", 0)
                })
                
            return True, reason
            
        return False, "Character continues despite fatigue"
    
    def apply_combat_stamina_interactions(self, material_change: float, character: Dict[str, Any], 
                                        match_context: Dict[str, Any]) -> None:
        """Apply stamina interactions for material changes in chess
        
        Args:
            material_change: The material value change (positive for captures, negative for losses)
            character: The character to update
            match_context: The current match context
        """
        # For captures (positive material change)
        if material_change > 0:
            # Apply stamina cost
            stamina_cost = material_change * 0.5  # 0.5 stamina per material point
            
            self.stamina_system.apply_stamina_cost(
                character,
                stamina_cost,
                "capturing_piece",
                match_context
            )
        
        # For losses (negative material change)
        elif material_change < 0:
            # Calculate morale impact
            # Note: This assumes the simulator has a morale system
            # If not, this can be commented out
            morale_system = self.registry.get("morale_system")
            if morale_system and hasattr(morale_system, "apply_morale_change"):
                # Losing pieces reduces morale
                morale_impact = material_change * 0.7  # 0.7 morale per material point lost
                
                morale_system.apply_morale_change(
                    character,
                    morale_impact,
                    "lost_piece",
                    match_context
                )
    
    def apply_counterattack_stamina_cost(self, character: Dict[str, Any], damage_dealt: float,
                                       match_context: Dict[str, Any]) -> None:
        """Apply stamina cost for counterattacks
        
        Args:
            character: The character counterattacking
            damage_dealt: The damage dealt by the counterattack
            match_context: The current match context
        """
        # Get base cost from stamina config
        action_costs = self.stamina_system.stamina_config.get("action_costs", {})
        base_cost = action_costs.get("counter_attack", 2.5)
        
        # Scale cost with damage
        scaled_cost = base_cost * (1 + (damage_dealt / 20))  # +5% per point of damage
        
        # Apply the cost
        self.stamina_system.apply_stamina_cost(
            character,
            scaled_cost,
            "counter_attack",
            match_context
        )
    
    def apply_dodging_stamina_cost(self, character: Dict[str, Any], attack_power: float,
                                 match_context: Dict[str, Any]) -> None:
        """Apply stamina cost for dodging attacks
        
        Args:
            character: The character dodging
            attack_power: The power of the attack being dodged
            match_context: The current match context
        """
        # Get base cost from stamina config
        action_costs = self.stamina_system.stamina_config.get("action_costs", {})
        base_cost = action_costs.get("dodging", 1.5)
        
        # Scale cost with attack power
        scaled_cost = base_cost * (1 + (attack_power / 30))  # +3.3% per point of attack power
        
        # Apply the cost
        self.stamina_system.apply_stamina_cost(
            character,
            scaled_cost,
            "dodging",
            match_context
        )
    
    def modify_critical_chance(self, character: Dict[str, Any], base_chance: float,
                             match_context: Dict[str, Any]) -> float:
        """Modify critical hit chance based on stamina
        
        Args:
            character: The character attacking
            base_chance: The base critical chance
            match_context: The current match context
            
        Returns:
            Modified critical chance
        """
        # Get character's stamina
        stamina = character.get("stamina", 0)
        
        # Calculate modifier based on stamina thresholds
        modifier = 1.0
        
        if stamina <= 20:
            # Severe fatigue: -40% critical chance
            modifier = 0.6
        elif stamina <= 40:
            # Moderate fatigue: -25% critical chance
            modifier = 0.75
        elif stamina <= 60:
            # Minor fatigue: -10% critical chance
            modifier = 0.9
        
        # Apply modifier
        modified_chance = base_chance * modifier
        
        return modified_chance
    
    def check_ko_from_exhaustion(self, character: Dict[str, Any], 
                               match_context: Dict[str, Any]) -> Tuple[bool, str]:
        """Check if a character should be KO'd due to complete exhaustion
        
        Args:
            character: The character to check
            match_context: The current match context
            
        Returns:
            (bool, str): Whether the character should be KO'd and reason
        """
        # Check if character is at extremely low stamina (below 5%)
        if character.get("stamina", 0) <= 5:
            # Roll for KO chance - 25% chance at 5 stamina, 100% chance at 0 stamina
            ko_chance = 0.25 + ((5 - character.get("stamina", 0)) / 5 * 0.75)
            
            roll = random.random()
            should_ko = roll < ko_chance
            
            if should_ko:
                reason = f"Character exhausted - collapsed from extreme fatigue (stamina: {character.get('stamina', 0)})"
                
                # Emit event
                if self.event_system:
                    self.event_system.emit({
                        "type": "stamina_exhaustion_ko",
                        "character_id": character.get("id", "unknown"),
                        "character_name": character.get("name", "Unknown"),
                        "stamina": character.get("stamina", 0),
                        "ko_chance": ko_chance,
                        "reason": reason,
                        "match_id": match_context.get("match_id", "unknown"),
                        "turn": match_context.get("round", 0)
                    })
                
                # Set character as KO'd
                character["is_ko"] = True
                
                return True, reason
                
        return False, "Character has sufficient stamina"


# Example integration usage
def integrate_stamina_combat_systems(registry):
    """Example of integrating stamina and combat systems"""
    integration = StaminaCombatIntegration(registry)
    
    # Perform the integration
    integration.integrate_systems()
    
    return integration
