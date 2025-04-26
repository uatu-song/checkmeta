"""
META Fantasy League Simulator - Leadership System
Handles leadership bonuses and effects for teams
"""

class LeadershipSystem:
    """System for calculating and applying leadership bonuses"""
    
    def __init__(self):
        """Initialize the leadership system"""
        pass
    
    def apply_leadership_bonuses(self, team):
        """Apply leadership bonuses to a team based on Field Leader
        
        Args:
            team: Team object with active_characters attribute
        """
        # Get the field leader
        leader = self.get_field_leader(team)
        
        if not leader:
            return
        
        # Get leadership stat - using direct attribute access
        leadership = 5  # Default value
        
        # Check different ways the leadership value might be stored
        if hasattr(leader, 'aLDR'):
            leadership = leader.aLDR
        elif hasattr(leader, 'stats') and 'aLDR' in leader.stats:
            leadership = leader.stats['aLDR']
        elif hasattr(leader, 'get_stat'):
            leadership = leader.get_stat('LDR')
        
        # Calculate bonus percentage (leadership stat affects the bonus)
        bonus_pct = (leadership - 5) * 0.02  # 2% per point above 5
        
        # Apply bonuses to all active characters
        for character in team.active_characters:
            # Skip the leader (doesn't boost themselves)
            if character == leader:
                continue
                
            # Apply bonuses based on leadership value
            character.leadership_modifiers = {
                'attribute_bonus': bonus_pct,
                'trait_activation_bonus': bonus_pct * 0.5,
                'convergence_bonus': bonus_pct * 0.75
            }
            
            # Apply attribute bonuses
            if hasattr(character, 'trait_activation_bonus'):
                character.trait_activation_bonus += character.leadership_modifiers['trait_activation_bonus']
    
    def get_field_leader(self, team):
        """Get the Field Leader character from a team
        
        Args:
            team: Team object with active_characters attribute
            
        Returns:
            Character: The Field Leader character or None
        """
        # First look for a character with FL role
        for character in team.active_characters:
            if hasattr(character, 'role') and character.role == 'FL' and not getattr(character, 'is_ko', False):
                return character
        
        # If no FL found, check for character with highest LDR stat
        best_leader = None
        highest_ldr = -1
        
        for character in team.active_characters:
            if getattr(character, 'is_ko', False):
                continue
                
            ldr_val = 0
            if hasattr(character, 'aLDR'):
                ldr_val = character.aLDR
            elif hasattr(character, 'stats') and 'aLDR' in character.stats:
                ldr_val = character.stats['aLDR']
            
            if ldr_val > highest_ldr:
                highest_ldr = ldr_val
                best_leader = character
        
        return best_leader