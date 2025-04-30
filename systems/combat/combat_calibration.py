"""
Combat Calibration System for META Fantasy League Simulator
Handles damage calculations, combat modifiers, and combat-related statistics

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

class CombatCalibrationSystem(SystemBase):
    """
    Combat Calibration System for META Fantasy League
    
    Compliant with Guardian standards:
    - Event emissions via EventEmitter
    - External configuration
    - Structured logging
    - Error handling
    - System registration
    """
    
    def __init__(self, config, registry=None):
        """Initialize the combat calibration system"""
        super().__init__(config)
        self.name = "combat_calibration_system"
        self.logger = logging.getLogger("META_SIMULATOR.CombatCalibrationSystem")
        
        # Store registry if provided
        self._registry = registry
        
        # Cache for commonly used systems and configurations
        self._event_system = None
        self._trait_system = None
        
        # Load combat calibration settings
        self._load_calibration_settings()
        
        # Initialize state
        self.active = False
        self.damage_statistics = defaultdict(int)
        self.modifier_statistics = defaultdict(int)
        
        self.logger.info("Combat calibration system initialized with damage_multiplier={:.2f}".format(
            self._damage_multiplier))
    
    def _load_calibration_settings(self):
        """Load calibration settings from configuration"""
        try:
            # Default combat calibration settings if not in config
            combat_defaults = {
                "health_settings": {
                    "base_hp_multiplier": 1.0
                },
                "damage_settings": {
                    "base_damage_multiplier": 1.25,
                    "critical_hit_chance": 0.05,
                    "critical_hit_multiplier": 2.0
                },
                "stamina_settings": {
                    "stamina_decay_per_round_multiplier": 1.15,
                    "low_stamina_extra_damage_taken_percent": 20,
                    "low_stamina_threshold": 30
                },
                "morale_settings": {
                    "morale_loss_per_ko_multiplier": 1.10,
                    "morale_collapse_enabled": True,
                    "morale_collapse_threshold_percent": 30
                },
                "convergence_settings": {
                    "convergence_damage_multiplier": 2.0
                },
                "injury_settings": {
                    "injury_enabled": True,
                    "injury_trigger_stamina_threshold_percent": 35,
                    "injury_threshold": 20,
                    "severe_injury_threshold": 30
                }
            }
            
            # Get calibration settings from config or use defaults
            combat_settings = self.config.get("combat_calibration", combat_defaults)
            
            # Extract and store settings for quick access
            self._hp_multiplier = combat_settings["health_settings"]["base_hp_multiplier"]
            self._damage_multiplier = combat_settings["damage_settings"]["base_damage_multiplier"]
            self._critical_hit_chance = combat_settings["damage_settings"]["critical_hit_chance"]
            self._critical_hit_multiplier = combat_settings["damage_settings"]["critical_hit_multiplier"]
            
            # Stamina settings
            self._stamina_decay_multiplier = combat_settings["stamina_settings"]["stamina_decay_per_round_multiplier"]
            self._low_stamina_damage_percent = combat_settings["stamina_settings"]["low_stamina_extra_damage_taken_percent"]
            self._low_stamina_threshold = combat_settings["stamina_settings"]["low_stamina_threshold"]
            
            # Morale settings
            self._morale_loss_multiplier = combat_settings["morale_settings"]["morale_loss_per_ko_multiplier"]
            self._morale_collapse_enabled = combat_settings["morale_settings"]["morale_collapse_enabled"]
            self._morale_collapse_threshold = combat_settings["morale_settings"]["morale_collapse_threshold_percent"]
            
            # Convergence settings
            self._convergence_damage_multiplier = combat_settings["convergence_settings"]["convergence_damage_multiplier"]
            
            # Injury settings
            self._injury_enabled = combat_settings["injury_settings"]["injury_enabled"]
            self._injury_stamina_threshold = combat_settings["injury_settings"]["injury_trigger_stamina_threshold_percent"]
            self._injury_threshold = combat_settings["injury_settings"]["injury_threshold"]
            self._severe_injury_threshold = combat_settings["injury_settings"]["severe_injury_threshold"]
            
            # Emit configuration loaded event
            self._emit_event("combat_configuration_loaded", {
                "hp_multiplier": self._hp_multiplier,
                "damage_multiplier": self._damage_multiplier,
                "critical_hit_chance": self._critical_hit_chance,
                "critical_hit_multiplier": self._critical_hit_multiplier,
                "convergence_damage_multiplier": self._convergence_damage_multiplier,
                "injury_threshold": self._injury_threshold
            })
            
        except Exception as e:
            self.logger.error("Error loading combat calibration settings: {}".format(e))
            self._emit_error_event("load_calibration_settings", str(e))
            
            # Set default values as fallback
            self._hp_multiplier = 1.0
            self._damage_multiplier = 1.25
            self._critical_hit_chance = 0.05
            self._critical_hit_multiplier = 2.0
            self._stamina_decay_multiplier = 1.15
            self._low_stamina_damage_percent = 20
            self._low_stamina_threshold = 30
            self._morale_loss_multiplier = 1.10
            self._morale_collapse_enabled = True
            self._morale_collapse_threshold = 30
            self._convergence_damage_multiplier = 2.0
            self._injury_enabled = True
            self._injury_stamina_threshold = 35
            self._injury_threshold = 20
            self._severe_injury_threshold = 30
    
    def activate(self):
        """Activate the combat calibration system"""
        self.active = True
        self.logger.info("Combat calibration system activated")
        return True
    
    def deactivate(self):
        """Deactivate the combat calibration system"""
        self.active = False
        self.logger.info("Combat calibration system deactivated")
        return True
    
    def is_active(self):
        """Check if the combat calibration system is active"""
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
    
    def set_hp_multiplier(self, multiplier: float) -> None:
        """Set the HP multiplier"""
        try:
            if multiplier <= 0:
                self.logger.error("Invalid HP multiplier: {}, must be positive".format(multiplier))
                return
                
            old_value = self._hp_multiplier
            self._hp_multiplier = multiplier
            self.logger.info("HP multiplier set to {:.2f}".format(multiplier))
            
            # Emit configuration changed event
            self._emit_event("combat_configuration_changed", {
                "parameter": "hp_multiplier",
                "old_value": old_value,
                "new_value": multiplier
            })
        except Exception as e:
            self.logger.error("Error setting HP multiplier: {}".format(e))
            self._emit_error_event("set_hp_multiplier", str(e))
    
    def set_damage_multiplier(self, multiplier: float) -> None:
        """Set the damage multiplier"""
        try:
            if multiplier <= 0:
                self.logger.error("Invalid damage multiplier: {}, must be positive".format(multiplier))
                return
                
            old_value = self._damage_multiplier
            self._damage_multiplier = multiplier
            self.logger.info("Damage multiplier set to {:.2f}".format(multiplier))
            
            # Emit configuration changed event
            self._emit_event("combat_configuration_changed", {
                "parameter": "damage_multiplier",
                "old_value": old_value,
                "new_value": multiplier
            })
        except Exception as e:
            self.logger.error("Error setting damage multiplier: {}".format(e))
            self._emit_error_event("set_damage_multiplier", str(e))
    
    def apply_damage(self, attacker: Dict[str, Any], target: Dict[str, Any], 
                    amount: float, match_context: Dict[str, Any], 
                    method: str = "standard") -> float:
        """
        Apply damage from attacker to target
        
        Args:
            attacker: Attacker character dictionary
            target: Target character dictionary
            amount: Base damage amount
            match_context: Match context dictionary
            method: Damage method (standard, convergence, trait, etc.)
            
        Returns:
            Final damage amount applied
        """
        if not self.active:
            self.logger.warning("Combat calibration system not active, damage will not be applied")
            return 0.0
            
        try:
            attacker_id = attacker.get("id", "unknown")
            target_id = target.get("id", "unknown")
            board_id = match_context.get("board_id", "unknown")
            round_num = match_context.get("round", 0)
            
            self.logger.info("{} deals {:.1f} base damage to {} via {} on board {}".format(
                attacker.get("name", attacker_id),
                amount,
                target.get("name", target_id),
                method,
                board_id
            ))
            
            # Apply damage multiplier
            modified_amount = amount * self._damage_multiplier
            
            # Check for critical hit
            is_critical = False
            critical_reason = None
            
            if method == "standard" and random.random() < self._critical_hit_chance:
                is_critical = True
                critical_reason = "random"
                modified_amount *= self._critical_hit_multiplier
                self.logger.debug("Critical hit! Damage increased to {:.1f}".format(modified_amount))
            
            # Apply trait effects to damage
            trait_system = self._get_trait_system()
            if trait_system:
                trait_multiplier = trait_system.get_damage_multiplier(attacker, target, method)
                if trait_multiplier != 1.0:
                    self.logger.debug("Trait effect: damage multiplier {:.2f}".format(trait_multiplier))
                    
                    if trait_multiplier >= 2.0 and not is_critical:
                        is_critical = True
                        critical_reason = "trait"
                        
                    modified_amount *= trait_multiplier
            
            # Apply low stamina penalty
            if target.get("stamina", 100) < self._low_stamina_threshold:
                stamina_multiplier = 1.0 + (self._low_stamina_damage_percent / 100.0)
                self.logger.debug("Low stamina: damage increased by {:.0f}%".format(self._low_stamina_damage_percent))
                modified_amount *= stamina_multiplier
            
            # Apply convergence multiplier if method is convergence
            if method == "convergence":
                modified_amount *= self._convergence_damage_multiplier
                self.logger.debug("Convergence damage: multiplier {:.2f}".format(self._convergence_damage_multiplier))
            
            # Apply final damage
            final_amount = round(modified_amount, 1)
            
            # Update target HP
            old_hp = target.get("HP", 100)
            new_hp = max(0, old_hp - final_amount)
            target["HP"] = new_hp
            
            # Check if target is knocked out
            was_ko = target.get("is_ko", False)
            is_ko = new_hp <= 0
            
            if is_ko and not was_ko:
                target["is_ko"] = True
                self.logger.info("{} knocked out by {}".format(
                    target.get("name", target_id),
                    attacker.get("name", attacker_id)
                ))
                
                # Emit knockout event
                self._emit_event("knockout", {
                    "character": target,
                    "source": attacker,
                    "match_context": match_context,
                    "damage_amount": final_amount,
                    "damage_method": method
                })
            
            # Check for potential injury
            if self._injury_enabled and final_amount >= self._injury_threshold:
                severity = "severe" if final_amount >= self._severe_injury_threshold else "moderate"
                
                # Emit injury event
                self._emit_event("injury_taken", {
                    "character": target,
                    "source": attacker,
                    "match_context": match_context,
                    "severity": severity,
                    "damage_amount": final_amount,
                    "reason": "combat",
                    "method": method
                })
            
            # Update damage statistics
            self.damage_statistics["total_damage"] += final_amount
            self.damage_statistics["damage_instances"] += 1
            
            if method in self.damage_statistics:
                self.damage_statistics[method] += final_amount
            else:
                self.damage_statistics[method] = final_amount
                
            if is_critical:
                self.damage_statistics["critical_hits"] += 1
                self.damage_statistics["critical_damage"] += final_amount
            
            # Emit damage_dealt event
            self._emit_event("damage_dealt", {
                "attacker": attacker,
                "target": target,
                "base_amount": amount,
                "final_amount": final_amount,
                "method": method,
                "match_context": match_context,
                "hp_before": old_hp,
                "hp_after": new_hp,
                "is_critical": is_critical,
                "critical_reason": critical_reason,
                "is_ko": is_ko
            })
            
            return final_amount
            
        except Exception as e:
            self.logger.error("Error applying damage: {}".format(e))
            self._emit_error_event("apply_damage", str(e), {
                "attacker_id": attacker.get("id", "unknown"),
                "target_id": target.get("id", "unknown"),
                "amount": amount,
                "method": method
            })
            return 0.0
    
    def apply_combat_modifier(self, character: Dict[str, Any], modifier_type: str, 
                            value: float, match_context: Dict[str, Any], 
                            duration: int = 1, source: Optional[Dict[str, Any]] = None) -> bool:
        """
        Apply a combat modifier to a character
        
        Args:
            character: Character dictionary
            modifier_type: Type of modifier (aSTR, aSPD, etc.)
            value: Modifier value
            match_context: Match context dictionary
            duration: Duration in rounds
            source: Source character (optional)
            
        Returns:
            True if modifier was applied, False otherwise
        """
        if not self.active:
            self.logger.warning("Combat calibration system not active, modifier will not be applied")
            return False
            
        try:
            character_id = character.get("id", "unknown")
            source_id = source.get("id", "unknown") if source else None
            board_id = match_context.get("board_id", "unknown")
            round_num = match_context.get("round", 0)
            
            self.logger.info("{} receives modifier {}={:.1f} for {} rounds on board {}".format(
                character.get("name", character_id),
                modifier_type,
                value,
                duration,
                board_id
            ))
            
            # Store original value if not already stored
            if modifier_type in character:
                orig_key = f"original_{modifier_type}"
                if orig_key not in character:
                    character[orig_key] = character[modifier_type]
                
                # Apply modifier
                old_value = character[modifier_type]
                new_value = old_value + value
                character[modifier_type] = new_value
                
                # Store modifier duration
                character[f"{modifier_type}_modifier_duration"] = duration
                
                # Update modifier statistics
                self.modifier_statistics["total_modifiers"] += 1
                
                if modifier_type in self.modifier_statistics:
                    self.modifier_statistics[modifier_type] += 1
                else:
                    self.modifier_statistics[modifier_type] = 1
                
                # Emit modifier_applied event
                self._emit_event("combat_modifier_applied", {
                    "character": character,
                    "source": source,
                    "modifier_type": modifier_type,
                    "value": value,
                    "old_value": old_value,
                    "new_value": new_value,
                    "duration": duration,
                    "match_context": match_context
                })
                
                return True
            else:
                self.logger.warning("Could not apply modifier: {} not found in character".format(modifier_type))
                return False
                
        except Exception as e:
            self.logger.error("Error applying combat modifier: {}".format(e))
            self._emit_error_event("apply_combat_modifier", str(e), {
                "character_id": character.get("id", "unknown"),
                "modifier_type": modifier_type,
                "value": value
            })
            return False
    
    def update_character_metrics(self, character: Dict[str, Any], 
                              material_change: int, match_context: Dict[str, Any]) -> None:
        """
        Update character metrics based on material change
        
        Args:
            character: Character dictionary
            material_change: Change in material value
            match_context: Match context dictionary
        """
        if not self.active:
            return
            
        try:
            character_id = character.get("id", "unknown")
            
            # Initialize rStats if not present
            if "rStats" not in character:
                character["rStats"] = {}
            
            # Update material-related stats
            if material_change > 0:
                # Material advantage gained
                if "MATERIAL_ADVANTAGE_GAINED" not in character["rStats"]:
                    character["rStats"]["MATERIAL_ADVANTAGE_GAINED"] = 0
                character["rStats"]["MATERIAL_ADVANTAGE_GAINED"] += material_change
                
                # Emit material_advantage_gained event
                self._emit_event("material_advantage_gained", {
                    "character": character,
                    "amount": material_change,
                    "match_context": match_context
                })
            elif material_change < 0:
                # Material advantage lost
                if "MATERIAL_ADVANTAGE_LOST" not in character["rStats"]:
                    character["rStats"]["MATERIAL_ADVANTAGE_LOST"] = 0
                character["rStats"]["MATERIAL_ADVANTAGE_LOST"] += abs(material_change)
                
                # Emit material_advantage_lost event
                self._emit_event("material_advantage_lost", {
                    "character": character,
                    "amount": abs(material_change),
                    "match_context": match_context
                })
            
            # Update captures if positive material change
            if material_change > 0:
                if "CAPTURES_MADE" not in character["rStats"]:
                    character["rStats"]["CAPTURES_MADE"] = 0
                character["rStats"]["CAPTURES_MADE"] += 1
                
                # Emit capture_made event
                self._emit_event("capture_made", {
                    "character": character,
                    "material_value": material_change,
                    "match_context": match_context
                })
            
            # Update pieces lost if negative material change
            if material_change < 0:
                if "PIECES_LOST" not in character["rStats"]:
                    character["rStats"]["PIECES_LOST"] = 0
                character["rStats"]["PIECES_LOST"] += 1
                
                # Emit piece_lost event
                self._emit_event("piece_lost", {
                    "character": character,
                    "material_value": abs(material_change),
                    "match_context": match_context
                })
                
        except Exception as e:
            self.logger.error("Error updating character metrics: {}".format(e))
            self._emit_error_event("update_character_metrics", str(e), {
                "character_id": character.get("id", "unknown"),
                "material_change": material_change
            })
    
    def apply_end_of_round_effects(self, characters: List[Dict[str, Any]], 
                                 match_context: Dict[str, Any]) -> None:
        """
        Apply end of round effects to all characters
        
        Args:
            characters: List of character dictionaries
            match_context: Match context dictionary
        """
        if not self.active:
            return
            
        try:
            round_num = match_context.get("round", 0)
            self.logger.info("Applying end of round effects for round {}".format(round_num))
            
            # Emit round_end event
            self._emit_event("round_end", {
                "round": round_num,
                "character_count": len(characters),
                "match_context": match_context
            })
            
            for character in characters:
                try:
                    character_id = character.get("id", "unknown")
                    
                    # Skip knocked out characters
                    if character.get("is_ko", False):
                        continue
                    
                    # Update rounds survived stat
                    if "rStats" not in character:
                        character["rStats"] = {}
                    
                    if "ROUNDS_SURVIVED" not in character["rStats"]:
                        character["rStats"]["ROUNDS_SURVIVED"] = 0
                    character["rStats"]["ROUNDS_SURVIVED"] += 1
                    
                    # Process modifiers - decrement duration and remove if expired
                    modifiers_to_remove = []
                    
                    for key in character:
                        if key.endswith("_modifier_duration"):
                            stat_name = key[:-17]  # Remove "_modifier_duration"
                            duration = character[key]
                            
                            # Decrement duration
                            character[key] = duration - 1
                            
                            # If expired, add to removal list
                            if character[key] <= 0:
                                modifiers_to_remove.append((stat_name, key))
                    
                    # Remove expired modifiers
                    for stat_name, key in modifiers_to_remove:
                        # Restore original value if available
                        orig_key = f"original_{stat_name}"
                        if orig_key in character:
                            character[stat_name] = character[orig_key]
                            
                            # Emit modifier_expired event
                            self._emit_event("combat_modifier_expired", {
                                "character": character,
                                "modifier_type": stat_name,
                                "match_context": match_context
                            })
                        
                        # Remove duration tracker
                        del character[key]
                    
                    # Emit round_survived event
                    self._emit_event("round_survived", {
                        "character": character,
                        "round": round_num,
                        "match_context": match_context
                    })
                    
                except Exception as e:
                    self.logger.error("Error processing end of round effects for character {}: {}".format(
                        character.get("id", "unknown"), e
                    ))
            
        except Exception as e:
            self.logger.error("Error applying end of round effects: {}".format(e))
            self._emit_error_event("apply_end_of_round_effects", str(e), {
                "round": match_context.get("round", 0)
            })
    
    def get_damage_statistics(self) -> Dict[str, Any]:
        """Get damage statistics"""
        stats = dict(self.damage_statistics)
        
        # Add derived statistics
        if stats.get("damage_instances", 0) > 0:
            stats["average_damage"] = stats.get("total_damage", 0) / stats.get("damage_instances")
        else:
            stats["average_damage"] = 0
            
        if stats.get("critical_hits", 0) > 0:
            stats["average_critical_damage"] = stats.get("critical_damage", 0) / stats.get("critical_hits")
        else:
            stats["average_critical_damage"] = 0
            
        stats["critical_hit_rate"] = stats.get("critical_hits", 0) / max(1, stats.get("damage_instances", 1))
        
        return stats
    
    def get_modifier_statistics(self) -> Dict[str, Any]:
        """Get modifier statistics"""
        return dict(self.modifier_statistics)
    
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
        """Save persistent data for the combat calibration system"""
        try:
            # Save combat statistics
            data_dir = self.config.get("paths.data_dir", "data")
            stats_dir = os.path.join(data_dir, "statistics")
            os.makedirs(stats_dir, exist_ok=True)
            
            stats_file = os.path.join(stats_dir, "combat_statistics.json")
            with open(stats_file, 'w') as f:
                json.dump({
                    "damage_statistics": dict(self.damage_statistics),
                    "modifier_statistics": dict(self.modifier_statistics),
                    "timestamp": datetime.datetime.now().isoformat()
                }, f, indent=2)
                
            self.logger.info("Combat statistics saved")
        except Exception as e:
            self.logger.error("Error saving persistent data: {}".format(e))
            self._emit_error_event("save_persistent_data", str(e))
    
    def export_state(self) -> Dict[str, Any]:
        """Export state for backup"""
        return {
            "hp_multiplier": self._hp_multiplier,
            "damage_multiplier": self._damage_multiplier,
            "critical_hit_chance": self._critical_hit_chance,
            "critical_hit_multiplier": self._critical_hit_multiplier,
            "damage_statistics": dict(self.damage_statistics),
            "modifier_statistics": dict(self.modifier_statistics),
            "active": self.active
        }