"""
META Fantasy League Simulator - Healing Integration
Integrates the Healing Mechanics with the Injury System
"""

import os
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger("HealingIntegration")

class HealingIntegration:
    """Integration module for Healing Mechanics in the MetaLeagueSimulator"""
    
    def __init__(self, simulator):
        """Initialize the healing integration
        
        Args:
            simulator: Reference to the main simulator instance
        """
        self.simulator = simulator
        self.healing_mechanics = None
        self.active = False
    
    def activate(self) -> bool:
        """Activate the healing mechanics
        
        Returns:
            bool: Success status
        """
        try:
            # Check if injury system is available
            if not hasattr(self.simulator, "injury_system"):
                logger.error("Injury system not found, required for healing mechanics")
                return False
            
            # Import healing mechanics
            from healing_mechanics import HealingMechanics
            
            # Initialize healing mechanics
            self.healing_mechanics = HealingMechanics(
                injury_system=self.simulator.injury_system,
                config=getattr(self.simulator, "config", None)
            )
            
            # Attach to simulator
            self.simulator.healing_mechanics = self.healing_mechanics
            
            # Enhance simulator methods
            self._enhance_simulator_methods()
            
            self.active = True
            logger.info("Healing Mechanics activated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error activating Healing Mechanics: {e}")
            self.active = False
            return False
    
    def _enhance_simulator_methods(self) -> None:
        """Enhance simulator methods with healing functionality"""
        # Store original methods for enhanced functionality
        if hasattr(self.simulator, "run_matchday"):
            self.simulator._original_run_matchday = self.simulator.run_matchday
        
        # Enhance run_matchday
        def enhanced_run_matchday(day_number=1, lineup_file=None, show_details=True):
            """Enhanced run_matchday with post-match healing"""
            # Run original method
            results = self.simulator._original_run_matchday(
                day_number, lineup_file, show_details
            )
            
            # Process post-match healing
            if self.healing_mechanics and results:
                try:
                    # Get all teams
                    teams = {}
                    
                    # Try to get teams from DataLoader if available
                    if hasattr(self.simulator, "DataLoader") and hasattr(self.simulator.DataLoader, "load_lineups_from_excel"):
                        try:
                            teams = self.simulator.DataLoader.load_lineups_from_excel(day_number, lineup_file)
                        except Exception as e:
                            logger.error(f"Error loading teams for healing: {e}")
                    
                    # Process healing for each team
                    healing_results = {}
                    
                    for team_id, characters in teams.items():
                        try:
                            # Attempt healing for this team
                            team_healing = self.healing_mechanics.heal_team_injuries(characters)
                            healing_results[team_id] = team_healing
                            
                            # Log healing results
                            if show_details and team_healing.get("successful_healings", 0) > 0:
                                logger.info(f"Team {team_id} performed {team_healing['successful_healings']} successful healings")
                                logger.info(f"  Healers used: {team_healing['healers_used']}")
                                logger.info(f"  Stamina spent: {team_healing['stamina_spent']:.1f}")
                        except Exception as e:
                            logger.error(f"Error processing healing for team {team_id}: {e}")
                    
                    # Generate healing reports
                    if show_details:
                        for team_id in healing_results.keys():
                            try:
                                healing_report = self.healing_mechanics.generate_healing_report(team_id)
                                logger.info(f"\n{healing_report}")
                            except Exception as e:
                                logger.error(f"Error generating healing report for team {team_id}: {e}")
                except Exception as e:
                    logger.error(f"Error processing post-match healing: {e}")
            
            return results
        
        # Replace simulator methods
        if hasattr(self.simulator, "run_matchday"):
            self.simulator.run_matchday = enhanced_run_matchday
    
    def enhance_visualization(self) -> bool:
        """Enhance match visualization with healing information
        
        Returns:
            bool: Success status
        """
        try:
            # Check if MatchVisualizer exists
            if not hasattr(self.simulator, "MatchVisualizer"):
                logger.warning("MatchVisualizer not found, skipping enhancement")
                return False
            
            # Check if MatchVisualizer.generate_match_summary exists
            if not hasattr(self.simulator.MatchVisualizer, "generate_match_summary"):
                logger.warning("MatchVisualizer.generate_match_summary not found, skipping enhancement")
                return False
            
            # Store original method
            original_generate_match_summary = self.simulator.MatchVisualizer.generate_match_summary
            
            # Create enhanced method
            def enhanced_generate_match_summary(result):
                """Enhanced match summary with healing information"""
                # Get original summary
                summary = original_generate_match_summary(result)
                
                # Add healing information if available
                if hasattr(result, "healing_results"):
                    healing_results = result.healing_results
                    
                    # Add healing section
                    summary += "\n\nHEALING ACTIVITY:\n"
                    
                    team_a_id = result.get("team_a_id", "unknown")
                    team_b_id = result.get("team_b_id", "unknown")
                    
                    # Add team A healing
                    if team_a_id in healing_results:
                        team_a_healing = healing_results[team_a_id]
                        summary += f"{result.get('team_a_name', 'Team A')}:\n"
                        summary += f"  Healings performed: {team_a_healing.get('successful_healings', 0)}\n"
                        
                        # Add details if any successful healings
                        if team_a_healing.get("successful_healings", 0) > 0:
                            summary += "  Details:\n"
                            for detail in team_a_healing.get("healing_details", []):
                                if detail.get("success", False):
                                    summary += f"    {detail.get('healer', 'Unknown')} healed {detail.get('injured', 'Unknown')}\n"
                    
                    # Add team B healing
                    if team_b_id in healing_results:
                        team_b_healing = healing_results[team_b_id]
                        summary += f"{result.get('team_b_name', 'Team B')}:\n"
                        summary += f"  Healings performed: {team_b_healing.get('successful_healings', 0)}\n"
                        
                        # Add details if any successful healings
                        if team_b_healing.get("successful_healings", 0) > 0:
                            summary += "  Details:\n"
                            for detail in team_b_healing.get("healing_details", []):
                                if detail.get("success", False):
                                    summary += f"    {detail.get('healer', 'Unknown')} healed {detail.get('injured', 'Unknown')}\n"
                
                return summary
            
            # Replace method
            self.simulator.MatchVisualizer.generate_match_summary = enhanced_generate_match_summary
            
            # Store original narrative method
            original_generate_narrative_report = self.simulator.MatchVisualizer.generate_narrative_report
            
            # Create enhanced narrative method
            def enhanced_generate_narrative_report(result):
                """Enhanced narrative report with healing narratives"""
                # Get original narrative
                narrative = original_generate_narrative_report(result)
                
                # Add healing narratives if available
                if hasattr(result, "healing_results"):
                    healing_results = result.healing_results
                    
                    # Count successful healings
                    successful_healings = 0
                    for team_id, team_healing in healing_results.items():
                        successful_healings += team_healing.get("successful_healings", 0)
                    
                    # Add narrative if any successful healings
                    if successful_healings > 0:
                        # Add healing paragraph
                        narrative += "\n\nIn the medical bay, "
                        
                        # Get notable healings
                        notable_healings = []
                        
                        for team_id, team_healing in healing_results.items():
                            team_name = result.get("team_a_name", "Team A") if team_id == result.get("team_a_id") else result.get("team_b_name", "Team B")
                            
                            for detail in team_healing.get("healing_details", []):
                                if detail.get("success", False):
                                    notable_healings.append({
                                        "healer": detail.get("healer", "Unknown"),
                                        "injured": detail.get("injured", "Unknown"),
                                        "team": team_name
                                    })
                        
                        # Highlight up to 2 notable healings
                        if notable_healings:
                            highlighted = notable_healings[:2]
                            
                            for i, healing in enumerate(highlighted):
                                healer = healing["healer"]
                                injured = healing["injured"]
                                team = healing["team"]
                                
                                if i == 0:
                                    narrative += f"{healer} of {team} successfully treated {injured}'s injuries"
                                else:
                                    narrative += f", while {healer} also provided medical attention to {injured}"
                            
                            narrative += f". In total, {successful_healings} successful treatment{'s' if successful_healings > 1 else ''} were performed after the match."
                
                return narrative
            
            # Replace narrative method
            self.simulator.MatchVisualizer.generate_narrative_report = enhanced_generate_narrative_report
            
            logger.info("Match visualization enhanced with healing information")
            return True
            
        except Exception as e:
            logger.error(f"Error enhancing visualization: {e}")
            return False
    
    def add_manual_healing_command(self) -> bool:
        """Add manual healing command to simulator
        
        Returns:
            bool: Success status
        """
        try:
            # Add healing command method to simulator
            def heal_injuries(self, healer_id, injured_id):
                """Manually heal an injured character using a healer
                
                Args:
                    healer_id: ID of healer character
                    injured_id: ID of injured character
                    
                Returns:
                    dict: Healing results
                """
                if not hasattr(self, "healing_mechanics") or not self.healing_mechanics:
                    return {"success": False, "error": "Healing mechanics not active"}
                
                # Find healer and injured characters
                healer = None
                injured = None
                
                # Look through all teams
                for team_id, team in self.teams.items():
                    for char in team:
                        if char.get("id") == healer_id:
                            healer = char
                        elif char.get("id") == injured_id:
                            injured = char
                
                if not healer:
                    return {"success": False, "error": f"Healer with ID {healer_id} not found"}
                
                if not injured:
                    return {"success": False, "error": f"Injured character with ID {injured_id} not found"}
                
                # Attempt healing
                return self.healing_mechanics.attempt_healing(healer, injured)
            
            # Add method to simulator
            self.simulator.heal_injuries = heal_injuries.__get__(self.simulator, type(self.simulator))
            
            logger.info("Manual healing command added to simulator")
            return True
            
        except Exception as e:
            logger.error(f"Error adding manual healing command: {e}")
            return False
    
    def deactivate(self) -> bool:
        """Deactivate the healing mechanics
        
        Returns:
            bool: Success status
        """
        try:
            # Restore original methods
            if hasattr(self.simulator, "_original_run_matchday"):
                self.simulator.run_matchday = self.simulator._original_run_matchday
                delattr(self.simulator, "_original_run_matchday")
            
            # Remove healing mechanics reference
            if hasattr(self.simulator, "healing_mechanics"):
                delattr(self.simulator, "healing_mechanics")
            
            # Remove manual healing command
            if hasattr(self.simulator, "heal_injuries"):
                delattr(self.simulator, "heal_injuries")
            
            self.healing_mechanics = None
            self.active = False
            
            logger.info("Healing Mechanics deactivated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error deactivating Healing Mechanics: {e}")
            return False

# Example usage
def integrate_healing_mechanics(simulator):
    """
    Integrate healing mechanics into the simulator
    
    Args:
        simulator: MetaLeagueSimulator instance
        
    Returns:
        bool: Success status
    """
    # Initialize integration
    healing_integration = HealingIntegration(simulator)
    
    # Activate healing mechanics
    success = healing_integration.activate()
    
    if success:
        # Enhance visualization
        healing_integration.enhance_visualization()
        
        # Add manual healing command
        healing_integration.add_manual_healing_command()
        
        logger.info("Healing Mechanics integrated successfully")
    else:
        logger.error("Failed to integrate Healing Mechanics")
    
    return success