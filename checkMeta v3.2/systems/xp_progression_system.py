"""
META Fantasy League - XP Progression System
Handles character XP, leveling, and attribute growth
"""

import random
from typing import Dict, List, Any

class XPProgressionSystem:
    """System for handling character XP, leveling, and stat growth"""
    
    def __init__(self):
        """Initialize the XP progression system"""
        # XP thresholds for leveling
        self.level_thresholds = [0, 100, 250, 450, 700, 1000, 1350, 1750, 2200, 2700]
        
        # Attribute growth per level (by role)
        self.growth_rates = {
            "FL": {"aLDR": 0.5, "aDUR": 0.3, "aSTR": 0.2, "aWIL": 0.2},  # Field Leader
            "VG": {"aSPD": 0.5, "aSTR": 0.3, "aDUR": 0.2},               # Vanguard
            "EN": {"aSTR": 0.5, "aDUR": 0.4, "aRES": 0.2},               # Enforcer
            "RG": {"aSPD": 0.4, "aFS": 0.3, "aOP": 0.2},                 # Ranger
            "GO": {"aSPD": 0.5, "aWIL": 0.3, "aSBY": 0.2},               # Ghost Operative
            "PO": {"aWIL": 0.5, "aOP": 0.4, "aAM": 0.3},                 # Psi Operative
            "SV": {"aOP": 0.6, "aLDR": 0.3, "aAM": 0.4}                  # Sovereign
        }
        
        # Default growth rates (fallback)
        self.default_growth = {"aSTR": 0.2, "aSPD": 0.2, "aHP": 0.3, "aWIL": 0.1}
        
        # XP rewards for various achievements
        self.xp_rewards = {
            "win": 30,                 # Match win
            "draw": 15,                # Match draw
            "loss": 10,                # Match loss (participation)
            "convergence_win": 5,      # Winning a convergence
            "knockout": 15,            # Knocking out an opponent
            "ko_recovery": 10,         # Recovering from KO
            "hp_damage_factor": 0.1,   # XP per HP damage dealt
            "healing_factor": 0.2,     # XP per HP healed
            "fl_leadership": 20        # Field Leader bonus
        }
    
    def calculate_match_xp(self, character, match_result):
        """Calculate XP earned in a match
        
        Args:
            character: Character to calculate XP for
            match_result: Match result data
            
        Returns:
            int: XP earned
        """
        xp_earned = 0
        
        # Base XP from match outcome
        result = character.get("result", "unknown")
        if result == "win":
            xp_earned += self.xp_rewards["win"]
        elif result == "draw":
            xp_earned += self.xp_rewards["draw"]
        elif result == "loss":
            xp_earned += self.xp_rewards["loss"]
        
        # XP from rStats
        rStats = character.get("rStats", {})
        
        # Convergence victories
        convergence_wins = rStats.get("rCVo", 0) + rStats.get("rMBi", 0)
        xp_earned += convergence_wins * self.xp_rewards["convergence_win"]
        
        # Additional XP calculations...
        
        return xp_earned
    
    def apply_xp_and_level(self, character, xp_earned):
        """Apply earned XP and handle leveling if applicable
        
        Args:
            character: Character to apply XP to
            xp_earned: Amount of XP earned
            
        Returns:
            dict: Leveling results
        """
        # Get current XP and level
        current_xp = character.get("xp_total", 0)
        current_level = self._calculate_level(current_xp)
        
        # Add new XP
        new_total_xp = current_xp + xp_earned
        character["xp_total"] = new_total_xp
        
        # Calculate new level
        new_level = self._calculate_level(new_total_xp)
        
        # Handle leveling up
        level_ups = new_level - current_level
        stat_increases = {}
        
        if level_ups > 0:
            # Apply attribute increases for each level gained
            for _ in range(level_ups):
                increases = self._apply_level_up_stats(character)
                
                # Combine increases
                for attr, value in increases.items():
                    stat_increases[attr] = stat_increases.get(attr, 0) + value
            
            # Set character level
            character["level"] = new_level
        
        return {
            "previous_level": current_level,
            "new_level": new_level,
            "level_ups": level_ups,
            "xp_earned": xp_earned,
            "total_xp": new_total_xp,
            "stat_increases": stat_increases,
            "next_level_xp": self._get_next_level_xp(new_level)
        }
    
    def _calculate_level(self, xp):
        """Calculate level based on XP
        
        Args:
            xp: Total XP
            
        Returns:
            int: Character level
        """
        level = 1
        for i, threshold in enumerate(self.level_thresholds[1:], 2):
            if xp < threshold:
                return i - 1
        
        # If beyond all thresholds, return max level
        return len(self.level_thresholds)
    
    def _get_next_level_xp(self, current_level):
        """Get XP needed for next level
        
        Args:
            current_level: Current level
            
        Returns:
            int: XP threshold for next level
        """
        if current_level >= len(self.level_thresholds):
            return None  # Max level reached
        
        return self.level_thresholds[current_level]
    
    def _apply_level_up_stats(self, character):
        """Apply stat increases from leveling up
        
        Args:
            character: Character to update
            
        Returns:
            dict: Stat increases
        """
        # Get growth rates based on role
        role = character.get("role", "")
        growth_rates = self.growth_rates.get(role, self.default_growth)
        
        increases = {}
        
        # Apply stat increases
        for attr, rate in growth_rates.items():
            # Chance-based increases
            if random.random() < rate:
                # Get current value
                current = character.get(attr, 5)
                
                # Increase stat (cap at 10)
                if current < 10:
                    character[attr] = current + 1
                    increases[attr] = 1
        
        return increases
    
    def get_character_progression_summary(self, character):
        """Get a summary of character progression
        
        Args:
            character: Character to summarize
            
        Returns:
            dict: Progression summary
        """
        level = character.get("level", 1)
        xp_total = character.get("xp_total", 0)
        next_level_xp = self._get_next_level_xp(level)
        
        # Calculate progression percentage
        if next_level_xp:
            current_level_xp = self.level_thresholds[level-1] if level > 1 else 0
            level_progress = ((xp_total - current_level_xp) / 
                             (next_level_xp - current_level_xp)) * 100
        else:
            level_progress = 100  # Max level
        
        return {
            "name": character.get("name", "Unknown"),
            "level": level,
            "xp_total": xp_total,
            "next_level_xp": next_level_xp,
            "level_progress": level_progress,
            "attributes": {
                "STR": character.get("aSTR", 5),
                "SPD": character.get("aSPD", 5),
                "DUR": character.get("aDUR", 5),
                "WIL": character.get("aWIL", 5),
                "FS": character.get("aFS", 5),
                "LDR": character.get("aLDR", 5),
                "OP": character.get("aOP", 5)
            }
        }