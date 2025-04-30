"""
End-of-Round Effects System for META Fantasy League Simulator
Handles all effects that occur at the end of each round in matches

Version: 5.1.0 - Guardian Compliant
"""

import time
import json
import datetime
import logging
import math
import random
from typing import Dict, List, Any, Optional, Tuple, Union, Set
from collections import defaultdict

from system_base import SystemBase

class EndOfRoundEffectsSystem(SystemBase):
    """
    End-of-Round Effects System for META Fantasy League
    
    Handles all effects that need to be processed at the end of each round:
    - Stamina decay and recovery
    - Stat modifier duration tracking
    - Trait cooldown updates
    - Morale updates
    - XP awards
    - Status effect processing
    
    Compliant with Guardian standards:
    - Event emissions via EventEmitter
    - External configuration
    - Structured logging
    - Error handling
    - System registration
    """
    
    def __init__(self, config, registry=None):
        """Initialize the end-of-round effects system"""
        super().__init__(config)
        self.name = "end_of_round_effects_system"
        self.logger = logging.getLogger("META_SIMULATOR.EndOfRoundEffectsSystem")
        
        # Store registry if provided
        self._registry = registry
        
        # Cache for commonly used systems and configurations
        self._event_system = None
        self._trait_system = None
        self._stamina_system = None
        self._morale_system = None
        self._xp_system = None
        
        # Load configuration settings
        self._load_configuration()
        
        # Initialize state
        self.active = False
        self.round_statistics = defaultdict(int)
        
        self.logger.info("End-of-round effects system initialized with stamina_decay_multiplier={:.2f}".format(
            self._stamina_decay_multiplier))
    
    def _load_configuration(self):
        """Load configuration settings"""
        try:
            # Load stamina settings
            stamina_config = self.config.get("combat_calibration.stamina_settings", {})
            self._stamina_decay_multiplier = stamina_config.get("stamina_decay_per_round_multiplier", 1.15)
            self._low_stamina_threshold = stamina_config.get("low_stamina_threshold", 30)
            self._base_stamina_decay = self.config.get("simulation.base_stamina_decay", 5)
            
            # Load XP settings
            xp_config = self.config.get("xp_settings", {})
            self._base_round_xp = xp_config.get("base_round_xp", 1)
            self._ko_xp_bonus = xp_config.get("ko_xp_bonus", 5)
            self._survival_xp_bonus = xp_config.get("survival_xp_bonus", 2)
            
            # Load trait settings
            trait_config = self.config.get("trait_settings", {})
            self._trait_cooldown_reduction_chance = trait_config.get("cooldown_reduction_chance", 0.1)
            
            # Load status effect settings
            status_config = self.config.get("status_effects", {})
            self._status_effect_duration_multiplier = status_config.get("duration_multiplier", 1.0)
            self._natural_recovery_chance = status_config.get("natural_recovery_chance", 0.05)
            
            # Emit configuration loaded event
            self._emit_event("end_of_round_configuration_loaded", {
                "stamina_decay_multiplier": self._stamina_decay_multiplier,
                "base_stamina_decay": self._base_stamina_decay,
                "base_round_xp": self._base_round_xp,
                "trait_cooldown_reduction_chance": self._trait_cooldown_reduction_chance
            })
            
        except Exception as e:
            self.logger.error("Error loading configuration: {}".format(e))
            self._emit_error_event("load_configuration", str(e))
            
            # Set default values as fallback
            self._stamina_decay_multiplier = 1.15
            self._low_stamina_threshold = 30
            self._base_stamina_decay = 5
            self._base_round_xp = 1
            self._ko_xp_bonus = 5
            self._survival_xp_bonus = 2
            self._trait_cooldown_reduction_chance = 0.1
            self._status_effect_duration_multiplier = 1.0
            self._natural_recovery_chance = 0.05
    
    def activate(self):
        """Activate the end-of-round effects system"""
        self.active = True
        self.logger.info("End-of-round effects system activated")
        return True
    
    def deactivate(self):
        """Deactivate the end-of-round effects system"""
        self.active = False
        self.logger.info("End-of-round effects system deactivated")
        return True
    
    def is_active(self):
        """Check if the end-of-round effects system is active"""
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
    
    def _get_trait_system(self):
        """Get trait system from registry (lazy loading)"""
        if not self._trait_system:
            registry = self._get_registry()
            self._trait_system = registry.get("trait_system")
            if not self._trait_system:
                self.logger.warning("Trait system not available, trait effects will not be applied")
        return self._trait_system
    
    def _get_stamina_system(self):
        """Get stamina system from registry (lazy loading)"""
        if not self._stamina_system:
            registry = self._get_registry()
            self._stamina_system = registry.get("stamina_system")
            if not self._stamina_system:
                self.logger.warning("Stamina system not available, stamina effects will not be applied")
        return self._stamina_system
    
    def _get_morale_system(self):
        """Get morale system from registry (lazy loading)"""
        if not self._morale_system:
            registry = self._get_registry()
            self._morale_system = registry.get("morale_system")
            if not self._morale_system:
                self.logger.warning("Morale system not available, morale effects will not be applied")
        return self._morale_system
    
    def _get_xp_system(self):
        """Get XP system from registry (lazy loading)"""
        if not self._xp_system:
            registry = self._get_registry()
            self._xp_system = registry.get("xp_system")
            if not self._xp_system:
                self.logger.warning("XP system not available, XP will not be awarded")
        return self._xp_system
    
    def apply_end_of_round_effects(self, characters: List[Dict[str, Any]], 
                                 match_context: Dict[str, Any]) -> None:
        """
        Apply end of round effects to all characters
        
        Args:
            characters: List of character dictionaries
            match_context: Match context dictionary
        """
        if not self.active:
            self.logger.warning("End-of-round effects system not active, effects will not be applied")
            return
            
        try:
            round_num = match_context.get("round", 0)
            character_count = len(characters)
            
            self.logger.info("Applying end of round effects for round {} to {} characters".format(
                round_num, character_count))
            
            # Track various statistics
            stats = {
                "stamina_decay_total": 0,
                "stamina_recovery_total": 0,
                "xp_granted_total": 0,
                "morale_changes_total": 0,
                "status_effects_processed": 0,
                "trait_cooldowns_reduced": 0,
                "active_characters": 0,
                "ko_characters": 0
            }
            
            # Emit round_effects_start event
            self._emit_event("round_effects_start", {
                "round": round_num,
                "character_count": character_count,
                "match_context": match_context
            })
            
            # Process each character
            for character in characters:
                try:
                    character_id = character.get("id", "unknown")
                    character_name = character.get("name", "Unknown")
                    
                    # Skip processing if character is KO'd
                    if character.get("is_ko", False):
                        stats["ko_characters"] += 1
                        continue
                    
                    stats["active_characters"] += 1
                    
                    # Apply stamina decay
                    stamina_changes = self._apply_stamina_effects(character, match_context)
                    stats["stamina_decay_total"] += stamina_changes.get("decay", 0)
                    stats["stamina_recovery_total"] += stamina_changes.get("recovery", 0)
                    
                    # Update trait cooldowns
                    trait_changes = self._update_trait_cooldowns(character, match_context)
                    stats["trait_cooldowns_reduced"] += trait_changes.get("reduced_count", 0)
                    
                    # Apply morale effects
                    morale_changes = self._apply_morale_effects(character, match_context)
                    stats["morale_changes_total"] += abs(morale_changes.get("change", 0))
                    
                    # Process status effects
                    status_changes = self._process_status_effects(character, match_context)
                    stats["status_effects_processed"] += status_changes.get("processed_count", 0)
                    
                    # Award XP
                    xp_awarded = self._award_round_xp(character, match_context)
                    stats["xp_granted_total"] += xp_awarded
                    
                    # Update round statistics
                    if "rStats" not in character:
                        character["rStats"] = {}
                    
                    if "ROUNDS_SURVIVED" not in character["rStats"]:
                        character["rStats"]["ROUNDS_SURVIVED"] = 0
                    character["rStats"]["ROUNDS_SURVIVED"] += 1
                    
                    # Emit character_round_effects_applied event
                    self._emit_event("character_round_effects_applied", {
                        "character": character,
                        "round": round_num,
                        "stamina_change": stamina_changes,
                        "trait_changes": trait_changes,
                        "morale_changes": morale_changes,
                        "status_changes": status_changes,
                        "xp_awarded": xp_awarded,
                        "match_context": match_context
                    })
                    
                except Exception as e:
                    self.logger.error("Error applying end of round effects to character {}: {}".format(
                        character_id, e))
                    self._emit_error_event("apply_character_effects", str(e), {
                        "character_id": character_id,
                        "round": round_num
                    })
            
            # Update round statistics
            self.round_statistics["total_rounds_processed"] += 1
            self.round_statistics["total_character_rounds"] += stats["active_characters"]
            self.round_statistics["total_stamina_decay"] += stats["stamina_decay_total"]
            self.round_statistics["total_xp_granted"] += stats["xp_granted_total"]
            
            # Emit round_effects_complete event
            self._emit_event("round_effects_complete", {
                "round": round_num,
                "active_characters": stats["active_characters"],
                "ko_characters": stats["ko_characters"],
                "stamina_decay_total": stats["stamina_decay_total"],
                "stamina_recovery_total": stats["stamina_recovery_total"],
                "xp_granted_total": stats["xp_granted_total"],
                "trait_cooldowns_reduced": stats["trait_cooldowns_reduced"],
                "match_context": match_context
            })
            
            self.logger.info("End of round effects for round {} completed".format(round_num))
            
        except Exception as e:
            self.logger.error("Error applying end of round effects for round {}: {}".format(
                match_context.get("round", 0), e))
            self._emit_error_event("apply_end_of_round_effects", str(e), {
                "round": match_context.get("round", 0)
            })
    
    def _apply_stamina_effects(self, character: Dict[str, Any], match_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply stamina effects to a character
        
        Args:
            character: Character dictionary
            match_context: Match context dictionary
            
        Returns:
            Dictionary with stamina changes
        """
        try:
            stamina_system = self._get_stamina_system()
            if stamina_system and hasattr(stamina_system, "apply_end_of_round_effects"):
                # If stamina system has its own implementation, use that
                return stamina_system.apply_character_end_of_round_effects(character, match_context)
            
            # Otherwise, use our implementation
            character_id = character.get("id", "unknown")
            character_name = character.get("name", "Unknown")
            round_num = match_context.get("round", 0)
            
            # Get current stamina
            current_stamina = character.get("stamina", 100)
            was_low_stamina = current_stamina < self._low_stamina_threshold
            
            # Calculate base stamina decay
            base_decay = self._base_stamina_decay
            decay_multiplier = self._stamina_decay_multiplier
            
            # Apply character-specific modifiers
            if "aRES" in character:
                # Higher RES (Resilience) reduces stamina decay
                res_factor = 1.0 - (min(100, character["aRES"]) / 200)  # 0.5 to 1.0
                decay_multiplier *= res_factor
            
            # Calculate final decay amount
            decay_amount = base_decay * decay_multiplier
            decay_amount = round(decay_amount, 1)
            
            # Apply decay
            new_stamina = max(0, current_stamina - decay_amount)
            
            # Check for stamina depletion
            is_depleted = new_stamina == 0
            is_newly_depleted = is_depleted and current_stamina > 0
            
            # Apply recovery effects if character has stamina recovery traits
            recovery_amount = 0
            
            if "stamina_recovery" in character:
                recovery_amount = character["stamina_recovery"]
                new_stamina = min(100, new_stamina + recovery_amount)
                self.logger.debug("Character {} has stamina recovery: +{:.1f}".format(
                    character_name, recovery_amount))
            
            # Update stamina
            character["stamina"] = new_stamina
            
            # Check for low stamina status
            is_now_low_stamina = new_stamina < self._low_stamina_threshold
            
            # Emit stamina_updated event
            self._emit_event("stamina_updated", {
                "character": character,
                "old_stamina": current_stamina,
                "new_stamina": new_stamina,
                "decay_amount": decay_amount,
                "recovery_amount": recovery_amount,
                "is_depleted": is_depleted,
                "is_newly_depleted": is_newly_depleted,
                "match_context": match_context
            })
            
            # Emit stamina_depleted event if newly depleted
            if is_newly_depleted:
                self._emit_event("stamina_depleted", {
                    "character": character,
                    "stamina_before": current_stamina,
                    "match_context": match_context
                })
                
                # Update rStats
                if "rStats" in character:
                    if "STAMINA_DEPLETED" not in character["rStats"]:
                        character["rStats"]["STAMINA_DEPLETED"] = 0
                    character["rStats"]["STAMINA_DEPLETED"] += 1
            
            # Emit low_stamina_entered event if newly entered low stamina
            if is_now_low_stamina and not was_low_stamina:
                self._emit_event("low_stamina_entered", {
                    "character": character,
                    "stamina_before": current_stamina,
                    "stamina_after": new_stamina,
                    "threshold": self._low_stamina_threshold,
                    "match_context": match_context
                })
            
            # Return stamina changes
            return {
                "old_stamina": current_stamina,
                "new_stamina": new_stamina,
                "decay": decay_amount,
                "recovery": recovery_amount,
                "is_depleted": is_depleted,
                "is_newly_depleted": is_newly_depleted,
                "was_low_stamina": was_low_stamina,
                "is_now_low_stamina": is_now_low_stamina
            }
            
        except Exception as e:
            self.logger.error("Error applying stamina effects: {}".format(e))
            self._emit_error_event("apply_stamina_effects", str(e), {
                "character_id": character.get("id", "unknown")
            })
            
            # Return minimal changes on error
            return {
                "old_stamina": character.get("stamina", 100),
                "new_stamina": character.get("stamina", 100),
                "decay": 0,
                "recovery": 0,
                "is_depleted": False,
                "is_newly_depleted": False,
                "was_low_stamina": False,
                "is_now_low_stamina": False
            }
    
    def _update_trait_cooldowns(self, character: Dict[str, Any], match_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update trait cooldowns for a character
        
        Args:
            character: Character dictionary
            match_context: Match context dictionary
            
        Returns:
            Dictionary with trait cooldown changes
        """
        try:
            trait_system = self._get_trait_system()
            if trait_system and hasattr(trait_system, "update_cooldowns"):
                # If trait system has its own implementation, use that
                return trait_system.update_character_cooldowns(character, match_context)
            
            # Otherwise, use our implementation
            character_id = character.get("id", "unknown")
            character_name = character.get("name", "Unknown")
            
            cooldowns_reduced = 0
            cooldowns_expired = 0
            traits_activated = []
            
            # Check if character has active traits
            if "traits" not in character:
                return {
                    "reduced_count": 0,
                    "expired_count": 0,
                    "traits_activated": []
                }
            
            # Update each trait cooldown
            for trait_id, trait_data in character["traits"].items():
                # Skip traits without cooldowns
                if "cooldown_remaining" not in trait_data:
                    continue
                
                # Get current cooldown
                current_cooldown = trait_data["cooldown_remaining"]
                
                # Skip traits not on cooldown
                if current_cooldown <= 0:
                    continue
                
                # Check for cooldown reduction chance
                reduced = False
                if random.random() < self._trait_cooldown_reduction_chance:
                    # Apply cooldown reduction
                    trait_data["cooldown_remaining"] = max(0, current_cooldown - 1)
                    reduced = True
                    cooldowns_reduced += 1
                    
                    # Log cooldown reduction
                    self.logger.debug("Trait {} cooldown reduced for character {}".format(
                        trait_id, character_name))
                else:
                    # Normal cooldown decrement
                    trait_data["cooldown_remaining"] = max(0, current_cooldown - 1)
                
                # Check if cooldown expired
                if trait_data["cooldown_remaining"] == 0 and current_cooldown > 0:
                    cooldowns_expired += 1
                    
                    # Log cooldown expiration
                    self.logger.debug("Trait {} cooldown expired for character {}".format(
                        trait_id, character_name))
                    
                    # Check if trait should auto-activate
                    if trait_data.get("auto_activate", False):
                        traits_activated.append(trait_id)
                        
                        # Emit trait_ready event
                        self._emit_event("trait_ready", {
                            "character": character,
                            "trait_id": trait_id,
                            "trait_name": trait_data.get("name", trait_id),
                            "auto_activate": True,
                            "match_context": match_context
                        })
                    else:
                        # Emit trait_ready event
                        self._emit_event("trait_ready", {
                            "character": character,
                            "trait_id": trait_id,
                            "trait_name": trait_data.get("name", trait_id),
                            "auto_activate": False,
                            "match_context": match_context
                        })
            
            # Return cooldown changes
            return {
                "reduced_count": cooldowns_reduced,
                "expired_count": cooldowns_expired,
                "traits_activated": traits_activated
            }
            
        except Exception as e:
            self.logger.error("Error updating trait cooldowns: {}".format(e))
            self._emit_error_event("update_trait_cooldowns", str(e), {
                "character_id": character.get("id", "unknown")
            })
            
            # Return minimal changes on error
            return {
                "reduced_count": 0,
                "expired_count": 0,
                "traits_activated": []
            }
    
    def _apply_morale_effects(self, character: Dict[str, Any], match_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply morale effects to a character
        
        Args:
            character: Character dictionary
            match_context: Match context dictionary
            
        Returns:
            Dictionary with morale changes
        """
        try:
            morale_system = self._get_morale_system()
            if morale_system and hasattr(morale_system, "apply_end_of_round_effects"):
                # If morale system has its own implementation, use that
                return morale_system.apply_character_end_of_round_effects(character, match_context)
            
            # Otherwise, use our implementation
            character_id = character.get("id", "unknown")
            character_name = character.get("name", "Unknown")
            
            # Skip if character doesn't have morale stat
            if "morale" not in character:
                return {"change": 0, "old_morale": 0, "new_morale": 0}
            
            # Get current morale
            current_morale = character.get("morale", 100)
            
            # Apply base morale decay/recovery
            morale_change = 0
            
            # Morale recovery for high HP
            if character.get("HP", 100) >= 80:
                morale_change += 1
            
            # Morale decay for low HP
            if character.get("HP", 100) < 30:
                morale_change -= 1
            
            # Morale decay for low stamina
            if character.get("stamina", 100) < self._low_stamina_threshold:
                morale_change -= 1
            
            # Apply character traits that affect morale
            if "aWIL" in character:
                # Higher WIL (Willpower) improves morale recovery/reduces decay
                wil_factor = character["aWIL"] / 100  # 0 to 1+
                if morale_change > 0:
                    morale_change *= (1 + (wil_factor * 0.5))  # Up to 50% more recovery
                elif morale_change < 0:
                    morale_change *= (1 - (wil_factor * 0.3))  # Up to 30% less decay
            
            # Round morale change
            morale_change = round(morale_change, 1)
            
            # Apply morale change
            new_morale = max(0, min(100, current_morale + morale_change))
            character["morale"] = new_morale
            
            # Check for morale collapse
            was_collapsed = character.get("morale_collapsed", False)
            
            # Determine collapse threshold
            collapse_threshold = match_context.get("morale_collapse_threshold", 30)
            
            # Check if character has collapsed
            is_collapsed = new_morale <= collapse_threshold
            is_newly_collapsed = is_collapsed and not was_collapsed
            
            # Update morale collapse state
            if is_newly_collapsed:
                character["morale_collapsed"] = True
                
                # Emit morale_collapsed event
                self._emit_event("morale_collapsed", {
                    "character": character,
                    "old_morale": current_morale,
                    "new_morale": new_morale,
                    "threshold": collapse_threshold,
                    "match_context": match_context
                })
                
                # Update rStats
                if "rStats" in character:
                    if "MORALE_COLLAPSED" not in character["rStats"]:
                        character["rStats"]["MORALE_COLLAPSED"] = 0
                    character["rStats"]["MORALE_COLLAPSED"] += 1
            
            # Emit morale_updated event
            self._emit_event("morale_updated", {
                "character": character,
                "old_morale": current_morale,
                "new_morale": new_morale,
                "change": morale_change,
                "is_collapsed": is_collapsed,
                "is_newly_collapsed": is_newly_collapsed,
                "match_context": match_context
            })
            
            # Return morale changes
            return {
                "change": morale_change,
                "old_morale": current_morale,
                "new_morale": new_morale,
                "is_collapsed": is_collapsed,
                "is_newly_collapsed": is_newly_collapsed
            }
            
        except Exception as e:
            self.logger.error("Error applying morale effects: {}".format(e))
            self._emit_error_event("apply_morale_effects", str(e), {
                "character_id": character.get("id", "unknown")
            })
            
            # Return minimal changes on error
            return {
                "change": 0,
                "old_morale": character.get("morale", 100),
                "new_morale": character.get("morale", 100),
                "is_collapsed": False,
                "is_newly_collapsed": False
            }
    
    def _process_status_effects(self, character: Dict[str, Any], match_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process status effects for a character
        
        Args:
            character: Character dictionary
            match_context: Match context dictionary
            
        Returns:
            Dictionary with status effect changes
        """
        try:
            character_id = character.get("id", "unknown")
            character_name = character.get("name", "Unknown")
            
            # Skip if character doesn't have status effects
            if "status_effects" not in character:
                return {"processed_count": 0, "expired_count": 0, "recovered_count": 0}
            
            processed_count = 0
            expired_count = 0
            recovered_count = 0
            
            # Process each status effect
            status_effects_to_remove = []
            
            for effect_id, effect_data in character["status_effects"].items():
                processed_count += 1
                
                # Get duration
                if "duration" not in effect_data:
                    continue
                
                current_duration = effect_data["duration"]
                
                # Apply duration multiplier
                duration_multiplier = self._status_effect_duration_multiplier
                
                # Apply character traits that affect duration
                if "aRES" in character and effect_data.get("type") in ["debuff", "negative", "damage"]:
                    # Higher RES (Resilience) reduces negative status effect duration
                    res_factor = character["aRES"] / 200  # 0 to 0.5
                    duration_multiplier *= (1 - res_factor)  # 0.5 to 1.0
                
                # Decrement duration
                effect_data["duration"] = max(0, current_duration - duration_multiplier)
                
                # Check for natural recovery
                recovered = False
                if random.random() < self._natural_recovery_chance:
                    effect_data["duration"] = 0
                    recovered = True
                    recovered_count += 1
                    
                    # Log natural recovery
                    self.logger.debug("Character {} naturally recovered from status effect {}".format(
                        character_name, effect_id))
                
                # Check if effect expired
                if effect_data["duration"] <= 0:
                    status_effects_to_remove.append(effect_id)
                    expired_count += 1
                    
                    # Emit status_effect_expired event
                    self._emit_event("status_effect_expired", {
                        "character": character,
                        "effect_id": effect_id,
                        "effect_name": effect_data.get("name", effect_id),
                        "natural_recovery": recovered,
                        "match_context": match_context
                    })
                else:
                    # Apply ongoing effect
                    if "ongoing_effect" in effect_data:
                        effect_type = effect_data["ongoing_effect"].get("type")
                        effect_value = effect_data["ongoing_effect"].get("value", 0)
                        
                        if effect_type == "damage":
                            # Apply damage
                            if "HP" in character:
                                old_hp = character["HP"]
                                new_hp = max(0, old_hp - effect_value)
                                character["HP"] = new_hp
                                
                                # Log damage
                                self.logger.debug("Status effect {} dealt {:.1f} damage to character {}".format(
                                    effect_id, effect_value, character_name))
                                
                                # Emit status_effect_damage event
                                self._emit_event("status_effect_damage", {
                                    "character": character,
                                    "effect_id": effect_id,
                                    "effect_name": effect_data.get("name", effect_id),
                                    "damage": effect_value,
                                    "old_hp": old_hp,
                                    "new_hp": new_hp,
                                    "match_context": match_context
                                })
                                
                                # Check if character is knocked out
                                if new_hp <= 0 and old_hp > 0:
                                    character["is_ko"] = True
                                    
                                    # Emit knockout event
                                    self._emit_event("status_effect_knockout", {
                                        "character": character,
                                        "effect_id": effect_id,
                                        "effect_name": effect_data.get("name", effect_id),
                                        "match_context": match_context
                                    })
                        
                        elif effect_type == "stamina_drain":
                            # Apply stamina drain
                            if "stamina" in character:
                                old_stamina = character["stamina"]
                                new_stamina = max(0, old_stamina - effect_value)
                                character["stamina"] = new_stamina
                                
                                # Log stamina drain
                                self.logger.debug("Status effect {} drained {:.1f} stamina from character {}".format(
                                    effect_id, effect_value, character_name))
                                
                                # Emit status_effect_stamina_drain event
                                self._emit_event("status_effect_stamina_drain", {
                                    "character": character,
                                    "effect_id": effect_id,
                                    "effect_name": effect_data.get("name", effect_id),
                                    "amount": effect_value,
                                    "old_stamina": old_stamina,
                                    "new_stamina": new_stamina,
                                    "match_context": match_context
                                })
                        
                        elif effect_type == "stat_modifier":
                            # Stat modifiers are already applied when the effect is added
                            pass
                    
                    # Emit status_effect_active event
                    self._emit_event("status_effect_active", {
                        "character": character,
                        "effect_id": effect_id,
                        "effect_name": effect_data.get("name", effect_id),
                        "remaining_duration": effect_data["duration"],
                        "match_context": match_context
                    })
            
            # Remove expired effects
            for effect_id in status_effects_to_remove:
                # Get effect data before removal
                effect_data = character["status_effects"][effect_id]
                
                # Check if effect has stat modifiers that need to be removed
                if "stat_modifiers" in effect_data:
                    for stat, modifier in effect_data["stat_modifiers"].items():
                        if stat in character:
                            # Restore original value if available
                            orig_key = f"original_{stat}"
                            if orig_key in character:
                                character[stat] = character[orig_key]
                                del character[orig_key]
                
                # Remove effect
                del character["status_effects"][effect_id]
            
            # Remove status_effects dictionary if empty
            if len(character["status_effects"]) == 0:
                del character["status_effects"]
            
            # Return status effect changes
            return {
                "processed_count": processed_count,
                "expired_count": expired_count,
                "recovered_count": recovered_count
            }
            
        except Exception as e:
            self.logger.error("Error processing status effects: {}".format(e))
            self._emit_error_event("process_status_effects", str(e), {
                "character_id": character.get("id", "unknown")
            })
            
            # Return minimal changes on error
            return {
                "processed_count": 0,
                "expired_count": 0,
                "recovered_count": 0
            }
    
    def _award_round_xp(self, character: Dict[str, Any], match_context: Dict[str, Any]) -> int:
        """
        Award XP for surviving a round
        
        Args:
            character: Character dictionary
            match_context: Match context dictionary
            
        Returns:
            Amount of XP awarded
        """
        try:
            xp_system = self._get_xp_system()
            if xp_system and hasattr(xp_system, "award_round_xp"):
                # If XP system has its own implementation, use that
                return xp_system.award_round_xp(character, match_context)
            
            # Otherwise, use our implementation
            character_id = character.get("id", "unknown")
            character_name = character.get("name", "Unknown")
            
            # Calculate base XP
            xp_amount = self._base_round_xp
            
            # Apply bonuses based on character state
            
            # XP for surviving at low HP
            if character.get("HP", 100) < 30:
                xp_amount += 1
            
            # XP for surviving at low stamina
            if character.get("stamina", 100) < self._low_stamina_threshold:
                xp_amount += 1
            
            # Apply character-specific modifiers
            if "xp_multiplier" in character:
                xp_amount *= character["xp_multiplier"]
            
            # Round XP amount
            xp_amount = round(xp_amount)
            
            # Update character XP
            if "XP" not in character:
                character["XP"] = 0
            character["XP"] += xp_amount
            
            # Update rStats
            if "rStats" in character:
                if "XP_EARNED" not in character["rStats"]:
                    character["rStats"]["XP_EARNED"] = 0
                character["rStats"]["XP_EARNED"] += xp_amount
            
            # Emit xp_awarded event
            self._emit_event("xp_awarded", {
                "character": character,
                "amount": xp_amount,
                "reason": "round_survival",
                "match_context": match_context
            })
            
            return xp_amount
            
        except Exception as e:
            self.logger.error("Error awarding round XP: {}".format(e))
            self._emit_error_event("award_round_xp", str(e), {
                "character_id": character.get("id", "unknown")
            })
            
            # Return 0 XP on error
            return 0
    
    def get_round_statistics(self) -> Dict[str, Any]:
        """Get round statistics"""
        return dict(self.round_statistics)
    
    def _emit_event(self, event_name: str, data: Dict[str, Any]) -> None:
        """Emit an event with the given name and data"""
        event_system = self._get_event_system()
        if event_system:
            try:
                event_system.emit(event_name, data)
            except Exception as e:
                self.logger.error("Error emitting event {}: {}".format(event_name, e))
    
    def _emit_error_event(self, function_name: str, error_message: str, 
                         context: Optional[Dict[str, Any]] = None) -> None:
        """Emit a system error event"""
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
    
    def save_persistent_data(self) -> None:
        """Save persistent data for the end-of-round effects system"""
        try:
            # Save round statistics
            data_dir = self.config.get("paths.data_dir", "data")
            stats_dir = os.path.join(data_dir, "statistics")
            os.makedirs(stats_dir, exist_ok=True)
            
            stats_file = os.path.join(stats_dir, "round_statistics.json")
            with open(stats_file, 'w') as f:
                json.dump({
                    "round_statistics": dict(self.round_statistics),
                    "timestamp": datetime.datetime.now().isoformat()
                }, f, indent=2)
                
            self.logger.info("Round statistics saved")
        except Exception as e:
            self.logger.error("Error saving persistent data: {}".format(e))
            self._emit_error_event("save_persistent_data", str(e))
    
    def export_state(self) -> Dict[str, Any]:
        """Export state for backup"""
        return {
            "round_statistics": dict(self.round_statistics),
            "active": self.active
        }
