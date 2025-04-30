"""
META Fantasy League Simulator - Stamina-Convergence System Integration
=====================================================================

This module implements the integration between the Stamina System
and the Convergence System, ensuring that convergence interactions
properly affect stamina and are affected by stamina levels.
"""

import logging
import random
import math
from typing import Dict, List, Any, Optional, Tuple, Union

# Import required system components
from system_base import SystemBase

class StaminaConvergenceIntegration:
    """Integrates stamina system with convergence system"""
    
    def __init__(self, registry):
        """Initialize the integration"""
        self.registry = registry
        self.logger = logging.getLogger("StaminaConvergenceIntegration")
        
        # Get required systems
        self.stamina_system = registry.get("stamina_system")
        if not self.stamina_system:
            raise ValueError("Stamina system not available in registry")
        
        self.convergence_system = registry.get("convergence_system")
        if not self.convergence_system:
            raise ValueError("Convergence system not available in registry")
        
        # Get event system if available
        self.event_system = registry.get("event_system")
        if not self.event_system:
            self.logger.warning("Event system not available, event emission disabled")
    
    def integrate_systems(self):
        """Integrate the systems by registering hooks and callbacks"""
        self.logger.info("Integrating stamina and convergence systems")
        
        # Register convergence check in convergence system
        if hasattr(self.convergence_system, "register_convergence_check"):
            self.convergence_system.register_convergence_check(self.check_convergence_availability)
            self.logger.info("Registered stamina-based convergence check")
        else:
            self.logger.warning("Convergence system does not support convergence check registration")
        
        # Register cost calculation in convergence system
        if hasattr(self.convergence_system, "register_cost_calculator"):
            self.convergence_system.register_cost_calculator(self.calculate_convergence_cost)
            self.logger.info("Registered stamina cost calculator for convergence")
        else:
            self.logger.warning("Convergence system does not support cost calculator registration")
        
        # Register post-convergence handler
        if hasattr(self.convergence_system, "register_post_convergence_handler"):
            self.convergence_system.register_post_convergence_handler(self.handle_post_convergence)
            self.logger.info("Registered post-convergence stamina handler")
        else:
            self.logger.warning("Convergence system does not support post-convergence handler registration")
        
        return True
    
    def check_convergence_availability(self, character: Dict[str, Any], target_character: Dict[str, Any],
                                     match_context: Dict[str, Any]) -> Tuple[bool, str]:
        """Check if a character can participate in a convergence based on stamina
        
        Args:
            character: The character initiating the convergence
            target_character: The target character of the convergence
            match_context: The current match context
            
        Returns:
            (bool, str): Whether convergence is allowed and reason if not
        """
        # Get convergence costs
        initiator_cost = self.calculate_convergence_cost(character, target_character, "assist", match_context)
        
        # Check if initiator has enough stamina
        initiator_stamina = character.get("stamina", 0)
        if initiator_stamina < initiator_cost:
            reason = f"Insufficient stamina for convergence: {initiator_stamina} < {initiator_cost}"
            
            # Emit event if event system available
            if self.event_system:
                self.event_system.emit({
                    "type": "convergence_blocked",
                    "character_id": character.get("id", "unknown"),
                    "target_id": target_character.get("id", "unknown"),
                    "reason": reason,
                    "stamina": initiator_stamina,
                    "required_stamina": initiator_cost,
                    "match_id": match_context.get("match_id", "unknown"),
                    "turn": match_context.get("round", 0)
                })
                
            return False, reason
        
        # Check for severe fatigue which blocks convergence
        if any(effect.startswith("stamina:severe_fatigue") for effect in character.get("effects", [])):
            reason = "Character is too fatigued to initiate convergence"
            
            # Emit event
            if self.event_system:
                self.event_system.emit({
                    "type": "convergence_blocked",
                    "character_id": character.get("id", "unknown"),
                    "target_id": target_character.get("id", "unknown"),
                    "reason": reason,
                    "stamina": initiator_stamina,
                    "match_id": match_context.get("match_id", "unknown"),
                    "turn": match_context.get("round", 0)
                })
                
            return False, reason
            
        # Check target character if they have enough stamina to handle the convergence
        target_cost = self.calculate_convergence_cost(target_character, character, "target", match_context)
        target_stamina = target_character.get("stamina", 0)
        
        # For targets, we don't block convergence but reduce its effectiveness if they're low on stamina
        # This is handled in the post-convergence process
        
        return True, "Sufficient stamina for convergence"
    
    def calculate_convergence_cost(self, character: Dict[str, Any], other_character: Dict[str, Any],
                                 role: str, match_context: Dict[str, Any]) -> float:
        """Calculate the stamina cost for a convergence interaction
        
        Args:
            character: The character involved in the convergence
            other_character: The other character in the convergence
            role: 'assist' for initiator, 'target' for target
            match_context: The current match context
            
        Returns:
            The stamina cost
        """
        # Get base costs from stamina config
        action_costs = self.stamina_system.stamina_config.get("action_costs", {})
        
        if role == "assist":
            base_cost = action_costs.get("convergence_assist", 3.0)
        else:  # target
            base_cost = action_costs.get("convergence_target", 5.0)
        
        # Apply character attribute modifiers
        # Characters with high LDR have more efficient convergence (initiator)
        # Characters with high RES resist convergence effects better (target)
        attribute_modifier = 1.0
        
        if role == "assist" and "aLDR" in character:
            # 5% reduction per 10 points of LDR above 50
            ldr_bonus = max(0, (character["aLDR"] - 50) / 200)
            attribute_modifier = max(0.7, 1.0 - ldr_bonus)  # Cap at 30% reduction
        elif role == "target" and "aRES" in character:
            # 5% reduction per 10 points of RES above 50
            res_bonus = max(0, (character["aRES"] - 50) / 200)
            attribute_modifier = max(0.7, 1.0 - res_bonus)  # Cap at 30% reduction
        
        # Apply stamina cost modifiers from traits if available
        stamina_trait_integration = self.registry.get("stamina_trait_integration")
        if stamina_trait_integration:
            trait_modifier = stamina_trait_integration.get_stamina_cost_modifier(character)
            attribute_modifier *= trait_modifier
        
        # Calculate round-based scaling (convergences get more costly in later rounds)
        round_number = match_context.get("round", 1)
        round_scaling = min(1.0 + ((round_number - 1) * 0.03), 1.3)  # Max 30% increase
        
        # Calculate final cost
        final_cost = base_cost * attribute_modifier * round_scaling
        
        # Round to one decimal place
        return round(final_cost, 1)
    
    def apply_convergence_costs(self, convergence: Dict[str, Any], match_context: Dict[str, Any]) -> bool:
        """Apply stamina costs for a convergence
        
        Args:
            convergence: The convergence details including initiator and target
            match_context: The current match context
            
        Returns:
            True if costs were applied, False otherwise
        """
        initiator = convergence.get("initiator")
        target = convergence.get("target")
        
        if not initiator or not target:
            self.logger.warning("Cannot apply convergence costs: missing initiator or target")
            return False
        
        # Calculate and apply costs
        initiator_cost = self.calculate_convergence_cost(initiator, target, "assist", match_context)
        target_cost = self.calculate_convergence_cost(target, initiator, "target", match_context)
        
        # Apply costs
        convergence_id = convergence.get("id", f"c_{random.randint(1000, 9999)}")
        
        # Apply to initiator
        self.stamina_system.apply_stamina_cost(
            initiator,
            initiator_cost,
            f"convergence_assist:{convergence_id}",
            match_context
        )
        
        # Apply to target
        self.stamina_system.apply_stamina_cost(
            target,
            target_cost,
            f"convergence_target:{convergence_id}",
            match_context
        )
        
        # Add stamina costs to convergence for reference
        convergence["stamina_costs"] = {
            "initiator": initiator_cost,
            "target": target_cost
        }
        
        return True
    
    def calculate_convergence_effectiveness(self, convergence: Dict[str, Any], match_context: Dict[str, Any]) -> float:
        """Calculate the effectiveness of a convergence based on stamina levels
        
        Args:
            convergence: The convergence details
            match_context: The current match context
            
        Returns:
            Effectiveness multiplier (0.0 to 1.0)
        """
        initiator = convergence.get("initiator")
        target = convergence.get("target")
        
        if not initiator or not target:
            return 0.0
        
        # Base effectiveness starts at 100%
        effectiveness = 1.0
        
        # Reduce effectiveness based on initiator's stamina level
        initiator_stamina = initiator.get("stamina", 0)
        if initiator_stamina <= 20:
            # Severe fatigue: 50% effectiveness
            effectiveness *= 0.5
        elif initiator_stamina <= 40:
            # Moderate fatigue: 75% effectiveness
            effectiveness *= 0.75
        elif initiator_stamina <= 60:
            # Minor fatigue: 90% effectiveness
            effectiveness *= 0.9
        
        # Target's resistance also affects effectiveness
        target_stamina = target.get("stamina", 0)
        if target_stamina <= 20:
            # At severe fatigue, target is more vulnerable (effectiveness increased)
            effectiveness *= 1.2
        elif target_stamina <= 40:
            # At moderate fatigue, target is somewhat vulnerable
            effectiveness *= 1.1
        
        # Cap effectiveness between 30% and 120%
        return max(0.3, min(effectiveness, 1.2))
    
    def handle_post_convergence(self, convergence: Dict[str, Any], match_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle post-convergence processing for stamina effects
        
        Args:
            convergence: The convergence details
            match_context: The current match context
            
        Returns:
            Updated convergence details
        """
        # Apply stamina costs
        self.apply_convergence_costs(convergence, match_context)
        
        # Calculate effectiveness
        effectiveness = self.calculate_convergence_effectiveness(convergence, match_context)
        
        # Update convergence with effectiveness
        convergence["effectiveness"] = effectiveness
        
        # Emit detailed event
        if self.event_system:
            initiator = convergence.get("initiator", {})
            target = convergence.get("target", {})
            
            self.event_system.emit({
                "type": "convergence_stamina_impact",
                "convergence_id": convergence.get("id", "unknown"),
                "initiator_id": initiator.get("id", "unknown"),
                "target_id": target.get("id", "unknown"),
                "initiator_stamina": initiator.get("stamina", 0),
                "target_stamina": target.get("stamina", 0),
                "effectiveness": effectiveness,
                "stamina_costs": convergence.get("stamina_costs", {}),
                "match_id": match_context.get("match_id", "unknown"),
                "turn": match_context.get("round", 0)
            })
        
        return convergence
    
    def apply_post_round_convergence_recovery(self, character: Dict[str, Any], match_context: Dict[str, Any]):
        """Apply special stamina recovery after convergence participation
        
        Args:
            character: The character to process
            match_context: The current match context
        """
        # Check if character participated in convergence this round
        round_logs = [log for log in character.get("stamina_log", []) 
                     if log.get("turn") == match_context.get("round")
                     and ("convergence_assist" in log.get("reason", "") 
                          or "convergence_target" in log.get("reason", ""))]
        
        if not round_logs:
            return  # No convergence this round
        
        # Characters get a small stamina boost after convergence due to adrenaline
        recovery_amount = 2.0  # Base recovery amount
        
        # Scale with leadership for initiators, resistance for targets
        if "convergence_assist" in round_logs[0].get("reason", ""):
            # Initiator recovery
            if "aLDR" in character:
                # Higher leadership = better recovery
                recovery_amount += (character["aLDR"] - 50) * 0.05  # +0.5 per 10 points above 50
        else:
            # Target recovery
            if "aRES" in character:
                # Higher resistance = better recovery
                recovery_amount += (character["aRES"] - 50) * 0.05  # +0.5 per 10 points above 50
        
        # Apply recovery (add to end of round recovery)
        # Note: This doesn't directly apply the recovery, just adds the bonus
        # The regular stamina system will apply recovery at end of round
        
        if "convergence_recovery_bonus" not in character:
            character["convergence_recovery_bonus"] = 0
            
        character["convergence_recovery_bonus"] += max(0, recovery_amount)
        
        # Log the bonus
        self.logger.debug(
            f"Character {character.get('name')} gets +{recovery_amount} stamina "
            f"recovery bonus from convergence"
        )


# Example integration usage
def integrate_stamina_convergence_systems(registry):
    """Example of integrating stamina and convergence systems"""
    integration = StaminaConvergenceIntegration(registry)
    
    # Perform the integration
    integration.integrate_systems()
    
    return integration
