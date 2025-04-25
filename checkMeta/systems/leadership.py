"""
Leadership system for META League Simulator
"""

from typing import Dict, Any, Optional
from ..models.team import Team
from ..models.character import Character

class LeadershipSystem:
    """System for managing leadership effects"""
    
    def apply_leadership_bonuses(self, team: Team) -> Team:
        """Apply leadership bonuses from the team's Field Leader"""
        # Find the Field Leader
        leader = team.get_field_leader()
        
        if not leader:
            return team  # No leader found
        
        # Get leadership value
        leadership = leader.get_attribute('LDR')
        
        # Leadership modifier based on leader's Leadership stat
        # Baseline is 5, so this calculates bonus for leadership above 5
        leadership_bonus = max(0, leadership - 5)
        
        # Basic leadership bonuses
        morale_boost = leadership_bonus * 2  # +2 morale per leadership point
        synergy_boost = leadership_bonus * 0.05  # +5% team synergy per leadership point
        
        # Apply bonuses to all team members
        for character in team.characters:
            # Don't apply to the leader
            if character.id == leader.id:
                continue
            
            # Apply morale boost
            character.morale = min(100, character.morale + morale_boost)
            
            # Store leadership bonuses
            character.leadership_bonuses = {
                "leader_name": leader.name,
                "leader_id": leader.id,
                "morale_boost": morale_boost,
                "synergy_boost": synergy_boost,
                "leadership_stat": leadership
            }
        
        # Mark the leader
        leader.is_leader = True
        
        return team
    
    def get_leadership_effect(self, leader: Character, effect_type: str) -> float:
        """Calculate leadership effect of specific type"""
        leadership = leader.get_attribute('LDR')
        bonus = max(0, leadership - 5)
        
        if effect_type == "morale":
            return bonus * 2  # +2 morale per leadership point
        elif effect_type == "synergy":
            return bonus * 0.05  # +5% synergy per leadership point
        elif effect_type == "combat":
            return bonus * 1.5  # +1.5 combat bonus per leadership point
        elif effect_type == "recovery":
            return bonus * 2  # +2 recovery per leadership point
        
        return 0

###############################
