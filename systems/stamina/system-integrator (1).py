"""
StaminaSystemIntegrator

This module serves as the central coordination point for all stamina system
integrations in the META Fantasy League Simulator v5.0.

It manages the initialization, configuration, and coordination of the
trait system, convergence system, and combat system integrations with
the stamina system.
"""

import logging
import json
import os
from typing import Dict, Any, List, Optional
from system_base import SystemBase

# Import integrators
from trait_stamina_integrator import TraitStaminaIntegrator
from convergence_stamina_integrator import ConvergenceStaminaIntegrator
from combat_stamina_integrator import CombatStaminaIntegrator


class StaminaSystemIntegrator(SystemBase):
    """
    Central coordination class for all stamina system integrations.
    
    This class manages the initialization and coordination of all subsystem
    integrations with the stamina system, ensuring consistent configuration
    and proper event handling across all integration points.
    """
    
    def __init__(self, config, registry):
        """Initialize the stamina system integrator"""
        super().__init__("stamina_system_integrator", registry, config)
        self.logger = logging.getLogger("STAMINA_SYSTEM_INTEGRATOR")
        self.integrators = {}
        self.event_system = None
        self.stamina_system = None
        
    def _activate_implementation(self):
        """Activate the integrator by initializing and activating all subsystem integrations"""
        # Get required systems from registry
        self.stamina_system = self.registry.get("stamina_system")
        if not self.stamina_system:
            raise ValueError("Stamina system is required but not available in the registry")
            
        self.event_system = self.registry.get("event_system")
        
        # Ensure config directory exists
        self._ensure_config_directory()
        
        # Load or create the integration configuration
        self._load_or_create_integration_config()
        
        # Initialize and register integrators
        self._initialize_trait_integrator()
        self._initialize_convergence_integrator()
        self._initialize_combat_integrator()
        
        # Subscribe to relevant events
        if self.event_system:
            self._subscribe_to_events()
            
        self.logger.info("Stamina System Integrator activated successfully")
        
    def _ensure_config_directory(self):
        """Ensure the configuration directory exists"""
        config_dir = os.path.dirname(self.config.get(
            "paths.stamina_integration_config", 
            "config/stamina_integration_config.json"
        ))
        
        os.makedirs(config_dir, exist_ok=True)
        
    def _load_or_create_integration_config(self):
        """Load existing integration config or create a default one if not found"""
        config_path = self.config.get(
            "paths.stamina_integration_config", 
            "config/stamina_integration_config.json"
        )
        
        try:
            # Try to load existing config
            with open(config_path, 'r') as f:
                self.integration_config = json.load(f)
                self.logger.info(f"Loaded stamina integration config from {config_path}")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.logger.warning(f"Failed to load stamina integration config: {e}")
            self.logger.info("Creating default stamina integration config")
            
            # Create default config
            self.integration_config = {
                "version": "1.0.0",
                "trait": {
                    "trait_costs": {
                        "default": 5.0,
                        "low": 2.0,
                        "medium": 5.0,
                        "high": 10.0,
                        "extreme": 15.0
                    },
                    "threshold_restrictions": {
                        "60": ["extreme"],
                        "40": ["extreme", "high"],
                        "20": ["extreme", "high", "medium"]
                    },
                    "fatigue_effectiveness": {
                        "60": 0.9,
                        "40": 0.75,
                        "20": 0.5
                    }
                },
                "convergence": {
                    "costs": {
                        "initiator": 5.0,
                        "target": 3.0,
                        "assist": 2.0,
                        "defense": 4.0
                    },
                    "threshold_modifiers": {
                        "chance": {
                            "60": 0.9,
                            "40": 0.7,
                            "20": 0.4
                        },
                        "damage": {
                            "60": 0.9,
                            "40": 0.75,
                            "20": 0.5
                        },
                        "defense": {
                            "60": 0.9,
                            "40": 0.75,
                            "20": 0.5
                        }
                    },
                    "leadership_stamina_factor": 0.5
                },
                "combat": {
                    "damage_taken_multipliers": {
                        "60": 1.05,
                        "40": 1.15,
                        "20": 1.30
                    },
                    "attack_effectiveness": {
                        "60": 0.95,
                        "40": 0.85,
                        "20": 0.70
                    },
                    "critical_chance_modifiers": {
                        "60": 0.9,
                        "40": 0.7,
                        "20": 0.4
                    },
                    "stamina_costs": {
                        "attack": 1.0,
                        "defense": 0.5,
                        "counter": 1.5,
                        "critical": 2.0,
                        "dodge": 2.0,
                        "per_damage_point": 0.05
                    }
                }
            }
            
            # Save the default config
            try:
                with open(config_path, 'w') as f:
                    json.dump(self.integration_config, f, indent=2)
                self.logger.info(f"Created default stamina integration config at {config_path}")
            except Exception as e:
                self.logger.error(f"Failed to save default stamina integration config: {e}")
                
    def _initialize_trait_integrator(self):
        """Initialize and register the trait stamina integrator"""
        try:
            # Create the integrator
            trait_integrator = TraitStaminaIntegrator(self.config, self.registry)
            
            # Register in our intergrators dict
            self.integrators["trait"] = trait_integrator
            
            # Register in the system registry
            self.registry.register("trait_stamina_integrator", trait_integrator)
            
            # Activate the integrator
            self.registry.activate("trait_stamina_integrator")
            
            self.logger.info("Trait stamina integrator initialized and activated")
        except Exception as e:
            self.logger.error(f"Failed to initialize trait stamina integrator: {e}")
            
    def _initialize_convergence_integrator(self):
        """Initialize and register the convergence stamina integrator"""
        try:
            # Create the integrator
            convergence_integrator = ConvergenceStaminaIntegrator(self.config, self.registry)
            
            # Register in our intergrators dict
            self.integrators["convergence"] = convergence_integrator
            
            # Register in the system registry
            self.registry.register("convergence_stamina_integrator", convergence_integrator)
            
            # Activate the integrator
            self.registry.activate("convergence_stamina_integrator")
            
            self.logger.info("Convergence stamina integrator initialized and activated")
        except Exception as e:
            self.logger.error(f"Failed to initialize convergence stamina integrator: {e}")
            
    def _initialize_combat_integrator(self):
        """Initialize and register the combat stamina integrator"""
        try:
            # Create the integrator
            combat_integrator = CombatStaminaIntegrator(self.config, self.registry)
            
            # Register in our intergrators dict
            self.integrators["combat"] = combat_integrator
            
            # Register in the system registry
            self.registry.register("combat_stamina_integrator", combat_integrator)
            
            # Activate the integrator
            self.registry.activate("combat_stamina_integrator")
            
            self.logger.info("Combat stamina integrator initialized and activated")
        except Exception as e:
            self.logger.error(f"Failed to initialize combat stamina integrator: {e}")
            
    def _subscribe_to_events(self):
        """Subscribe to relevant events from the event system"""
        if not self.event_system or not hasattr(self.event_system, "subscribe"):
            self.logger.warning("Event system not available or does not support subscription")
            return
            
        # Subscribe to end of round events
        self.event_system.subscribe("round_end", self._handle_round_end_event)
        
        # Subscribe to match end events
        self.event_system.subscribe("match_end", self._handle_match_end_event)
        
        # Subscribe to stamina threshold events
        self.event_system.subscribe("stamina_threshold_crossed", self._handle_stamina_threshold_event)
        
        self.logger.info("Subscribed to relevant events")
        
    def _handle_round_end_event(self, event):
        """Handle end of round events"""
        # Check for character resignations due to stamina exhaustion
        match_context = event.get("match_context", {})
        characters = event.get("characters", [])
        
        combat_integrator = self.integrators.get("combat")
        if combat_integrator and hasattr(combat_integrator, "check_resignation"):
            for character in characters:
                if not character.get("is_ko", False):
                    combat_integrator.check_resignation(character, match_context)
                    
    def _handle_match_end_event(self, event):
        """Handle match end events"""
        # Currently nothing to do here, but could be used for match-end stamina analysis
        pass
        
    def _handle_stamina_threshold_event(self, event):
        """Handle stamina threshold crossing events"""
        # Log the threshold crossing
        character_name = event.get("character_name", "Unknown")
        threshold = event.get("threshold", 0)
        stamina = event.get("stamina", 0)
        
        self.logger.info(f"{character_name} crossed stamina threshold {threshold} " +
                        f"with current stamina {stamina:.1f}")
        
    def process_day_transition(self, day_number: int, characters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process stamina adjustments for a day transition.
        
        Args:
            day_number: Current day number
            characters: List of all characters to process
            
        Returns:
            Dictionary with stamina transition results
        """
        results = {
            "day": day_number,
            "characters_processed": len(characters),
            "recovered": []
        }
        
        if not self.stamina_system:
            self.logger.error("Stamina system not available for day transition processing")
            return results
            
        # Use stamina system to process overnight recovery
        for character in characters:
            if hasattr(self.stamina_system, "process_overnight_recovery"):
                old_stamina = character.get("stamina", 0)
                new_stamina = self.stamina_system.process_overnight_recovery(character)
                
                if new_stamina > old_stamina:
                    results["recovered"].append({
                        "character_id": character.get("id", "unknown"),
                        "character_name": character.get("name", "Unknown"),
                        "old_stamina": old_stamina,
                        "new_stamina": new_stamina,
                        "recovery": new_stamina - old_stamina
                    })
                    
        # Log and return results
        self.logger.info(f"Processed day transition {day_number} for {len(characters)} characters")
        self.logger.info(f"{len(results['recovered'])} characters recovered stamina")
        
        return results
        
    def generate_stamina_analytics(self, match_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate analytics for stamina usage in a match.
        
        Args:
            match_results: Match results data
            
        Returns:
            Stamina analytics data
        """
        analytics = {
            "match_id": match_results.get("match_id", "unknown"),
            "team_data": {},
            "character_data": {},
            "threshold_crossings": [],
            "high_cost_actions": []
        }
        
        # Process character results
        character_results = match_results.get("character_results", [])
        for char_result in character_results:
            char_id = char_result.get("character_id", "unknown")
            team_id = char_result.get("team_id", "unknown")
            
            # Initialize team data if not exists
            if team_id not in analytics["team_data"]:
                analytics["team_data"][team_id] = {
                    "avg_final_stamina": 0,
                    "total_stamina_spent": 0,
                    "threshold_crossings": {
                        "60": 0,
                        "40": 0,
                        "20": 0
                    }
                }
                
            # Process stamina logs
            stamina_log = char_result.get("stamina_log", [])
            if not stamina_log:
                continue
                
            # Get initial and final stamina
            initial_stamina = stamina_log[0]["stamina"] if stamina_log else 100
            final_stamina = stamina_log[-1]["stamina"] if stamina_log else 0
            
            # Calculate stamina spent
            stamina_spent = initial_stamina - final_stamina
            
            # Add to team totals
            analytics["team_data"][team_id]["total_stamina_spent"] += stamina_spent
            
            # Track character data
            analytics["character_data"][char_id] = {
                "initial_stamina": initial_stamina,
                "final_stamina": final_stamina,
                "stamina_spent": stamina_spent,
                "highest_cost_action": {
                    "cost": 0,
                    "action": "none"
                }
            }
            
            # Process log entries for threshold crossings and high cost actions
            current_stamina = initial_stamina
            prev_stamina = initial_stamina
            
            for entry in stamina_log:
                entry_stamina = entry.get("stamina", current_stamina)
                reason = entry.get("reason", "unknown")
                
                # Check for threshold crossings
                for threshold in [60, 40, 20]:
                    if prev_stamina > threshold and entry_stamina <= threshold:
                        analytics["threshold_crossings"].append({
                            "character_id": char_id,
                            "threshold": threshold,
                            "round": entry.get("round", 0),
                            "reason": reason
                        })
                        analytics["team_data"][team_id]["threshold_crossings"][str(threshold)] += 1
                        
                # Check for high cost actions
                cost = prev_stamina - entry_stamina
                if cost > 0 and ":" in reason:  # Structured reason like "trait_activation:power_strike"
                    action_type, action_name = reason.split(":", 1)
                    
                    # Track highest cost action for character
                    if cost > analytics["character_data"][char_id]["highest_cost_action"]["cost"]:
                        analytics["character_data"][char_id]["highest_cost_action"] = {
                            "cost": cost,
                            "action": reason
                        }
                        
                    # Track high cost actions overall
                    if cost >= 5.0:  # Threshold for "high cost" action
                        analytics["high_cost_actions"].append({
                            "character_id": char_id,
                            "cost": cost,
                            "action": reason,
                            "round": entry.get("round", 0)
                        })
                
                # Update for next iteration
                prev_stamina = entry_stamina
                current_stamina = entry_stamina
                
        # Calculate team averages
        for team_id, team_data in analytics["team_data"].items():
            team_char_count = sum(1 for char in character_results if char.get("team_id") == team_id)
            if team_char_count > 0:
                team_final_stamina = sum(
                    char["final_stamina"] for char_id, char in analytics["character_data"].items()
                    if any(cr.get("character_id") == char_id and cr.get("team_id") == team_id 
                         for cr in character_results)
                )
                team_data["avg_final_stamina"] = team_final_stamina / team_char_count
                
        return analytics
