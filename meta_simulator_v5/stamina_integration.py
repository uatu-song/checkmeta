"""
META Fantasy League Simulator - Stamina Tracker Integration
Integrates the Stamina Tracker with the main simulator
"""

import os
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger("StaminaIntegration")

class StaminaIntegration:
    """Integration module for Stamina Tracker in the MetaLeagueSimulator"""
    
    def __init__(self, simulator):
        """Initialize the stamina integration
        
        Args:
            simulator: Reference to the main simulator instance
        """
        self.simulator = simulator
        self.stamina_tracker = None
        self.active = False
    
    def activate(self) -> bool:
        """Activate the stamina tracker
        
        Returns:
            bool: Success status
        """
        try:
            # Import stamina tracker
            from stamina_tracker import StaminaTracker
            
            # Initialize stamina tracker
            self.stamina_tracker = StaminaTracker(
                config=getattr(self.simulator, "config", None)
            )
            
            # Attach to simulator
            self.simulator.stamina_tracker = self.stamina_tracker
            
            # Enhance simulator methods
            self._enhance_simulator_methods()
            
            self.active = True
            logger.info("Stamina Tracker activated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error activating Stamina Tracker: {e}")
            self.active = False
            return False
    
    def _enhance_simulator_methods(self) -> None:
        """Enhance simulator methods with stamina tracking"""
        # Store original methods for enhanced functionality
        if hasattr(self.simulator, "simulate_match"):
            self.simulator._original_simulate_match = self.simulator.simulate_match
        
        if hasattr(self.simulator, "run_matchday"):
            self.simulator._original_run_matchday = self.simulator.run_matchday
        
        # Enhance simulate_match
        def enhanced_simulate_match(team_a, team_b, day_number=1, show_details=True):
            """Enhanced simulate_match with stamina tracking"""
            # Run original method
            match_result = self.simulator._original_simulate_match(
                team_a, team_b, day_number, show_details
            )
            
            # Update stamina levels after match
            if self.stamina_tracker:
                try:
                    # Update team A stamina
                    team_a_stamina = self.stamina_tracker.update_stamina_levels(team_a, day_number)
                    
                    # Update team B stamina
                    team_b_stamina = self.stamina_tracker.update_stamina_levels(team_b, day_number)
                    
                    # Add to match result
                    match_result["stamina_updates"] = {
                        "team_a": team_a_stamina,
                        "team_b": team_b_stamina
                    }
                    
                    # Generate dashboard files
                    try:
                        team_a_id = team_a[0].get("team_id", "unknown") if team_a else "unknown"
                        team_b_id = team_b[0].get("team_id", "unknown") if team_b else "unknown"
                        
                        self.stamina_tracker.export_dashboard_txt(team_a_id)
                        self.stamina_tracker.export_dashboard_txt(team_b_id)
                    except Exception as e:
                        logger.error(f"Error generating stamina dashboards: {e}")
                except Exception as e:
                    logger.error(f"Error updating stamina levels: {e}")
            
            return match_result
        
        # Enhance run_matchday
        def enhanced_run_matchday(day_number=1, lineup_file=None, show_details=True):
            """Enhanced run_matchday with daily stamina recovery"""
            # Simulate daily recovery before matchday
            if self.stamina_tracker:
                try:
                    # Get all teams
                    teams = {}
                    
                    # Try to get teams from DataLoader if available
                    if hasattr(self.simulator, "DataLoader") and hasattr(self.simulator.DataLoader, "load_lineups_from_excel"):
                        try:
                            teams = self.simulator.DataLoader.load_lineups_from_excel(day_number, lineup_file)
                        except Exception as e:
                            logger.error(f"Error loading teams for stamina recovery: {e}")
                    
                    # Process recovery for each team
                    if teams:
                        for team_id, characters in teams.items():
                            try:
                                recovery_results = self.stamina_tracker.simulate_daily_recovery(characters)
                                
                                if show_details:
                                    logger.info(f"Team {team_id} daily stamina recovery:")
                                    total_recovery = sum(r["recovery_amount"] for r in recovery_results["records"])
                                    logger.info(f"  Total recovery: {total_recovery:.1f}%")
                            except Exception as e:
                                logger.error(f"Error simulating stamina recovery for team {team_id}: {e}")
                except Exception as e:
                    logger.error(f"Error in daily stamina recovery: {e}")
            
            # Run original method
            results = self.simulator._original_run_matchday(
                day_number, lineup_file, show_details
            )
            
            # Generate stamina reports after matchday
            if self.stamina_tracker and results:
                try:
                    # Get all teams again (may have been updated during matches)
                    teams = {}
                    
                    # Try to get teams from DataLoader
                    if hasattr(self.simulator, "DataLoader") and hasattr(self.simulator.DataLoader, "load_lineups_from_excel"):
                        try:
                            teams = self.simulator.DataLoader.load_lineups_from_excel(day_number, lineup_file)
                        except Exception as e:
                            logger.error(f"Error loading teams for stamina reports: {e}")
                    
                    # Generate reports for all teams
                    if teams:
                        for team_id in teams.keys():
                            # Export dashboard files
                            try:
                                self.stamina_tracker.export_dashboard_txt(team_id)
                                self.stamina_tracker.export_dashboard_json(team_id)
                                
                                if show_details:
                                    report = self.stamina_tracker.generate_team_stamina_report(team_id)
                                    logger.info(f"\n{report}")
                            except Exception as e:
                                logger.error(f"Error generating stamina dashboard for team {team_id}: {e}")
                except Exception as e:
                    logger.error(f"Error generating stamina reports: {e}")
            
            return results
        
        # Replace simulator methods
        if hasattr(self.simulator, "simulate_match"):
            self.simulator.simulate_match = enhanced_simulate_match
        
        if hasattr(self.simulator, "run_matchday"):
            self.simulator.run_matchday = enhanced_run_matchday
        
        # Add manual stamina update method
        def update_team_stamina(self, team_id, day_number=0):
            """Manually update stamina for a team
            
            Args:
                team_id: Team ID to update
                day_number: Optional match day number (0 for non-match day)
                
            Returns:
                dict: Update results
            """
            if not hasattr(self, "stamina_tracker") or not self.stamina_tracker:
                return {"error": "Stamina tracker not active"}
            
            # Find team
            team = None
            
            if hasattr(self, "teams") and team_id in self.teams:
                team = self.teams[team_id]
            else:
                # Try to load from DataLoader
                if hasattr(self, "DataLoader") and hasattr(self.DataLoader, "load_lineups_from_excel"):
                    try:
                        teams = self.DataLoader.load_lineups_from_excel(day_number)
                        if team_id in teams:
                            team = teams[team_id]
                    except Exception as e:
                        return {"error": f"Error loading team: {e}"}
            
            if not team:
                return {"error": f"Team with ID {team_id} not found"}
            
            # Update stamina levels
            return self.stamina_tracker.update_stamina_levels(team, day_number)
        
        # Add manual recovery method
        def simulate_team_recovery(self, team_id):
            """Manually simulate stamina recovery for a team
            
            Args:
                team_id: Team ID
                
            Returns:
                dict: Recovery results
            """
            if not hasattr(self, "stamina_tracker") or not self.stamina_tracker:
                return {"error": "Stamina tracker not active"}
            
            # Find team
            team = None
            
            if hasattr(self, "teams") and team_id in self.teams:
                team = self.teams[team_id]
            else:
                # Try to load from DataLoader
                if hasattr(self, "DataLoader") and hasattr(self.DataLoader, "load_lineups_from_excel"):
                    try:
                        teams = self.DataLoader.load_lineups_from_excel(1)  # Use day 1 as default
                        if team_id in teams:
                            team = teams[team_id]
                    except Exception as e:
                        return {"error": f"Error loading team: {e}"}
            
            if not team:
                return {"error": f"Team with ID {team_id} not found"}
            
            # Simulate recovery
            return self.stamina_tracker.simulate_daily_recovery(team)
        
        # Add stamina dashboard method
        def generate_stamina_dashboard(self, team_id, format="txt"):
            """Generate stamina dashboard for a team
            
            Args:
                team_id: Team ID
                format: Output format ('txt' or 'json')
                
            Returns:
                str: Path to dashboard file
            """
            if not hasattr(self, "stamina_tracker") or not self.stamina_tracker:
                return "Error: Stamina tracker not active"
            
            # Generate dashboard
            if format.lower() == "json":
                return self.stamina_tracker.export_dashboard_json(team_id)
            else:
                return self.stamina_tracker.export_dashboard_txt(team_id)
        
        # Add methods to simulator
        self.simulator.update_team_stamina = update_team_stamina.__get__(self.simulator, type(self.simulator))
        self.simulator.simulate_team_recovery = simulate_team_recovery.__get__(self.simulator, type(self.simulator))
        self.simulator.generate_stamina_dashboard = generate_stamina_dashboard.__get__(self.simulator, type(self.simulator))
    
    def deactivate(self) -> bool:
        """Deactivate the stamina tracker
        
        Returns:
            bool: Success status
        """
        try:
            # Restore original methods
            if hasattr(self.simulator, "_original_simulate_match"):
                self.simulator.simulate_match = self.simulator._original_simulate_match
                delattr(self.simulator, "_original_simulate_match")
            
            if hasattr(self.simulator, "_original_run_matchday"):
                self.simulator.run_matchday = self.simulator._original_run_matchday
                delattr(self.simulator, "_original_run_matchday")
            
            # Remove stamina tracker methods
            if hasattr(self.simulator, "update_team_stamina"):
                delattr(self.simulator, "update_team_stamina")
            
            if hasattr(self.simulator, "simulate_team_recovery"):
                delattr(self.simulator, "simulate_team_recovery")
            
            if hasattr(self.simulator, "generate_stamina_dashboard"):
                delattr(self.simulator, "generate_stamina_dashboard")
            
            # Remove stamina tracker reference
            if hasattr(self.simulator, "stamina_tracker"):
                delattr(self.simulator, "stamina_tracker")
            
            self.stamina_tracker = None
            self.active = False
            
            logger.info("Stamina Tracker deactivated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error deactivating Stamina Tracker: {e}")
            return False

# Example usage
def integrate_stamina_tracker(simulator):
    """
    Integrate stamina tracker into the simulator
    
    Args:
        simulator: MetaLeagueSimulator instance
        
    Returns:
        bool: Success status
    """
    # Initialize integration
    stamina_integration = StaminaIntegration(simulator)
    
    # Activate stamina tracker
    success = stamina_integration.activate()
    
    if success:
        logger.info("Stamina Tracker integrated successfully")
    else:
        logger.error("Failed to integrate Stamina Tracker")
    
    return success