"""
META Fantasy League Simulator - Morale System
Handles morale effects and calculations
"""

class MoraleSystem:
    """System for calculating and applying morale effects"""
    
    def __init__(self):
        """Initialize the morale system"""
        self.morale_thresholds = {
            'very_low': 20,
            'low': 40,
            'neutral': 60,
            'high': 80,
            'very_high': 100
        }
    
    def calculate_morale_modifiers(self, morale):
        """Calculate modifiers based on morale level
        
        Args:
            morale (int): Morale value (0-100)
            
        Returns:
            dict: Morale modifiers
        """
        # Default neutral modifiers
        modifiers = {
            'combat_bonus': 0.0,
            'defense_bonus': 0.0,
            'stamina_regen': 0.0,
            'trait_activation': 0.0
        }
        
        # Very low morale (0-20)
        if morale <= self.morale_thresholds['very_low']:
            modifiers['combat_bonus'] = -0.2
            modifiers['defense_bonus'] = -0.15
            modifiers['stamina_regen'] = -0.2
            modifiers['trait_activation'] = -0.1
        
        # Low morale (21-40)
        elif morale <= self.morale_thresholds['low']:
            modifiers['combat_bonus'] = -0.1
            modifiers['defense_bonus'] = -0.05
            modifiers['stamina_regen'] = -0.1
            modifiers['trait_activation'] = -0.05
        
        # High morale (61-80)
        elif morale <= self.morale_thresholds['high']:
            modifiers['combat_bonus'] = 0.1
            modifiers['defense_bonus'] = 0.05
            modifiers['stamina_regen'] = 0.1
            modifiers['trait_activation'] = 0.05
        
        # Very high morale (81-100)
        elif morale <= self.morale_thresholds['very_high']:
            modifiers['combat_bonus'] = 0.2
            modifiers['defense_bonus'] = 0.15
            modifiers['stamina_regen'] = 0.2
            modifiers['trait_activation'] = 0.1
        
        return modifiers
    
    def update_team_morale(self, team, match_result):
        """Update team morale based on match result
        
        Args:
            team: Team object or list of characters
            match_result (str): 'win', 'loss', or 'draw'
        """
        # Determine morale change based on result
        if match_result == 'win':
            morale_change = 10
        elif match_result == 'loss':
            morale_change = -5
        else:  # draw
            morale_change = 2
        
        # Apply to all characters
        characters = team.active_characters if hasattr(team, 'active_characters') else team
        
        for character in characters:
            if hasattr(character, 'morale'):
                character.morale = max(0, min(100, character.morale + morale_change))