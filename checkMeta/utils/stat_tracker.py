"""
META Fantasy League Simulator - Stat Tracking System
Handles tracking, validation, and processing of result statistics
"""

import os
import csv
import json
import datetime
from collections import defaultdict
from typing import Dict, List, Any, Optional

class StatTracker:
    """System for tracking character and team statistics"""
    
    def __init__(self):
        """Initialize the stat tracker"""
        self.character_stats = {}
        self.team_stats = {}
        self.canonical_rstats = self._get_canonical_rstats()
    
    def _get_canonical_rstats(self):
        """Get the canonical rStat definitions"""
        return {
            # Get all stat fields
            all_fields = set()
            for stats in self.team_stats.values():
                all_fields.update(stats.keys())
            
            # Remove basic fields that should come first
            base_fields = ["team_id", "team_name", "matches", "wins", "losses", "draws"]
            stat_fields = sorted([f for f in all_fields if f not in base_fields and f != "characters"])
            
            # Create writer with all fields
            writer = csv.DictWriter(f, fieldnames=base_fields + stat_fields)
            writer.writeheader()
            
            # Write team stats
            for team_id, stats in self.team_stats.items():
                # Create a copy without the characters list
                row = {k: v for k, v in stats.items() if k != "characters"}
                writer.writerow(row)
        
        # Export stat definitions for reference
        def_path = f"{output_path}_definitions.json"
        
        with open(def_path, "w") as f:
            json.dump(self.canonical_rstats, f, indent=2)
        
        print(f"Exported stats to {char_path} and {team_path}")
        return (char_path, team_path, def_path)
    
    def export_stats_json(self, output_path=None):
        """Export tracked stats to JSON files"""
        # Generate default path if none provided
        timestamp = int(datetime.datetime.now().timestamp())
        if output_path is None:
            output_path = f"results/stats/stats_{timestamp}"
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Export character stats
        char_path = f"{output_path}_characters.json"
        
        with open(char_path, "w") as f:
            json.dump(self.character_stats, f, indent=2)
        
        # Export team stats
        team_path = f"{output_path}_teams.json"
        
        with open(team_path, "w") as f:
            json.dump(self.team_stats, f, indent=2)
        
        # Export stat definitions
        def_path = f"{output_path}_definitions.json"
        
        with open(def_path, "w") as f:
            json.dump(self.canonical_rstats, f, indent=2)
        
        print(f"Exported JSON stats to {char_path} and {team_path}")
        return (char_path, team_path, def_path)
    
    def get_top_performers(self, stat_name, limit=5):
        """Get top performers for a specific stat"""
        # Ensure rStat format
        if not stat_name.startswith('r'):
            stat_name = 'r' + stat_name
        
        # Collect characters with this stat
        performers = []
        for char_id, stats in self.character_stats.items():
            if stat_name in stats:
                performers.append({
                    "id": char_id,
                    "name": stats.get("name", "Unknown"),
                    "value": stats[stat_name],
                    "team_id": stats.get("team_id", "unknown"),
                    "role": stats.get("role", "Unknown")
                })
        
        # Sort by value (descending)
        performers.sort(key=lambda x: x["value"], reverse=True)
        
        # Return top performers
        return performers[:limit]
    
    def get_team_rankings(self, sort_by="wins"):
        """Get team rankings sorted by a specific stat"""
        # Collect teams with rankings
        rankings = []
        for team_id, stats in self.team_stats.items():
            # Calculate win percentage
            matches = stats.get("matches", 0)
            win_pct = 0
            if matches > 0:
                wins = stats.get("wins", 0)
                draws = stats.get("draws", 0)
                win_pct = ((wins + (draws * 0.5)) / matches) * 100
            
            rankings.append({
                "team_id": team_id,
                "team_name": stats.get("team_name", "Unknown"),
                "matches": stats.get("matches", 0),
                "wins": stats.get("wins", 0),
                "losses": stats.get("losses", 0),
                "draws": stats.get("draws", 0),
                "win_pct": win_pct
            })
        
        # Sort by requested field
        if sort_by == "win_pct":
            rankings.sort(key=lambda x: x["win_pct"], reverse=True)
        else:
            rankings.sort(key=lambda x: x.get(sort_by, 0), reverse=True)
        
        return rankings Shared stats (used by both divisions)
            "DD": {
                "name": "Damage Dealt",
                "domain": "b",
                "description": "Total damage inflicted on opponents"
            },
            "DS": {
                "name": "Damage Sustained",
                "domain": "b",
                "description": "Total damage received from opponents"
            },
            "OTD": {
                "name": "Opponent Takedown",
                "domain": "b",
                "description": "Successfully defeating an opponent"
            },
            "AST": {
                "name": "Assists",
                "domain": "b",
                "description": "Contributing to an opponent's defeat without landing the final blow"
            },
            "ULT": {
                "name": "Ultimate Move Impact",
                "domain": "b",
                "description": "Successful execution of a character's ultimate ability"
            },
            "LVS": {
                "name": "Lives Saved",
                "domain": "b",
                "description": "Preventing an ally from being defeated"
            },
            "LLS": {
                "name": "Lives Lost",
                "domain": "b",
                "description": "Instances of ally defeat"
            },
            "CTT": {
                "name": "Counterattacks",
                "domain": "b",
                "description": "Successful defensive attacks"
            },
            "EVS": {
                "name": "Evasion Success",
                "domain": "b",
                "description": "Successfully avoiding enemy attacks"
            },
            "HLG": {
                "name": "Healing",
                "domain": "b",
                "description": "Total healing provided to allies"
            },
            "WIN": {
                "name": "Matches Won",
                "domain": "b",
                "description": "Number of matches won"
            },
            "LOSS": {
                "name": "Matches Lost",
                "domain": "b",
                "description": "Number of matches lost"
            },
            "DRAW": {
                "name": "Matches Drawn",
                "domain": "b",
                "description": "Number of matches drawn"
            },
            
            # Operations division specific
            "CVo": {
                "name": "Convergence Victory",
                "domain": "o",
                "description": "Winning a convergence battle (Operations)"
            },
            "DVo": {
                "name": "Defensive Victory",
                "domain": "o",
                "description": "Successfully defending against an attack (Operations)"
            },
            "KNBo": {
                "name": "Knockbacks",
                "domain": "o",
                "description": "Pushing back opponents with forceful attacks (Operations)"
            },
            "DDo": {
                "name": "Damage Dealt - Ops",
                "domain": "o",
                "description": "Damage dealt by Operations characters"
            },
            "DSo": {
                "name": "Damage Sustained - Ops",
                "domain": "o",
                "description": "Damage taken by Operations characters"
            },
            
            # Intelligence division specific
            "MBi": {
                "name": "Mind Break",
                "domain": "i",
                "description": "Winning a convergence battle (Intelligence)"
            },
            "ILSi": {
                "name": "Illusion Success",
                "domain": "i",
                "description": "Successfully creating tactical illusions (Intelligence)"
            },
            "DDi": {
                "name": "Damage Dealt - Intel",
                "domain": "i",
                "description": "Damage dealt by Intelligence characters"
            },
            "DSi": {
                "name": "Damage Sustained - Intel",
                "domain": "i",
                "description": "Damage taken by Intelligence characters"
            }
        }
    
    def register_character(self, character):
        """Register a character for stat tracking"""
        char_id = character.get("id", "unknown")
        
        if char_id not in self.character_stats:
            self.character_stats[char_id] = {
                "id": char_id,
                "name": character.get("name", "Unknown"),
                "team_id": character.get("team_id", "unknown"),
                "role": character.get("role", "Unknown"),
                "division": character.get("division", "o"),
                "matches": 0,
                "wins": 0,
                "losses": 0,
                "draws": 0
            }
            
            # Register team if needed
            team_id = character.get("team_id", "unknown")
            if team_id not in self.team_stats:
                self.team_stats[team_id] = {
                    "team_id": team_id,
                    "team_name": character.get("team_name", "Unknown Team"),
                    "matches": 0,
                    "wins": 0,
                    "losses": 0,
                    "draws": 0,
                    "characters": []
                }
            
            # Add character to team roster
            if char_id not in self.team_stats[team_id]["characters"]:
                self.team_stats[team_id]["characters"].append(char_id)
    
    def record_match_result(self, character, result):
        """Record match result for a character"""
        char_id = character.get("id", "unknown")
        team_id = character.get("team_id", "unknown")
        
        # Update character stats
        if char_id in self.character_stats:
            self.character_stats[char_id]["matches"] += 1
            
            if result == "win":
                self.character_stats[char_id]["wins"] += 1
            elif result == "loss":
                self.character_stats[char_id]["losses"] += 1
            elif result == "draw":
                self.character_stats[char_id]["draws"] += 1
        
        # Update team stats
        if team_id in self.team_stats:
            # Team match results are tracked separately based on team-level outcomes
            pass
    
    def record_team_result(self, team_id, result):
        """Record match result for a team"""
        if team_id in self.team_stats:
            self.team_stats[team_id]["matches"] += 1
            
            if result == "win":
                self.team_stats[team_id]["wins"] += 1
            elif result == "loss":
                self.team_stats[team_id]["losses"] += 1
            elif result == "draw":
                self.team_stats[team_id]["draws"] += 1
    
    def update_character_stat(self, char_id, stat_name, value, operation="add"):
        """Update a specific stat for a character"""
        # Ensure rStat names start with 'r'
        if not stat_name.startswith('r'):
            stat_name = 'r' + stat_name
        
        if char_id in self.character_stats:
            if operation == "add":
                if stat_name not in self.character_stats[char_id]:
                    self.character_stats[char_id][stat_name] = 0
                self.character_stats[char_id][stat_name] += value
            elif operation == "set":
                self.character_stats[char_id][stat_name] = value
            elif operation == "max":
                if stat_name not in self.character_stats[char_id]:
                    self.character_stats[char_id][stat_name] = value
                else:
                    self.character_stats[char_id][stat_name] = max(
                        self.character_stats[char_id][stat_name],
                        value
                    )
    
    def update_team_stat(self, team_id, stat_name, value, operation="add"):
        """Update a specific stat for a team"""
        # Ensure team stat names start with 't'
        if not stat_name.startswith('t'):
            stat_name = 't' + stat_name
        
        if team_id in self.team_stats:
            if operation == "add":
                if stat_name not in self.team_stats[team_id]:
                    self.team_stats[team_id][stat_name] = 0
                self.team_stats[team_id][stat_name] += value
            elif operation == "set":
                self.team_stats[team_id][stat_name] = value
            elif operation == "max":
                if stat_name not in self.team_stats[team_id]:
                    self.team_stats[team_id][stat_name] = value
                else:
                    self.team_stats[team_id][stat_name] = max(
                        self.team_stats[team_id][stat_name],
                        value
                    )
    
    def validate_rstats(self, character):
        """Validate and normalize rStats for a character"""
        # Get character division
        division = character.get("division", "o")
        
        # Ensure rStats exists
        if "rStats" not in character:
            character["rStats"] = {}
        
        # Get current rStats
        rstats = character["rStats"]
        
        # Check each stat against canonical definitions
        validated = {}
        
        for stat_name, stat_value in rstats.items():
            # Strip 'r' prefix if present
            base_stat = stat_name[1:] if stat_name.startswith('r') else stat_name
            
            # Check if stat is in canonical list
            if base_stat in self.canonical_rstats:
                stat_def = self.canonical_rstats[base_stat]
                
                # Check if stat is valid for this division
                if stat_def["domain"] == "b" or stat_def["domain"] == division:
                    # Add 'r' prefix for storage
                    validated[f"r{base_stat}"] = stat_value
        
        # Update character's rStats
        character["rStats"] = validated
        
        return validated
    
    def track_combat_event(self, character, event_type, value=1, opponent=None, context=None):
        """Track a combat-related event"""
        # Get character properties
        division = character.get("division", "o")
        
        # Map events to stats
        event_to_stat = {
            # General stats
            "damage_dealt": "DD",
            "damage_taken": "DS",
            "ko_caused": "OTD",
            "assist": "AST",
            "ultimate_move": "ULT",
            "lives_saved": "LVS",
            "evasion": "EVS",
            "healing": "HLG",
            
            # Specific stats
            "convergence_win": "CVo" if division == "o" else "MBi",
            "counterattack": "CTT",
            "illusion": "ILSi",
            "knockback": "KNBo"
        }
        
        # Update appropriate stat
        if event_type in event_to_stat:
            stat_name = event_to_stat[event_type]
            
            # Add division suffix for damage stats
            if stat_name == "DD" or stat_name == "DS":
                stat_name = f"{stat_name}{division}"
                
            self.update_character_stat(character.get("id", "unknown"), stat_name, value)
        
        # Special handling for KO events
        if event_type == "ko_caused" and opponent:
            # Update team KO stats
            team_id = character.get("team_id", "unknown")
            opp_team_id = opponent.get("team_id", "unknown")
            
            self.update_team_stat(team_id, "KO_CAUSED", 1)
            self.update_team_stat(opp_team_id, "KO_SUFFERED", 1)
            
            # Special handling for Field Leader KO
            if opponent.get("role") == "FL":
                self.update_team_stat(team_id, "FL_KO_CAUSED", 1)
                self.update_team_stat(opp_team_id, "FL_KO_SUFFERED", 1)
    
    def export_stats(self, output_path=None):
        """Export all stats to CSV files"""
        # Create default output path if needed
        timestamp = int(datetime.datetime.now().timestamp())
        if output_path is None:
            output_path = f"results/stats/stats_{timestamp}"
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Export character stats
        char_path = f"{output_path}_characters.csv"
        
        with open(char_path, "w", newline="") as f:
            # Get all stat fields
            all_fields = set()
            for stats in self.character_stats.values():
                all_fields.update(stats.keys())
            
            # Remove basic fields that should come first
            base_fields = ["id", "name", "team_id", "role", "division", "matches", "wins", "losses", "draws"]
            stat_fields = sorted([f for f in all_fields if f not in base_fields])
            
            # Create writer with all fields
            writer = csv.DictWriter(f, fieldnames=base_fields + stat_fields)
            writer.writeheader()
            
            # Write character stats
            for char_id, stats in self.character_stats.items():
                writer.writerow(stats)
        
        # Export team stats
        team_path = f"{output_path}_teams.csv"
        
        with open(team_path, "w", newline="") as f:
            #