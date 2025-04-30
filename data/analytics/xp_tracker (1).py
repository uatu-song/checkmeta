"""
XP Tracker System for META Fantasy League Simulator
Processes event logs to award and track experience points for characters

Version: 5.1.0 - Guardian Compliant
"""

import os
import json
import logging
import datetime
from typing import Dict, List, Any, Optional, Set, Tuple
from collections import defaultdict

from core.system_base import SystemBase

class XPTrackerSystem(SystemBase):
    """
    XP Tracker System for META Fantasy League
    
    Analyzes event logs (.jsonl files) to calculate and award experience points
    based on gameplay actions, motifs, and achievements.
    
    Compliant with Guardian standards:
    - Event emissions via EventEmitter
    - External configuration
    - Structured logging
    - Error handling
    - System registration
    """
    
    def __init__(self, config, registry=None):
        """Initialize the XP tracker system"""
        super().__init__(config)
        self.name = "xp_tracker_system"
        self.logger = logging.getLogger("META_SIMULATOR.XPTrackerSystem")
        
        # Store registry if provided
        self._registry = registry
        
        # Cache for commonly used systems
        self._event_system = None
        self._stat_tracker = None
        
        # Load XP configuration
        self._load_xp_configuration()
        
        # Initialize state
        self.active = False
        self.xp_awards = defaultdict(int)
        self.level_ups = defaultdict(int)
        self.xp_reasons = defaultdict(int)
        
        self.logger.info("XP tracker system initialized with {} XP rules".format(
            len(self._xp_rules)))
    
    def _load_xp_configuration(self):
        """Load XP configuration from config"""
        try:
            # Load XP settings
            xp_config = self.config.get("xp_settings", {})
            
            # XP level thresholds
            self._level_thresholds = xp_config.get("level_thresholds", [
                0,      # Level 1
                100,    # Level 2
                250,    # Level 3
                450,    # Level 4
                700,    # Level 5
                1000,   # Level 6
                1350,   # Level 7
                1750,   # Level 8
                2200,   # Level 9
                2700    # Level 10
            ])
            
            # XP rules for different actions
            self._xp_rules = xp_config.get("xp_rules", {})
            
            # If no rules in config, use default rules
            if not self._xp_rules:
                self._xp_rules = {
                    # Combat XP
                    "damage_dealt": {
                        "base_xp": 1,
                        "per_unit": 0.1,  # XP per point of damage
                        "max_per_instance": 5,
                        "category": "combat"
                    },
                    "knockout": {
                        "base_xp": 10,
                        "per_unit": 0,
                        "max_per_instance": 10,
                        "category": "combat"
                    },
                    
                    # Tactical XP
                    "motif_detected": {
                        "base_xp": 2,
                        "per_unit": 0.5,  # XP per motif score point
                        "max_per_instance": 15,
                        "category": "tactical"
                    },
                    "convergence_triggered": {
                        "base_xp": 5,
                        "per_unit": 0,
                        "max_per_instance": 5,
                        "category": "tactical"
                    },
                    
                    # Support XP
                    "assist_given": {
                        "base_xp": 7,
                        "per_unit": 0,
                        "max_per_instance": 7,
                        "category": "support"
                    },
                    "healing_applied": {
                        "base_xp": 3,
                        "per_unit": 0.2,  # XP per point of healing
                        "max_per_instance": 8,
                        "category": "support"
                    },
                    
                    # Survival XP
                    "round_survived": {
                        "base_xp": 1,
                        "per_unit": 0,
                        "max_per_instance": 1,
                        "category": "survival"
                    },
                    "match_won": {
                        "base_xp": 15,
                        "per_unit": 0,
                        "max_per_instance": 15,
                        "category": "survival"
                    },
                    
                    # Special achievements
                    "trait_activated": {
                        "base_xp": 3,
                        "per_unit": 0,
                        "max_per_instance": 3,
                        "category": "special"
                    }
                }
            
            # XP Multipliers
            self._xp_multipliers = xp_config.get("xp_multipliers", {})
            
            # Default multipliers if not specified
            if not self._xp_multipliers:
                self._xp_multipliers = {
                    "role": {
                        "tank": {
                            "combat": 1.2,
                            "tactical": 0.8,
                            "support": 0.9,
                            "survival": 1.3,
                            "special": 1.0
                        },
                        "damage": {
                            "combat": 1.3,
                            "tactical": 1.0,
                            "support": 0.7,
                            "survival": 0.9,
                            "special": 1.0
                        },
                        "support": {
                            "combat": 0.7,
                            "tactical": 1.0,
                            "support": 1.5,
                            "survival": 0.9,
                            "special": 1.2
                        },
                        "control": {
                            "combat": 0.9,
                            "tactical": 1.4,
                            "support": 1.0,
                            "survival": 0.8,
                            "special": 1.1
                        }
                    },
                    "level": {
                        "diminishing_returns": True,
                        "factor": 0.95  # 5% less XP per level above 1
                    }
                }
            
            # Event mapping settings
            self._event_to_xp_mapping = xp_config.get("event_mapping", {})
            
            # Default mappings if not specified
            if not self._event_to_xp_mapping:
                self._event_to_xp_mapping = {
                    "damage_dealt": ["damage_dealt"],
                    "knockout": ["knockout"],
                    "motif_detected": ["motif_detected"],
                    "convergence_triggered": ["convergence_triggered"],
                    "assist_given": ["assist_given"],
                    "healing_applied": ["healing_applied"],
                    "round_survived": ["round_survived"],
                    "match_complete": ["match_won"],
                    "trait_activated": ["trait_activated"]
                }
            
            # Maximum XP per day setting
            self._max_xp_per_day = xp_config.get("max_xp_per_day", 200)
            
            # Level-up bonus settings
            self._level_up_bonuses = xp_config.get("level_up_bonuses", {
                "hp_increase": 5,
                "stat_points": 2,
                "trait_slot_levels": [1, 3, 6, 9]  # Levels that grant extra trait slots
            })
            
            # Emit configuration loaded event
            self._emit_event("xp_configuration_loaded", {
                "rule_count": len(self._xp_rules),
                "level_count": len(self._level_thresholds),
                "max_xp_per_day": self._max_xp_per_day
            })
            
        except Exception as e:
            self.logger.error("Error loading XP configuration: {}".format(e))
            self._emit_error_event("load_xp_configuration", str(e))
            
            # Set minimal defaults
            self._level_thresholds = [0, 100, 250, 450, 700, 1000]
            self._xp_rules = {}
            self._xp_multipliers = {}
            self._event_to_xp_mapping = {}
            self._max_xp_per_day = 200
            self._level_up_bonuses = {}
    
    def activate(self):
        """Activate the XP tracker system"""
        self.active = True
        self.logger.info("XP tracker system activated")
        return True
    
    def deactivate(self):
        """Deactivate the XP tracker system"""
        self.active = False
        self.logger.info("XP tracker system deactivated")
        return True
    
    def is_active(self):
        """Check if the XP tracker system is active"""
        return self.active
    
    def _get_registry(self):
        """Get system registry (lazy loading)"""
        if not self._registry:
            from core.system_registry import SystemRegistry
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
    
    def _get_stat_tracker(self):
        """Get stat tracker from registry (lazy loading)"""
        if not self._stat_tracker:
            registry = self._get_registry()
            self._stat_tracker = registry.get("stat_tracker")
            if not self._stat_tracker:
                self.logger.warning("Stat tracker not available, stats will not be updated")
        return self._stat_tracker
    
    def process_event_log(self, log_file: str) -> Dict[str, Any]:
        """
        Process an event log file to award XP
        
        Args:
            log_file: Path to the event log file (.jsonl)
            
        Returns:
            Dictionary with processing results
        """
        if not self.active:
            self.logger.warning("XP tracker system not active, events will not be processed")
            return {"error": "System not active"}
        
        try:
            # Check if file exists
            if not os.path.isfile(log_file):
                error_msg = "Event log file not found: {}".format(log_file)
                self.logger.error(error_msg)
                return {"error": error_msg}
            
            # Initialize processing stats
            processing_stats = {
                "events_processed": 0,
                "xp_awards": defaultdict(int),
                "level_ups": defaultdict(int),
                "xp_by_category": defaultdict(int),
                "errors": []
            }
            
            self.logger.info("Processing event log: {}".format(log_file))
            
            # Read event log file line by line
            with open(log_file, 'r') as f:
                for line_number, line in enumerate(f, 1):
                    try:
                        # Parse JSON event
                        event = json.loads(line.strip())
                        processing_stats["events_processed"] += 1
                        
                        # Process event for XP
                        self._process_event(event, processing_stats)
                        
                    except json.JSONDecodeError as e:
                        error = "Invalid JSON at line {}: {}".format(line_number, e)
                        self.logger.warning(error)
                        processing_stats["errors"].append(error)
                    except Exception as e:
                        error = "Error processing event at line {}: {}".format(line_number, e)
                        self.logger.error(error)
                        processing_stats["errors"].append(error)
            
            # Convert defaultdicts to regular dicts for output
            processing_stats["xp_awards"] = dict(processing_stats["xp_awards"])
            processing_stats["level_ups"] = dict(processing_stats["level_ups"])
            processing_stats["xp_by_category"] = dict(processing_stats["xp_by_category"])
            
            # Emit processing complete event
            self._emit_event("xp_processing_complete", {
                "log_file": log_file,
                "events_processed": processing_stats["events_processed"],
                "xp_awards_count": len(processing_stats["xp_awards"]),
                "level_ups_count": sum(processing_stats["level_ups"].values()),
                "error_count": len(processing_stats["errors"])
            })
            
            self.logger.info("Processed {} events from log file {}".format(
                processing_stats["events_processed"], log_file))
            
            return processing_stats
            
        except Exception as e:
            self.logger.error("Error processing event log {}: {}".format(log_file, e))
            self._emit_error_event("process_event_log", str(e), {"log_file": log_file})
            return {"error": str(e)}
    
    def _process_event(self, event: Dict[str, Any], stats: Dict[str, Any]) -> None:
        """
        Process a single event for XP awards
        
        Args:
            event: Event dictionary
            stats: Processing statistics to update
        """
        try:
            # Get event name
            event_name = event.get("_event_name", event.get("event_name"))
            if not event_name:
                return
            
            # Check if event is mapped to XP rules
            xp_rule_names = self._event_to_xp_mapping.get(event_name, [])
            if not xp_rule_names:
                return
            
            # Get character from event
            character = event.get("character")
            if not character:
                return
            
            # Get character ID
            character_id = character.get("id")
            if not character_id:
                return
            
            # Process each XP rule for this event
            for rule_name in xp_rule_names:
                # Get XP rule
                xp_rule = self._xp_rules.get(rule_name)
                if not xp_rule:
                    continue
                
                # Calculate base XP
                xp_amount = xp_rule.get("base_xp", 0)
                
                # Calculate variable XP if applicable
                per_unit = xp_rule.get("per_unit", 0)
                if per_unit > 0:
                    # Determine the value to multiply by per_unit
                    if rule_name == "damage_dealt":
                        unit_value = event.get("final_amount", event.get("amount", 0))
                    elif rule_name == "healing_applied":
                        unit_value = event.get("amount", 0)
                    elif rule_name == "motif_detected":
                        unit_value = event.get("motif_score", 0)
                    else:
                        unit_value = 0
                    
                    # Add variable XP component
                    xp_amount += unit_value * per_unit
                
                # Apply max per instance cap
                max_per_instance = xp_rule.get("max_per_instance", float('inf'))
                xp_amount = min(xp_amount, max_per_instance)
                
                # Apply role-based multipliers
                category = xp_rule.get("category", "general")
                character_role = character.get("role", "").lower()
                
                if character_role in self._xp_multipliers.get("role", {}):
                    role_multipliers = self._xp_multipliers["role"][character_role]
                    if category in role_multipliers:
                        xp_amount *= role_multipliers[category]
                
                # Apply level-based diminishing returns if enabled
                character_level = self._get_level_from_xp(character.get("XP", 0))
                if (character_level > 1 and 
                    self._xp_multipliers.get("level", {}).get("diminishing_returns", False)):
                    
                    level_factor = self._xp_multipliers["level"]["factor"]
                    level_multiplier = level_factor ** (character_level - 1)
                    xp_amount *= level_multiplier
                
                # Round XP amount
                xp_amount = round(xp_amount)
                
                # Update statistics
                if xp_amount > 0:
                    stats["xp_awards"][character_id] += xp_amount
                    stats["xp_by_category"][category] += xp_amount
                    
                    # Update internal tracking
                    self.xp_awards[character_id] += xp_amount
                    self.xp_reasons[rule_name] += xp_amount
            
        except Exception as e:
            self.logger.error("Error processing event for XP: {}".format(e))
            if "errors" in stats:
                stats["errors"].append(str(e))
    
    def apply_xp_to_characters(self, characters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Apply accumulated XP to characters
        
        Args:
            characters: List of character dictionaries
            
        Returns:
            Dictionary with XP application results
        """
        if not self.active:
            self.logger.warning("XP tracker system not active, XP will not be applied")
            return {"error": "System not active"}
        
        try:
            results = {
                "xp_applied": {},
                "level_ups": {},
                "trait_slots_gained": {},
                "errors": []
            }
            
            character_dict = {char.get("id"): char for char in characters}
            
            # Apply XP to each character
            for character_id, xp_amount in self.xp_awards.items():
                if xp_amount <= 0:
                    continue
                
                # Get character
                character = character_dict.get(character_id)
                if not character:
                    error = "Character not found: {}".format(character_id)
                    self.logger.warning(error)
                    results["errors"].append(error)
                    continue
                
                try:
                    # Get current XP and level
                    current_xp = character.get("XP", 0)
                    current_level = self._get_level_from_xp(current_xp)
                    
                    # Check daily XP cap
                    daily_xp = character.get("daily_XP", 0)
                    remaining_daily_xp = max(0, self._max_xp_per_day - daily_xp)
                    
                    # Cap XP award if needed
                    if xp_amount > remaining_daily_xp:
                        xp_amount = remaining_daily_xp
                        
                        # Log if XP capped
                        if xp_amount == 0:
                            self.logger.info("Character {} reached daily XP cap".format(
                                character.get("name", character_id)))
                    
                    # Apply XP
                    new_xp = current_xp + xp_amount
                    character["XP"] = new_xp
                    
                    # Update daily XP
                    character["daily_XP"] = daily_xp + xp_amount
                    
                    # Track XP applied
                    results["xp_applied"][character_id] = xp_amount
                    
                    # Check for level ups
                    new_level = self._get_level_from_xp(new_xp)
                    levels_gained = new_level - current_level
                    
                    if levels_gained > 0:
                        # Update character level
                        character["level"] = new_level
                        
                        # Track level ups
                        results["level_ups"][character_id] = levels_gained
                        self.level_ups[character_id] += levels_gained
                        
                        # Apply level up bonuses
                        trait_slots_gained = self._apply_level_up_bonuses(character, current_level, new_level)
                        if trait_slots_gained > 0:
                            results["trait_slots_gained"][character_id] = trait_slots_gained
                        
                        # Emit level up event
                        self._emit_event("character_level_up", {
                            "character": character,
                            "old_level": current_level,
                            "new_level": new_level,
                            "levels_gained": levels_gained,
                            "trait_slots_gained": trait_slots_gained
                        })
                        
                        self.logger.info("Character {} leveled up from {} to {}".format(
                            character.get("name", character_id), current_level, new_level))
                    
                    # Update rStats if available
                    if "rStats" in character:
                        if "XP_EARNED" not in character["rStats"]:
                            character["rStats"]["XP_EARNED"] = 0
                        character["rStats"]["XP_EARNED"] += xp_amount
                        
                        if levels_gained > 0:
                            if "LEVEL_UPS" not in character["rStats"]:
                                character["rStats"]["LEVEL_UPS"] = 0
                            character["rStats"]["LEVEL_UPS"] += levels_gained
                
                except Exception as e:
                    error = "Error applying XP to character {}: {}".format(character_id, e)
                    self.logger.error(error)
                    results["errors"].append(error)
            
            # Emit XP application complete event
            self._emit_event("xp_application_complete", {
                "characters_updated": len(results["xp_applied"]),
                "total_xp_applied": sum(results["xp_applied"].values()),
                "level_ups": sum(results["level_ups"].values()),
                "trait_slots_gained": sum(results["trait_slots_gained"].values())
            })
            
            self.logger.info("Applied XP to {} characters, {} level ups".format(
                len(results["xp_applied"]), sum(results["level_ups"].values())))
            
            # Reset XP awards after application
            self.xp_awards = defaultdict(int)
            
            return results
            
        except Exception as e:
            self.logger.error("Error applying XP to characters: {}".format(e))
            self._emit_error_event("apply_xp_to_characters", str(e))
            return {"error": str(e)}
    
    def _get_level_from_xp(self, xp: int) -> int:
        """
        Calculate level from XP
        
        Args:
            xp: Current XP amount
            
        Returns:
            Character level
        """
        # Find the highest level threshold that the XP exceeds
        level = 1
        for i, threshold in enumerate(self._level_thresholds):
            if xp >= threshold:
                level = i + 1
            else:
                break
        
        return level
    
    def _apply_level_up_bonuses(self, character: Dict[str, Any], old_level: int, new_level: int) -> int:
        """
        Apply bonuses for leveling up
        
        Args:
            character: Character dictionary
            old_level: Previous level
            new_level: New level
            
        Returns:
            Number of trait slots gained
        """
        # Apply HP increase
        hp_increase = self._level_up_bonuses.get("hp_increase", 0) * (new_level - old_level)
        if "max_HP" in character:
            character["max_HP"] += hp_increase
        else:
            character["max_HP"] = 100 + hp_increase
        
        # Apply stat points
        stat_points = self._level_up_bonuses.get("stat_points", 0) * (new_level - old_level)
        if "stat_points" in character:
            character["stat_points"] += stat_points
        else:
            character["stat_points"] = stat_points
        
        # Apply trait slots
        trait_slot_levels = self._level_up_bonuses.get("trait_slot_levels", [])
        trait_slots_gained = 0
        
        for level in range(old_level + 1, new_level + 1):
            if level in trait_slot_levels:
                trait_slots_gained += 1
        
        if trait_slots_gained > 0:
            if "trait_slots" in character:
                character["trait_slots"] += trait_slots_gained
            else:
                character["trait_slots"] = 3 + trait_slots_gained  # Assuming base of 3 slots
        
        return trait_slots_gained
    
    def process_character_daily_reset(self, characters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Reset daily XP tracking for characters
        
        Args:
            characters: List of character dictionaries
            
        Returns:
            Dictionary with reset results
        """
        if not self.active:
            self.logger.warning("XP tracker system not active, daily reset will not be performed")
            return {"error": "System not active"}
        
        try:
            reset_count = 0
            
            for character in characters:
                if "daily_XP" in character:
                    character["daily_XP"] = 0
                    reset_count += 1
            
            self.logger.info("Reset daily XP for {} characters".format(reset_count))
            
            # Emit daily reset event
            self._emit_event("daily_xp_reset", {
                "character_count": reset_count,
                "timestamp": datetime.datetime.now().isoformat()
            })
            
            return {
                "reset_count": reset_count
            }
            
        except Exception as e:
            self.logger.error("Error resetting daily XP: {}".format(e))
            self._emit_error_event("process_character_daily_reset", str(e))
            return {"error": str(e)}
    
    def get_xp_statistics(self) -> Dict[str, Any]:
        """Get XP tracking statistics"""
        total_xp = sum(self.xp_awards.values())
        total_levels = sum(self.level_ups.values())
        
        stats = {
            "total_xp_awarded": total_xp,
            "total_level_ups": total_levels,
            "xp_by_character": dict(self.xp_awards),
            "level_ups_by_character": dict(self.level_ups),
            "xp_by_reason": dict(self.xp_reasons)
        }
        
        return stats
    
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
        """Save persistent data for XP tracker system"""
        try:
            # Save XP statistics
            data_dir = self.config.get("paths.data_dir", "data")
            stats_dir = os.path.join(data_dir, "statistics")
            os.makedirs(stats_dir, exist_ok=True)
            
            stats_file = os.path.join(stats_dir, "xp_statistics.json")
            with open(stats_file, 'w') as f:
                json.dump({
                    "xp_statistics": self.get_xp_statistics(),
                    "timestamp": datetime.datetime.now().isoformat()
                }, f, indent=2)
                
            self.logger.info("XP statistics saved")
        except Exception as e:
            self.logger.error("Error saving persistent data: {}".format(e))
            self._emit_error_event("save_persistent_data", str(e))
    
    def export_state(self) -> Dict[str, Any]:
        """Export state for backup"""
        return {
            "xp_awards": dict(self.xp_awards),
            "level_ups": dict(self.level_ups),
            "xp_reasons": dict(self.xp_reasons),
            "active": self.active
        }
