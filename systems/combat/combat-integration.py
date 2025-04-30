"""
CombatStaminaIntegrator

This module implements the integration between the Stamina System and the Combat System
for the META Fantasy League Simulator v5.0.

It provides functions for:
- Applying stamina-based modifiers to damage calculations
- Adjusting combat effectiveness based on stamina levels
- Managing combat-related stamina costs
"""

import logging
import math
from typing import Dict, Any, List, Tuple, Optional
from system_base import SystemBase


class CombatStaminaIntegrator(SystemBase):
    """
    Integration class between Combat System and Stamina System.
    
    This class handles all interactions between combat mechanics and stamina:
    - Applying stamina-based damage modifiers
    - Adjusting combat effectiveness based on fatigue levels
    - Managing stamina costs for combat actions
    """
    
    def __init__(self, config, registry):
        """Initialize the combat-stamina integrator"""
        super().__init__("combat_stamina_integrator", registry, config)
        self.logger = logging.getLogger("COMBAT_STAMINA_INTEGRATOR")
        self.combat_system = None
        self.stamina_system = None
        
    def _activate_implementation(self):
        """Activate the integrator by connecting to required systems"""
        # Get required systems from registry
        self.combat_system = self.registry.get("combat_system")
        if not self.combat_system:
            raise ValueError("Combat system is required but not available in the registry")
            
        self.stamina_system = self.registry.get("stamina_system")
        if not self.stamina_system:
            raise ValueError("Stamina system is required but not available in the registry")
            
        # Load combat stamina configuration
        self._load_combat_stamina_config()
        
        # Register with combat system's hooks
        if hasattr(self.combat_system, "register_damage_modifier"):
            self.combat_system.register_damage_modifier(self.modify_damage_taken)
            
        if hasattr(self.combat_system, "register_attack_modifier"):
            self.combat_system.register_attack_modifier(self.modify_attack_effectiveness)
            
        if hasattr(self.combat_system, "register_critical_modifier"):
            self.combat_system.register_critical_modifier(self.modify_critical_chance)
            
        if hasattr(self.combat_system, "register_post_damage_hook"):
            self.combat_system.register_post_damage_hook(self.apply_combat_stamina_cost)
            
        self.logger.info("Combat-Stamina integrator activated successfully")
        
    def _load_combat_stamina_config(self):
        """Load combat stamina configuration"""
        stamina_config_path = self.config.get(
            "paths.stamina_integration_config", 
            "config/stamina_integration_config.json"
        )
        
        try:
            import json
            with open(stamina_config_path, 'r') as f:
                config_data = json.load(f)
                self.stamina_config = config_data.get("combat", {})
                if not self.stamina_config:
                    raise ValueError("No combat configuration found in stamina integration config")
        except Exception as e:
            self.logger.warning(f"Failed to load stamina integration config: {e}")
            # Use default configuration
            self.stamina_config = {
                "damage_taken_multipliers": {
                    "60": 1.05,  # 5% more damage at minor fatigue
                    "40": 1.15,  # 15% more damage at moderate fatigue
                    "20": 1.30   # 30% more damage at severe fatigue
                },
                "attack_effectiveness": {
                    "60": 0.95,  # 95% effectiveness at minor fatigue
                    "40": 0.85,  # 85% effectiveness at moderate fatigue 
                    "20": 0.70   # 70% effectiveness at severe fatigue
                },
                "critical_chance_modifiers": {
                    "60": 0.9,   # 90% of normal crit chance at minor fatigue
                    "40": 0.7,   # 70% of normal crit chance at moderate fatigue
                    "20": 0.4    # 40% of normal crit chance at severe fatigue
                },
                "stamina_costs": {
                    "attack": 1.0,
                    "defense": 0.5,
                    "counter": 1.5,
                    "critical": 2.0,
                    "dodge": 2.0,
                    "per_damage_point": 0.05  # Additional cost per point of damage taken
                }
            }
            
    def modify_damage_taken(self, character: Dict[str, Any], damage: float, 
                           damage_type: str, match_context: Dict[str, Any]) -> float:
        """
        Modify damage taken based on character's stamina level.
        
        Args:
            character: Character taking damage
            damage: Base damage amount
            damage_type: Type of damage being dealt
            match_context: Current match context
            
        Returns:
            Modified damage amount
        """
        # Get current stamina
        current_stamina = character.get("stamina", 100)
        
        # Default multiplier = no change
        multiplier = 1.0
        
        # Apply stamina-based damage multipliers
        thresholds = sorted([int(t) for t in self.stamina_config["damage_taken_multipliers"].keys()], 
                           reverse=False)
        
        for threshold in thresholds:
            if current_stamina <= threshold:
                multiplier = self.stamina_config["damage_taken_multipliers"][str(threshold)]
                
        # Apply the multiplier
        modified_damage = damage * multiplier
        
        # Log significant modifications
        if abs(modified_damage - damage) > 1.0:
            self.logger.debug(f"Damage modified for {character.get('name', 'Unknown')}: " +
                             f"{damage:.1f} -> {modified_damage:.1f} due to stamina level {current_stamina:.1f}")
            
        return modified_damage
        
    def modify_attack_effectiveness(self, attacker: Dict[str, Any], target: Dict[str, Any],
                                   base_effectiveness: float, match_context: Dict[str, Any]) -> float:
        """
        Modify attack effectiveness based on attacker's stamina level.
        
        Args:
            attacker: Character performing the attack
            target: Target of the attack
            base_effectiveness: Base attack effectiveness
            match_context: Current match context
            
        Returns:
            Modified attack effectiveness
        """
        # Get current stamina
        current_stamina = attacker.get("stamina", 100)
        
        # Default modifier = no change
        modifier = 1.0
        
        # Apply stamina-based effectiveness modifiers
        thresholds = sorted([int(t) for t in self.stamina_config["attack_effectiveness"].keys()], 
                           reverse=False)
        
        for threshold in thresholds:
            if current_stamina <= threshold:
                modifier = self.stamina_config["attack_effectiveness"][str(threshold)]
                
        # Apply the modifier
        modified_effectiveness = base_effectiveness * modifier
        
        # Log significant modifications
        if abs(modified_effectiveness - base_effectiveness) > 0.1:
            self.logger.debug(f"Attack effectiveness modified for {attacker.get('name', 'Unknown')}: " +
                             f"{base_effectiveness:.2f} -> {modified_effectiveness:.2f} due to stamina level {current_stamina:.1f}")
            
        return modified_effectiveness
        
    def modify_critical_chance(self, character: Dict[str, Any], base_chance: float, 
                              attack_type: str, match_context: Dict[str, Any]) -> float:
        """
        Modify critical hit chance based on character's stamina level.
        
        Args:
            character: Character attempting critical hit
            base_chance: Base critical hit chance
            attack_type: Type of attack being performed
            match_context: Current match context
            
        Returns:
            Modified critical hit chance
        """
        # Get current stamina
        current_stamina = character.get("stamina", 100)
        
        # Default modifier = no change
        modifier = 1.0
        
        # Apply stamina-based critical chance modifiers
        thresholds = sorted([int(t) for t in self.stamina_config["critical_chance_modifiers"].keys()], 
                           reverse=False)
        
        for threshold in thresholds:
            if current_stamina <= threshold:
                modifier = self.stamina_config["critical_chance_modifiers"][str(threshold)]
                
        # Apply the modifier
        modified_chance = base_chance * modifier
        
        # Log significant modifications
        if abs(modified_chance - base_chance) > 0.05:
            self.logger.debug(f"Critical chance modified for {character.get('name', 'Unknown')}: " +
                             f"{base_chance:.2f} -> {modified_chance:.2f} due to stamina level {current_stamina:.1f}")
            
        return modified_chance
        
    def apply_combat_stamina_cost(self, attacker: Optional[Dict[str, Any]], target: Dict[str, Any],
                                 damage: float, attack_data: Dict[str, Any], match_context: Dict[str, Any]) -> None:
        """
        Apply stamina costs for combat actions.
        
        Args:
            attacker: Character performing the attack (None for environment damage)
            target: Character receiving damage
            damage: Amount of damage dealt
            attack_data: Data about the attack
            match_context: Current match context
        """
        # Apply costs to attacker if present
        if attacker:
            # Get base cost for attack type
            attack_type = attack_data.get("type", "attack")
            base_cost = self.stamina_config["stamina_costs"].get(attack_type, 
                                                                self.stamina_config["stamina_costs"]["attack"])
            
            # Add cost for critical hits
            if attack_data.get("is_critical", False):
                base_cost += self.stamina_config["stamina_costs"]["critical"]
                
            # Apply the cost
            self.stamina_system.apply_stamina_cost(
                attacker,
                base_cost,
                f"combat_action:{attack_type}",
                match_context
            )
            
        # Apply costs to target
        # Base cost for defense
        defense_type = attack_data.get("defense_type", "defense")
        base_defense_cost = self.stamina_config["stamina_costs"].get(defense_type,
                                                                   self.stamina_config["stamina_costs"]["defense"])
        
        # Add cost based on damage taken
        damage_cost = damage * self.stamina_config["stamina_costs"]["per_damage_point"]
        
        # Apply the cost
        self.stamina_system.apply_stamina_cost(
            target,
            base_defense_cost + damage_cost,
            f"combat_defense:{defense_type}",
            match_context
        )
        
        # Log the costs
        if attacker:
            self.logger.debug(f"Applied stamina cost {base_cost:.1f} to {attacker.get('name', 'Unknown')} for attack")
        self.logger.debug(f"Applied stamina cost {base_defense_cost + damage_cost:.1f} to {target.get('name', 'Unknown')} for defense")
        
    def check_resignation(self, character: Dict[str, Any], match_context: Dict[str, Any]) -> bool:
        """
        Check if a character resigns due to stamina exhaustion.
        
        Args:
            character: Character to check
            match_context: Current match context
            
        Returns:
            True if character resigns, False otherwise
        """
        # Get current stamina
        current_stamina = character.get("stamina", 100)
        
        # Only check for severe fatigue
        if current_stamina > 20:
            return False
            
        # Get resignation chance
        import random
        resignation_chance = 0.05  # 5% chance per round at severe fatigue
        
        # Check for resignation
        if random.random() < resignation_chance:
            self.logger.info(f"{character.get('name', 'Unknown')} resigns due to stamina exhaustion")
            
            # Mark character as resigned
            character["is_ko"] = True
            character["ko_reason"] = "stamina_exhaustion"
            
            # Emit event if event system is available
            event_system = self.registry.get("event_system")
            if event_system and hasattr(event_system, "emit"):
                event_system.emit({
                    "type": "character_resignation",
                    "character_id": character.get("id", "unknown"),
                    "character_name": character.get("name", "Unknown"),
                    "team_id": character.get("team_id", "unknown"),
                    "reason": "stamina_exhaustion",
                    "stamina": current_stamina,
                    "match_id": match_context.get("match_id", "unknown"),
                    "round": match_context.get("round", 0)
                })
                
            return True
            
        return False
