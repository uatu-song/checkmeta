"""
Day Simulation System for META Fantasy League Simulator
Orchestrates a full day of matches with proper event emissions

Version: 5.1.0 - Guardian Compliant
"""

import os
import sys
import time
import json
import datetime
import logging
import traceback
from typing import Dict, List, Any, Optional, Tuple, Union, Set
from collections import defaultdict

from system_base import SystemBase

class DaySimulationSystem(SystemBase):
    """
    Day Simulation System for META Fantasy League
    
    Compliant with Guardian standards:
    - Event emissions via EventEmitter
    - External configuration
    - Structured logging
    - Error handling
    - System registration
    """
    
    def __init__(self, config, registry=None):
        """Initialize the day simulation system"""
        super().__init__(config)
        self.name = "day_simulation_system"
        self.logger = logging.getLogger("META_SIMULATOR.DaySimulationSystem")
        
        # Store registry if provided
        self._registry = registry
        
        # Cache for commonly used systems and configurations
        self._event_system = None
        self._matches_per_day = self.config.get("simulation.matches_per_day", 5)
        self._auto_backup_frequency = self.config.get("advanced.auto_backup_frequency", 5)
        self._dump_state_on_error = self.config.get("development.dump_state_on_error", True)
        
        # Load calendar configuration
        self._calendar_start_date = self._parse_date(
            self.config.get("calendar.start_date", "2025-04-07")
        )
        
        # Initialize state
        self.active = False
        self.current_day = 0
        self.day_statistics = defaultdict(dict)
        
        self.logger.info("Day simulation system initialized with matches_per_day={}".format(self._matches_per_day))
    
    def activate(self):
        """Activate the day simulation system"""
        self.active = True
        self.logger.info("Day simulation system activated")
        return True
    
    def deactivate(self):
        """Deactivate the day simulation system"""
        self.active = False
        self.logger.info("Day simulation system deactivated")
        return True
    
    def is_active(self):
        """Check if the day simulation system is active"""
        return self.active
    
    def _get_registry(self):
        """Get system registry (lazy loading)"""
        if not self._registry:
            from system_registry import SystemRegistry
            self._registry = SystemRegistry()
        return self._registry
    
    def _get_event_system(self):
        """Get event system from registry (lazy loading)"""
        if not self._event_system:
            registry = self._get_registry()
            self._event_system = registry.get("event_system")
            if not self._event_system:
                self.logger.warning("Event system not available, events will not be emitted")
        return self._event_system
    
    def _get_system(self, system_name):
        """Get a system from the registry"""
        try:
            registry = self._get_registry()
            return registry.get(system_name)
        except Exception as e:
            self.logger.error("Error getting system {}: {}".format(system_name, e))
            self._emit_error_event("get_system", str(e), {"system_name": system_name})
            return None
    
    def simulate_day(self, day_number: int, show_details: bool = True) -> Dict[str, Any]:
        """
        Simulate a full day of matches
        
        Args:
            day_number: The day number to simulate
            show_details: Whether to show detailed output
            
        Returns:
            Dictionary with day results
        """
        if not self.active:
            self.logger.warning("Day simulation system not active, cannot simulate day")
            return {"error": "System not active"}
        
        try:
            simulation_start_time = time.time()
            
            self.logger.info("Starting simulation for day {}".format(day_number))
            self.current_day = day_number
            
            # Emit day_simulation_start event
            self._emit_event("day_simulation_start", {
                "day": day_number,
                "date": self._get_calendar_date(day_number),
                "weekday": self._get_weekday_name(day_number),
                "timestamp": datetime.datetime.now().isoformat()
            })
            
            # Check if this is a valid match day (Monday-Friday)
            if not self._is_valid_match_day(day_number):
                error_msg = "Day {} is not a valid match day (must be Mon-Fri)".format(day_number)
                self.logger.error(error_msg)
                self._emit_event("day_simulation_error", {
                    "day": day_number,
                    "error": error_msg,
                    "error_type": "invalid_day"
                })
                return {"error": error_msg}
            
            # Load data for this day
            data_loader = self._get_system("data_loader")
            if not data_loader:
                error_msg = "Data loader not available"
                self.logger.error(error_msg)
                self._emit_event("day_simulation_error", {
                    "day": day_number,
                    "error": error_msg,
                    "error_type": "system_not_available"
                })
                return {"error": error_msg}
                
            # Load lineups for this day
            try:
                lineups = data_loader.load_lineups(day_number)
                self.logger.info("Loaded lineups for day {}: {} teams".format(day_number, len(lineups)))
                
                # Emit lineups_loaded event
                self._emit_event("lineups_loaded", {
                    "day": day_number,
                    "team_count": len(lineups),
                    "teams": list(lineups.keys())
                })
            except Exception as e:
                error_msg = "Error loading lineups for day {}: {}".format(day_number, e)
                self.logger.error(error_msg)
                self._emit_event("day_simulation_error", {
                    "day": day_number,
                    "error": error_msg,
                    "error_type": "lineup_load_error"
                })
                return {"error": error_msg}
            
            # Generate matchups
            try:
                matchups = data_loader.get_matchups(day_number, lineups)
                self.logger.info("Generated matchups for day {}: {}".format(day_number, matchups))
                
                # Emit matchups_generated event
                self._emit_event("matchups_generated", {
                    "day": day_number,
                    "matchups": matchups
                })
            except Exception as e:
                error_msg = "Error generating matchups for day {}: {}".format(day_number, e)
                self.logger.error(error_msg)
                self._emit_event("day_simulation_error", {
                    "day": day_number,
                    "error": error_msg,
                    "error_type": "matchup_generation_error"
                })
                return {"error": error_msg}
            
            # Check matchup count
            if len(matchups) != self._matches_per_day:
                error_msg = "Invalid matchup count: {}, expected {}".format(len(matchups), self._matches_per_day)
                self.logger.error(error_msg)
                self._emit_event("day_simulation_error", {
                    "day": day_number,
                    "error": error_msg,
                    "error_type": "invalid_matchup_count"
                })
                return {"error": error_msg}
            
            # Process injuries if enabled
            injury_system = self._get_system("injury_system")
            if injury_system:
                try:
                    injury_report = injury_system.process_day_change(day_number)
                    self.logger.info("Processed injuries: {} recovered, {} still injured".format(
                        len(injury_report.get('recovered', [])),
                        len(injury_report.get('still_injured', []))
                    ))
                    
                    # Emit injuries_processed event
                    self._emit_event("injuries_processed", {
                        "day": day_number,
                        "recovered_count": len(injury_report.get('recovered', [])),
                        "still_injured_count": len(injury_report.get('still_injured', [])),
                        "recovered": [char.get("id") for char in injury_report.get('recovered', [])],
                        "still_injured": [char.get("id") for char in injury_report.get('still_injured', [])]
                    })
                except Exception as e:
                    self.logger.warning("Error processing injuries: {}".format(e))
                    self._emit_error_event("process_injuries", str(e), {"day": day_number})
            
            # Simulate each match
            match_results = []
            match_simulator = self._get_system("match_simulator")
            
            if not match_simulator:
                error_msg = "Match simulator not available"
                self.logger.error(error_msg)
                self._emit_event("day_simulation_error", {
                    "day": day_number,
                    "error": error_msg,
                    "error_type": "system_not_available"
                })
                return {"error": error_msg}
            
            for match_number, (team_a_id, team_b_id) in enumerate(matchups, 1):
                self.logger.info("Starting match {}: {} vs {}".format(match_number, team_a_id, team_b_id))
                
                # Emit match_simulation_start event
                self._emit_event("match_simulation_start", {
                    "day": day_number,
                    "match_number": match_number,
                    "team_a_id": team_a_id,
                    "team_b_id": team_b_id
                })
                
                # Get team lineups
                team_a = lineups.get(team_a_id, [])
                team_b = lineups.get(team_b_id, [])
                
                # Simulate the match
                try:
                    match_start_time = time.time()
                    
                    result = match_simulator.simulate_match(team_a, team_b, day_number, match_number, show_details)
                    match_results.append(result)
                    
                    match_duration = time.time() - match_start_time
                    
                    self.logger.info("Match {} completed: {} ({:.2f} seconds)".format(
                        match_number, result['winning_team'], match_duration
                    ))
                    
                    # Emit match_simulation_complete event
                    self._emit_event("match_simulation_complete", {
                        "day": day_number,
                        "match_number": match_number,
                        "team_a_id": team_a_id,
                        "team_b_id": team_b_id,
                        "winning_team": result['winning_team'],
                        "duration": match_duration,
                        "rounds_played": result.get('rounds_played', 0)
                    })
                except Exception as e:
                    error_msg = "Error simulating match {}: {}".format(match_number, e)
                    self.logger.error(error_msg)
                    
                    # Dump error state if configured
                    if self._dump_state_on_error:
                        self._dump_error_state(day_number, match_number, team_a_id, team_b_id, e)
                    
                    # Emit match_simulation_error event
                    self._emit_event("match_simulation_error", {
                        "day": day_number,
                        "match_number": match_number,
                        "team_a_id": team_a_id,
                        "team_b_id": team_b_id,
                        "error": str(e),
                        "traceback": traceback.format_exc()
                    })
                    
                    # Continue with next match instead of failing the whole day
                    continue
            
            # Generate day summary
            day_results = self._generate_day_summary(day_number, match_results, lineups)
            
            # Record day stats
            stat_tracker = self._get_system("stat_tracker")
            if stat_tracker and hasattr(stat_tracker, "record_day_summary"):
                try:
                    stat_tracker.record_day_summary(day_number, day_results)
                    self.logger.info("Recorded day summary in stat tracker")
                except Exception as e:
                    self.logger.warning("Error recording day summary: {}".format(e))
                    self._emit_error_event("record_day_summary", str(e), {"day": day_number})
            
            # Generate day report if enabled
            report_file = None
            if self.config.get("reporting.generate_day_reports", True):
                try:
                    report_file = self._generate_day_report(day_number, day_results)
                    self.logger.info("Generated day report: {}".format(report_file))
                    
                    # Emit report_generated event
                    self._emit_event("report_generated", {
                        "day": day_number,
                        "report_type": "day",
                        "report_file": report_file
                    })
                except Exception as e:
                    self.logger.warning("Error generating day report: {}".format(e))
                    self._emit_error_event("generate_day_report", str(e), {"day": day_number})
            
            # Create backup if configured
            if self._auto_backup_frequency > 0 and day_number % self._auto_backup_frequency == 0:
                try:
                    backup_path = self._create_backup(day_number)
                    self.logger.info("Created backup for day {} at {}".format(day_number, backup_path))
                    
                    # Emit backup_created event
                    self._emit_event("backup_created", {
                        "day": day_number,
                        "backup_path": backup_path,
                        "backup_type": "auto",
                        "backup_frequency": self._auto_backup_frequency
                    })
                except Exception as e:
                    self.logger.warning("Error creating backup: {}".format(e))
                    self._emit_error_event("create_backup", str(e), {"day": day_number})
            
            # Add report file to results
            day_results["report_file"] = report_file
            
            # Calculate simulation duration
            simulation_duration = time.time() - simulation_start_time
            day_results["simulation_duration"] = simulation_duration
            
            # Store statistics
            self.day_statistics[day_number] = {
                "match_count": len(match_results),
                "teams": list(lineups.keys()),
                "duration": simulation_duration
            }
            
            # Emit day_simulation_complete event
            self._emit_event("day_simulation_complete", {
                "day": day_number,
                "date": self._get_calendar_date(day_number),
                "weekday": self._get_weekday_name(day_number),
                "match_count": len(match_results),
                "team_count": len(lineups),
                "duration": simulation_duration,
                "report_file": report_file
            })
            
            self.logger.info("Day {} simulation completed in {:.2f} seconds".format(day_number, simulation_duration))
            
            return day_results
            
        except Exception as e:
            error_msg = "Error simulating day {}: {}".format(day_number, e)
            self.logger.error(error_msg)
            self._emit_error_event("simulate_day", str(e), {"day": day_number})
            return {"error": error_msg}
    
    def _is_valid_match_day(self, day_number: int) -> bool:
        """
        Check if a day number is a valid match day (Mon-Fri)
        
        Args:
            day_number: Day number to check
            
        Returns:
            True if valid match day, False otherwise
        """
        try:
            # First day is Monday (typically)
            # Day 1-5 is week 1, Day 6-10 is week 2, etc.
            # So we need to check if (day_number - 1) % 7 < 5
            return (day_number - 1) % 7 < 5
        except Exception as e:
            self.logger.error("Error checking valid match day: {}".format(e))
            return False
    
    def _generate_day_summary(self, day_number: int, match_results: List[Dict[str, Any]], 
                             lineups: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Generate a summary of the day's results
        
        Args:
            day_number: Day number
            match_results: List of match result dictionaries
            lineups: Dictionary of team lineups
            
        Returns:
            Dictionary with day summary
        """
        try:
            # Calculate team standings
            team_standings = {}
            
            for match in match_results:
                team_a_id = match["team_a_id"]
                team_b_id = match["team_b_id"]
                
                # Initialize team records if not exists
                if team_a_id not in team_standings:
                    team_standings[team_a_id] = {"wins": 0, "losses": 0, "draws": 0}
                if team_b_id not in team_standings:
                    team_standings[team_b_id] = {"wins": 0, "losses": 0, "draws": 0}
                    
                # Update based on result
                if match["result"] == "win":
                    team_standings[team_a_id]["wins"] += 1
                    team_standings[team_b_id]["losses"] += 1
                elif match["result"] == "loss":
                    team_standings[team_a_id]["losses"] += 1
                    team_standings[team_b_id]["wins"] += 1
                else:
                    team_standings[team_a_id]["draws"] += 1
                    team_standings[team_b_id]["draws"] += 1
            
            # Calculate team data
            team_data = {}
            
            data_loader = self._get_system("data_loader")
            
            for team_id, team_chars in lineups.items():
                team_name = data_loader.get_team_name(team_id) if data_loader else f"Team {team_id[1:]}" if team_id.startswith('t') else team_id
                division = data_loader.get_team_division(team_id) if data_loader else "Unknown"
                
                team_data[team_id] = {
                    "name": team_name,
                    "division": division,
                    "active_count": sum(1 for char in team_chars if char.get("is_active", True)),
                    "injured_count": sum(1 for char in team_chars if char.get("is_injured", False)),
                    "total_count": len(team_chars)
                }
            
            # Get calendar date for this day
            calendar_date = self._get_calendar_date(day_number)
            weekday = self._get_weekday_name(day_number)
            
            # Create summary
            summary = {
                "day": day_number,
                "date": calendar_date,
                "weekday": weekday,
                "matches": match_results,
                "standings": team_standings,
                "teams": team_data
            }
            
            # Emit day_summary_generated event
            self._emit_event("day_summary_generated", {
                "day": day_number,
                "date": calendar_date,
                "weekday": weekday,
                "team_count": len(team_data),
                "match_count": len(match_results)
            })
            
            return summary
            
        except Exception as e:
            self.logger.error("Error generating day summary: {}".format(e))
            self._emit_error_event("generate_day_summary", str(e), {"day": day_number})
            return {
                "day": day_number,
                "date": self._get_calendar_date(day_number),
                "weekday": self._get_weekday_name(day_number),
                "error": str(e)
            }
    
    def _get_calendar_date(self, day_number: int) -> str:
        """
        Get calendar date for a given day number
        
        Args:
            day_number: Day number
            
        Returns:
            Calendar date string (YYYY-MM-DD)
        """
        try:
            # Calculate date from start date + day number
            if not self._calendar_start_date:
                # Fallback to default start date
                start_date = datetime.date(2025, 4, 7)
            else:
                start_date = self._calendar_start_date
                
            target_date = start_date + datetime.timedelta(days=day_number - 1)
            return target_date.strftime("%Y-%m-%d")
        except Exception as e:
            self.logger.error("Error getting calendar date: {}".format(e))
            return "Unknown"
    
    def _get_weekday_name(self, day_number: int) -> str:
        """
        Get weekday name for a given day number
        
        Args:
            day_number: Day number
            
        Returns:
            Weekday name (Monday-Sunday)
        """
        try:
            # Start date is Monday for day 1
            weekday_index = (day_number - 1) % 7
            weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            return weekdays[weekday_index]
        except Exception as e:
            self.logger.error("Error getting weekday name: {}".format(e))
            return "Unknown"
    
    def _parse_date(self, date_str: str) -> Optional[datetime.date]:
        """
        Parse a date string into a datetime.date object
        
        Args:
            date_str: Date string (YYYY-MM-DD)
            
        Returns:
            datetime.date object or None if parsing fails
        """
        try:
            if not date_str:
                return None
            return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        except Exception as e:
            self.logger.error("Error parsing date {}: {}".format(date_str, e))
            return None
    
    def _generate_day_report(self, day_number: int, day_results: Dict[str, Any]) -> str:
        """
        Generate a report for the day's matches
        
        Args:
            day_number: Day number
            day_results: Day results dictionary
            
        Returns:
            Path to generated report file
        """
        try:
            match_visualizer = self._get_system("match_visualizer")
            if not match_visualizer:
                self.logger.warning("Match visualizer not available, cannot generate day report")
                return None
            
            report_file = match_visualizer.generate_day_report(day_number, day_results)
            self.logger.info("Day report generated: {}".format(report_file))
            return report_file
        except Exception as e:
            self.logger.error("Error generating day report: {}".format(e))
            self._emit_error_event("generate_day_report", str(e), {"day": day_number})
            return None
    
    def _create_backup(self, day_number: int) -> str:
        """
        Create a backup of the current state
        
        Args:
            day_number: Day number
            
        Returns:
            Path to backup directory
        """
        try:
            # Get backup manager
            backup_manager = self._get_system("backup_manager")
            if backup_manager:
                # Use backup manager if available
                return backup_manager.create_backup(f"day{day_number}")
            
            # Fallback to basic backup if no backup manager
            backup_dir = self.config.get("paths.backups_dir", "backups")
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(backup_dir, f"day{day_number}_{timestamp}")
            os.makedirs(backup_path, exist_ok=True)
            
            # Save configuration
            config_file = os.path.join(backup_path, "config.json")
            with open(config_file, 'w') as f:
                json.dump(self.config.to_dict(), f, indent=2)
            
            # Save system states
            registry = self._get_registry()
            systems_to_backup = [
                "trait_system", 
                "injury_system", 
                "stat_tracker", 
                "xp_system", 
                "morale_system", 
                "stamina_system"
            ]
            
            for system_name in systems_to_backup:
                system = registry.get(system_name)
                if system and hasattr(system, "export_state"):
                    try:
                        state_file = os.path.join(backup_path, f"{system_name}_state.json")
                        state = system.export_state()
                        with open(state_file, 'w') as f:
                            json.dump(state, f, indent=2)
                    except Exception as e:
                        self.logger.error("Error backing up {}: {}".format(system_name, e))
            
            self.logger.info("Backup created at {}".format(backup_path))
            return backup_path
        except Exception as e:
            self.logger.error("Error creating backup: {}".format(e))
            self._emit_error_event("create_backup", str(e), {"day": day_number})
            return None
    
    def _dump_error_state(self, day: int, match: int, team_a_id: str, team_b_id: str, 
                         error: Exception) -> None:
        """
        Dump simulation state on errors
        
        Args:
            day: Day number
            match: Match number
            team_a_id: Team A ID
            team_b_id: Team B ID
            error: Exception object
        """
        try:
            # Create dump directory
            dump_dir = os.path.join(self.config.get("paths.logs_dir", "logs"), "error_dumps")
            os.makedirs(dump_dir, exist_ok=True)
            
            # Create dump filename
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            dump_file = os.path.join(dump_dir, f"error_day{day}_match{match}_{timestamp}.json")
            
            # Create error data
            error_data = {
                "timestamp": timestamp,
                "day": day,
                "match": match,
                "team_a_id": team_a_id,
                "team_b_id": team_b_id,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "traceback": traceback.format_exc(),
                "simulator_version": self.config.get("meta.version", "unknown"),
                "config": self.config.to_dict()
            }
            
            # Write error data
            with open(dump_file, 'w') as f:
                json.dump(error_data, f, indent=2)
                
            self.logger.info("Error state dumped to {}".format(dump_file))
            
            # Emit error_state_dumped event
            self._emit_event("error_state_dumped", {
                "day": day,
                "match": match,
                "team_a_id": team_a_id,
                "team_b_id": team_b_id,
                "dump_file": dump_file,
                "error_type": type(error).__name__
            })
        except Exception as e:
            self.logger.error("Error dumping error state: {}".format(e))
            self._emit_error_event("dump_error_state", str(e), {
                "day": day,
                "match": match
            })
    
    def _emit_event(self, event_name: str, data: Dict[str, Any]) -> None:
        """
        Emit an event with the given name and data
        
        Args:
            event_name: Name of the event
            data: Event data dictionary
        """
        event_system = self._get_event_system()
        if event_system:
            try:
                event_system.emit(event_name, data)
            except Exception as e:
                self.logger.error("Error emitting event {}: {}".format(event_name, e))
    
    def _emit_error_event(self, function_name: str, error_message: str, 
                         context: Optional[Dict[str, Any]] = None) -> None:
        """
        Emit a system error event
        
        Args:
            function_name: Name of the function where error occurred
            error_message: Error message
            context: Additional context (optional)
        """
        event_system = self._get_event_system()
        if event_system:
            try:
                error_data = {
                    "system": self.name,
                    "function": function_name,
                    "error": error_message,
                    "timestamp": datetime.datetime.now().isoformat()
                }
                
                if context:
                    error_data["context"] = context
                    
                event_system.emit("system_error", error_data)
            except Exception as e:
                self.logger.error("Error emitting error event: {}".format(e))
    
    def get_day_statistics(self) -> Dict[int, Dict[str, Any]]:
        """
        Get statistics for all simulated days
        
        Returns:
            Dictionary of day statistics
        """
        return dict(self.day_statistics)
    
    def save_persistent_data(self) -> None:
        """Save persistent data for the day simulation system"""
        try:
            # Save day statistics
            data_dir = self.config.get("paths.data_dir", "data")
            stats_dir = os.path.join(data_dir, "statistics")
            os.makedirs(stats_dir, exist_ok=True)
            
            stats_file = os.path.join(stats_dir, "day_simulation_stats.json")
            with open(stats_file, 'w') as f:
                json.dump({
                    "day_statistics": dict(self.day_statistics),
                    "last_day": self.current_day,
                    "timestamp": datetime.datetime.now().isoformat()
                }, f, indent=2)
                
            self.logger.info("Day simulation statistics saved")
        except Exception as e:
            self.logger.error("Error saving persistent data: {}".format(e))
            self._emit_error_event("save_persistent_data", str(e))
    
    def export_state(self) -> Dict[str, Any]:
        """
        Export state for backup
        
        Returns:
            State dictionary
        """
        return {
            "current_day": self.current_day,
            "day_statistics": dict(self.day_statistics),
            "active": self.active
        }
