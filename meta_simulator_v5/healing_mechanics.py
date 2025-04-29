"""
META Fantasy League Simulator - Healing Mechanics
Extends the injury system with healing capabilities
"""

import os
import json
import random
import logging
import datetime
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum

logger = logging.getLogger("HealingMechanics")

class HealingMechanics:
    """System for handling healing of injuries and stamina restoration"""
    
    def __init__(self, injury_system=None, config=None):
        """Initialize the healing mechanics
        
        Args:
            injury_system: Reference to the injury system
            config: Optional configuration object
        """
        self.injury_system = injury_system
        self.config = config
        
        # Healing trait identifiers
        self.healing_traits = [
            "healing",               # Main healing trait
            "rapid_healing",         # Variant
            "regeneration",          # Variant
            "medical_expertise",     # Variant
            "restoration",           # Variant
            "recovery_aura"          # Team healing variant
        ]
        
        # Healing power by trait (1-10 scale)
        self.healing_power = {
            "healing": 5,            # Standard healing
            "rapid_healing": 7,      # Enhanced healing
            "regeneration": 8,       # Powerful healing
            "medical_expertise": 6,  # Technical healing
            "restoration": 6,        # Restorative healing
            "recovery_aura": 4       # Team-wide but weaker
        }
        
        # Stamina cost per healing attempt
        self.base_stamina_cost = 15  # Base cost
        
        # Stamina cost multipliers by injury severity
        self.severity_cost_multipliers = {
            "MINOR": 1.0,            # Standard cost
            "MODERATE": 1.5,         # 50% more stamina
            "MAJOR": 2.0,            # Double stamina
            "SEVERE": 3.0            # Triple stamina
        }
        
        # Healing success chances by severity
        self.base_success_chances = {
            "MINOR": 0.8,            # 80% chance
            "MODERATE": 0.6,         # 60% chance
            "MAJOR": 0.4,            # 40% chance
            "SEVERE": 0.2            # 20% chance
        }
        
        # Recovery match reduction by severity (on successful healing)
        self.recovery_reductions = {
            "MINOR": 1,              # Complete healing
            "MODERATE": 1,           # Reduce by 1 match
            "MAJOR": 1,              # Reduce by 1 match
            "SEVERE": 1              # Reduce by 1 match
        }
        
        # Healing logs
        self.healing_history = {}
        
        # Initialize persistence
        self._ensure_persistence_directory()
    
    def _ensure_persistence_directory(self) -> None:
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
    
    def _get_healing_history_path(self, team_id: str) -> str:
        """Get path to healing history file for a team
        
        Args:
            team_id: Team ID
            
        Returns:
            str: Path to healing history file
        """
        persistence_dir = self._get_persistence_directory()
        return os.path.join(persistence_dir, f"{team_id}_healing_history.json")
    
    def identify_healers(self, team: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify characters with healing capabilities in a team
        
        Args:
            team: List of team characters
            
        Returns:
            list: Characters with healing capabilities
        """
        healers = []
        
        for character in team:
            # Check for healing traits
            has_healing_trait = False
            for trait in character.get("traits", []):
                if trait in self.healing_traits:
                    has_healing_trait = True
                    break
            
            # Add character if they have healing traits
            if has_healing_trait:
                healers.append({
                    "character": character,
                    "healing_trait": trait,
                    "healing_power": self.healing_power.get(trait, 5)
                })
        
        return healers
    
    def attempt_healing(self, healer: Dict[str, Any], injured: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt to heal an injured character
        
        Args:
            healer: Healer character
            injured: Injured character
            
        Returns:
            dict: Healing results
        """
        # Check if injury system is available
        if not self.injury_system:
            return {"success": False, "error": "Injury system not available"}
        
        # Check if healer has healing trait
        healing_trait = None
        healing_power = 0
        
        for trait in healer.get("traits", []):
            if trait in self.healing_traits:
                healing_trait = trait
                healing_power = self.healing_power.get(trait, 5)
                break
        
        if not healing_trait:
            return {"success": False, "error": "Character does not have healing capabilities"}
        
        # Check if injured character is actually injured
        if not self.injury_system.is_character_injured(injured):
            return {"success": False, "error": "Character is not injured"}
        
        # Get injury details
        char_id = injured.get("id", "unknown")
        injury = self.injury_system.injured_reserve.get(char_id)
        
        if not injury:
            return {"success": False, "error": "Injury details not found"}
        
        # Get injury severity
        severity = injury.get("severity", "MINOR")
        
        # Calculate stamina cost
        base_cost = self.base_stamina_cost
        multiplier = self.severity_cost_multipliers.get(severity, 1.0)
        stamina_cost = base_cost * multiplier
        
        # Check if healer has enough stamina
        if healer.get("stamina", 0) < stamina_cost:
            return {"success": False, "error": "Insufficient stamina to perform healing"}
        
        # Calculate success chance
        base_chance = self.base_success_chances.get(severity, 0.5)
        
        # Modify chance based on healing power and attributes
        power_modifier = (healing_power / 10.0) * 0.3  # 0-30% bonus
        
        # WIL (Willpower) improves healing
        wil = healer.get("aWIL", 5)
        wil_modifier = ((wil - 5) / 5.0) * 0.2  # +/- 20% based on WIL
        
        # RES (Resilience) of injured character improves chance
        res = injured.get("aRES", 5)
        res_modifier = ((res - 5) / 5.0) * 0.1  # +/- 10% based on RES
        
        # Calculate final success chance
        success_chance = base_chance + power_modifier + wil_modifier + res_modifier
        success_chance = max(0.05, min(success_chance, 0.95))  # Clamp between 5-95%
        
        # Apply stamina cost
        healer["stamina"] = max(0, healer.get("stamina", 100) - stamina_cost)
        
        # Roll for success
        success = random.random() < success_chance
        
        # Process healing outcome
        if success:
            # Determine recovery reduction
            reduction = self.recovery_reductions.get(severity, 1)
            
            # Apply recovery reduction
            current_remaining = injury.get("matches_remaining", 0)
            new_remaining = max(0, current_remaining - reduction)
            
            # Update injury
            injury["matches_remaining"] = new_remaining
            
            # If fully healed, remove from IR
            if new_remaining == 0:
                # Get recovery bonuses
                self.injury_system.restore_attributes(injured)
                del self.injury_system.injured_reserve[char_id]
                logger.info(f"{injured.get('name', 'Unknown')} fully healed by {healer.get('name', 'Unknown')}")
            else:
                # Update injury record
                self.injury_system.injured_reserve[char_id] = injury
                logger.info(f"{injured.get('name', 'Unknown')}'s recovery time reduced by {reduction} matches")
            
            # Save IR list
            self.injury_system._save_ir_list()
            
            # Record healing in history
            self._record_healing_attempt(healer, injured, True, stamina_cost, reduction)
            
            # Return success details
            return {
                "success": True,
                "stamina_cost": stamina_cost,
                "previous_remaining": current_remaining,
                "new_remaining": new_remaining,
                "reduction": reduction,
                "fully_healed": new_remaining == 0
            }
        else:
            # Record failed attempt
            self._record_healing_attempt(healer, injured, False, stamina_cost, 0)
            
            logger.info(f"{healer.get('name', 'Unknown')} failed to heal {injured.get('name', 'Unknown')}")
            
            # Return failure details
            return {
                "success": False,
                "stamina_cost": stamina_cost,
                "previous_remaining": injury.get("matches_remaining", 0),
                "new_remaining": injury.get("matches_remaining", 0),
                "reduction": 0,
                "error": "Healing attempt failed"
            }
    
    def _record_healing_attempt(self, healer: Dict[str, Any], injured: Dict[str, Any], success: bool, stamina_cost: float, reduction: int) -> None:
        """Record a healing attempt in history
        
        Args:
            healer: Healer character
            injured: Injured character
            success: Whether the attempt was successful
            stamina_cost: Stamina cost of the attempt
            reduction: Recovery time reduction (if successful)
        """
        team_id = healer.get("team_id", "unknown")
        
        # Create healing record
        healing_record = {
            "timestamp": self._get_timestamp(),
            "healer_id": healer.get("id", "unknown"),
            "healer_name": healer.get("name", "Unknown"),
            "injured_id": injured.get("id", "unknown"),
            "injured_name": injured.get("name", "Unknown"),
            "success": success,
            "stamina_cost": stamina_cost,
            "reduction": reduction,
            "injury_type": self.injury_system.injured_reserve.get(injured.get("id", "unknown"), {}).get("injury_type", "Unknown")
        }
        
        # Load healing history
        history = self._load_healing_history(team_id)
        
        # Add new record
        if team_id not in history:
            history[team_id] = []
        
        history[team_id].append(healing_record)
        
        # Save updated history
        self._save_healing_history(team_id, history)
    
    def _load_healing_history(self, team_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """Load healing history for a team
        
        Args:
            team_id: Team ID
            
        Returns:
            dict: Healing history by team ID
        """
        history_path = self._get_healing_history_path(team_id)
        
        if os.path.exists(history_path):
            try:
                with open(history_path, 'r') as f:
                    history = json.load(f)
                return history
            except Exception as e:
                logger.error(f"Error loading healing history for {team_id}: {e}")
        
        return {}
    
    def _save_healing_history(self, team_id: str, history: Dict[str, List[Dict[str, Any]]]) -> None:
        """Save healing history for a team
        
        Args:
            team_id: Team ID
            history: Healing history to save
        """
        history_path = self._get_healing_history_path(team_id)
        
        try:
            with open(history_path, 'w') as f:
                json.dump(history, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving healing history for {team_id}: {e}")
    
    def heal_team_injuries(self, team: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Attempt to heal all injured characters in a team
        using available healers
        
        Args:
            team: List of team characters
            
        Returns:
            dict: Healing results
        """
        results = {
            "successful_healings": 0,
            "failed_attempts": 0,
            "healers_used": 0,
            "stamina_spent": 0,
            "healing_details": []
        }
        
        # Identify healers
        healers = self.identify_healers(team)
        
        if not healers:
            return {**results, "error": "No healers found in team"}
        
        # Identify injured characters
        injured_chars = []
        for char in team:
            if self.injury_system and self.injury_system.is_character_injured(char):
                injured_chars.append(char)
        
        if not injured_chars:
            return {**results, "error": "No injured characters found in team"}
        
        # Sort injured characters by severity (most severe first)
        injured_chars.sort(key=lambda x: self._get_injury_severity_value(x), reverse=True)
        
        # Sort healers by healing power (most powerful first)
        healers.sort(key=lambda x: x["healing_power"], reverse=True)
        
        # Process healing attempts
        healers_used = set()
        
        for injured in injured_chars:
            # Try each healer until successful or all healers exhausted
            for healer_info in healers:
                healer = healer_info["character"]
                
                # Skip healers with insufficient stamina
                char_id = injured.get("id", "unknown")
                injury = self.injury_system.injured_reserve.get(char_id, {})
                severity = injury.get("severity", "MINOR")
                stamina_needed = self.base_stamina_cost * self.severity_cost_multipliers.get(severity, 1.0)
                
                if healer.get("stamina", 0) < stamina_needed:
                    continue
                
                # Attempt healing
                healing_result = self.attempt_healing(healer, injured)
                
                # Record result
                results["healing_details"].append({
                    "healer": healer.get("name", "Unknown"),
                    "injured": injured.get("name", "Unknown"),
                    "success": healing_result.get("success", False),
                    "stamina_cost": healing_result.get("stamina_cost", 0),
                    "recovery_reduction": healing_result.get("reduction", 0)
                })
                
                # Update statistics
                if healing_result.get("success", False):
                    results["successful_healings"] += 1
                else:
                    results["failed_attempts"] += 1
                
                healers_used.add(healer.get("id", "unknown"))
                results["stamina_spent"] += healing_result.get("stamina_cost", 0)
                
                # If successful or this is the last healer, move to next injured
                if healing_result.get("success", False) or healer == healers[-1]["character"]:
                    break
        
        # Update final statistics
        results["healers_used"] = len(healers_used)
        
        return results
    
    def _get_injury_severity_value(self, character: Dict[str, Any]) -> int:
        """Get numeric severity value for an injured character
        
        Args:
            character: Character to check
            
        Returns:
            int: Severity value (0-4, higher is more severe)
        """
        if not self.injury_system:
            return 0
            
        char_id = character.get("id", "unknown")
        injury = self.injury_system.injured_reserve.get(char_id, {})
        severity = injury.get("severity", "MINOR")
        
        severity_values = {
            "MINOR": 1,
            "MODERATE": 2,
            "MAJOR": 3,
            "SEVERE": 4
        }
        
        return severity_values.get(severity, 0)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp
        
        Returns:
            str: Formatted timestamp
        """
        return datetime.datetime.now().isoformat()
    
    def generate_healing_report(self, team_id: str) -> str:
        """Generate a text report of healing activities
        
        Args:
            team_id: Team ID
            
        Returns:
            str: Formatted healing report
        """
        # Load healing history
        history = self._load_healing_history(team_id)
        team_history = history.get(team_id, [])
        
        if not team_history:
            return f"No healing history found for team {team_id}"
        
        # Build report text
        text = f"=== HEALING REPORT: TEAM {team_id} ===\n"
        text += f"Total healing attempts: {len(team_history)}\n"
        
        # Calculate statistics
        successful = sum(1 for record in team_history if record.get("success", False))
        stamina_spent = sum(record.get("stamina_cost", 0) for record in team_history)
        recovery_reduced = sum(record.get("reduction", 0) for record in team_history)
        
        text += f"Successful healings: {successful} ({successful/len(team_history)*100:.1f}%)\n"
        text += f"Total stamina spent: {stamina_spent:.1f}\n"
        text += f"Total recovery time reduced: {recovery_reduced} matches\n\n"
        
        # Add recent healing activities
        text += "RECENT HEALING ACTIVITIES:\n"
        
        # Sort by timestamp (most recent first)
        recent = sorted(team_history, key=lambda x: x.get("timestamp", ""), reverse=True)[:5]
        
        for record in recent:
            timestamp = record.get("timestamp", "").split("T")[0]  # Extract date part
            healer = record.get("healer_name", "Unknown")
            injured = record.get("injured_name", "Unknown")
            injury_type = record.get("injury_type", "Unknown Injury")
            success = "Successful" if record.get("success", False) else "Failed"
            stamina = record.get("stamina_cost", 0)
            reduction = record.get("reduction", 0)
            
            text += f"  {timestamp}: {healer} -> {injured} ({injury_type})\n"
            text += f"    {success} attempt, {stamina:.1f} stamina used"
            
            if record.get("success", False):
                text += f", {reduction} matches reduced"
            
            text += "\n"
        
        return text
    
    def get_healer_efficiency(self, team: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Calculate healing efficiency for all healers in a team
        
        Args:
            team: Team characters
            
        Returns:
            dict: Healer efficiency stats by character ID
        """
        team_id = team[0].get("team_id", "unknown") if team else "unknown"
        
        # Load healing history
        history = self._load_healing_history(team_id)
        team_history = history.get(team_id, [])
        
        # Group by healer
        healer_stats = {}
        
        for record in team_history:
            healer_id = record.get("healer_id", "unknown")
            
            if healer_id not in healer_stats:
                healer_stats[healer_id] = {
                    "healer_name": record.get("healer_name", "Unknown"),
                    "attempts": 0,
                    "successes": 0,
                    "stamina_spent": 0,
                    "recovery_reduced": 0
                }
            
            # Update stats
            healer_stats[healer_id]["attempts"] += 1
            
            if record.get("success", False):
                healer_stats[healer_id]["successes"] += 1
                healer_stats[healer_id]["recovery_reduced"] += record.get("reduction", 0)
            
            healer_stats[healer_id]["stamina_spent"] += record.get("stamina_cost", 0)
        
        # Calculate efficiency metrics
        for healer_id, stats in healer_stats.items():
            if stats["attempts"] > 0:
                stats["success_rate"] = stats["successes"] / stats["attempts"]
                stats["stamina_per_success"] = stats["stamina_spent"] / max(1, stats["successes"])
                stats["reduction_per_stamina"] = stats["recovery_reduced"] / max(1, stats["stamina_spent"])
            else:
                stats["success_rate"] = 0
                stats["stamina_per_success"] = 0
                stats["reduction_per_stamina"] = 0
        
        return healer_stats