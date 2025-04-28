"""
META Fantasy League Simulator - XP Progression System
Handles character XP, leveling, and attribute growth
"""

import os
import json
import random
import logging
import math
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict

logger = logging.getLogger("XPProgressionSystem")

class XPProgressionSystem:
    """System for handling character XP, leveling, and stat growth"""
    
    def __init__(self, config=None):
        """Initialize the XP progression system
        
        Args:
            config: Optional configuration object
        """
        self.config = config
        
        # XP thresholds for leveling
        self.level_thresholds = [0, 100, 250, 450, 700, 1000, 1350, 1750, 2200, 2700]
        
        # Maximum level
        self.max_level = len(self.level_thresholds)
        
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
        
        # Character progression tracking
        self.progression_history = {}
        
        # Create persistence directory
        self._ensure_persistence_directory()
    
    def _ensure_persistence_directory(self):
        """Ensure persistence directory exists"""
        persistence_dir = self._get_persistence_directory()
        os.makedirs(persistence_dir, exist_ok=True)
    
    def _get_persistence_directory(self) -> str:
        """Get directory for persistence files
        
        Returns:
            str: Path to persistence directory
        """
        # Try to get from config
        if self.config and hasattr(self.config, "paths"):
            if hasattr(self.config.paths, "get"):
                persistence_dir = self.config.paths.get("persistence_dir")
                if persistence_dir:
                    return persistence_dir
        
        # Default to 'data/persistence'
        return "data/persistence"
    
    def calculate_match_xp(self, character: Dict[str, Any], match_result: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate XP earned in a match
        
        Args:
            character: Character to calculate XP for
            match_result: Match result data
            
        Returns:
            dict: XP calculation details
        """
        xp_earned = 0
        xp_breakdown = {}
        
        # Character must be active to earn XP
        if not character.get("was_active", True):
            return {"xp_earned": 0, "breakdown": {"inactive": 0}}
        
        # Base XP from match outcome
        result = character.get("result", "unknown")
        if result == "win":
            xp_earned += self.xp_rewards["win"]
            xp_breakdown["win"] = self.xp_rewards["win"]
        elif result == "draw":
            xp_earned += self.xp_rewards["draw"]
            xp_breakdown["draw"] = self.xp_rewards["draw"]
        elif result == "loss":
            xp_earned += self.xp_rewards["loss"]
            xp_breakdown["loss"] = self.xp_rewards["loss"]
        
        # XP from rStats
        rStats = character.get("rStats", {})
        
        # Convergence victories
        convergence_wins = rStats.get("rCVo", 0) + rStats.get("rMBi", 0)
        if convergence_wins > 0:
            convergence_xp = convergence_wins * self.xp_rewards["convergence_win"]
            xp_earned += convergence_xp
            xp_breakdown["convergence_wins"] = convergence_xp
        
        # Opponent takedowns
        knockouts = rStats.get("rOTD", 0)
        if knockouts > 0:
            knockout_xp = knockouts * self.xp_rewards["knockout"]
            xp_earned += knockout_xp
            xp_breakdown["knockouts"] = knockout_xp
        
        # Evasion success (recovering from KO)
        recoveries = rStats.get("rEVS", 0)
        if recoveries > 0:
            recovery_xp = recoveries * self.xp_rewards["ko_recovery"]
            xp_earned += recovery_xp
            xp_breakdown["ko_recoveries"] = recovery_xp
        
        # Damage dealt
        damage_dealt = rStats.get("rDD", 0) + rStats.get("rDDo", 0) + rStats.get("rDDi", 0)
        if damage_dealt > 0:
            damage_xp = int(damage_dealt * self.xp_rewards["hp_damage_factor"])
            xp_earned += damage_xp
            xp_breakdown["damage_dealt"] = damage_xp
        
        # Healing provided
        healing = rStats.get("rHLG", 0)
        if healing > 0:
            healing_xp = int(healing * self.xp_rewards["healing_factor"])
            xp_earned += healing_xp
            xp_breakdown["healing"] = healing_xp
        
        # Field Leader bonus
        if character.get("role") == "FL":
            xp_earned += self.xp_rewards["fl_leadership"]
            xp_breakdown["fl_leadership"] = self.xp_rewards["fl_leadership"]
        
        # Pack everything into a detailed result
        return {
            "xp_earned": xp_earned,
            "breakdown": xp_breakdown
        }
    
    def apply_xp_and_level(self, character: Dict[str, Any], xp_earned: int) -> Dict[str, Any]:
        """Apply earned XP and handle leveling if applicable
        
        Args:
            character: Character to apply XP to
            xp_earned: Amount of XP earned
            
        Returns:
            dict: Leveling results
        """
        # Ensure character has base XP fields
        if "xp_total" not in character:
            character["xp_total"] = 0
        
        if "level" not in character:
            character["level"] = self._calculate_level(character["xp_total"])
        
        # Get current XP and level
        current_xp = character.get("xp_total", 0)
        current_level = character.get("level", 1)
        
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
            
            # Log level up
            logger.info(f"{character['name']} leveled up to {new_level}!")
        
        # Get XP for next level
        next_level_xp = self._get_next_level_xp(new_level)
        
        # Track progression history
        char_id = character.get("id", "unknown")
        if char_id not in self.progression_history:
            self.progression_history[char_id] = []
        
        # Add progression event
        self.progression_history[char_id].append({
            "timestamp": self._get_timestamp(),
            "xp_earned": xp_earned,
            "previous_level": current_level,
            "new_level": new_level,
            "level_ups": level_ups,
            "stat_increases": stat_increases
        })
        
        # Return detailed result
        return {
            "previous_level": current_level,
            "new_level": new_level,
            "level_ups": level_ups,
            "xp_earned": xp_earned,
            "total_xp": new_total_xp,
            "stat_increases": stat_increases,
            "next_level_xp": next_level_xp
        }
    
    def _calculate_level(self, xp: int) -> int:
        """Calculate level based on XP
        
        Args:
            xp: Total XP
            
        Returns:
            int: Character level
        """
        for i, threshold in enumerate(self.level_thresholds[1:], 2):
            if xp < threshold:
                return i - 1
        
        # If beyond all thresholds, return max level
        return self.max_level
    
    def _get_next_level_xp(self, current_level: int) -> Optional[int]:
        """Get XP needed for next level
        
        Args:
            current_level: Current level
            
        Returns:
            int: XP threshold for next level, or None if at max level
        """
        if current_level >= self.max_level:
            return None  # Max level reached
        
        return self.level_thresholds[current_level]
    
    def _apply_level_up_stats(self, character: Dict[str, Any]) -> Dict[str, int]:
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
    
    def _get_timestamp(self) -> str:
        """Get current timestamp
        
        Returns:
            str: Formatted timestamp
        """
        import datetime
        return datetime.datetime.now().isoformat()
    
    def get_character_progression_summary(self, character: Dict[str, Any]) -> Dict[str, Any]:
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
        
        # Get all available attributes
        attrs = {}
        for key, value in character.items():
            if key.startswith('a') and len(key) > 1 and isinstance(value, (int, float)):
                attrs[key[1:]] = value
        
        return {
            "name": character.get("name", "Unknown"),
            "id": character.get("id", "unknown"),
            "team_id": character.get("team_id", "unknown"),
            "role": character.get("role", "Unknown"),
            "level": level,
            "xp_total": xp_total,
            "next_level_xp": next_level_xp,
            "level_progress": level_progress,
            "attributes": attrs
        }
    
    def save_character_progression(self, character: Dict[str, Any]) -> str:
        """Save character progression to disk
        
        Args:
            character: Character to save
            
        Returns:
            str: Path to saved file
        """
        char_id = character.get("id", "unknown")
        
        # Get persistence directory
        persistence_dir = self._get_persistence_directory()
        os.makedirs(persistence_dir, exist_ok=True)
        
        # Create character file path
        char_file = os.path.join(persistence_dir, f"{char_id}_progression.json")
        
        # Get progression data
        progression_data = {
            "character_id": char_id,
            "character_name": character.get("name", "Unknown"),
            "team_id": character.get("team_id", "unknown"),
            "role": character.get("role", ""),
            "level": character.get("level", 1),
            "xp_total": character.get("xp_total", 0),
            "attributes": {},
            "history": self.progression_history.get(char_id, [])
        }
        
        # Add all attributes
        for key, value in character.items():
            if key.startswith('a') and len(key) > 1 and isinstance(value, (int, float)):
                progression_data["attributes"][key] = value
        
        # Save to file
        with open(char_file, 'w') as f:
            json.dump(progression_data, f, indent=2)
        
        return char_file
    
    def load_character_progression(self, character_id: str) -> Optional[Dict[str, Any]]:
        """Load character progression from disk
        
        Args:
            character_id: Character ID to load
            
        Returns:
            dict: Loaded progression data or None if not found
        """
        # Get persistence directory
        persistence_dir = self._get_persistence_directory()
        
        # Create character file path
        char_file = os.path.join(persistence_dir, f"{character_id}_progression.json")
        
        # Check if file exists
        if not os.path.exists(char_file):
            return None
        
        # Load from file
        try:
            with open(char_file, 'r') as f:
                progression_data = json.load(f)
            
            return progression_data
        except Exception as e:
            logger.error(f"Error loading character progression: {e}")
            return None
    
    def apply_progression_to_character(self, character: Dict[str, Any]) -> Dict[str, Any]:
        """Apply saved progression data to a character
        
        Args:
            character: Character to update
            
        Returns:
            dict: Updated character data
        """
        char_id = character.get("id", "unknown")
        
        # Try to load progression data
        progression_data = self.load_character_progression(char_id)
        
        if not progression_data:
            # No saved data, return character as-is
            return character
        
        # Apply level and XP
        character["level"] = progression_data.get("level", 1)
        character["xp_total"] = progression_data.get("xp_total", 0)
        
        # Apply attributes
        for attr, value in progression_data.get("attributes", {}).items():
            character[attr] = value
        
        # Load history
        self.progression_history[char_id] = progression_data.get("history", [])
        
        return character
    
    def generate_character_progression_report(self, character: Dict[str, Any]) -> str:
        """Generate a text report of character progression
        
        Args:
            character: Character to report on
            
        Returns:
            str: Formatted progression report
        """
        char_id = character.get("id", "unknown")
        
        # Get progression history
        history = self.progression_history.get(char_id, [])
        
        # Get progression summary
        summary = self.get_character_progression_summary(character)
        
        # Build report
        report = f"""
=== CHARACTER PROGRESSION REPORT ===
Name: {summary['name']}
Role: {summary['role']}
Team: {character.get('team_name', 'Unknown')}

Current Level: {summary['level']}
Total XP: {summary['xp_total']}
Progress to Next Level: {summary['level_progress']:.1f}%

Attributes:
"""
        
        # Add attributes
        attrs = summary["attributes"]
        max_key_len = max(len(key) for key in attrs.keys()) if attrs else 3
        
        for key, value in sorted(attrs.items()):
            padding = ' ' * (max_key_len - len(key))
            report += f"  {key.upper()}{padding}: {value}\n"
        
        # Add recent progression
        report += "\nRecent Progression:\n"
        
        if history:
            # Show last 5 entries
            recent = history[-5:]
            for entry in reversed(recent):
                report += f"  {entry.get('timestamp', 'Unknown date').split('T')[0]}: "
                report += f"+{entry.get('xp_earned', 0)} XP"
                
                if entry.get('level_ups', 0) > 0:
                    report += f" (Leveled up to {entry.get('new_level', '?')}!)"
                    
                    # Show stat increases
                    stat_increases = entry.get('stat_increases', {})
                    if stat_increases:
                        increases = []
                        for attr, value in stat_increases.items():
                            increases.append(f"{attr[1:].upper()}+{value}")
                        
                        report += f" {', '.join(increases)}"
                
                report += "\n"
        else:
            report += "  No progression history available.\n"
        
        report += "================================="
        
        return report
    
    def process_match_results(self, match_result: Dict[str, Any]) -> Dict[str, Any]:
        """Process XP and leveling for all characters in a match
        
        Args:
            match_result: Match result data
            
        Returns:
            dict: Processed XP and leveling data
        """
        processed_results = {
            "match_id": match_result.get("match_id", "unknown"),
            "day": match_result.get("day", 1),
            "character_progression": []
        }
        
        # Get character results
        character_results = match_result.get("character_results", [])
        
        # Process each character
        for char_result in character_results:
            character = char_result.copy()
            
            # Calculate XP
            xp_result = self.calculate_match_xp(character, match_result)
            xp_earned = xp_result["xp_earned"]
            
            # Apply XP and level up if needed
            level_result = self.apply_xp_and_level(character, xp_earned)
            
            # Save progression
            self.save_character_progression(character)
            
            # Add to processed results
            processed_results["character_progression"].append({
                "character_id": character.get("id", character.get("character_id", "unknown")),
                "character_name": character.get("name", character.get("character_name", "Unknown")),
                "xp_earned": xp_earned,
                "xp_breakdown": xp_result["breakdown"],
                "previous_level": level_result["previous_level"],
                "new_level": level_result["new_level"],
                "level_ups": level_result["level_ups"],
                "stat_increases": level_result["stat_increases"]
            })
        
        return processed_results
    
    def get_growth_potential(self, character: Dict[str, Any]) -> Dict[str, float]:
        """Get growth potential for character attributes
        
        Args:
            character: Character to analyze
            
        Returns:
            dict: Growth potential by attribute
        """
        # Get growth rates based on role
        role = character.get("role", "")
        growth_rates = self.growth_rates.get(role, self.default_growth)
        
        # Calculate potential
        potential = {}
        for attr, rate in growth_rates.items():
            current = character.get(attr, 5)
            max_value = 10
            
            # Calculate remaining growth
            remaining = max_value - current
            
            # Calculate potential (remaining * chance)
            if remaining > 0:
                potential[attr] = remaining * rate
            else:
                potential[attr] = 0
        
        return potential