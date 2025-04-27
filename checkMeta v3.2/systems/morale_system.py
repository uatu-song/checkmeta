"""
META Fantasy League - Morale System
Handles character morale, team morale, and momentum effects
"""

import random
from typing import Dict, List, Any

class MoraleSystem:
    """System for managing character and team morale with momentum effects"""
    
    def __init__(self):
        """Initialize the morale system"""
        # Morale thresholds
        self.morale_thresholds = {
            'very_low': 20,  # 0-20
            'low': 40,       # 21-40
            'neutral': 60,   # 41-60
            'high': 80,      # 61-80
            'very_high': 100 # 81-100
        }
        
        # Momentum thresholds
        self.momentum_thresholds = {
            'crash': -3,     # <= -3
            'building': 3    # >= 3
        }
        
        # Morale effects
        self.morale_effects = {
            'very_low': {
                'combat_bonus': -20,
                'defense_bonus': -15,
                'stamina_regen': -2,
                'trait_activation': -0.1
            },
            'low': {
                'combat_bonus': -10,
                'defense_bonus': -5,
                'stamina_regen': -1,
                'trait_activation': -0.05
            },
            'neutral': {
                'combat_bonus': 0,
                'defense_bonus': 0,
                'stamina_regen': 0,
                'trait_activation': 0
            },
            'high': {
                'combat_bonus': 10,
                'defense_bonus': 5,
                'stamina_regen': 1,
                'trait_activation': 0.05
            },
            'very_high': {
                'combat_bonus': 20,
                'defense_bonus': 15,
                'stamina_regen': 2,
                'trait_activation': 0.1
            }
        }
    
    def initialize_character_morale(self, characters):
        """Initialize morale for all characters
        
        Args:
            characters: List of characters to initialize
            
        Returns:
            int: Number of characters initialized
        """
        count = 0
        for character in characters:
            # Default morale value if not set
            if "morale" not in character:
                character["morale"] = 50
                count += 1
            
            # Set morale level
            character["morale_level"] = self.calculate_morale_level(character["morale"])
            
            # Initialize momentum state if not set
            if "momentum_state" not in character:
                character["momentum_state"] = "stable"
                character["momentum_value"] = 0
        
        return count
    
    def calculate_morale_level(self, morale):
        """Calculate morale level based on value
        
        Args:
            morale (int): Morale value (0-100)
            
        Returns:
            str: Morale level
        """
        if morale <= self.morale_thresholds['very_low']:
            return 'very_low'
        elif morale <= self.morale_thresholds['low']:
            return 'low'
        elif morale <= self.morale_thresholds['neutral']:
            return 'neutral'
        elif morale <= self.morale_thresholds['high']:
            return 'high'
        else:
            return 'very_high'
    
    def calculate_morale_modifiers(self, morale):
        """Calculate modifiers based on morale level
        
        Args:
            morale (int): Morale value (0-100)
            
        Returns:
            dict: Dictionary of morale modifiers
        """
        level = self.calculate_morale_level(morale)
        return self.morale_effects.get(level, self.morale_effects['neutral'])
    
    def update_morale(self, character, event_type, value=None):
        """Update character morale based on events
        
        Args:
            character: Character to update
            event_type: Type of event (win, loss, ko, etc.)
            value: Optional direct value to modify by
            
        Returns:
            int: New morale value
        """
        # Current morale
        current_morale = character.get("morale", 50)
        
        # Calculate change based on event
        morale_change = 0
        
        if value is not None:
            # Direct value provided
            morale_change = value
        else:
            # Calculate based on event type
            event_changes = {
                "win": 10,
                "loss": -5,
                "draw": 2,
                "knockout": -10,
                "revival": 5,
                "critical_success": 8,
                "critical_failure": -8,
                "team_win": 5,
                "team_loss": -3,
                "ally_ko": -2,
                "enemy_ko": 3
            }
            
            morale_change = event_changes.get(event_type, 0)
        
        # Apply Leadership bonus to morale change
        if morale_change > 0 and character.get("role") == "FL":
            morale_change = int(morale_change * 1.5)  # 50% bonus for Field Leaders
        
        # Apply change
        new_morale = max(0, min(100, current_morale + morale_change))
        character["morale"] = new_morale
        
        # Update morale level
        character["morale_level"] = self.calculate_morale_level(new_morale)
        
        # Update morale modifiers
        character["morale_modifiers"] = self.calculate_morale_modifiers(new_morale)
        
        return new_morale
    
    def update_team_morale(self, team, event_type, value=None):
        """Update morale for all characters in a team
        
        Args:
            team: List of team characters
            event_type: Type of event
            value: Optional direct value to modify by
            
        Returns:
            float: Average team morale
        """
        total_morale = 0
        count = 0
        
        for character in team:
            self.update_morale(character, event_type, value)
            total_morale += character.get("morale", 50)
            count += 1
        
        return total_morale / count if count > 0 else 0