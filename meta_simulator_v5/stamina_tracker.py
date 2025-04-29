"""
META Fantasy League Simulator - Stamina Tracker
Monitors and reports character stamina levels for manager dashboards
"""

import os
import json
import logging
import datetime
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger("StaminaTracker")

class StaminaTracker:
    """System for monitoring and reporting character stamina levels"""
    
    def __init__(self, config=None):
        """Initialize the stamina tracker
        
        Args:
            config: Optional configuration object
        """
        self.config = config
        
        # Stamina threshold levels (percentage)
        self.stamina_thresholds = {
            "critical": 20,    # Below 20% stamina
            "low": 40,         # Below 40% stamina
            "moderate": 70,    # Below 70% stamina
            "high": 90,        # Below 90% stamina
            "full": 100        # At or near 100% stamina
        }
        
        # Stamina recovery rate per day (when resting)
        self.base_recovery_rate = 15  # 15% per day
        
        # Stamina history
        self.stamina_history = {}
        
        # Current stamina snapshots by team
        self.stamina_snapshots = {}
        
        # Initialize persistence
        self._ensure_persistence_directory()
        self._load_stamina_history()
    
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
    
    def _get_stamina_history_path(self, team_id: str) -> str:
        """Get path to stamina history file for a team
        
        Args:
            team_id: Team ID
            
        Returns:
            str: Path to stamina history file
        """
        persistence_dir = self._get_persistence_directory()
        return os.path.join(persistence_dir, f"{team_id}_stamina_history.json")
    
    def _get_stamina_snapshot_path(self, team_id: str) -> str:
        """Get path to stamina snapshot file for a team
        
        Args:
            team_id: Team ID
            
        Returns:
            str: Path to stamina snapshot file
        """
        persistence_dir = self._get_persistence_directory()
        return os.path.join(persistence_dir, f"{team_id}_stamina_snapshot.json")
    
    def _load_stamina_history(self) -> None:
        """Load all stamina history files"""
        persistence_dir = self._get_persistence_directory()
        
        # Look for all stamina history files
        for filename in os.listdir(persistence_dir):
            if filename.endswith("_stamina_history.json"):
                team_id = filename.split("_stamina_history.json")[0]
                
                try:
                    file_path = os.path.join(persistence_dir, filename)
                    with open(file_path, 'r') as f:
                        self.stamina_history[team_id] = json.load(f)
                    
                    logger.debug(f"Loaded stamina history for team {team_id}")
                except Exception as e:
                    logger.error(f"Error loading stamina history for team {team_id}: {e}")
        
        # Look for all stamina snapshot files
        for filename in os.listdir(persistence_dir):
            if filename.endswith("_stamina_snapshot.json"):
                team_id = filename.split("_stamina_snapshot.json")[0]
                
                try:
                    file_path = os.path.join(persistence_dir, filename)
                    with open(file_path, 'r') as f:
                        self.stamina_snapshots[team_id] = json.load(f)
                    
                    logger.debug(f"Loaded stamina snapshot for team {team_id}")
                except Exception as e:
                    logger.error(f"Error loading stamina snapshot for team {team_id}: {e}")
    
    def update_stamina_levels(self, team: List[Dict[str, Any]], match_day: int = 0) -> Dict[str, Any]:
        """Update stamina levels for a team after a match or daily update
        
        Args:
            team: List of team characters
            match_day: Match day number (0 for non-match day)
            
        Returns:
            dict: Stamina update results
        """
        if not team:
            return {"error": "No team provided"}
        
        team_id = team[0].get("team_id", "unknown")
        update_type = "match" if match_day > 0 else "daily"
        update_time = self._get_timestamp()
        
        # Create stamina records
        stamina_records = []
        
        for character in team:
            char_id = character.get("id", "unknown")
            char_name = character.get("name", "Unknown")
            current_stamina = character.get("stamina", 100)
            
            # Create record
            record = {
                "character_id": char_id,
                "character_name": char_name,
                "stamina_level": current_stamina,
                "stamina_status": self._get_stamina_status(current_stamina),
                "update_type": update_type,
                "match_day": match_day,
                "timestamp": update_time
            }
            
            stamina_records.append(record)
        
        # Update history
        self._update_stamina_history(team_id, stamina_records)
        
        # Update snapshot
        self._update_stamina_snapshot(team_id, stamina_records)
        
        return {
            "team_id": team_id,
            "update_type": update_type,
            "match_day": match_day,
            "timestamp": update_time,
            "records": stamina_records
        }
    
    def simulate_daily_recovery(self, team: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Simulate daily stamina recovery for a team
        
        Args:
            team: List of team characters
            
        Returns:
            dict: Recovery results
        """
        if not team:
            return {"error": "No team provided"}
        
        team_id = team[0].get("team_id", "unknown")
        recovery_time = self._get_timestamp()
        
        # Create recovery records
        recovery_records = []
        
        for character in team:
            char_id = character.get("id", "unknown")
            char_name = character.get("name", "Unknown")
            
            # Calculate recovery amount
            base_recovery = self.base_recovery_rate
            
            # WIL (Willpower) increases recovery rate
            wil = character.get("aWIL", 5)
            wil_bonus = (wil - 5) * 2  # 2% per point above 5
            
            # Apply injury reduction if injured
            is_injured = character.get("is_injured", False)
            injury_factor = 0.5 if is_injured else 1.0  # 50% recovery if injured
            
            # Apply active/bench modifier
            is_active = character.get("is_active", True)
            activity_factor = 0.8 if is_active else 1.2  # Active: 80%, Bench: 120%
            
            # Calculate final recovery amount
            recovery_amount = base_recovery + wil_bonus
            recovery_amount *= injury_factor
            recovery_amount *= activity_factor
            
            # Apply recovery
            old_stamina = character.get("stamina", 100)
            new_stamina = min(100, old_stamina + recovery_amount)
            
            # Update character
            character["stamina"] = new_stamina
            
            # Create record
            record = {
                "character_id": char_id,
                "character_name": char_name,
                "old_stamina": old_stamina,
                "new_stamina": new_stamina,
                "recovery_amount": recovery_amount,
                "is_injured": is_injured,
                "is_active": is_active,
                "timestamp": recovery_time
            }
            
            recovery_records.append(record)
        
        # Update stamina levels
        self.update_stamina_levels(team)
        
        return {
            "team_id": team_id,
            "timestamp": recovery_time,
            "records": recovery_records
        }
    
    def _update_stamina_history(self, team_id: str, records: List[Dict[str, Any]]) -> None:
        """Update stamina history for a team
        
        Args:
            team_id: Team ID
            records: Stamina records to add
        """
        # Load existing history
        history_path = self._get_stamina_history_path(team_id)
        history = {}
        
        if os.path.exists(history_path):
            try:
                with open(history_path, 'r') as f:
                    history = json.load(f)
            except Exception as e:
                logger.error(f"Error loading stamina history for team {team_id}: {e}")
        
        # Initialize character histories
        for record in records:
            char_id = record["character_id"]
            
            if char_id not in history:
                history[char_id] = []
            
            # Add new record
            history[char_id].append(record)
            
            # Limit history size (keep last 30 entries)
            if len(history[char_id]) > 30:
                history[char_id] = history[char_id][-30:]
        
        # Save updated history
        try:
            with open(history_path, 'w') as f:
                json.dump(history, f, indent=2)
            
            # Update in-memory history
            self.stamina_history[team_id] = history
            
            logger.debug(f"Updated stamina history for team {team_id}")
        except Exception as e:
            logger.error(f"Error saving stamina history for team {team_id}: {e}")
    
    def _update_stamina_snapshot(self, team_id: str, records: List[Dict[str, Any]]) -> None:
        """Update stamina snapshot for a team
        
        Args:
            team_id: Team ID
            records: Stamina records to update snapshot
        """
        # Create snapshot
        snapshot = {
            "team_id": team_id,
            "timestamp": self._get_timestamp(),
            "characters": {}
        }
        
        # Add character snapshots
        for record in records:
            char_id = record["character_id"]
            
            snapshot["characters"][char_id] = {
                "character_id": char_id,
                "character_name": record["character_name"],
                "stamina_level": record["stamina_level"],
                "stamina_status": record["stamina_status"],
                "last_update": record["timestamp"]
            }
        
        # Save snapshot
        snapshot_path = self._get_stamina_snapshot_path(team_id)
        
        try:
            with open(snapshot_path, 'w') as f:
                json.dump(snapshot, f, indent=2)
            
            # Update in-memory snapshot
            self.stamina_snapshots[team_id] = snapshot
            
            logger.debug(f"Updated stamina snapshot for team {team_id}")
        except Exception as e:
            logger.error(f"Error saving stamina snapshot for team {team_id}: {e}")
    
    def _get_stamina_status(self, stamina_level: float) -> str:
        """Get status label for a stamina level
        
        Args:
            stamina_level: Stamina level (0-100)
            
        Returns:
            str: Status label
        """
        if stamina_level <= self.stamina_thresholds["critical"]:
            return "critical"
        elif stamina_level <= self.stamina_thresholds["low"]:
            return "low"
        elif stamina_level <= self.stamina_thresholds["moderate"]:
            return "moderate"
        elif stamina_level <= self.stamina_thresholds["high"]:
            return "high"
        else:
            return "full"
    
    def _get_timestamp(self) -> str:
        """Get current timestamp
        
        Returns:
            str: Formatted timestamp
        """
        return datetime.datetime.now().isoformat()
    
    def generate_team_stamina_report(self, team_id: str) -> str:
        """Generate a text report of team stamina levels
        
        Args:
            team_id: Team ID
            
        Returns:
            str: Formatted stamina report
        """
        # Get team snapshot
        if team_id not in self.stamina_snapshots:
            return f"No stamina data available for team {team_id}"
        
        snapshot = self.stamina_snapshots[team_id]
        
        # Build report
        report = f"=== STAMINA REPORT: TEAM {team_id} ===\n"
        report += f"Last updated: {snapshot['timestamp'].split('T')[0]}\n\n"
        
        # Count status levels
        status_counts = {
            "critical": 0,
            "low": 0,
            "moderate": 0,
            "high": 0,
            "full": 0
        }
        
        # Process characters
        characters = []
        for char_id, char_data in snapshot["characters"].items():
            characters.append(char_data)
            status = char_data.get("stamina_status", "unknown")
            if status in status_counts:
                status_counts[status] += 1
        
        # Add status summary
        report += "TEAM STAMINA STATUS:\n"
        for status, count in status_counts.items():
            report += f"  {status.upper()}: {count}\n"
        
        report += "\nPLAYER STAMINA LEVELS:\n"
        
        # Sort by stamina level (ascending)
        characters.sort(key=lambda x: x.get("stamina_level", 0))
        
        for char in characters:
            stamina = char.get("stamina_level", 0)
            status = char.get("stamina_status", "unknown").upper()
            name = char.get("character_name", "Unknown")
            
            # Add basic info
            report += f"  {name}: {stamina:.1f}% ({status})\n"
        
        return report
    
    def generate_stamina_dashboard_data(self, team_id: str) -> Dict[str, Any]:
        """Generate stamina data for manager dashboards
        
        Args:
            team_id: Team ID
            
        Returns:
            dict: Dashboard data
        """
        # Get team snapshot
        if team_id not in self.stamina_snapshots:
            return {"error": f"No stamina data available for team {team_id}"}
        
        snapshot = self.stamina_snapshots[team_id]
        
        # Create dashboard data
        dashboard_data = {
            "team_id": team_id,
            "timestamp": snapshot["timestamp"],
            "summary": {
                "critical": 0,
                "low": 0,
                "moderate": 0,
                "high": 0,
                "full": 0,
                "team_average": 0
            },
            "players": []
        }
        
        # Process characters
        total_stamina = 0
        player_count = 0
        
        for char_id, char_data in snapshot["characters"].items():
            # Update summary counts
            status = char_data.get("stamina_status", "unknown")
            if status in dashboard_data["summary"]:
                dashboard_data["summary"][status] += 1
            
            # Update average
            stamina = char_data.get("stamina_level", 0)
            total_stamina += stamina
            player_count += 1
            
            # Add player data
            dashboard_data["players"].append({
                "id": char_id,
                "name": char_data.get("character_name", "Unknown"),
                "stamina": stamina,
                "status": status,
                "trend": self._get_stamina_trend(team_id, char_id)
            })
        
        # Calculate average
        if player_count > 0:
            dashboard_data["summary"]["team_average"] = total_stamina / player_count
        
        # Sort players by stamina level (ascending)
        dashboard_data["players"].sort(key=lambda x: x["stamina"])
        
        return dashboard_data
    
    def _get_stamina_trend(self, team_id: str, char_id: str) -> str:
        """Get stamina trend direction for a character
        
        Args:
            team_id: Team ID
            char_id: Character ID
            
        Returns:
            str: Trend direction ('up', 'down', 'stable')
        """
        # Get character history
        if team_id not in self.stamina_history or char_id not in self.stamina_history[team_id]:
            return "stable"
        
        history = self.stamina_history[team_id][char_id]
        
        # Need at least 2 entries
        if len(history) < 2:
            return "stable"
        
        # Get last two entries
        last = history[-1].get("stamina_level", 0)
        previous = history[-2].get("stamina_level", 0)
        
        # Calculate difference
        diff = last - previous
        
        # Determine trend
        if diff > 5:  # At least 5% increase
            return "up"
        elif diff < -5:  # At least 5% decrease
            return "down"
        else:
            return "stable"
    
    def export_dashboard_txt(self, team_id: str, output_path: Optional[str] = None) -> str:
        """Export stamina dashboard data as a simple text file
        for manager dashboards
        
        Args:
            team_id: Team ID
            output_path: Optional custom output path
            
        Returns:
            str: Path to saved file
        """
        # Generate dashboard data
        dashboard_data = self.generate_stamina_dashboard_data(team_id)
        
        if "error" in dashboard_data:
            return f"Error: {dashboard_data['error']}"
        
        # Format dashboard text
        dashboard_txt = f"TEAM {team_id} STAMINA DASHBOARD\n"
        dashboard_txt += f"Last Updated: {dashboard_data['timestamp'].split('T')[0]}\n\n"
        
        # Add summary
        dashboard_txt += "TEAM SUMMARY:\n"
        dashboard_txt += f"Average Stamina: {dashboard_data['summary']['team_average']:.1f}%\n"
        dashboard_txt += f"Critical: {dashboard_data['summary']['critical']}\n"
        dashboard_txt += f"Low: {dashboard_data['summary']['low']}\n"
        dashboard_txt += f"Moderate: {dashboard_data['summary']['moderate']}\n"
        dashboard_txt += f"High: {dashboard_data['summary']['high']}\n"
        dashboard_txt += f"Full: {dashboard_data['summary']['full']}\n\n"
        
        # Add player data
        dashboard_txt += "PLAYER STAMINA:\n"
        
        for player in dashboard_data["players"]:
            trend_symbol = "↑" if player["trend"] == "up" else "↓" if player["trend"] == "down" else "→"
            dashboard_txt += f"{player['name']}: {player['stamina']:.1f}% ({player['status'].upper()}) {trend_symbol}\n"
        
        # Determine output path
        if output_path is None:
            persistence_dir = self._get_persistence_directory()
            output_path = os.path.join(persistence_dir, f"{team_id}_stamina_dashboard.txt")
        
        # Save to file
        try:
            with open(output_path, 'w') as f:
                f.write(dashboard_txt)
            
            logger.info(f"Exported stamina dashboard to {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error exporting stamina dashboard: {e}")
            return f"Error: {e}"
    
    def export_dashboard_json(self, team_id: str, output_path: Optional[str] = None) -> str:
        """Export stamina dashboard data as JSON
        for manager dashboards
        
        Args:
            team_id: Team ID
            output_path: Optional custom output path
            
        Returns:
            str: Path to saved file
        """
        # Generate dashboard data
        dashboard_data = self.generate_stamina_dashboard_data(team_id)
        
        if "error" in dashboard_data:
            return f"Error: {dashboard_data['error']}"
        
        # Determine output path
        if output_path is None:
            persistence_dir = self._get_persistence_directory()
            output_path = os.path.join(persistence_dir, f"{team_id}_stamina_dashboard.json")
        
        # Save to file
        try:
            with open(output_path, 'w') as f:
                json.dump(dashboard_data, f, indent=2)
            
            logger.info(f"Exported stamina dashboard to {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error exporting stamina dashboard: {e}")
            return f"Error: {e}"