"""
Team model for META League Simulator
"""

from typing import List, Dict, Any, Optional
from ..models.character import Character
from ..config.game_config import MAX_ACTIVE_ROSTER_SIZE

class Team:
    """Team model representing a group of characters in the META League"""
    
    def __init__(self, characters: List[Character] = None):
        """Initialize a team with a list of characters"""
        if characters is None:
            characters = []
            
        self.characters = characters
        self.team_id = characters[0].team_id if characters else None
        self.team_name = characters[0].team_name if characters else None
        
        # Split into active and bench
        self.active_characters = characters[:MAX_ACTIVE_ROSTER_SIZE] if len(characters) > MAX_ACTIVE_ROSTER_SIZE else characters
        self.bench_characters = characters[MAX_ACTIVE_ROSTER_SIZE:] if len(characters) > MAX_ACTIVE_ROSTER_SIZE else []
    
    def get_field_leader(self) -> Optional[Character]:
        """Get the team's Field Leader"""
        # Find characters with FL role
        field_leaders = [char for char in self.active_characters if char.role == "FL"]
        
        if not field_leaders:
            return None
        
        # Take the one with highest LDR
        return max(field_leaders, key=lambda x: x.get_attribute('LDR'))
    
    def get_active_count(self) -> int:
        """Get count of active (non-KO, non-dead) characters"""
        return sum(1 for char in self.active_characters 
                if not char.is_ko and not char.is_dead)
    
    def update_morale(self, change: float) -> None:
        """Update morale for all team members"""
        for character in self.characters:
            character.morale = max(0, min(100, character.morale + change))
    
    def to_dict_list(self) -> List[Dict[str, Any]]:
        """Convert team to a list of character dictionaries"""
        return [char.to_dict() for char in self.characters]
    
    @classmethod
    def from_dict_list(cls, dict_list: List[Dict[str, Any]]) -> 'Team':
        """Create a Team instance from a list of character dictionaries"""
        characters = [Character.from_dict(char_dict) for char_dict in dict_list]
        return cls(characters)