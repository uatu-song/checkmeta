"""
Match Scheduler for META League Simulator v4.2.1
Handles scheduling matches with division separation rules
"""

import random
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from system_base import SystemBase

class MatchScheduler(SystemBase):
    """
    Match Scheduler system for META League simulations
    Enforces division separation rules, home/away alternation, and fairness
    """
    
    def __init__(self, config, data_loader=None):
        """Initialize the match scheduler"""
        super().__init__("match_scheduler", None)
        self.config = config
        self.data_loader = data_loader
        
        # Configuration values
        self.matches_per_day = config.get("simulation.matches_per_day", 5)
        self.undercurrent_division = config.get("divisions.undercurrent", "undercurrent")
        self.overlay_division = config.get("divisions.overlay", "overlay")
        
        # Cache for team information
        self.division_teams = None
        self.match_history = {}
        
        self.logger.info(f"Match Scheduler initialized with {self.matches_per_day} matches per day")
    
    def _activate_implementation(self) -> bool:
        """Implementation-specific activation logic"""
        self.logger.info("Activating Match Scheduler")
        
        # Update data_loader reference if in registry
        if self.registry and not self.data_loader:
            self.data_loader = self.registry.get("data_loader")
            if not self.data_loader:
                self.logger.error("DataLoader not found in registry")
                return False
        
        # Pre-load divisions to check team counts
        try:
            self._load_division_teams()
            
            # Verify we have enough teams per division
            undercurrent_count = len(self.division_teams.get(self.undercurrent_division, []))
            overlay_count = len(self.division_teams.get(self.overlay_division, []))
            
            if undercurrent_count < self.matches_per_day:
                self.logger.error(f"Not enough teams in {self.undercurrent_division} division for scheduling")
                return False
            
            if overlay_count < self.matches_per_day:
                self.logger.error(f"Not enough teams in {self.overlay_division} division for scheduling")
                return False
            
            self.logger.info(f"Division team counts verified: {self.undercurrent_division}={undercurrent_count}, {self.overlay_division}={overlay_count}")
            
        except Exception as e:
            self.logger.error(f"Error loading division teams: {e}")
            return False
        
        return True
    
    def _load_division_teams(self) -> None:
        """Load teams by division"""
        if self.division_teams is not None:
            return
            
        # Make sure we have a data loader
        if not self.data_loader:
            self.logger.error("DataLoader not available for loading division teams")
            raise ValueError("DataLoader not available")
        
        # Load divisions
        divisions = self.data_loader.load_divisions()
        
        # Group teams by division
        self.division_teams = {}
        
        for team_id, division in divisions.items():
            division = division.lower()
            if division not in self.division_teams:
                self.division_teams[division] = []
            
            self.division_teams[division].append(team_id)
        
        # Log division counts
        for division, teams in self.division_teams.items():
            self.logger.info(f"Division '{division}' has {len(teams)} teams")
    
    def schedule_matches(self, day_number: int, lineups: Dict[str, List[Dict[str, Any]]]) -> List[Tuple[str, str]]:
        """
        Schedule matches for a specific day following division separation rules
        
        Args:
            day_number: Day number to schedule matches for
            lineups: Dict mapping team_id to list of character dictionaries
            
        Returns:
            List of (team_a_id, team_b_id) tuples for scheduled matches
        """
        self.logger.info(f"Scheduling matches for day {day_number}")
        
        # Make sure division teams are loaded
        if self.division_teams is None:
            self._load_division_teams()
        
        # Determine eligible teams with enough active players
        undercurrent_eligible = self._get_eligible_teams(self.undercurrent_division, lineups)
        overlay_eligible = self._get_eligible_teams(self.overlay_division, lineups)
        
        # Check if we have enough teams
        if len(undercurrent_eligible) < self.matches_per_day:
            self.logger.warning(f"Not enough eligible teams in {self.undercurrent_division} division: {len(undercurrent_eligible)}/{self.matches_per_day}")
            undercurrent_eligible = self._get_eligible_teams(self.undercurrent_division, lineups, enforce_active_count=False)
        
        if len(overlay_eligible) < self.matches_per_day:
            self.logger.warning(f"Not enough eligible teams in {self.overlay_division} division: {len(overlay_eligible)}/{self.matches_per_day}")
            overlay_eligible = self._get_eligible_teams(self.overlay_division, lineups, enforce_active_count=False)
        
        # Final check
        if len(undercurrent_eligible) < self.matches_per_day or len(overlay_eligible) < self.matches_per_day:
            self.logger.error(f"Cannot schedule {self.matches_per_day} matches: Undercurrent={len(undercurrent_eligible)}, Overlay={len(overlay_eligible)}")
            raise ValueError(f"Not enough teams for {self.matches_per_day} matches")
        
        # Randomize teams within each division for fairness
        random.shuffle(undercurrent_eligible)
        random.shuffle(overlay_eligible)
        
        # Prioritize teams that haven't played recently
        undercurrent_eligible = self._prioritize_teams(undercurrent_eligible, day_number)
        overlay_eligible = self._prioritize_teams(overlay_eligible, day_number)
        
        # Determine home vs away based on day number
        # Even days: undercurrent teams are home (team_a), odd days: overlay teams are home (team_a)
        is_even_day = day_number % 2 == 0
        
        matchups = []
        for i in range(self.matches_per_day):
            if i < len(undercurrent_eligible) and i < len(overlay_eligible):
                if is_even_day:
                    # Even day: undercurrent is home (team_a)
                    matchups.append((undercurrent_eligible[i], overlay_eligible[i]))
                else:
                    # Odd day: overlay is home (team_a)
                    matchups.append((overlay_eligible[i], undercurrent_eligible[i]))
                
                # Record in match history
                self._record_match(undercurrent_eligible[i], overlay_eligible[i], day_number)
        
        self.logger.info(f"Scheduled {len(matchups)} matches for day {day_number}")
        
        # Log the matchups
        for i, (team_a, team_b) in enumerate(matchups):
            self.logger.info(f"  Match {i+1}: {team_a} vs {team_b}")
        
        return matchups
    
    def _get_eligible_teams(self, division: str, lineups: Dict[str, List[Dict[str, Any]]], enforce_active_count: bool = True) -> List[str]:
        """
        Get eligible teams from a division for scheduling
        
        Args:
            division: Division name
            lineups: Dict mapping team_id to list of character dictionaries
            enforce_active_count: Whether to enforce the minimum active character count
            
        Returns:
            List of eligible team IDs
        """
        division_teams = self.division_teams.get(division.lower(), [])
        teams_per_match = self.config.get("simulation.teams_per_match")
        
        eligible = []
        for team_id in division_teams:
            # Check if team has lineup data
            if team_id not in lineups:
                continue
            
            # Check for minimum active characters if enforcing
            if enforce_active_count:
                active_chars = [c for c in lineups[team_id] if c.get("is_active", True)]
                if len(active_chars) < teams_per_match:
                    continue
            
            eligible.append(team_id)
        
        return eligible
    
    def _prioritize_teams(self, teams: List[str], current_day: int) -> List[str]:
        """
        Prioritize teams that haven't played recently
        
        Args:
            teams: List of team IDs
            current_day: Current day number
            
        Returns:
            Prioritized list of team IDs
        """
        # Calculate days since last match for each team
        days_since_match = {}
        for team_id in teams:
            last_match_day = 0
            for day in range(current_day - 1, 0, -1):
                if team_id in self.match_history.get(day, []):
                    last_match_day = day
                    break
            
            days_since_match[team_id] = current_day - last_match_day
        
        # Sort teams by days since last match (descending)
        return sorted(teams, key=lambda t: days_since_match[t], reverse=True)
    
    def _record_match(self, team_a: str, team_b: str, day_number: int) -> None:
        """
        Record a match in the history
        
        Args:
            team_a: First team ID
            team_b: Second team ID
            day_number: Day number
        """
        if day_number not in self.match_history:
            self.match_history[day_number] = set()
        
        self.match_history[day_number].add(team_a)
        self.match_history[day_number].add(team_b)
    
    def get_match_history(self) -> Dict[int, Set[str]]:
        """
        Get the match history
        
        Returns:
            Dict mapping day number to set of team IDs that played that day
        """
        return self.match_history