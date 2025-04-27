"""
META Fantasy League Simulator - Initiative Randomizer
Prevents first-mover advantage with fair turn order
"""

import random
from typing import Dict, List, Any, Optional, Tuple
from config import get_config

class InitiativeRandomizer:
    """System for randomizing initiative and turn order"""
    
    def __init__(self):
        """Initialize the initiative randomizer"""
        self.config = get_config()
        self.initiative_order = []
        self.current_index = 0
        self.round_num = 0
        self.a_first_count = 0
        self.b_first_count = 0
    
    def reset(self):
        """Reset the randomizer state"""
        self.initiative_order = []
        self.current_index = 0
        self.round_num = 0
    
    def roll_initiative(self, team_a, team_b):
        """Roll initiative for both teams
        
        Args:
            team_a: Team A characters
            team_b: Team B characters
            
        Returns:
            list: Initiative order
        """
        self.initiative_order = []
        self.current_index = 0
        self.round_num += 1
        
        # Use weighted randomization for first team
        # This ensures a fair distribution over time
        if self.a_first_count > self.b_first_count:
            # Team B has gone first less often, increase its chance
            first_team = "B" if random.random() < 0.7 else "A"
        elif self.b_first_count > self.a_first_count:
            # Team A has gone first less often, increase its chance
            first_team = "A" if random.random() < 0.7 else "B"
        else:
            # Equal counts, pure random
            first_team = "A" if random.random() < 0.5 else "B"
        
        # Update counters
        if first_team == "A":
            self.a_first_count += 1
        else:
            self.b_first_count += 1
        
        # Set initiative order
        active_a = [c for c in team_a if c.get("is_active", True) and not c.get("is_ko", False)]
        active_b = [c for c in team_b if c.get("is_active", True) and not c.get("is_ko", False)]
        
        # Shuffle each team separately
        random.shuffle(active_a)
        random.shuffle(active_b)
        
        # Assign initiative values
        if first_team == "A":
            self.initiative_order = list(zip(active_a, ["A"] * len(active_a)))
            self.initiative_order += list(zip(active_b, ["B"] * len(active_b)))
        else:
            self.initiative_order = list(zip(active_b, ["B"] * len(active_b)))
            self.initiative_order += list(zip(active_a, ["A"] * len(active_a)))
        
        return self.initiative_order
    
    def get_next_character(self):
        """Get the next character in initiative order
        
        Returns:
            tuple: (character, team_key) or (None, None) if end of order
        """
        if not self.initiative_order or self.current_index >= len(self.initiative_order):
            return None, None
        
        char, team = self.initiative_order[self.current_index]
        self.current_index += 1
        
        return char, team
    
    def is_initiative_complete(self):
        """Check if all characters have taken their turns
        
        Returns:
            bool: Whether initiative is complete
        """
        return self.current_index >= len(self.initiative_order)
    
    def get_initiative_stats(self):
        """Get statistics about initiative order
        
        Returns:
            dict: Initiative statistics
        """
        return {
            "a_first_count": self.a_first_count,
            "b_first_count": self.b_first_count,
            "current_round": self.round_num,
            "current_order": "A first" if self.a_first_count > self.b_first_count else "B first"
        }