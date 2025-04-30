"""
ConvergenceStaminaIntegrator

This module implements the integration between the Stamina System and the Convergence System
for the META Fantasy League Simulator v5.0.

It provides functions for:
- Applying stamina costs to convergence initiators and targets
- Modifying convergence effectiveness based on stamina levels
- Providing stamina-based convergence chance modifiers
"""

import logging
import random
from typing import Dict, Any, List, Tuple, Optional
from system_base import SystemBase


class ConvergenceStaminaIntegrator(SystemBase):
    """
    Integration class between Convergence System and Stamina System.
    
    This class handles all interactions between convergences and stamina:
    - Determining stamina costs for convergence participation
    - Applying stamina-based modifiers to convergence chances
    - Modifying convergence effectiveness based on stamina levels
    """
    
    def __init__(self, config, registry):
        """Initialize the convergence-stamina integrator"""
        super().__init__("convergence_stamina_integrator", registry, config)
        self.logger = logging.getLogger("CONVERGENCE_STAMINA_INTEGRATOR")
        self.convergence_system = None
        self.stamina_system = None
        
    def _activate_implementation(self):
        """Activate the integrator by connecting to required systems"""
        # Get required systems from registry
        self.convergence_system = self.registry.get("convergence_system")
        if not self.convergence_system:
            raise ValueError("Convergence system is required but not available in the registry")
            
        self.stamina_system = self.registry.get("stamina_system")
        if not self.stamina_system:
            raise ValueError("Stamina system is required but not available in the registry")
            
        # Load convergence stamina configuration
        self._load_convergence_stamina_config()
        
        # Register with convergence system's hooks
        if hasattr(self.convergence_system, "register_pre_convergence_hook"):
            self.convergence_system.register_pre_convergence_hook(self.pre_convergence_check)
            
        if hasattr(self.convergence_system, "register_post_convergence_hook"):
            self.convergence_system.register_post_convergence_hook(self.post_convergence_process)
            
        # Register convergence chance modifier
        if hasattr(self.convergence_system, "register_chance_modifier"):
            self.convergence_system.register_chance_modifier(self.modify_convergence_chance)
            
        # Register convergence damage modifier
        if hasattr(self.convergence_system, "register_damage_modifier"):
            self.convergence_system.register_damage_modifier(self.modify_convergence_damage)
            
        self.logger.info("Convergence-Stamina integrator activated successfully")
        
    def _load_convergence_stamina_config(self):
        """Load convergence stamina configuration"""
        stamina_config_path = self.config.get(
            "paths.stamina_integration_config", 
            "config/stamina_integration_config.json"
        )
        
        try:
            import json
            with open(stamina_config_path, 'r') as f:
                config_data = json.load(f)
                self.stamina_config = config_data.get("convergence", {})
                if not self.stamina_config:
                    raise ValueError("No convergence configuration found in stamina integration config")
        except Exception as e:
            self.logger.warning(f"Failed to load stamina integration config: {e}")
            # Use default configuration
            self.stamina_config = {
                "costs": {
                    "initiator": 5.0,
                    "target": 3.0,
                    "assist": 2.0,
                    "defense": 4.0
                },
                "threshold_modifiers": {
                    "chance": {
                        "60": 0.9,  # 90% of normal chance at minor fatigue
                        "40": 0.7,  # 70% of normal chance at moderate fatigue
                        "20": 0.4   # 40% of normal chance at severe fatigue
                    },
                    "damage": {
                        "60": 0.9,  # 90% of normal damage at minor fatigue
                        "40": 0.75, # 75% of normal damage at moderate fatigue
                        "20": 0.5   # 50% of normal damage at severe fatigue
                    },
                    "defense": {
                        "60": 0.9,  # 90% of normal defense at minor fatigue
                        "40": 0.75, # 75% of normal defense at moderate fatigue
                        "20": 0.5   # 50% of normal defense at severe fatigue
                    }
                },
                "leadership_stamina_factor": 0.5  # How much leadership affects stamina costs
            }
            
    def pre_convergence_check(self, initiator: Dict[str, Any], target: Dict[str, Any], 
                             assists: List[Dict[str, Any]], match_context: Dict[str, Any]) -> bool:
        """
        Check if a convergence can proceed based on stamina levels.
        
        Args:
            initiator: Character initiating the convergence
            target: Target character
            assists: List of assisting characters
            match_context: Current match context
            
        Returns:
            True if convergence can proceed, False otherwise
        """
        # Check initiator's stamina
        initiator_cost = self.calculate_convergence_stamina_cost(initiator, "initiator")
        if initiator.get("stamina", 0) < initiator_cost:
            self.logger.info(f"Convergence blocked: {initiator.get('name', 'Unknown')} has insufficient stamina ({initiator.get('stamina', 0):.1f}/{initiator_cost:.1f})")
            return False
            
        # All checks passed
        return True
        
    def post_convergence_process(self, convergence_result: Dict[str, Any], match_context: Dict[str, Any]) -> None:
        """
        Apply stamina costs after a convergence is processed.
        
        Args:
            convergence_result: Result data from the convergence
            match_context: Current match context
        """
        # Extract characters from result
        initiator = convergence_result.get("initiator")
        target = convergence_result.get("target")
        assists = convergence_result.get("assists", [])
        
        # Apply costs to each participant
        if initiator:
            cost = self.calculate_convergence_stamina_cost(initiator, "initiator")
            self.stamina_system.apply_stamina_cost(
                initiator, 
                cost, 
                "convergence_initiate", 
                match_context
            )
            
        if target:
            cost = self.calculate_convergence_stamina_cost(target, "target")
            self.stamina_system.apply_stamina_cost(
                target, 
                cost, 
                "convergence_target", 
                match_context
            )
            
        for assistant in assists:
            cost = self.calculate_convergence_stamina_cost(assistant, "assist")
            self.stamina_system.apply_stamina_cost(
                assistant, 
                cost, 
                "convergence_assist", 
                match_context
            )
            
        # Log the costs
        self.logger.debug(f"Applied stamina costs for convergence {convergence_result.get('id', 'unknown')}")
        
    def calculate_convergence_stamina_cost(self, character: Dict[str, Any], role: str) -> float:
        """
        Calculate the stamina cost for a character's participation in a convergence.
        
        Args:
            character: Character data dictionary
            role: Role in convergence ('initiator', 'target', 'assist', or 'defense')
            
        Returns:
            Calculated stamina cost
        """
        # Get base cost for the role
        base_cost = self.stamina_config["costs"].get(role, 5.0)
        
        # Apply leadership modifier if available
        if "aLDR" in character:
            # Higher leadership reduces stamina cost for initiator and assists
            if role in ["initiator", "assist"]:
                leadership_mod = 1.0 - (max(0, character["aLDR"] - 50) / 200.0 * 
                                       self.stamina_config["leadership_stamina_factor"])
                base_cost *= max(0.5, leadership_mod)  # Cap at 50% reduction
                
        # Apply willpower modifier if available
        if "aWIL" in character:
            # Higher willpower reduces stamina cost for all roles
            willpower_mod = 1.0 - (max(0, character["aWIL"] - 50) / 200.0 * 0.5)
            base_cost *= max(0.7, willpower_mod)  # Cap at 30% reduction
            
        # Round to 1 decimal place
        return round(base_cost, 1)
        
    def modify_convergence_chance(self, initiator: Dict[str, Any], target: Dict[str, Any], 
                                 base_chance: float, match_context: Dict[str, Any]) -> float:
        """
        Modify convergence chance based on stamina levels.
        
        Args:
            initiator: Character initiating the convergence
            target: Target character
            base_chance: Base convergence chance
            match_context: Current match context
            
        Returns:
            Modified convergence chance
        """
        # Get stamina levels
        initiator_stamina = initiator.get("stamina", 100)
        
        # Get applicable modifier based on stamina thresholds
        chance_mod = 1.0  # Default = no modification
        
        # Apply initiator stamina threshold modifiers
        thresholds = sorted([int(t) for t in self.stamina_config["threshold_modifiers"]["chance"].keys()], 
                           reverse=False)
        
        for threshold in thresholds:
            if initiator_stamina <= threshold:
                chance_mod = self.stamina_config["threshold_modifiers"]["chance"][str(threshold)]
                
        # Apply the modifier
        modified_chance = base_chance * chance_mod
        
        # Log significant modifications
        if abs(modified_chance - base_chance) > 0.1:
            self.logger.debug(f"Convergence chance modified: {base_chance:.2f} -> {modified_chance:.2f} due to stamina")
            
        return modified_chance
        
    def modify_convergence_damage(self, initiator: Dict[str, Any], target: Dict[str, Any], 
                                base_damage: float, match_context: Dict[str, Any]) -> float:
        """
        Modify convergence damage based on stamina levels.
        
        Args:
            initiator: Character initiating the convergence
            target: Target character
            base_damage: Base convergence damage
            match_context: Current match context
            
        Returns:
            Modified convergence damage
        """
        # Get stamina levels
        initiator_stamina = initiator.get("stamina", 100)
        target_stamina = target.get("stamina", 100)
        
        # Get applicable modifier based on stamina thresholds
        damage_mod = 1.0  # Default = no modification
        defense_mod = 1.0  # Default = no modification
        
        # Apply initiator stamina threshold modifiers (for damage)
        thresholds = sorted([int(t) for t in self.stamina_config["threshold_modifiers"]["damage"].keys()], 
                           reverse=False)
        
        for threshold in thresholds:
            if initiator_stamina <= threshold:
                damage_mod = self.stamina_config["threshold_modifiers"]["damage"][str(threshold)]
                
        # Apply target stamina threshold modifiers (for defense)
        thresholds = sorted([int(t) for t in self.stamina_config["threshold_modifiers"]["defense"].keys()], 
                           reverse=False)
        
        for threshold in thresholds:
            if target_stamina <= threshold:
                defense_mod = self.stamina_config["threshold_modifiers"]["defense"][str(threshold)]
                
        # Calculate final damage
        # Lower defense modifier means LESS defense, so we invert it
        final_damage = base_damage * damage_mod * (2.0 - defense_mod)
        
        # Log significant modifications
        if abs(final_damage - base_damage) > 1.0:
            self.logger.debug(f"Convergence damage modified: {base_damage:.1f} -> {final_damage:.1f} due to stamina")
            
        return final_damage
