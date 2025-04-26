"""
META Fantasy League Simulator - Team Model
Defines the Team class for representing in-game teams
"""

from typing import List, Dict, Any, Optional

class Team:
    """Model representing a team in the META Fantasy League"""
    
    def __init__(self, active_characters=None, bench=None):
        """Initialize a team with characters
        
        Args:
            active_characters (list, optional): List of active Character objects. Defaults to None.
            bench (list, optional): List of bench Character objects. Defaults to None.
        """
        self.active_characters = active_characters or []
        self.bench = bench or []
        
        # Set team properties from first character if available
        if self.active_characters:
            first_char = self.active_characters[0]
            self.team_id = first_char.team_id
            self.team_name = first_char.team_name
        else:
            self.team_id = ""
            self.team_name = "Unknown Team"
        
        # Calculated properties
        self.synergy_score = 0
        self.leadership_score = 0
        self.operations_score = 0
        self.intelligence_score = 0
        
        # Cached values
        self._field_leader = None
        self._division_map = None
    
    def get_field_leader(self):
        """Get the Field Leader character
        
        Returns:
            Character: The Field Leader character or None
        """
        # Use cached value if available
        if self._field_leader is not None:
            return self._field_leader
        
        # Find Field Leader
        for character in self.active_characters:
            if character.role == "FL" and character.is_active():
                self._field_leader = character
                return character
        
        # If no active Field Leader, find any Field Leader
        for character in self.active_characters:
            if character.role == "FL":
                self._field_leader = character
                return character
        
        # If still not found, return the first character
        if self.active_characters:
            self._field_leader = self.active_characters[0]
            return self._field_leader
        
        return None
    
    def get_characters_by_division(self):
        """Get characters organized by division
        
        Returns:
            dict: Dictionary with 'o' and 'i' keys containing lists of characters
        """
        # Use cached value if available
        if self._division_map is not None:
            return self._division_map
        
        # Organize characters by division
        self._division_map = {
            'o': [],  # Operations
            'i': []   # Intelligence
        }
        
        for character in self.active_characters:
            division = character.division if character.division in ['o', 'i'] else 'o'
            self._division_map[division].append(character)
        
        return self._division_map
    
    def get_characters_by_role(self):
        """Get characters organized by role
        
        Returns:
            dict: Dictionary with role keys containing lists of characters
        """
        role_map = {}
        
        for character in self.active_characters:
            if character.role not in role_map:
                role_map[character.role] = []
            
            role_map[character.role].append(character)
        
        return role_map
    
    def get_active_character_count(self):
        """Get the number of active (not KO'd or dead) characters
        
        Returns:
            int: Number of active characters
        """
        return sum(1 for character in self.active_characters if character.is_active())
    
    def substitute_character(self, active_idx, bench_idx):
        """Substitute a character from the bench for an active character
        
        Args:
            active_idx (int): Index of active character to replace
            bench_idx (int): Index of bench character to bring in
        
        Returns:
            bool: True if successful, False otherwise
        """
        if (active_idx < 0 or active_idx >= len(self.active_characters) or
            bench_idx < 0 or bench_idx >= len(self.bench)):
            return False
        
        # Swap characters
        active_char = self.active_characters[active_idx]
        bench_char = self.bench[bench_idx]
        
        self.active_characters[active_idx] = bench_char
        self.bench[bench_idx] = active_char
        
        # Reset cached values
        self._field_leader = None
        self._division_map = None
        
        return True
    
    def to_dict_list(self):
        """Convert team to a list of character dictionaries
        
        Returns:
            list: List of character dictionaries
        """
        # Convert active characters
        active_dicts = [char.to_dict() for char in self.active_characters]
        
        # Convert bench characters
        bench_dicts = [char.to_dict() for char in self.bench]
        
        # Combine with active characters first
        return active_dicts + bench_dicts