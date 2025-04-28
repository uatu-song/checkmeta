"""
META Fantasy League Simulator - Synergy Integration Module
Integrates the SynergyEngine with the main simulator
"""

import os
import logging
from typing import Dict, List, Any, Optional
from synergy_engine import SynergyEngine

logger = logging.getLogger("SynergyIntegration")

class SynergyIntegration:
    """Integration module for SynergyEngine in the MetaLeagueSimulator"""
    
    def __init__(self, simulator):
        """Initialize the synergy integration
        
        Args:
            simulator: Reference to the main simulator instance
        """
        self.simulator = simulator
        self.synergy_engine = None
        self.active = False
    
    def activate(self) -> bool:
        """Activate the synergy system
        
        Returns:
            bool: Success status
        """
        try:
            # Initialize synergy engine
            self.synergy_engine = SynergyEngine(
                trait_system=self.simulator.trait_system,
                config=getattr(self.simulator, "config", None)
            )
            
            # Attach to simulator
            self.simulator.synergy_engine = self.synergy_engine
            
            # Register enhancement methods
            self._enhance_simulator_methods()
            
            self.active = True
            logger.info("Synergy system activated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error activating synergy system: {e}")
            self.active = False
            return False
    
    def _enhance_simulator_methods(self) -> None:
        """Enhance simulator methods with synergy functionality"""
        # Store original methods for enhanced functionality
        original_simulate_match = self.simulator.simulate_match
        
        # Enhance simulate_match
        def enhanced_simulate_match(team_a, team_b, day_number=1, show_details=True):
            """Enhanced simulate_match with synergy support"""
            # Initial synergy setup
            if show_details:
                logger.info("Detecting team synergies...")
            
            team_a_id = team_a[0]["team_id"] if team_a else "unknown"
            team_b_id = team_b[0]["team_id"] if team_b else "unknown"
            
            # Detect and apply synergies
            if self.synergy_engine:
                try:
                    # Detect and apply team A synergies
                    active_synergies_a = self.synergy_engine.detect_team_synergies(team_a, team_a_id)
                    self.synergy_engine.apply_synergy_effects(team_a, team_a_id)
                    
                    # Detect and apply team B synergies
                    active_synergies_b = self.synergy_engine.detect_team_synergies(team_b, team_b_id)
                    self.synergy_engine.apply_synergy_effects(team_b, team_b_id)
                    
                    # Log active synergies
                    if show_details:
                        logger.info(f"Team {team_a_id}: {len(active_synergies_a)} active synergies")
                        logger.info(f"Team {team_b_id}: {len(active_synergies_b)} active synergies")
                except Exception as e:
                    logger.error(f"Error processing synergies: {e}")
            
            # Call original method
            result = original_simulate_match(team_a, team_b, day_number, show_details)
            
            # Add synergy information to result
            if self.synergy_engine:
                try:
                    # Add synergy reports
                    result["team_a_synergies"] = self.synergy_engine.get_active_synergies_report(team_a_id)
                    result["team_b_synergies"] = self.synergy_engine.get_active_synergies_report(team_b_id)
                    
                    # Add dynamics reports
                    result["team_a_dynamics"] = self.synergy_engine.get_team_dynamics_report(team_a)
                    result["team_b_dynamics"] = self.synergy_engine.get_team_dynamics_report(team_b)
                except Exception as e:
                    logger.error(f"Error adding synergy information to result: {e}")
            
            # Reset synergy engine for next match
            if self.synergy_engine:
                self.synergy_engine.reset()
            
            return result
        
        # Attach enhanced methods
        self.simulator.simulate_match = enhanced_simulate_match
        self.simulator.original_simulate_match = original_simulate_match
        
        # Enhance other methods as needed
        self._enhance_convergence_system()
        self._enhance_trait_system()
    
    def _enhance_convergence_system(self) -> None:
        """Enhance convergence system with synergy support"""
        # Only proceed if convergence system exists
        if not hasattr(self.simulator, "convergence_system") or not self.simulator.convergence_system:
            logger.warning("Convergence system not found, skipping enhancement")
            return
            
        # Store original method
        original_process_convergences = self.simulator.convergence_system.process_convergences
        
        # Enhance process_convergences
        def enhanced_process_convergences(team_a, team_a_boards, team_b, team_b_boards, 
                                         context, max_per_char, show_details=True):
            """Enhanced process_convergences with synergy integration"""
            # Process convergences normally
            convergences = original_process_convergences(team_a, team_a_boards, team_b, team_b_boards, 
                                                       context, max_per_char, show_details)
            
            # Record convergence interactions in synergy engine
            if self.synergy_engine:
                try:
                    for conv in convergences:
                        # Find corresponding characters
                        a_char = next((c for c in team_a if c["name"] == conv["a_character"]), None)
                        b_char = next((c for c in team_b if c["name"] == conv["b_character"]), None)
                        
                        if a_char and b_char:
                            # Determine result
                            result = "win" if conv["winner"] == conv["a_character"] else "loss"
                            damage = conv.get("reduced_damage", 0)
                            
                            # Record interaction
                            self.synergy_engine.record_convergence_interaction(a_char, b_char, result, damage)
                            
                            # Apply dynamic bonuses
                            self.synergy_engine.apply_dynamic_bonuses(a_char, team_a)
                            self.synergy_engine.apply_dynamic_bonuses(b_char, team_b)
                except Exception as e:
                    logger.error(f"Error recording convergence interactions: {e}")
            
            return convergences
        
        # Attach enhanced method
        self.simulator.convergence_system.process_convergences = enhanced_process_convergences
        self.simulator.convergence_system.original_process_convergences = original_process_convergences
    
    def _enhance_trait_system(self) -> None:
        """Enhance trait system with synergy support"""
        # Only proceed if trait system exists
        if not hasattr(self.simulator, "trait_system") or not self.simulator.trait_system:
            logger.warning("Trait system not found, skipping enhancement")
            return
            
        # Store original method
        original_check_trait_activation = self.simulator.trait_system.check_trait_activation
        
        # Enhance check_trait_activation
        def enhanced_check_trait_activation(character, trigger, context=None):
            """Enhanced check_trait_activation with synergy support"""
            # Process normal trait activation
            activated_traits = original_check_trait_activation(character, trigger, context)
            
            # Apply synergy bonuses to trait activation chance
            if self.synergy_engine and "synergy_bonuses" in character:
                try:
                    # Apply trait activation bonus from synergies
                    trait_activation_bonus = character["synergy_bonuses"].get("trait_activation", 0)
                    dynamic_bonus = character["synergy_bonuses"].get("dynamic_trait_activation", 0)
                    
                    total_bonus = trait_activation_bonus + dynamic_bonus
                    
                    # If we have a bonus and no traits activated yet, try again
                    if total_bonus > 0 and not activated_traits:
                        # This gives a second chance for traits to activate
                        # with the synergy bonus applied
                        context = context or {}
                        context["activation_bonus"] = total_bonus
                        
                        # Call original method with modified context
                        activated_traits = original_check_trait_activation(character, trigger, context)
                except Exception as e:
                    logger.error(f"Error applying synergy bonus to trait activation: {e}")
            
            return activated_traits
        
        # Attach enhanced method
        self.simulator.trait_system.check_trait_activation = enhanced_check_trait_activation
        self.simulator.trait_system.original_check_trait_activation = original_check_trait_activation
        
        # Enhance _calculate_activation_chance if it exists
        if hasattr(self.simulator.trait_system, "_calculate_activation_chance"):
            original_calculate_activation_chance = self.simulator.trait_system._calculate_activation_chance
            
            # Enhance calculate_activation_chance
            def enhanced_calculate_activation_chance(character, trait, context):
                """Enhanced _calculate_activation_chance with synergy support"""
                # Get base activation chance
                base_chance = original_calculate_activation_chance(character, trait, context)
                
                # Apply bonus from context if present
                context = context or {}
                if "activation_bonus" in context:
                    base_chance += context["activation_bonus"]
                    
                    # Cap at reasonable range (20-95%)
                    return max(0.2, min(base_chance, 0.95))
                
                return base_chance
            
            # Attach enhanced method
            self.simulator.trait_system._calculate_activation_chance = enhanced_calculate_activation_chance
            self.simulator.trait_system.original_calculate_activation_chance = original_calculate_activation_chance
    
    def deactivate(self) -> bool:
        """Deactivate the synergy system
        
        Returns:
            bool: Success status
        """
        try:
            # Restore original methods
            if hasattr(self.simulator, "original_simulate_match"):
                self.simulator.simulate_match = self.simulator.original_simulate_match
                delattr(self.simulator, "original_simulate_match")
            
            if hasattr(self.simulator.convergence_system, "original_process_convergences"):
                self.simulator.convergence_system.process_convergences = self.simulator.convergence_system.original_process_convergences
                delattr(self.simulator.convergence_system, "original_process_convergences")
            
            if hasattr(self.simulator.trait_system, "original_check_trait_activation"):
                self.simulator.trait_system.check_trait_activation = self.simulator.trait_system.original_check_trait_activation
                delattr(self.simulator.trait_system, "original_check_trait_activation")
            
            if hasattr(self.simulator.trait_system, "original_calculate_activation_chance"):
                self.simulator.trait_system._calculate_activation_chance = self.simulator.trait_system.original_calculate_activation_chance
                delattr(self.simulator.trait_system, "original_calculate_activation_chance")
            
            # Remove synergy engine reference
            if hasattr(self.simulator, "synergy_engine"):
                delattr(self.simulator, "synergy_engine")
            
            self.synergy_engine = None
            self.active = False
            
            logger.info("Synergy system deactivated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error deactivating synergy system: {e}")
            return False