"""
META Fantasy League Simulator - XP System Integration
Integrates the XP Progression System with the main simulator
"""

import os
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger("XPIntegration")

class XPIntegration:
    """Integration module for XP Progression System in the MetaLeagueSimulator"""
    
    def __init__(self, simulator):
        """Initialize the XP integration
        
        Args:
            simulator: Reference to the main simulator instance
        """
        self.simulator = simulator
        self.xp_system = None
        self.active = False
    
    def activate(self) -> bool:
        """Activate the XP progression system
        
        Returns:
            bool: Success status
        """
        try:
            # Import XP progression system
            from xp_progression_system import XPProgressionSystem
            
            # Initialize XP system
            self.xp_system = XPProgressionSystem(
                config=getattr(self.simulator, "config", None)
            )
            
            # Attach to simulator
            self.simulator.xp_system = self.xp_system
            
            # Enhance simulator methods
            self._enhance_simulator_methods()
            
            self.active = True
            logger.info("XP Progression System activated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error activating XP Progression System: {e}")
            self.active = False
            return False
    
    def _enhance_simulator_methods(self) -> None:
        """Enhance simulator methods with XP functionality"""
        # Store original methods for enhanced functionality
        self.simulator._original_simulate_match = self.simulator.simulate_match
        self.simulator._original_run_matchday = self.simulator.run_matchday
        
        # Enhance simulate_match
        def enhanced_simulate_match(team_a, team_b, day_number=1, show_details=True):
            """Enhanced simulate_match with XP progression"""
            # Load saved progression data for all characters
            for character in team_a + team_b:
                if self.xp_system:
                    self.xp_system.apply_progression_to_character(character)
            
            # Run original method
            match_result = self.simulator._original_simulate_match(
                team_a, team_b, day_number, show_details
            )
            
            # Process XP and leveling
            if self.xp_system:
                try:
                    xp_results = self.xp_system.process_match_results(match_result)
                    match_result["xp_progression"] = xp_results
                    
                    # Log XP results
                    if show_details:
                        logger.info("XP Progression processed:")
                        for char_prog in xp_results["character_progression"]:
                            if char_prog["level_ups"] > 0:
                                logger.info(f"  {char_prog['character_name']} leveled up to {char_prog['new_level']}!")
                            else:
                                logger.info(f"  {char_prog['character_name']} earned {char_prog['xp_earned']} XP")
                except Exception as e:
                    logger.error(f"Error processing XP progression: {e}")
            
            return match_result
        
        # Enhance run_matchday
        def enhanced_run_matchday(day_number=1, lineup_file=None, show_details=True):
            """Enhanced run_matchday with XP progression"""
            # Run original method
            results = self.simulator._original_run_matchday(
                day_number, lineup_file, show_details
            )
            
            # Process XP summary
            if self.xp_system and results:
                try:
                    # Log XP summary
                    if show_details:
                        logger.info("\n=== XP PROGRESSION SUMMARY ===")
                        logger.info(f"Day {day_number} completed")
                        
                        total_level_ups = 0
                        total_xp_gained = 0
                        
                        for match_result in results:
                            if "xp_progression" in match_result:
                                for char_prog in match_result["xp_progression"]["character_progression"]:
                                    total_level_ups += char_prog["level_ups"]
                                    total_xp_gained += char_prog["xp_earned"]
                        
                        logger.info(f"Total XP gained: {total_xp_gained}")
                        logger.info(f"Total level ups: {total_level_ups}")
                        logger.info("===============================")
                except Exception as e:
                    logger.error(f"Error generating XP summary: {e}")
            
            return results
        
        # Replace simulator methods
        self.simulator.simulate_match = enhanced_simulate_match
        self.simulator.run_matchday = enhanced_run_matchday
    
    def enhance_visualization(self) -> bool:
        """Enhance match visualization with XP progression
        
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
                """Enhanced match summary with XP progression"""
                # Get original summary
                summary = original_generate_match_summary(result)
                
                # Add XP progression if available
                if "xp_progression" in result:
                    xp_prog = result["xp_progression"]
                    
                    # Add XP section
                    summary += "\n\nXP PROGRESSION:\n"
                    
                    # Add character progression
                    for char_prog in xp_prog["character_progression"]:
                        char_name = char_prog["character_name"]
                        xp_earned = char_prog["xp_earned"]
                        
                        summary += f"- {char_name}: +{xp_earned} XP"
                        
                        # Add level up info
                        if char_prog["level_ups"] > 0:
                            new_level = char_prog["new_level"]
                            summary += f" (Level {new_level})"
                            
                            # Add stat increases
                            stat_increases = char_prog["stat_increases"]
                            if stat_increases:
                                increases = []
                                for attr, value in stat_increases.items():
                                    increases.append(f"{attr[1:].upper()}+{value}")
                                
                                summary += f" [{', '.join(increases)}]"
                        
                        summary += "\n"
                
                return summary
            
            # Replace method
            self.simulator.MatchVisualizer.generate_match_summary = enhanced_generate_match_summary
            
            # Store original narrative method
            original_generate_narrative_report = self.simulator.MatchVisualizer.generate_narrative_report
            
            # Create enhanced narrative method
            def enhanced_generate_narrative_report(result):
                """Enhanced narrative report with XP progression"""
                # Get original narrative
                narrative = original_generate_narrative_report(result)
                
                # Add XP progression if available
                if "xp_progression" in result:
                    xp_prog = result["xp_progression"]
                    
                    # Find significant level ups
                    level_ups = [p for p in xp_prog["character_progression"] if p["level_ups"] > 0]
                    
                    if level_ups:
                        # Add narrative paragraph about growth
                        narrative += "\n\nThe match provided valuable experience for several fighters. "
                        
                        # Highlight up to 2 level ups
                        highlighted = level_ups[:2]
                        for prog in highlighted:
                            char_name = prog["character_name"]
                            new_level = prog["new_level"]
                            
                            # Get primary stat increase
                            primary_stat = ""
                            if prog["stat_increases"]:
                                # Find highest stat increase
                                primary_attr = max(prog["stat_increases"].items(), key=lambda x: x[1])[0]
                                attr_name = primary_attr[1:].upper()
                                primary_stat = f" with notable gains in {attr_name}"
                            
                            narrative += f"{char_name} reached level {new_level}{primary_stat}. "
                
                return narrative
            
            # Replace narrative method
            self.simulator.MatchVisualizer.generate_narrative_report = enhanced_generate_narrative_report
            
            logger.info("Match visualization enhanced with XP progression")
            return True
            
        except Exception as e:
            logger.error(f"Error enhancing visualization: {e}")
            return False
    
    def deactivate(self) -> bool:
        """Deactivate the XP progression system
        
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
            
            # Remove XP system reference
            if hasattr(self.simulator, "xp_system"):
                delattr(self.simulator, "xp_system")
            
            self.xp_system = None
            self.active = False
            
            logger.info("XP Progression System deactivated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error deactivating XP Progression System: {e}")
            return False

# Example usage
def integrate_xp_progression(simulator):
    """
    Integrate XP progression system into the simulator
    
    Args:
        simulator: MetaLeagueSimulator instance
        
    Returns:
        bool: Success status
    """
    # Initialize integration
    xp_integration = XPIntegration(simulator)
    
    # Activate XP system
    success = xp_integration.activate()
    
    if success:
        # Enhance visualization
        xp_integration.enhance_visualization()
        
        logger.info("XP Progression System integrated successfully")
    else:
        logger.error("Failed to integrate XP Progression System")
    
    return success