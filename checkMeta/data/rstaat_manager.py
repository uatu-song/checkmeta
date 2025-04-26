# systems/rstat_manager.py

import csv
import os
import datetime
from collections import defaultdict

class RStatManager:
    """
    Manages recording and tracking of rStats based on the correct original design.
    """
    
    def __init__(self):
        """Initialize the rStat Manager with the canonical rStat definitions"""
        # Dictionary to store all unit stats
        self.unit_stats = defaultdict(lambda: defaultdict(int))
        
        # Basic canonical rStats (corrected based on your feedback)
        self.canonical_rstats = {
            # General stats (shared across divisions)
            "DD": "Damage Dealt",
            "DS": "Damage Sustained",
            "OTD": "Opponent Takedown",  # Shared stat as requested
            "AST": "Assists",
            "ULT": "Ultimate Ability Uses",
            "LVS": "Lives Saved",
            "LLS": "Lives Lost",
            "CTT": "Critical Hits",
            "EVS": "Evasions",
            "FFD": "Friendly Fire Damage",
            "FFI": "Friendly Fire Incidents",
            "HLG": "Healing Provided",
            "LKO": "Loss by KO",
            "WIN": "Matches Won",
            "LOSS": "Matches Lost",
            "DRAW": "Matches Drawn",
            "CVG_WIN": "Convergence Wins",
            "CVG_LOSS": "Convergence Losses",
            
            # Operations division specific
            "RTDo": "Ranged Takedowns",  # Corrected from RTOo
            "CQTo": "Close Quarters Takedowns",
            "BRXo": "Breach Executions",
            "HWIo": "Heavy Weapons Impact",
            "MOTo": "Mobility Tactics",
            "AMBo": "Ambush Successes",
            
            # Intelligence division specific
            "MBi": "Mental Battles",
            "ILSi": "Illusion Success",  # Corrected
            "FEi": "Field Encryptions",
            "DSRi": "Disruption Effect",  # Corrected
            "INFi": "Infiltration Success",  # Corrected
            "RSPi": "Remote System Penetrations"
        }
        
        # Team-level stats
        self.team_stats = defaultdict(lambda: defaultdict(int))
        self.team_stat_categories = {
            "FL_SUB": "Field Leader Substitutions",
            "FL_DOWN": "Field Leader Knocked Down",
            "TOTAL_WIN": "Total Team Wins",
            "TOTAL_LOSS": "Total Team Losses"
        }
    
    def register_unit(self, unit_id, name, division, role, team_id):
        """Register a unit for stat tracking with its basic metadata"""
        self.unit_stats[unit_id]["unit_id"] = unit_id
        self.unit_stats[unit_id]["name"] = name
        self.unit_stats[unit_id]["division"] = division
        self.unit_stats[unit_id]["role"] = role
        self.unit_stats[unit_id]["team_id"] = team_id
    
    def update_stat(self, unit_id, stat_name, value=1, operation="add"):
        """
        Update a specific stat for a unit
        
        Parameters:
        - unit_id: ID of the character
        - stat_name: Name of the stat to update (with or without 'r' prefix)
        - value: Value to add/set
        - operation: 'add' (default), 'set', or 'max'
        """
        # Strip 'r' prefix if present
        base_stat = stat_name[1:] if stat_name.startswith('r') else stat_name
        
        # Add 'r' prefix for storage
        full_stat_name = f"r{base_stat}"
        
        # Update based on operation type
        if operation == "add":
            self.unit_stats[unit_id][full_stat_name] += value
        elif operation == "set":
            self.unit_stats[unit_id][full_stat_name] = value
        elif operation == "max":
            self.unit_stats[unit_id][full_stat_name] = max(self.unit_stats[unit_id][full_stat_name], value)
    
    def update_team_stat(self, team_id, stat_name, value=1, operation="add"):
        """Update a team-level stat"""
        # Add 't' prefix for storage
        full_stat_name = f"t{stat_name}"
        
        # Update based on operation type
        if operation == "add":
            self.team_stats[team_id][full_stat_name] += value
        elif operation == "set":
            self.team_stats[team_id][full_stat_name] = value
        elif operation == "max":
            self.team_stats[team_id][full_stat_name] = max(self.team_stats[team_id][full_stat_name], value)
    
    def track_combat_event(self, unit, event_type, context=None, value=1, opponent=None):
        """
        Track a combat-related event and update appropriate stats
        
        Parameters:
        - unit: Unit dictionary
        - event_type: Type of combat event
        - context: Match context (optional)
        - value: Numeric value for the event
        - opponent: Optional opponent unit
        """
        unit_id = unit["id"]
        division = unit.get("division", "o")  # Default to operations if not specified
        
        # Simple mapping of events to stats
        event_to_stat = {
            "damage_dealt": "DD",
            "damage_taken": "DS",
            "ko_caused": "OTD",
            "ko_suffered": "LKO",
            "critical_hit": "CTT",
            "evasion": "EVS",
            "healing": "HLG",
            "civilian_rescue": "LVS",
            "civilian_loss": "LLS",
            "friendly_fire": "FFI",
            "assist": "AST",
            "special_ability": "ULT",
            "convergence_win": "CVG_WIN",
            "convergence_loss": "CVG_LOSS"
        }
        
        # Division-specific events
        ops_events = {
            "ranged_takedown": "RTDo",  # Corrected
            "close_quarters_takedown": "CQTo",
            "breakthrough": "BRXo",
            "heavy_weapons_impact": "HWIo",
            "multi_opponent_takedown": "MOTo",
            "ambush": "AMBo"
        }
        
        intel_events = {
            "mindbreak": "MBi",
            "illusion": "ILSi",  # Corrected
            "forced_errors": "FEi",
            "disruption": "DSRi",  # Corrected
            "infiltration": "INFi",  # Corrected
            "reality_shift_impact": "RSIi"
        }
        
        # Update general stats
        if event_type in event_to_stat:
            self.update_stat(unit_id, event_to_stat[event_type], value)
        
        # Update division-specific stats
        if division == "o" and event_type in ops_events:
            self.update_stat(unit_id, ops_events[event_type], value)
        elif division == "i" and event_type in intel_events:
            self.update_stat(unit_id, intel_events[event_type], value)
            
        # Special case for Field Leader KO
        if event_type == "ko_suffered" and unit.get("role") == "FL":
            team_id = unit.get("team_id", "unknown")
            self.update_team_stat(team_id, "FL_DOWN", 1)
    
    def record_match_result(self, unit, result):
        """Record the result of a match for a unit"""
        unit_id = unit["id"]
        team_id = unit.get("team_id", "unknown")
        
        if result == "win":
            self.update_stat(unit_id, "WIN", 1)
            self.update_team_stat(team_id, "TOTAL_WIN", 1)
        elif result == "loss":
            self.update_stat(unit_id, "LOSS", 1)
            self.update_team_stat(team_id, "TOTAL_LOSS", 1)
        elif result == "draw":
            self.update_stat(unit_id, "DRAW", 1)
    
    def handle_field_leader_substitution(self, team_id, old_fl, new_fl):
        """Handle a Field Leader substitution"""
        self.update_team_stat(team_id, "FL_SUB", 1)
        
        # Track special ability use for the new FL
        if new_fl and "id" in new_fl:
            self.update_stat(new_fl["id"], "ULT", 1)
    
    def export_stats_to_csv(self, output_path=None):
        """Export all rStats to CSV file"""
        if output_path is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = "rstats_records"
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"rstats_{timestamp}.csv")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Define metadata fields
        metadata_fields = ["unit_id", "name", "division", "role", "team_id"]
        
        # Get all actual stats fields
        stat_fields = []
        for unit_stats in self.unit_stats.values():
            for key in unit_stats.keys():
                if key not in metadata_fields and key not in stat_fields:
                    stat_fields.append(key)
        
        # Create fieldnames with metadata first
        fieldnames = metadata_fields + sorted(stat_fields)
        
        # Write CSV
        with open(output_path, "w", newline='', encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for unit_id, stats in self.unit_stats.items():
                writer.writerow(stats)
        
        # Export team stats as well
        team_output = os.path.join(os.path.dirname(output_path), f"team_stats_{timestamp}.csv")
        with open(team_output, "w", newline='', encoding="utf-8") as csvfile:
            team_fields = ["team_id"] + sorted(f"t{field}" for field in self.team_stat_categories.keys())
            writer = csv.DictWriter(csvfile, fieldnames=team_fields)
            writer.writeheader()
            
            for team_id, stats in self.team_stats.items():
                row = {"team_id": team_id}
                row.update(stats)
                writer.writerow(row)
        
        return output_path