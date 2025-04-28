"""
META Fantasy League Simulator - Injury System Integration
Integrates the Injury System with the main simulator
"""

import os
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger("InjuryIntegration")

class InjuryIntegration:
    """Integration module for Injury System in the MetaLeagueSimulator"""
    
    def __init__(self, simulator):
        """Initialize the injury integration
        
        Args:
            simulator: Reference to the main simulator instance
        """
        self.simulator = simulator
        self.injury_system = None
        self.active = False
    
    def activate(self) -> bool:
        """Activate the injury system
        
        Returns:
            bool: Success status
        """
        try:
            # Import injury system
            from injury_system import InjurySystem, InjurySeverity
            
            # Initialize injury system
            self.injury_system = InjurySystem(
                config=getattr(self.simulator, "config", None)
            )
            
            # Attach to simulator
            self.simulator.injury_system = self.injury_system
            
            # Also expose InjurySeverity enum
            self.simulator.InjurySeverity = InjurySeverity
            
            # Enhance simulator methods
            self._enhance_simulator_methods()
            
            self.active = True
            logger.info("Injury System activated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error activating Injury System: {e}")
            self.active = False
            return False
    
    def _enhance_simulator_methods(self) -> None:
        """Enhance simulator methods with injury functionality"""
        # Store original methods for enhanced functionality
        self.simulator._original_simulate_match = self.simulator.simulate_match
        self.simulator._original_run_matchday = self.simulator.run_matchday
        
        # Enhance simulate_match
        def enhanced_simulate_match(team_a, team_b, day_number=1, show_details=True):
            """Enhanced simulate_match with injury handling"""
            # Apply injury effects to characters before match
            if self.injury_system:
                # Process team A
                for character in team_a:
                    # Apply injury effects if injured
                    self.injury_system.apply_injury_effects(character)
                    
                    # Mark as inactive if injured
                    if character.get("is_injured", False):
                        character["was_active"] = False
                        if show_details:
                            logger.info(f"{character['name']} is inactive due to injury")
                
                # Process team B
                for character in team_b:
                    # Apply injury effects if injured
                    self.injury_system.apply_injury_effects(character)
                    
                    # Mark as inactive if injured
                    if character.get("is_injured", False):
                        character["was_active"] = False
                        if show_details:
                            logger.info(f"{character['name']} is inactive due to injury")
            
            # Run original method
            match_result = self.simulator._original_simulate_match(
                team_a, team_b, day_number, show_details
            )
            
            # Process injuries after match
            if self.injury_system:
                try:
                    injury_results = self.injury_system.handle_post_match_injuries(match_result)
                    match_result["injury_results"] = injury_results
                    
                    # Log injury results
                    if show_details:
                        new_injuries = injury_results.get("new_injuries", [])
                        if new_injuries:
                            logger.info(f"New injuries: {len(new_injuries)}")
                            for injury in new_injuries:
                                logger.info(f"  {injury['character_name']} - {injury['injury_type']} ({injury['severity']})")
                                logger.info(f"    Recovery: {injury['recovery_matches']} matches")
                        
                        recovered = injury_results.get("recovered", [])
                        if recovered:
                            logger.info(f"Recovered from injury: {len(recovered)}")
                            for recovery in recovered:
                                logger.info(f"  {recovery['character_name']} recovered from {recovery['injury_type']}")
                except Exception as e:
                    logger.error(f"Error processing injuries: {e}")
            
            return match_result
        
        # Enhance run_matchday
        def enhanced_run_matchday(day_number=1, lineup_file=None, show_details=True):
            """Enhanced run_matchday with injury reporting"""
            # Run original method
            results = self.simulator._original_run_matchday(
                day_number, lineup_file, show_details
            )
            
            # Process injury summary
            if self.injury_system and results:
                try:
                    # Generate injury report
                    injury_report = self.injury_system.generate_injury_report_text()
                    
                    # Log injury report
                    if show_details:
                        logger.info("\n=== INJURY REPORT SUMMARY ===")
                        logger.info(f"Day {day_number} completed")
                        logger.info(injury_report)
                except Exception as e:
                    logger.error(f"Error generating injury report: {e}")
            
            return results
        
        # Replace simulator methods
        self.simulator.simulate_match = enhanced_simulate_match
        self.simulator.run_matchday = enhanced_run_matchday
        
        # Enhance lineup loading if available
        if hasattr(self.simulator, "DataLoader") and hasattr(self.simulator.DataLoader, "load_lineups_from_excel"):
            self._enhance_lineup_loading()
    
    def _enhance_lineup_loading(self) -> None:
        """Enhance lineup loading to exclude injured players"""
        # Get original method
        original_load_lineups = self.simulator.DataLoader.load_lineups_from_excel
        
        # Create enhanced method
        def enhanced_load_lineups(day_number=1, lineup_file=None):
            """Enhanced lineup loading with injury handling"""
            # Call original method
            lineups = original_load_lineups(day_number, lineup_file)
            
            # Process injuries if injury system is active
            if self.injury_system:
                # Process each team
                for team_id, characters in lineups.items():
                    for character in characters:
                        char_id = character.get("id", "unknown")
                        
                        # Check if injured
                        if self.injury_system.is_character_injured(character):
                            # Mark as inactive
                            character["is_active"] = False
                            character["was_active"] = False
                            
                            # Apply injury effects
                            self.injury_system.apply_injury_effects(character)
                            
                            logger.debug(f"{character.get('name', 'Unknown')} marked inactive due to injury")
            
            return lineups
        
        # Replace method
        self.simulator.DataLoader.load_lineups_from_excel = enhanced_load_lineups
    
    def enhance_visualization(self) -> bool:
        """Enhance match visualization with injury information
        
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
                """Enhanced match summary with injury information"""
                # Get original summary
                summary = original_generate_match_summary(result)
                
                # Add injury information if available
                if "injury_results" in result:
                    injury_results = result["injury_results"]
                    
                    # Add injury section
                    summary += "\n\nINJURY REPORT:\n"
                    
                    # Add new injuries
                    new_injuries = injury_results.get("new_injuries", [])
                    if new_injuries:
                        summary += "New Injuries:\n"
                        for injury in new_injuries:
                            summary += f"- {injury['character_name']}: {injury['injury_type']} ({injury['severity']})\n"
                            summary += f"  Recovery time: {injury['recovery_matches']} matches\n"
                    else:
                        summary += "No new injuries\n"
                    
                    # Add recoveries
                    recovered = injury_results.get("recovered", [])
                    if recovered:
                        summary += "\nRecovered from Injury:\n"
                        for recovery in recovered:
                            summary += f"- {recovery['character_name']} recovered from {recovery['injury_type']}\n"
                
                return summary
            
            # Replace method
            self.simulator.MatchVisualizer.generate_match_summary = enhanced_generate_match_summary
            
            # Store original narrative method
            original_generate_narrative_report = self.simulator.MatchVisualizer.generate_narrative_report
            
            # Create enhanced narrative method
            def enhanced_generate_narrative_report(result):
                """Enhanced narrative report with injury narratives"""
                # Get original narrative
                narrative = original_generate_narrative_report(result)
                
                # Add injury narratives if available
                if "injury_results" in result:
                    injury_results = result["injury_results"]
                    
                    # Add narrative for new injuries
                    new_injuries = injury_results.get("new_injuries", [])
                    if new_injuries:
                        # Add narrative paragraph about injuries
                        narrative += "\n\nThe match took its toll physically. "
                        
                        # Highlight up to 2 significant injuries
                        significant = sorted(new_injuries, 
                                            key=lambda x: self._get_severity_value(x["severity"]), 
                                            reverse=True)[:2]
                        
                        for injury in significant:
                            char_name = injury["character_name"]
                            injury_type = injury["injury_type"]
                            severity = injury["severity"]
                            recovery = injury["recovery_matches"]
                            
                            if severity in ["MAJOR", "SEVERE"]:
                                narrative += f"{char_name} suffered a serious {injury_type.lower()} that will keep them sidelined for {recovery} matches. "
                            else:
                                narrative += f"{char_name} sustained a {injury_type.lower()} and is expected to miss {recovery} matches. "
                    
                    # Add narrative for recoveries
                    recovered = injury_results.get("recovered", [])
                    if recovered and len(recovered) <= 2:
                        # For 1-2 recoveries, highlight them specifically
                        narrative += "\n\nOn the medical front, "
                        
                        for i, recovery in enumerate(recovered):
                            char_name = recovery["character_name"]
                            injury_type = recovery["injury_type"]
                            
                            if i == 0:
                                narrative += f"{char_name} has recovered from {injury_type.lower()} and is cleared to return"
                            else:
                                narrative += f", while {char_name} has also overcome {injury_type.lower()}"
                                
                        narrative += ". "
                    elif recovered and len(recovered) > 2:
                        # For many recoveries, summarize
                        narrative += f"\n\nThe medical team had good news as {len(recovered)} players were cleared to return from their injuries. "
                
                return narrative
            
            # Replace narrative method
            self.simulator.MatchVisualizer.generate_narrative_report = enhanced_generate_narrative_report
            
            logger.info("Match visualization enhanced with injury information")
            return True
            
        except Exception as e:
            logger.error(f"Error enhancing visualization: {e}")
            return False
    
    def _get_severity_value(self, severity: str) -> int:
        """Get numeric value for injury severity
        
        Args:
            severity: Severity string
            
        Returns:
            int: Numeric value
        """
        severity_values = {
            "MINOR": 1,
            "MODERATE": 2,
            "MAJOR": 3,
            "SEVERE": 4
        }
        
        return severity_values.get(severity, 0)
    
    def deactivate(self) -> bool:
        """Deactivate the injury system
        
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
            
            # Restore lineup loading method if enhanced
            if hasattr(self.simulator, "DataLoader") and hasattr(self.simulator.DataLoader, "original_load_lineups"):
                self.simulator.DataLoader.load_lineups_from_excel = self.simulator.DataLoader.original_load_lineups
                delattr(self.simulator.DataLoader, "original_load_lineups")
            
            # Remove injury system reference
            if hasattr(self.simulator, "injury_system"):
                delattr(self.simulator, "injury_system")
            
            if hasattr(self.simulator, "InjurySeverity"):
                delattr(self.simulator, "InjurySeverity")
            
            self.injury_system = None
            self.active = False
            
            logger.info("Injury System deactivated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error deactivating Injury System: {e}")
            return False

# Example usage
def integrate_injury_system(simulator):
    """
    Integrate injury system into the simulator
    
    Args:
        simulator: MetaLeagueSimulator instance
        
    Returns:
        bool: Success status
    """
    # Initialize integration
    injury_integration = InjuryIntegration(simulator)
    
    # Activate injury system
    success = injury_integration.activate()
    
    if success:
        # Enhance visualization
        injury_integration.enhance_visualization()
        
        logger.info("Injury System integrated successfully")
    else:
        logger.error("Failed to integrate Injury System")
    
    return success