"""
Morale system for META League Simulator
"""

from typing import Dict, Any, Optional
from ..models.character import Character

class MoraleSystem:
    """System for managing morale effects"""
    
    def calculate_morale_modifiers(self, morale: float) -> Dict[str, Any]:
        """Calculate modifiers based on morale level"""
        # High morale
        if morale >= 80:
            return {
                "attribute_bonus": 1,     # +1 to all attributes
                "stamina_regen": 1.2,     # 20% better stamina regen
                "combat_bonus": 10,       # +10 to combat rolls
                "damage_reduction": 10,   # 10% damage reduction
                "healing_modifier": 1.2   # 20% better healing
            }
        # Good morale
        elif morale >= 60:
            return {
                "attribute_bonus": 0.5,   # +0.5 to all attributes
                "stamina_regen": 1.1,     # 10% better stamina regen
                "combat_bonus": 5,        # +5 to combat rolls
                "damage_reduction": 5,    # 5% damage reduction
                "healing_modifier": 1.1   # 10% better healing
            }
        # Neutral morale
        elif morale >= 40:
            return {
                "attribute_bonus": 0,     # No attribute change
                "stamina_regen": 1.0,     # Normal stamina regen
                "combat_bonus": 0,        # No combat bonus
                "damage_reduction": 0,    # No damage reduction
                "healing_modifier": 1.0   # Normal healing
            }
        # Low morale
        elif morale >= 20:
            return {
                "attribute_bonus": -0.5,  # -0.5 to all attributes
                "stamina_regen": 0.9,     # 10% worse stamina regen
                "combat_bonus": -5,       # -5 to combat rolls
                "damage_reduction": -5,   # 5% damage increase
                "healing_modifier": 0.9   # 10% worse healing
            }
        # Very low morale
        else:
            return {
                "attribute_bonus": -1.0,  # -1 to all attributes
                "stamina_regen": 0.8,     # 20% worse stamina regen
                "combat_bonus": -10,      # -10 to combat rolls
                "damage_reduction": -10,  # 10% damage increase
                "healing_modifier": 0.8   # 20% worse healing
            }
    
    def update_morale(self, character: Character, event: str, magnitude: Optional[float] = None) -> float:
        """Update character morale based on game events"""
        current_morale = character.morale
        morale_change = 0
        
        # Different events affect morale differently
        if event == "victory":
            morale_change = 10
        elif event == "defeat":
            morale_change = -5
        elif event == "draw":
            morale_change = 2
        elif event == "teammate_ko":
            morale_change = -3
        elif event == "teammate_dead":
            morale_change = -8
        elif event == "teammate_recovery":
            morale_change = 5
        elif event == "successful_convergence":
            morale_change = 2
        elif event == "failed_convergence":
            morale_change = -1
        elif event == "custom":
            # Use provided magnitude
            morale_change = magnitude if magnitude is not None else 0
        
        # Apply the change with bounds
        new_morale = max(0, min(100, current_morale + morale_change))
        character.morale = new_morale
        
        # Update morale modifiers
        character.morale_modifiers = self.calculate_morale_modifiers(new_morale)
        
        return new_morale

###############################
