"""
META Fantasy League Simulator - Enhanced Field Leader System
Handles Field Leader substitutions and special abilities
"""

import random
from typing import Dict, List, Any, Optional, Tuple
from config import get_config

class FieldLeaderEnhancer:
    """System for enhancing Field Leader mechanics and substitutions"""
    
    def __init__(self):
        """Initialize the Field Leader enhancer"""
        self.config = get_config()
        self.substitutions = []
        self.active_field_leaders = {}
        self.bench = {}
        self.knockouts = {}
    
    def initialize_team_leaders(self, team_a, team_b):
        """Initialize Field Leaders for both teams
        
        Args:
            team_a: Team A characters
            team_b: Team B characters
            
        Returns:
            tuple: Field Leaders for both teams
        """
        # Reset trackers
        self.substitutions = []
        self.active_field_leaders = {}
        self.bench = {"A": [], "B": []}
        self.knockouts = {"A": [], "B": []}
        
        # Find Field Leaders
        team_a_fl = self._find_field_leader(team_a, "A")
        team_b_fl = self._find_field_leader(team_b, "B")
        
        # Set active field leaders
        if team_a_fl:
            self.active_field_leaders["A"] = team_a_fl["id"]
        
        if team_b_fl:
            self.active_field_leaders["B"] = team_b_fl["id"]
        
        # Set bench characters
        self.bench["A"] = [c for c in team_a if not c.get("is_active", True)]
        self.bench["B"] = [c for c in team_b if not c.get("is_active", True)]
        
        return team_a_fl, team_b_fl
    
    def _find_field_leader(self, team, team_key):
        """Find the Field Leader in a team
        
        Args:
            team: Team characters
            team_key: Team identifier ("A" or "B")
            
        Returns:
            dict: Field Leader character or None
        """
        for char in team:
            if char.get("role") == "FL" and char.get("is_active", True):
                return char
        
        # If no active FL found, try to find one on the bench
        for char in team:
            if char.get("role") == "FL" and not char.get("is_active", True):
                # Mark as active and move from bench
                char["is_active"] = True
                
                # Log substitution
                self.substitutions.append({
                    "team": team_key,
                    "type": "initial_activation",
                    "character": char["name"],
                    "reason": "No active Field Leader"
                })
                
                return char
        
        # If no FL at all, promote highest LDR character
        if team:
            # Sort by Leadership attribute
            sorted_team = sorted(team, key=lambda x: x.get("aLDR", 0), reverse=True)
            
            # Get highest LDR character
            new_fl = sorted_team[0]
            new_fl["role"] = "FL"
            
            # Log promotion
            self.substitutions.append({
                "team": team_key,
                "type": "promotion",
                "character": new_fl["name"],
                "reason": "No Field Leader available"
            })
            
            return new_fl
        
        return None
    
    def handle_field_leader_ko(self, team, team_key, show_details=False):
        """Handle Field Leader knockout with substitution
        
        Args:
            team: Team characters
            team_key: Team identifier ("A" or "B")
            show_details: Whether to show detailed output
            
        Returns:
            dict: New Field Leader or None
        """
        # Get current Field Leader
        current_fl_id = self.active_field_leaders.get(team_key)
        
        if not current_fl_id:
            return None
        
        # Find Field Leader in team
        current_fl = None
        for char in team:
            if char.get("id") == current_fl_id:
                current_fl = char
                break
        
        if not current_fl:
            return None
        
        # Check if Field Leader is KO'd
        if not current_fl.get("is_ko", False):
            return current_fl
            
        # Record knockout
        self.knockouts[team_key].append(current_fl["id"])
        
        # Field Leader is KO'd, find replacement
        new_fl = self._find_replacement_leader(team, team_key)
        
        if new_fl:
            # Log substitution
            substitution = {
                "team": team_key,
                "type": "substitution",
                "ko_character": current_fl["name"],
                "replacement": new_fl["name"],
                "reason": "Field Leader KO"
            }
            
            self.substitutions.append(substitution)
            self.active_field_leaders[team_key] = new_fl["id"]
            
            if show_details:
                print(f"Field Leader substitution: {current_fl['name']} → {new_fl['name']}")
            
            # Apply Field Leader buffs to new leader
            self._apply_field_leader_buffs(new_fl)
            
            return new_fl
        
        # No replacement found
        if show_details:
            print(f"No replacement found for KO'd Field Leader {current_fl['name']}")
        
        return None
    
    def _find_replacement_leader(self, team, team_key):
        """Find a replacement Field Leader
        
        Args:
            team: Team characters
            team_key: Team identifier ("A" or "B")
            
        Returns:
            dict: Replacement Field Leader or None
        """
        # First check active characters with high Leadership
        active_candidates = [c for c in team if c.get("is_active", True) and not c.get("is_ko", False)]
        
        if active_candidates:
            # Sort by Leadership attribute
            sorted_candidates = sorted(active_candidates, key=lambda x: x.get("aLDR", 0), reverse=True)
            
            # Select highest LDR character
            new_fl = sorted_candidates[0]
            new_fl["role"] = "FL"
            return new_fl
        
        # Check bench if no active candidates
        bench_candidates = self.bench[team_key]
        
        if bench_candidates:
            # Sort by Leadership attribute
            sorted_bench = sorted(bench_candidates, key=lambda x: x.get("aLDR", 0), reverse=True)
            
            # Select highest LDR character
            new_fl = sorted_bench[0]
            new_fl["role"] = "FL"
            new_fl["is_active"] = True
            
            # Remove from bench
            self.bench[team_key] = [c for c in self.bench[team_key] if c["id"] != new_fl["id"]]
            
            return new_fl
        
        return None
    
    def _apply_field_leader_buffs(self, character):
        """Apply Field Leader buffs to a character
        
        Args:
            character: Character to buff
            
        Returns:
            dict: Buffed character
        """
        # Boost Leadership impact
        leadership = character.get("aLDR", 5)
        
        # HP/Stamina boost based on LDR
        character["HP"] = min(100, character.get("HP", 100) + leadership * 2)
        character["stamina"] = min(100, character.get("stamina", 100) + leadership * 3)
        
        # Add Field Leader trait if not present
        if "traits" in character and "leadership" not in character["traits"]:
            character["traits"].append("leadership")
        
        return character
    
    def get_substitution_stats(self):
        """Get statistics about Field Leader substitutions
        
        Returns:
            dict: Substitution statistics
        """
        stats = {
            "total_substitutions": len(self.substitutions),
            "team_a_substitutions": sum(1 for s in self.substitutions if s["team"] == "A"),
            "team_b_substitutions": sum(1 for s in self.substitutions if s["team"] == "B"),
            "substitution_log": self.substitutions,
            "team_a_knockouts": len(self.knockouts["A"]),
            "team_b_knockouts": len(self.knockouts["B"])
        }
        
        return stats