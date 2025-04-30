"""
Trait Reactor System for META Fantasy League Simulator
Listens for game events and triggers appropriate trait activations

Version: 5.1.0 - Guardian Compliant
"""

import os
import json
import logging
import datetime
import random
from typing import Dict, List, Any, Optional, Set, Tuple
from collections import defaultdict

from core.system_base import SystemBase

class TraitReactorSystem(SystemBase):
    """
    Trait Reactor System for META Fantasy League
    
    Monitors game events and activates character traits when trigger conditions are met.
    Manages cooldowns, stamina costs, and trait side effects.
    
    Compliant with Guardian standards:
    - Event emissions via EventEmitter
    - External configuration
    - Structured logging
    - Error handling
    - System registration
    """
    
    def __init__(self, config, registry=None):
        """Initialize the trait reactor system"""
        super().__init__(config)
        self.name = "trait_reactor_system"
        self.logger = logging.getLogger("META_SIMULATOR.TraitReactorSystem")
        
        # Store registry if provided
        self._registry = registry
        
        # Cache for commonly used systems
        self._event_system = None
        self._trait_catalog = None
        
        # Load trait configuration
        self._load_trait_configuration()
        
        # Register event handlers
        self._setup_event_handlers()
        
        # Initialize state
        self.active = False
        self.trait_activations = defaultdict(int)
        self.trait_cooldowns = defaultdict(dict)
        
        self.logger.info("Trait reactor system initialized with {} trait triggers".format(
            len(self._trait_triggers)))
    
    def _load_trait_configuration(self):
        """Load trait configuration"""
        try:
            # Load trait settings
            trait_config = self.config.get("trait_settings", {})
            
            # Load trait triggers
            self._trait_triggers = trait_config.get("triggers", {})
            
            # If no triggers specified, use default mapping
            if not self._trait_triggers:
                self._trait_triggers = {
                    "pre-move": ["pre_move"],
                    "post-move": ["post_move"],
                    "damage_taken": ["damage_taken"],
                    "hp_below_30": ["hp_updated"],
                    "hp_below_40": ["hp_updated"],
                    "hp_below_50": ["hp_updated"],
                    "ally_hp_below_40": ["hp_updated"],
                    "ally_in_danger": ["hp_updated", "damage_dealt"],
                    "convergence": ["convergence_triggered"],
                    "stamina_regen": ["round_end"],
                    "ally_ko": ["knockout"],
                    "attack": ["damage_dealt"],
                    "round_start": ["round_start"],
                    "when_hit": ["damage_taken"],
                    "morale_low": ["morale_updated"],
                    "stamina_below_30": ["stamina_updated"],
                    "consecutive_hits": ["damage_dealt"],
                    "ko_resist": ["knockout"],
                    "ally_defeated": ["knockout"],
                    "match_point": ["match_point"],
                    "high_threat": ["threat_updated", "damage_dealt"],
                    "adjacent_ally": ["board_position_updated"],
                    "piece_sacrifice": ["piece_captured"],
                    "board_position": ["board_position_updated"],
                    "stamina_full": ["stamina_updated"],
                    "morale_defense": ["morale_updated"],
                    "move_pattern": ["move_made"],
                    "match_start": ["match_start"],
                    "last_survivor": ["knockout"],
                    "board_evaluation": ["pre_move"]
                }
            
            # Special trigger conditions that need additional logic
            self._special_triggers = trait_config.get("special_triggers", {})
            
            # Default special trigger conditions
            if not self._special_triggers:
                self._special_triggers = {
                    "hp_below_30": {"threshold": 30, "stat": "HP", "compare": "less_than"},
                    "hp_below_40": {"threshold": 40, "stat": "HP", "compare": "less_than"},
                    "hp_below_50": {"threshold": 50, "stat": "HP", "compare": "less_than"},
                    "ally_hp_below_40": {"threshold": 40, "stat": "HP", "compare": "less_than", "target": "ally"},
                    "stamina_below_30": {"threshold": 30, "stat": "stamina", "compare": "less_than"},
                    "stamina_full": {"threshold": 95, "stat": "stamina", "compare": "greater_than"},
                    "morale_low": {"threshold": 40, "stat": "morale", "compare": "less_than"}
                }
            
            # Load cooldown modifiers
            self._cooldown_modifiers = trait_config.get("cooldown_modifiers", {})
            
            # Default cooldown modifiers
            if not self._cooldown_modifiers:
                self._cooldown_modifiers = {
                    "level_scaling": 0.9,  # 10% reduction per level
                    "willpower_factor": 0.02,  # 2% reduction per willpower point
                    "minimum_cooldown": 1
                }
            
            # Load stamina cost modifiers
            self._stamina_cost_modifiers = trait_config.get("stamina_cost_modifiers", {})
            
            # Default stamina cost modifiers
            if not self._stamina_cost_modifiers:
                self._stamina_cost_modifiers = {
                    "endurance_factor": 0.03,  # 3% reduction per endurance point
                    "minimum_cost": 0
                }
            
            # Emit configuration loaded event
            self._emit_event("trait_configuration_loaded", {
                "trigger_count": len(self._trait_triggers),
                "special_trigger_count": len(self._special_triggers)
            })
            
        except Exception as e:
            self.logger.error("Error loading trait configuration: {}".format(e))
            self._emit_error_event("load_trait_configuration", str(e))
            
            # Set minimal defaults
            self._trait_triggers = {}
            self._special_triggers = {}
            self._cooldown_modifiers = {}
            self._stamina_cost_modifiers = {}
    
    def _setup_event_handlers(self):
        """Set up event handlers for trait triggers"""
        # Map of event types to handler methods
        self._event_handlers = {
            "pre_move": self._handle_pre_move_event,
            "post_move": self._handle_post_move_event,
            "damage_dealt": self._handle_damage_event,
            "damage_taken": self._handle_damage_taken_event,
            "hp_updated": self._handle_hp_update_event,
            "round_start": self._handle_round_start_event,
            "round_end": self._handle_round_end_event,
            "knockout": self._handle_knockout_event,
            "convergence_triggered": self._handle_convergence_event,
            "stamina_updated": self._handle_stamina_update_event,
            "morale_updated": self._handle_morale_update_event,
            "match_start": self._handle_match_start_event,
            "match_point": self._handle_match_point_event,
            "board_position_updated": self._handle_board_position_event,
            "piece_captured": self._handle_piece_captured_event,
            "move_made": self._handle_move_made_event
        }
    
    def activate(self):
        """Activate the trait reactor system"""
        self.active = True
        
        # Register for events
        event_system = self._get_event_system()
        if event_system:
            # Register handlers for each event type
            for event_type in set(self._event_handlers.keys()):
                handler = self._event_handlers.get(event_type)
                if handler:
                    event_system.register_handler(event_type, handler)
        
        self.logger.info("Trait reactor system activated and event handlers registered")
        return True
    
    def deactivate(self):
        """Deactivate the trait reactor system"""
        self.active = False
        
        # Unregister from events
        event_system = self._get_event_system()
        if event_system:
            # Unregister handlers for each event type
            for event_type in set(self._event_handlers.keys()):
                handler = self._event_handlers.get(event_type)
                if handler:
                    event_system.unregister_handler(event_type, handler)
        
        self.logger.info("Trait reactor system deactivated and event handlers unregistered")
        return True
    
    def is_active(self):
        """Check if the trait reactor system is active"""
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
                self.logger.warning("Event system not available, events will not be emitted or received")
        return self._event_system
    
    def _get_trait_catalog(self):
        """Get trait catalog (lazy loading)"""
        if not self._trait_catalog:
            try:
                # Try to load from registry first
                registry = self._get_registry()
                trait_system = registry.get("trait_system")
                if trait_system and hasattr(trait_system, "get_trait_catalog"):
                    self._trait_catalog = trait_system.get_trait_catalog()
                
                # If not available from registry, load from file
                if not self._trait_catalog:
                    trait_file = self.config.get("paths.trait_catalog", "data/traits/trait_catalog.json")
                    if os.path.isfile(trait_file):
                        with open(trait_file, 'r') as f:
                            self._trait_catalog = json.load(f)
                    else:
                        self.logger.warning("Trait catalog file not found: {}".format(trait_file))
                        self._trait_catalog = {}
                        
            except Exception as e:
                self.logger.error("Error loading trait catalog: {}".format(e))
                self._trait_catalog = {}
        
        return self._trait_catalog
    
    def _handle_pre_move_event(self, event_data: Dict[str, Any]) -> None:
        """Handle pre-move events"""
        if not self.active:
            return
            
        try:
            character = event_data.get("character")
            if not character:
                return
                
            # Check for pre-move traits
            character_traits = character.get("traits", {})
            for trait_id, trait_data in character_traits.items():
                try:
                    # Get trait catalog data
                    trait_catalog = self._get_trait_catalog()
                    trait_info = trait_catalog.get(trait_id, {})
                    
                    # Check if trait triggers on pre-move
                    if trait_info.get("triggers") == "pre-move":
                        # Check if trait is on cooldown
                        if self._is_trait_on_cooldown(character, trait_id):
                            continue
                            
                        # Check if character has enough stamina
                        if not self._has_enough_stamina(character, trait_info):
                            continue
                            
                        # Activate the trait
                        self._activate_trait(character, trait_id, trait_info, event_data)
                except Exception as e:
                    self.logger.error("Error processing pre-move trait {}: {}".format(trait_id, e))
                    
        except Exception as e:
            self.logger.error("Error handling pre-move event: {}".format(e))
            self._emit_error_event("handle_pre_move_event", str(e))
    
    def _handle_post_move_event(self, event_data: Dict[str, Any]) -> None:
        """Handle post-move events"""
        if not self.active:
            return
            
        try:
            character = event_data.get("character")
            if not character:
                return
                
            # Check for post-move traits
            character_traits = character.get("traits", {})
            for trait_id, trait_data in character_traits.items():
                try:
                    # Get trait catalog data
                    trait_catalog = self._get_trait_catalog()
                    trait_info = trait_catalog.get(trait_id, {})
                    
                    # Check if trait triggers on post-move
                    if trait_info.get("triggers") == "post-move":
                        # Check if trait is on cooldown
                        if self._is_trait_on_cooldown(character, trait_id):
                            continue
                            
                        # Check if character has enough stamina
                        if not self._has_enough_stamina(character, trait_info):
                            continue
                            
                        # Activate the trait
                        self._activate_trait(character, trait_id, trait_info, event_data)
                except Exception as e:
                    self.logger.error("Error processing post-move trait {}: {}".format(trait_id, e))
                    
        except Exception as e:
            self.logger.error("Error handling post-move event: {}".format(e))
            self._emit_error_event("handle_post_move_event", str(e))
    
    def _handle_damage_event(self, event_data: Dict[str, Any]) -> None:
        """Handle damage dealt events"""
        if not self.active:
            return
            
        try:
            attacker = event_data.get("attacker")
            if not attacker:
                return
                
            # Check for attack traits
            attacker_traits = attacker.get("traits", {})
            for trait_id, trait_data in attacker_traits.items():
                try:
                    # Get trait catalog data
                    trait_catalog = self._get_trait_catalog()
                    trait_info = trait_catalog.get(trait_id, {})
                    
                    # Check if trait triggers on attack
                    if trait_info.get("triggers") == "attack":
                        # Check if trait is on cooldown
                        if self._is_trait_on_cooldown(attacker, trait_id):
                            continue
                            
                        # Check if character has enough stamina
                        if not self._has_enough_stamina(attacker, trait_info):
                            continue
                            
                        # Activate the trait
                        self._activate_trait(attacker, trait_id, trait_info, event_data)
                except Exception as e:
                    self.logger.error("Error processing attack trait {}: {}".format(trait_id, e))
                    
            # Check for consecutive hits traits
            for trait_id, trait_data in attacker_traits.items():
                try:
                    # Get trait catalog data
                    trait_catalog = self._get_trait_catalog()
                    trait_info = trait_catalog.get(trait_id, {})
                    
                    # Check if trait triggers on consecutive hits
                    if trait_info.get("triggers") == "consecutive_hits":
                        # This trait doesn't use cooldown, just increment the hit counter
                        hit_counter_key = f"{trait_id}_hit_counter"
                        if hit_counter_key not in attacker:
                            attacker[hit_counter_key] = 0
                        
                        # Increment hit counter
                        attacker[hit_counter_key] += 1
                        
                        # Apply effect based on hit counter
                        self._apply_consecutive_hit_effect(attacker, trait_id, trait_info, event_data)
                except Exception as e:
                    self.logger.error("Error processing consecutive hits trait {}: {}".format(trait_id, e))
                    
        except Exception as e:
            self.logger.error("Error handling damage event: {}".format(e))
            self._emit_error_event("handle_damage_event", str(e))
    
    def _handle_damage_taken_event(self, event_data: Dict[str, Any]) -> None:
        """Handle damage taken events"""
        if not self.active:
            return
            
        try:
            target = event_data.get("target")
            if not target:
                return
                
            # Check for damage_taken traits
            target_traits = target.get("traits", {})
            for trait_id, trait_data in target_traits.items():
                try:
                    # Get trait catalog data
                    trait_catalog = self._get_trait_catalog()
                    trait_info = trait_catalog.get(trait_id, {})
                    
                    # Check if trait triggers on damage taken
                    if trait_info.get("triggers") == "damage_taken":
                        # Check if trait is on cooldown
                        if self._is_trait_on_cooldown(target, trait_id):
                            continue
                            
                        # Check if character has enough stamina
                        if not self._has_enough_stamina(target, trait_info):
                            continue
                            
                        # Activate the trait
                        self._activate_trait(target, trait_id, trait_info, event_data)
                except Exception as e:
                    self.logger.error("Error processing damage_taken trait {}: {}".format(trait_id, e))
                    
            # Check for when_hit traits
            for trait_id, trait_data in target_traits.items():
                try:
                    # Get trait catalog data
                    trait_catalog = self._get_trait_catalog()
                    trait_info = trait_catalog.get(trait_id, {})
                    
                    # Check if trait triggers when hit
                    if trait_info.get("triggers") == "when_hit":
                        # Check if trait is on cooldown
                        if self._is_trait_on_cooldown(target, trait_id):
                            continue
                            
                        # Activate the trait (passive traits usually don't have stamina cost)
                        self._activate_trait(target, trait_id, trait_info, event_data)
                except Exception as e:
                    self.logger.error("Error processing when_hit trait {}: {}".format(trait_id, e))
                    
        except Exception as e:
            self.logger.error("Error handling damage taken event: {}".format(e))
            self._emit_error_event("handle_damage_taken_event", str(e))
    
    def _handle_hp_update_event(self, event_data: Dict[str, Any]) -> None:
        """Handle HP update events"""
        if not self.active:
            return
            
        try:
            character = event_data.get("character")
            if not character:
                return
                
            # Get character HP
            hp = character.get("HP", 100)
            
            # Check for HP threshold traits
            character_traits = character.get("traits", {})
            for trait_id, trait_data in character_traits.items():
                try:
                    # Get trait catalog data
                    trait_catalog = self._get_trait_catalog()
                    trait_info = trait_catalog.get(trait_id, {})
                    
                    # Check specific HP threshold triggers
                    triggers = trait_info.get("triggers")
                    
                    if triggers == "hp_below_30" and hp < 30:
                        # Check if trait is on cooldown
                        if self._is_trait_on_cooldown(character, trait_id):
                            continue
                            
                        # Check if character has enough stamina
                        if not self._has_enough_stamina(character, trait_info):
                            continue
                            
                        # Activate the trait
                        self._activate_trait(character, trait_id, trait_info, event_data)
                        
                    elif triggers == "hp_below_40" and hp < 40:
                        # Check if trait is on cooldown
                        if self._is_trait_on_cooldown(character, trait_id):
                            continue
                            
                        # Check if character has enough stamina
                        if not self._has_enough_stamina(character, trait_info):
                            continue
                            
                        # Activate the trait
                        self._activate_trait(character, trait_id, trait_info, event_data)
                        
                    elif triggers == "hp_below_50" and hp < 50:
                        # Check if trait is on cooldown
                        if self._is_trait_on_cooldown(character, trait_id):
                            continue
                            
                        # Check if character has enough stamina
                        if not self._has_enough_stamina(character, trait_info):
                            continue
                            
                        # Activate the trait
                        self._activate_trait(character, trait_id, trait_info, event_data)
                        
                except Exception as e:
                    self.logger.error("Error processing HP threshold trait {}: {}".format(trait_id, e))
                    
            # Check for ally_hp_below_40 traits (needs team info)
            match_context = event_data.get("match_context", {})
            team_data = match_context.get("team_data", {})
            
            if team_data:
                # Get character's team
                character_id = character.get("id")
                character_team = None
                
                for team_id, team_chars in team_data.items():
                    if character_id in team_chars:
                        character_team = team_id
                        break
                
                if character_team and hp < 40:
                    # Alert teammates with ally_hp_below traits
                    for team_char_id in team_data.get(character_team, []):
                        if team_char_id == character_id:
                            continue  # Skip self
                            
                        # Find the teammate character
                        teammate = None
                        for char in match_context.get("characters", []):
                            if char.get("id") == team_char_id:
                                teammate = char
                                break
                        
                        if not teammate:
                            continue
                            
                        # Check for ally_hp_below_40 traits
                        teammate_traits = teammate.get("traits", {})
                        for trait_id, trait_data in teammate_traits.items():
                            try:
                                # Get trait catalog data
                                trait_catalog = self._get_trait_catalog()
                                trait_info = trait_catalog.get(trait_id, {})
                                
                                # Check if trait triggers on ally_hp_below_40
                                if trait_info.get("triggers") == "ally_hp_below_40":
                                    # Check if trait is on cooldown
                                    if self._is_trait_on_cooldown(teammate, trait_id):
                                        continue
                                        
                                    # Check if character has enough stamina
                                    if not self._has_enough_stamina(teammate, trait_info):
                                        continue
                                        
                                    # Create modified event data with target information
                                    ally_event_data = event_data.copy()
                                    ally_event_data["target"] = character
                                    
                                    # Activate the trait
                                    self._activate_trait(teammate, trait_id, trait_info, ally_event_data)
                            except Exception as e:
                                self.logger.error("Error processing ally_hp_below trait {}: {}".format(trait_id, e))
                
        except Exception as e:
            self.logger.error("Error handling HP update event: {}".format(e))
            self._emit_error_event("handle_hp_update_event", str(e))
    
    def _handle_round_start_event(self, event_data: Dict[str, Any]) -> None:
        """Handle round start events"""
        if not self.active:
            return
            
        try:
            # Get all characters from match context
            match_context = event_data.get("match_context", {})
            characters = match_context.get("characters", [])
            
            # Process each character for round_start traits
            for character in characters:
                # Skip knocked out characters
                if character.get("is_ko", False):
                    continue
                    
                # Check for round_start traits
                character_traits = character.get("traits", {})
                for trait_id, trait_data in character_traits.items():
                    try:
                        # Get trait catalog data
                        trait_catalog = self._get_trait_catalog()
                        trait_info = trait_catalog.get(trait_id, {})
                        
                        # Check if trait triggers on round_start
                        if trait_info.get("triggers") == "round_start":
                            # Check if trait is on cooldown
                            if self._is_trait_on_cooldown(character, trait_id):
                                continue
                                
                            # Check if character has enough stamina
                            if not self._has_enough_stamina(character, trait_info):
                                continue
                                
                            # Create character-specific event data
                            char_event_data = event_data.copy()
                            char_event_data["character"] = character
                            
                            # Activate the trait
                            self._activate_trait(character, trait_id, trait_info, char_event_data)
                    except Exception as e:
                        self.logger.error("Error processing round_start trait {}: {}".format(trait_id, e))
                    
        except Exception as e:
            self.logger.error("Error handling round start event: {}".format(e))
            self._emit_error_event("handle_round_start_event", str(e))
    
    def _handle_round_end_event(self, event_data: Dict[str, Any]) -> None:
        """Handle round end events"""
        if not self.active:
            return
            
        try:
            # Get all characters from match context
            match_context = event_data.get("match_context", {})
            characters = match_context.get("characters", [])
            
            # Process each character for stamina_regen traits
            for character in characters:
                # Skip knocked out characters
                if character.get("is_ko", False):
                    continue
                    
                # Check for stamina_regen traits (these are usually passive)
                character_traits = character.get("traits", {})
                for trait_id, trait_data in character_traits.items():
                    try:
                        # Get trait catalog data
                        trait_catalog = self._get_trait_catalog()
                        trait_info = trait_catalog.get(trait_id, {})
                        
                        # Check if trait triggers on stamina_regen
                        if trait_info.get("triggers") == "stamina_regen":
                            # Create character-specific event data
                            char_event_data = event_data.copy()
                            char_event_data["character"] = character
                            
                            # Apply stamina regeneration
                            self._apply_stamina_regen(character, trait_id, trait_info, char_event_data)
                    except Exception as e:
                        self.logger.error("Error processing stamina_regen trait {}: {}".format(trait_id, e))
                    
                # Reset consecutve hit counters at end of round
                for trait_id in character_traits:
                    hit_counter_key = f"{trait_id}_hit_counter"
                    if hit_counter_key in character:
                        character[hit_counter_key] = 0
                    
        except Exception as e:
            self.logger.error("Error handling round end event: {}".format(e))
            self._emit_error_event("handle_round_end_event", str(e))
    
    def _handle_knockout_event(self, event_data: Dict[str, Any]) -> None:
        """Handle knockout events"""
        if not self.active:
            return
            
        try:
            # Handle ko_resist traits for targets being knocked out
            target = event_data.get("character")
            if target:
                # Check for ko_resist traits
                target_traits = target.get("traits", {})
                for trait_id, trait_data in target_traits.items():
                    try:
                        # Get trait catalog data
                        trait_catalog = self._get_trait_catalog()
                        trait_info = trait_catalog.get(trait_id, {})
                        
                        # Check if trait triggers on ko_resist
                        if trait_info.get("triggers") == "ko_resist":
                            # Try to resist the knockout
                            self._apply_ko_resist(target, trait_id, trait_info, event_data)
                    except Exception as e:
                        self.logger.error("Error processing ko_resist trait {}: {}".format(trait_id, e))
            
            # Handle ally_ko and ally_defeated traits for teammates
            match_context = event_data.get("match_context", {})
            team_data = match_context.get("team_data", {})
            
            if target and team_data:
                # Get character's team
                target_id = target.get("id")
                target_team = None
                
                for team_id, team_chars in team_data.items():
                    if target_id in team_chars:
                        target_team = team_id
                        break
                
                if target_team:
                    # Alert teammates with ally_ko and ally_defeated traits
                    for team_char_id in team_data.get(target_team, []):
                        if team_char_id == target_id:
                            continue  # Skip self
                            
                        # Find the teammate character
                        teammate = None
                        for char in match_context.get("characters", []):
                            if char.get("id") == team_char_id:
                                teammate = char
                                break
                        
                        if not teammate or teammate.get("is_ko", False):
                            continue
                            
                        # Check for ally_ko and ally_defeated traits
                        teammate_traits = teammate.get("traits", {})
                        for trait_id, trait_data in teammate_traits.items():
                            try:
                                # Get trait catalog data
                                trait_catalog = self._get_trait_catalog()
                                trait_info = trait_catalog.get(trait_id, {})
                                
                                # Check if trait triggers on ally_ko
                                if trait_info.get("triggers") == "ally_ko":
                                    # Check if trait is on cooldown
                                    if self._is_trait_on_cooldown(teammate, trait_id):
                                        continue
                                        
                                    # Check if character has enough stamina
                                    if not self._has_enough_stamina(teammate, trait_info):
                                        continue
                                        
                                    # Create modified event data with ally information
                                    ally_event_data = event_data.copy()
                                    ally_event_data["character"] = teammate
                                    ally_event_data["ally"] = target
                                    
                                    # Activate the trait
                                    self._activate_trait(teammate, trait_id, trait_info, ally_event_data)
                                    
                                # Check if trait triggers on ally_defeated
                                elif trait_info.get("triggers") == "ally_defeated":
                                    # Check if trait is on cooldown
                                    if self._is_trait_on_cooldown(teammate, trait_id):
                                        continue
                                        
                                    # Check if character has enough stamina
                                    if not self._has_enough_stamina(teammate, trait_info):
                                        continue
                                        
                                    # Create modified event data with ally information
                                    ally_event_data = event_data.copy()
                                    ally_event_data["character"] = teammate
                                    ally_event_data["ally"] = target
                                    
                                    # Activate the trait
                                    self._activate_trait(teammate, trait_id, trait_info, ally_event_data)
                                    
                            except Exception as e:
                                self.logger.error("Error processing ally_ko/defeated trait {}: {}".format(trait_id, e))
            
            # Check for last_survivor traits
            if team_data:
                for team_id, team_chars in team_data.items():
                    # Count active characters on the team
                    active_count = 0
                    last_survivor = None
                    
                    for team_char_id in team_chars:
                        # Find the character
                        for char in match_context.get("characters", []):
                            if char.get("id") == team_char_id and not char.get("is_ko", False):
                                active_count += 1
                                last_survivor = char
                                break
                    
                    # If only one character remains active
                    if active_count == 1 and last_survivor:
                        # Check for last_survivor traits
                        survivor_traits = last_survivor.get("traits", {})
                        for trait_id, trait_data in survivor_traits.items():
                            try:
                                # Get trait catalog data
                                trait_catalog = self._get_trait_catalog()
                    trait_info = trait_catalog.get(trait_id, {})
                                
                                # Check if trait triggers on last_survivor
                                if trait_info.get("triggers") == "last_survivor":
                                    # Check if trait is on cooldown
                                    if self._is_trait_on_cooldown(last_survivor, trait_id):
                                        continue
                                        
                                    # Create modified event data
                                    survivor_event_data = event_data.copy()
                                    survivor_event_data["character"] = last_survivor
                                    
                                    # Activate the trait
                                    self._activate_trait(last_survivor, trait_id, trait_info, survivor_event_data)
                            except Exception as e:
                                self.logger.error("Error processing last_survivor trait {}: {}".format(trait_id, e))
                    
        except Exception as e:
            self.logger.error("Error handling knockout event: {}".format(e))
            self._emit_error_event("handle_knockout_event", str(e))
    
    def _handle_convergence_event(self, event_data: Dict[str, Any]) -> None:
        """Handle convergence events"""
        if not self.active:
            return
            
        try:
            character = event_data.get("character")
            if not character:
                return
                
            # Check for convergence traits
            character_traits = character.get("traits", {})
            for trait_id, trait_data in character_traits.items():
                try:
                    # Get trait catalog data
                    trait_catalog = self._get_trait_catalog()
                    trait_info = trait_catalog.get(trait_id, {})
                    
                    # Check if trait triggers on convergence
                    if trait_info.get("triggers") == "convergence":
                        # Convergence traits are often passive and don't use cooldowns
                        # Apply convergence effect
                        self._apply_convergence_effect(character, trait_id, trait_info, event_data)
                except Exception as e:
                    self.logger.error("Error processing convergence trait {}: {}".format(trait_id, e))
                    
        except Exception as e:
            self.logger.error("Error handling convergence event: {}".format(e))
            self._emit_error_event("handle_convergence_event", str(e))
    
    def _handle_stamina_update_event(self, event_data: Dict[str, Any]) -> None:
        """Handle stamina update events"""
        if not self.active:
            return
            
        try:
            character = event_data.get("character")
            if not character:
                return
                
            # Get character stamina
            stamina = character.get("stamina", 100)
            
            # Check for stamina threshold traits
            character_traits = character.get("traits", {})
            for trait_id, trait_data in character_traits.items():
                try:
                    # Get trait catalog data
                    trait_catalog = self._get_trait_catalog()
                    trait_info = trait_catalog.get(trait_id, {})
                    
                    # Check specific stamina threshold triggers
                    triggers = trait_info.get("triggers")
                    
                    if triggers == "stamina_below_30" and stamina < 30:
                        # Check if trait is on cooldown
                        if self._is_trait_on_cooldown(character, trait_id):
                            continue
                            
                        # Check if character has enough stamina
                        if not self._has_enough_stamina(character, trait_info):
                            continue
                            
                        # Activate the trait
                        self._activate_trait(character, trait_id, trait_info, event_data)
                        
                    elif triggers == "stamina_full" and stamina > 95:
                        # Check if trait is on cooldown
                        if self._is_trait_on_cooldown(character, trait_id):
                            continue
                            
                        # Check if character has enough stamina
                        if not self._has_enough_stamina(character, trait_info):
                            continue
                            
                        # Activate the trait
                        self._activate_trait(character, trait_id, trait_info, event_data)
                        
                except Exception as e:
                    self.logger.error("Error processing stamina threshold trait {}: {}".format(trait_id, e))
                    
        except Exception as e:
            self.logger.error("Error handling stamina update event: {}".format(e))
            self._emit_error_event("handle_stamina_update_event", str(e))
    
    def _handle_morale_update_event(self, event_data: Dict[str, Any]) -> None:
        """Handle morale update events"""
        if not self.active:
            return
            
        try:
            character = event_data.get("character")
            if not character:
                return
                
            # Get character morale
            morale = character.get("morale", 100)
            
            # Check for morale threshold traits
            character_traits = character.get("traits", {})
            for trait_id, trait_data in character_traits.items():
                try:
                    # Get trait catalog data
                    trait_catalog = self._get_trait_catalog()
                    trait_info = trait_catalog.get(trait_id, {})
                    
                    # Check specific morale threshold triggers
                    triggers = trait_info.get("triggers")
                    
                    if triggers == "morale_low" and morale < 40:
                        # Check if trait is on cooldown
                        if self._is_trait_on_cooldown(character, trait_id):
                            continue
                            
                        # Check if character has enough stamina
                        if not self._has_enough_stamina(character, trait_info):
                            continue
                            
                        # Activate the trait
                        self._activate_trait(character, trait_id, trait_info, event_data)
                        
                    elif triggers == "morale_defense":
                        # Passive trait, applies automatically
                        self._apply_morale_defense(character, trait_id, trait_info, event_data)
                        
                except Exception as e:
                    self.logger.error("Error processing morale trait {}: {}".format(trait_id, e))
                    
        except Exception as e:
            self.logger.error("Error handling morale update event: {}".format(e))
            self._emit_error_event("handle_morale_update_event", str(e))
    
    def _handle_match_start_event(self, event_data: Dict[str, Any]) -> None:
        """Handle match start events"""
        if not self.active:
            return
            
        try:
            # Get all characters from match context
            match_context = event_data.get("match_context", {})
            characters = match_context.get("characters", [])
            
            # Process each character for match_start traits
            for character in characters:
                # Check for match_start traits
                character_traits = character.get("traits", {})
                for trait_id, trait_data in character_traits.items():
                    try:
                        # Get trait catalog data
                        trait_catalog = self._get_trait_catalog()
                        trait_info = trait_catalog.get(trait_id, {})
                        
                        # Check if trait triggers on match_start
                        if trait_info.get("triggers") == "match_start":
                            # Check if trait is on cooldown
                            if self._is_trait_on_cooldown(character, trait_id):
                                continue
                                
                            # Check if character has enough stamina
                            if not self._has_enough_stamina(character, trait_info):
                                continue
                                
                            # Create character-specific event data
                            char_event_data = event_data.copy()
                            char_event_data["character"] = character
                            
                            # Activate the trait
                            self._activate_trait(character, trait_id, trait_info, char_event_data)
                    except Exception as e:
                        self.logger.error("Error processing match_start trait {}: {}".format(trait_id, e))
                    
        except Exception as e:
            self.logger.error("Error handling match start event: {}".format(e))
            self._emit_error_event("handle_match_start_event", str(e))
    
    def _handle_match_point_event(self, event_data: Dict[str, Any]) -> None:
        """Handle match point events"""
        if not self.active:
            return
            
        try:
            # Get all characters from match context
            match_context = event_data.get("match_context", {})
            characters = match_context.get("characters", [])
            
            # Process each character for match_point traits
            for character in characters:
                # Skip knocked out characters
                if character.get("is_ko", False):
                    continue
                    
                # Check for match_point traits
                character_traits = character.get("traits", {})
                for trait_id, trait_data in character_traits.items():
                    try:
                        # Get trait catalog data
                        trait_catalog = self._get_trait_catalog()
                        trait_info = trait_catalog.get(trait_id, {})
                        
                        # Check if trait triggers on match_point
                        if trait_info.get("triggers") == "match_point":
                            # Create character-specific event data
                            char_event_data = event_data.copy()
                            char_event_data["character"] = character
                            
                            # Activate the trait
                            self._activate_trait(character, trait_id, trait_info, char_event_data)
                    except Exception as e:
                        self.logger.error("Error processing match_point trait {}: {}".format(trait_id, e))
                    
        except Exception as e:
            self.logger.error("Error handling match point event: {}".format(e))
            self._emit_error_event("handle_match_point_event", str(e))
    
    def _handle_board_position_event(self, event_data: Dict[str, Any]) -> None:
        """Handle board position events"""
        if not self.active:
            return
            
        try:
            character = event_data.get("character")
            if not character:
                return
                
            # Check for board_position traits
            character_traits = character.get("traits", {})
            for trait_id, trait_data in character_traits.items():
                try:
                    # Get trait catalog data
                    trait_catalog = self._get_trait_catalog()
                    trait_info = trait_catalog.get(trait_id, {})
                    
                    # Check if trait triggers on board_position
                    if trait_info.get("triggers") == "board_position":
                        # These are typically passive traits
                        self._apply_board_position_effect(character, trait_id, trait_info, event_data)
                except Exception as e:
                    self.logger.error("Error processing board_position trait {}: {}".format(trait_id, e))
                    
            # Check for adjacent_ally traits
            if trait_info.get("triggers") == "adjacent_ally":
                # These require additional board analysis
                self._apply_adjacent_ally_effect(character, trait_id, trait_info, event_data)
                    
        except Exception as e:
            self.logger.error("Error handling board position event: {}".format(e))
            self._emit_error_event("handle_board_position_event", str(e))
    
    def _handle_piece_captured_event(self, event_data: Dict[str, Any]) -> None:
        """Handle piece captured events"""
        if not self.active:
            return
            
        try:
            character = event_data.get("character")
            if not character:
                return
                
            # Check for piece_sacrifice traits
            character_traits = character.get("traits", {})
            for trait_id, trait_data in character_traits.items():
                try:
                    # Get trait catalog data
                    trait_catalog = self._get_trait_catalog()
                    trait_info = trait_catalog.get(trait_id, {})
                    
                    # Check if trait triggers on piece_sacrifice
                    if trait_info.get("triggers") == "piece_sacrifice":
                        # Check if trait is on cooldown
                        if self._is_trait_on_cooldown(character, trait_id):
                            continue
                            
                        # Check if character has enough stamina
                        if not self._has_enough_stamina(character, trait_info):
                            continue
                            
                        # Check if this was a sacrifice (losing a piece)
                        if event_data.get("is_sacrifice", False):
                            # Activate the trait
                            self._activate_trait(character, trait_id, trait_info, event_data)
                except Exception as e:
                    self.logger.error("Error processing piece_sacrifice trait {}: {}".format(trait_id, e))
                    
        except Exception as e:
            self.logger.error("Error handling piece captured event: {}".format(e))
            self._emit_error_event("handle_piece_captured_event", str(e))
    
    def _handle_move_made_event(self, event_data: Dict[str, Any]) -> None:
        """Handle move made events"""
        if not self.active:
            return
            
        try:
            character = event_data.get("character")
            if not character:
                return
                
            # Check for move_pattern traits
            character_traits = character.get("traits", {})
            for trait_id, trait_data in character_traits.items():
                try:
                    # Get trait catalog data
                    trait_catalog = self._get_trait_catalog()
                    trait_info = trait_catalog.get(trait_id, {})
                    
                    # Check if trait triggers on move_pattern
                    if trait_info.get("triggers") == "move_pattern":
                        # This requires tracking move patterns
                        self._update_move_pattern(character, trait_id, trait_info, event_data)
                except Exception as e:
                    self.logger.error("Error processing move_pattern trait {}: {}".format(trait_id, e))
                    
        except Exception as e:
            self.logger.error("Error handling move made event: {}".format(e))
            self._emit_error_event("handle_move_made_event", str(e))
    
    def _is_trait_on_cooldown(self, character: Dict[str, Any], trait_id: str) -> bool:
        """
        Check if a trait is on cooldown
        
        Args:
            character: Character dictionary
            trait_id: Trait ID
            
        Returns:
            True if trait is on cooldown, False otherwise
        """
        # Get character ID
        character_id = character.get("id")
        if not character_id:
            return True  # Treat as on cooldown if no character ID
        
        # Check if trait has cooldown tracking
        character_cooldowns = self.trait_cooldowns.get(character_id, {})
        cooldown_remaining = character_cooldowns.get(trait_id, 0)
        
        return cooldown_remaining > 0
    
    def _has_enough_stamina(self, character: Dict[str, Any], trait_info: Dict[str, Any]) -> bool:
        """
        Check if character has enough stamina for a trait
        
        Args:
            character: Character dictionary
            trait_info: Trait info dictionary
            
        Returns:
            True if character has enough stamina, False otherwise
        """
        # Get stamina cost
        stamina_cost = trait_info.get("stamina_cost", 0)
        if stamina_cost <= 0:
            return True  # No stamina cost
        
        # Apply character modifiers
        if "aRES" in character and self._stamina_cost_modifiers.get("endurance_factor"):
            endurance_factor = self._stamina_cost_modifiers["endurance_factor"]
            stamina_reduction = character["aRES"] * endurance_factor
            stamina_cost = max(self._stamina_cost_modifiers.get("minimum_cost", 0), 
                               stamina_cost - stamina_reduction)
        
        # Check current stamina
        current_stamina = character.get("stamina", 100)
        
        return current_stamina >= stamina_cost
    
    def _get_trait_stamina_cost(self, character: Dict[str, Any], trait_info: Dict[str, Any]) -> float:
        """
        Calculate the actual stamina cost for a trait
        
        Args:
            character: Character dictionary
            trait_info: Trait info dictionary
            
        Returns:
            Actual stamina cost after modifiers
        """
        # Get base stamina cost
        stamina_cost = trait_info.get("stamina_cost", 0)
        if stamina_cost <= 0:
            return 0  # No stamina cost
        
        # Apply character modifiers
        if "aRES" in character and self._stamina_cost_modifiers.get("endurance_factor"):
            endurance_factor = self._stamina_cost_modifiers["endurance_factor"]
            stamina_reduction = character["aRES"] * endurance_factor
            stamina_cost = max(self._stamina_cost_modifiers.get("minimum_cost", 0), 
                              stamina_cost - stamina_reduction)
        
        return stamina_cost
    
    def _calculate_trait_cooldown(self, character: Dict[str, Any], trait_info: Dict[str, Any]) -> int:
        """
        Calculate cooldown for a trait
        
        Args:
            character: Character dictionary
            trait_info: Trait info dictionary
            
        Returns:
            Actual cooldown after modifiers
        """
        # Get base cooldown
        cooldown = trait_info.get("cooldown", 0)
        if cooldown <= 0:
            return 0  # No cooldown
        
        # Apply level scaling if available
        character_level = character.get("level", 1)
        if character_level > 1 and self._cooldown_modifiers.get("level_scaling"):
            level_factor = self._cooldown_modifiers["level_scaling"]
            cooldown *= level_factor ** (character_level - 1)
        
        # Apply willpower factor
        if "aWIL" in character and self._cooldown_modifiers.get("willpower_factor"):
            wil_factor = self._cooldown_modifiers["willpower_factor"]
            cooldown_reduction = character["aWIL"] * wil_factor * cooldown
            cooldown -= cooldown_reduction
        
        # Apply minimum cooldown
        cooldown = max(self._cooldown_modifiers.get("minimum_cooldown", 1), cooldown)
        
        # Round to integer
        return round(cooldown)
    
    def _activate_trait(self, character: Dict[str, Any], trait_id: str, 
                       trait_info: Dict[str, Any], event_data: Dict[str, Any]) -> bool:
        """
        Activate a trait
        
        Args:
            character: Character dictionary
            trait_id: Trait ID
            trait_info: Trait info dictionary
            event_data: Event data that triggered the trait
            
        Returns:
            True if trait was activated, False otherwise
        """
        try:
            character_id = character.get("id", "unknown")
            trait_name = trait_info.get("name", trait_id)
            trait_type = trait_info.get("type", "unknown")
            
            # Apply trait effect
            effect_applied = self._apply_trait_effect(character, trait_id, trait_info, event_data)
            
            if not effect_applied:
                return False
            
            # Apply stamina cost
            stamina_cost = self._get_trait_stamina_cost(character, trait_info)
            if stamina_cost > 0:
                current_stamina = character.get("stamina", 100)
                new_stamina = max(0, current_stamina - stamina_cost)
                character["stamina"] = new_stamina
            
            # Apply cooldown
            cooldown = self._calculate_trait_cooldown(character, trait_info)
            if cooldown > 0:
                if character_id not in self.trait_cooldowns:
                    self.trait_cooldowns[character_id] = {}
                self.trait_cooldowns[character_id][trait_id] = cooldown
            
            # Track activation
            self.trait_activations[trait_id] += 1
            
            # Update character trait activation count
            if "traits" in character and trait_id in character["traits"]:
                if "activations" not in character["traits"][trait_id]:
                    character["traits"][trait_id]["activations"] = 0
                character["traits"][trait_id]["activations"] += 1
            
            # Update rStats
            if "rStats" in character:
                if "TRAIT_ACTIVATIONS" not in character["rStats"]:
                    character["rStats"]["TRAIT_ACTIVATIONS"] = 0
                character["rStats"]["TRAIT_ACTIVATIONS"] += 1
                
                # Update trait type specific counter
                if trait_type == "active":
                    stat_name = "ACTIVE_TRAIT_ACTIVATIONS"
                elif trait_type == "passive":
                    stat_name = "PASSIVE_TRAIT_ACTIVATIONS"
                else:
                    stat_name = "OTHER_TRAIT_ACTIVATIONS"
                    
                if stat_name not in character["rStats"]:
                    character["rStats"][stat_name] = 0
                character["rStats"][stat_name] += 1
            
            # Emit trait_activated event
            self._emit_event("trait_activated", {
                "character": character,
                "trait_id": trait_id,
                "trait_name": trait_name,
                "trait_type": trait_type,
                "stamina_cost": stamina_cost,
                "cooldown": cooldown,
                "trigger": trait_info.get("triggers", "unknown"),
                "match_context": event_data.get("match_context", {})
            })
            
            self.logger.info("Trait {} activated for character {}".format(
                trait_name, character.get("name", character_id)))
            
            return True
            
        except Exception as e:
            self.logger.error("Error activating trait {}: {}".format(trait_id, e))
            self._emit_error_event("activate_trait", str(e), {
                "character_id": character.get("id", "unknown"),
                "trait_id": trait_id
            })
            return False
    
    def _apply_trait_effect(self, character: Dict[str, Any], trait_id: str,
                           trait_info: Dict[str, Any], event_data: Dict[str, Any]) -> bool:
        """
        Apply trait effect based on formula
        
        Args:
            character: Character dictionary
            trait_id: Trait ID
            trait_info: Trait info dictionary
            event_data: Event data that triggered the trait
            
        Returns:
            True if effect was applied, False otherwise
        """
        try:
            formula_key = trait_info.get("formula_key")
            formula_expr = trait_info.get("formula_expr")
            
            if not formula_key or not formula_expr:
                return False
            
            # Process different formula types
            if formula_key == "board_evaluate":
                # Improve board evaluation
                if formula_expr.endswith("%"):
                    # Percentage boost
                    boost = float(formula_expr.rstrip("%")) / 100.0
                    if "board_evaluation_boost" not in character:
                        character["board_evaluation_boost"] = 0.0
                    character["board_evaluation_boost"] += boost
                else:
                    # Flat boost
                    boost = float(formula_expr)
                    if "board_evaluation_boost" not in character:
                        character["board_evaluation_boost"] = 0.0
                    character["board_evaluation_boost"] += boost / 100.0  # Convert to percentage
            
            elif formula_key == "team_morale":
                # Boost team morale
                boost = float(formula_expr.lstrip("+"))
                
                # Apply to all team members
                match_context = event_data.get("match_context", {})
                team_data = match_context.get("team_data", {})
                
                if team_data:
                    # Get character's team
                    character_id = character.get("id")
                    character_team = None
                    
                    for team_id, team_chars in team_data.items():
                        if character_id in team_chars:
                            character_team = team_id
                            break
                    
                    if character_team:
                        # Boost morale for all team members
                        for team_char_id in team_data.get(character_team, []):
                            # Find the teammate character
                            teammate = None
                            for char in match_context.get("characters", []):
                                if char.get("id") == team_char_id:
                                    teammate = char
                                    break
                            
                            if not teammate or teammate.get("is_ko", False):
                                continue
                                
                            # Apply morale boost
                            if "morale" in teammate:
                                current_morale = teammate["morale"]
                                new_morale = min(100, current_morale + boost)
                                teammate["morale"] = new_morale
            
            elif formula_key == "damage_taken":
                # Reduce incoming damage
                if formula_expr.endswith("%"):
                    # Percentage reduction
                    reduction = float(formula_expr.rstrip("%").lstrip("-")) / 100.0
                    if "damage_reduction" not in character:
                        character["damage_reduction"] = 0.0
                    character["damage_reduction"] += reduction
                else:
                    # Flat reduction
                    reduction = float(formula_expr.lstrip("-"))
                    if "flat_damage_reduction" not in character:
                        character["flat_damage_reduction"] = 0.0
                    character["flat_damage_reduction"] += reduction
            
            elif formula_key == "move_speed":
                # Increase move speed (candidate move count)
                boost = int(formula_expr.lstrip("+"))
                if "move_speed_boost" not in character:
                    character["move_speed_boost"] = 0
                character["move_speed_boost"] += boost
            
            elif formula_key == "attack_power":
                # Increase attack power
                if formula_expr.endswith("%"):
                    # Percentage boost
                    boost = float(formula_expr.rstrip("%").lstrip("+")) / 100.0
                    if "attack_power_boost" not in character:
                        character["attack_power_boost"] = 0.0
                    character["attack_power_boost"] += boost
                else:
                    # Flat boost
                    boost = float(formula_expr.lstrip("+"))
                    if "flat_attack_boost" not in character:
                        character["flat_attack_boost"] = 0.0
                    character["flat_attack_boost"] += boost
            
            elif formula_key == "heal_ally":
                # Heal an ally
                heal_amount = float(formula_expr.lstrip("+"))
                
                # Get target from event data
                target = event_data.get("target")
                if not target:
                    return False
                
                # Apply healing
                current_hp = target.get("HP", 0)
                new_hp = min(100, current_hp + heal_amount)
                target["HP"] = new_hp
                
                # Emit healing_applied event
                self._emit_event("healing_applied", {
                    "source": character,
                    "target": target,
                    "amount": heal_amount,
                    "source_trait": trait_id,
                    "match_context": event_data.get("match_context", {})
                })
            
            elif formula_key == "convergence_power":
                # Increase convergence power
                if formula_expr.endswith("%"):
                    # Percentage boost
                    boost = float(formula_expr.rstrip("%").lstrip("+")) / 100.0
                    if "convergence_power_boost" not in character:
                        character["convergence_power_boost"] = 0.0
                    character["convergence_power_boost"] += boost
                else:
                    # Flat boost
                    boost = float(formula_expr.lstrip("+"))
                    if "flat_convergence_boost" not in character:
                        character["flat_convergence_boost"] = 0.0
                    character["flat_convergence_boost"] += boost
            
            elif formula_key == "stamina_regen":
                # Increase stamina regeneration
                regen_amount = float(formula_expr.lstrip("+"))
                if "stamina_regen_boost" not in character:
                    character["stamina_regen_boost"] = 0.0
                character["stamina_regen_boost"] += regen_amount
            
            elif formula_key == "revenge_boost":
                # Boost all stats after ally KO
                if formula_expr.endswith("%"):
                    # Percentage boost
                    boost = float(formula_expr.rstrip("%").lstrip("+")) / 100.0
                    
                    # Apply to all base stats
                    for stat in ["aSTR", "aSPD", "aFS", "aLDR", "aDUR", "aRES", "aWIL"]:
                        if stat in character:
                            # Store original value if not already stored
                            orig_key = f"original_{stat}"
                            if orig_key not in character:
                                character[orig_key] = character[stat]
                            
                            # Apply boost
                            character[stat] = character[orig_key] * (1 + boost)
            
            elif formula_key == "critical_chance":
                # Increase critical hit chance
                if formula_expr.endswith("%"):
                    # Percentage chance
                    chance = float(formula_expr.rstrip("%")) / 100.0
                    if "critical_chance" not in character:
                        character["critical_chance"] = 0.0
                    character["critical_chance"] += chance
                else:
                    # Flat chance (assume decimal)
                    chance = float(formula_expr)
                    if "critical_chance" not in character:
                        character["critical_chance"] = 0.0
                    character["critical_chance"] += chance
            
            elif formula_key == "team_boost":
                # Boost team stats
                if formula_expr.endswith("%"):
                    # Percentage boost
                    boost = float(formula_expr.rstrip("%").lstrip("+")) / 100.0
                    
                    # Apply to all team members
                    match_context = event_data.get("match_context", {})
                    team_data = match_context.get("team_data", {})
                    
                    if team_data:
                        # Get character's team
                        character_id = character.get("id")
                        character_team = None
                        
                        for team_id, team_chars in team_data.items():
                            if character_id in team_chars:
                                character_team = team_id
                                break
                        
                        if character_team:
                            # Boost stats for all team members
                            for team_char_id in team_data.get(character_team, []):
                                if team_char_id == character_id:
                                    continue  # Skip self
                                    
                                # Find the teammate character
                                teammate = None
                                for char in match_context.get("characters", []):
                                    if char.get("id") == team_char_id:
                                        teammate = char
                                        break
                                
                                if not teammate or teammate.get("is_ko", False):
                                    continue
                                    
                                # Apply boost to all stats
                                for stat in ["aSTR", "aSPD", "aFS", "aLDR", "aDUR", "aRES", "aWIL"]:
                                    if stat in teammate:
                                        # Store original value if not already stored
                                        orig_key = f"original_{stat}"
                                        if orig_key not in teammate:
                                            teammate[orig_key] = teammate[stat]
                                        
                                        # Apply boost
                                        teammate[stat] = teammate[orig_key] * (1 + boost)
            
            elif formula_key == "counter_damage":
                # Set up counter damage effect
                if formula_expr.endswith("%"):
                    # Percentage of incoming damage
                    counter_percent = float(formula_expr.rstrip("%")) / 100.0
                    character["counter_damage_percent"] = counter_percent
                else:
                    # Flat counter damage
                    counter_damage = float(formula_expr)
                    character["counter_damage_flat"] = counter_damage
            
            elif formula_key == "accuracy":
                # Increase move accuracy
                if formula_expr.endswith("%"):
                    # Percentage boost
                    boost = float(formula_expr.rstrip("%").lstrip("+")) / 100.0
                    if "accuracy_boost" not in character:
                        character["accuracy_boost"] = 0.0
                    character["accuracy_boost"] += boost
                else:
                    # Flat boost (assume decimal)
                    boost = float(formula_expr.lstrip("+"))
                    if "accuracy_boost" not in character:
                        character["accuracy_boost"] = 0.0
                    character["accuracy_boost"] += boost / 100.0  # Convert to percentage
            
            elif formula_key == "speed_boost":
                # Increase speed stat
                if formula_expr.endswith("%"):
                    # Percentage boost
                    boost = float(formula_expr.rstrip("%").lstrip("+")) / 100.0
                    if "aSPD" in character:
                        # Store original value if not already stored
                        orig_key = "original_aSPD"
                        if orig_key not in character:
                            character[orig_key] = character["aSPD"]
                        
                        # Apply boost
                        character["aSPD"] = character[orig_key] * (1 + boost)
                else:
                    # Flat boost
                    boost = float(formula_expr.lstrip("+"))
                    if "aSPD" in character:
                        # Store original value if not already stored
                        orig_key = "original_aSPD"
                        if orig_key not in character:
                            character[orig_key] = character["aSPD"]
                        
                        # Apply boost
                        character["aSPD"] = character[orig_key] + boost
            
            elif formula_key == "team_defense":
                # Increase team defense
                if formula_expr.endswith("%"):
                    # Percentage boost
                    boost = float(formula_expr.rstrip("%").lstrip("+")) / 100.0
                    
                    # Apply to all team members
                    match_context = event_data.get("match_context", {})
                    team_data = match_context.get("team_data", {})
                    
                    if team_data:
                        # Get character's team
                        character_id = character.get("id")
                        character_team = None
                        
                        for team_id, team_chars in team_data.items():
                            if character_id in team_chars:
                                character_team = team_id
                                break
                        
                        if character_team:
                            # Boost defense for all team members
                            for team_char_id in team_data.get(character_team, []):
                                # Find the teammate character
                                teammate = None
                                for char in match_context.get("characters", []):
                                    if char.get("id") == team_char_id:
                                        teammate = char
                                        break
                                
                                if not teammate or teammate.get("is_ko", False):
                                    continue
                                    
                                # Apply defense boost
                                if "aDUR" in teammate:
                                    # Store original value if not already stored
                                    orig_key = "original_aDUR"
                                    if orig_key not in teammate:
                                        teammate[orig_key] = teammate["aDUR"]
                                    
                                    # Apply boost
                                    teammate["aDUR"] = teammate[orig_key] * (1 + boost)
            
            elif formula_key == "damage_avoid":
                # Set up damage avoidance
                if formula_expr.endswith("%"):
                    # Percentage chance to avoid
                    avoid_chance = float(formula_expr.rstrip("%")) / 100.0
                    character["damage_avoid_chance"] = avoid_chance
                else:
                    # Assume 100% if no percentage
                    character["damage_avoid_next"] = True
            
            elif formula_key == "xp_boost":
                # Increase XP gain for allies
                if formula_expr.endswith("%"):
                    # Percentage boost
                    boost = float(formula_expr.rstrip("%").lstrip("+")) / 100.0
                    
                    # Apply to all team members
                    match_context = event_data.get("match_context", {})
                    team_data = match_context.get("team_data", {})
                    
                    if team_data:
                        # Get character's team
                        character_id = character.get("id")
                        character_team = None
                        
                        for team_id, team_chars in team_data.items():
                            if character_id in team_chars:
                                character_team = team_id
                                break
                        
                        if character_team:
                            # Apply XP boost for all team members
                            for team_char_id in team_data.get(character_team, []):
                                if team_char_id == character_id:
                                    continue  # Skip self
                                    
                                # Find the teammate character
                                teammate = None
                                for char in match_context.get("characters", []):
                                    if char.get("id") == team_char_id:
                                        teammate = char
                                        break
                                
                                if not teammate:
                                    continue
                                    
                                # Apply XP boost
                                if "xp_multiplier" not in teammate:
                                    teammate["xp_multiplier"] = 1.0
                                teammate["xp_multiplier"] += boost
            
            elif formula_key == "checkmate_sight":
                # Increase checkmate lookahead
                lookahead = int(formula_expr.lstrip("+"))
                character["checkmate_sight"] = lookahead
            
            elif formula_key == "stat_adapt":
                # Adapt stats based on opponents
                if formula_expr.endswith("%"):
                    # Percentage adaptation
                    adapt_percent = float(formula_expr.rstrip("%").lstrip("+")) / 100.0
                    character["stat_adapt_percent"] = adapt_percent
            
            elif formula_key == "morale_restore":
                # Restore morale
                restore_amount = float(formula_expr.lstrip("+"))
                
                # Apply to all team members
                match_context = event_data.get("match_context", {})
                team_data = match_context.get("team_data", {})
                
                if team_data:
                    # Get character's team
                    character_id = character.get("id")
                    character_team = None
                    
                    for team_id, team_chars in team_data.items():
                        if character_id in team_chars:
                            character_team = team_id
                            break
                    
                    if character_team:
                        # Restore morale for all team members
                        for team_char_id in team_data.get(character_team, []):
                            # Find the teammate character
                            teammate = None
                            for char in match_context.get("characters", []):
                                if char.get("id") == team_char_id:
                                    teammate = char
                                    break
                            
                            if not teammate or teammate.get("is_ko", False):
                                continue
                                
                            # Apply morale restoration
                            if "morale" in teammate:
                                current_morale = teammate["morale"]
                                new_morale = min(100, current_morale + restore_amount)
                                teammate["morale"] = new_morale
            
            elif formula_key == "stamina_restore":
                # Restore stamina
                restore_amount = float(formula_expr.lstrip("+"))
                
                # Apply to character
                current_stamina = character.get("stamina", 0)
                new_stamina = min(100, current_stamina + restore_amount)
                character["stamina"] = new_stamina
            
            elif formula_key == "ignore_defense":
                # Set defense penetration
                if formula_expr.endswith("%"):
                    # Percentage of defense ignored
                    ignore_percent = float(formula_expr.rstrip("%")) / 100.0
                    character["defense_ignore_percent"] = ignore_percent
            
            elif formula_key == "damage_redirect":
                # Set up damage redirection
                if formula_expr.endswith("%"):
                    # Percentage of damage redirected
                    redirect_percent = float(formula_expr.rstrip("%")) / 100.0
                    character["damage_redirect_percent"] = redirect_percent
                    
                    # Store target info
                    ally = event_data.get("ally", event_data.get("target"))
                    if ally:
                        character["damage_redirect_target"] = ally.get("id")
            
            elif formula_key == "damage_stack":
                # Set up damage stacking
                if formula_expr.endswith("%"):
                    # Percentage increase per stack
                    stack_percent = float(formula_expr.rstrip("%").lstrip("+")) / 100.0
                    character["damage_stack_percent"] = stack_percent
            
            elif formula_key == "intimidate":
                # Set intimidate chance
                if formula_expr.endswith("%"):
                    # Percentage chance
                    intimidate_chance = float(formula_expr.rstrip("%")) / 100.0
                    character["intimidate_chance"] = intimidate_chance
            
            elif formula_key == "opponent_predict":
                # Set prediction chance
                if formula_expr.endswith("%"):
                    # Percentage chance
                    predict_chance = float(formula_expr.rstrip("%")) / 100.0
                    character["predict_chance"] = predict_chance
            
            elif formula_key == "survive_lethal":
                # Set survival chance
                if formula_expr.endswith("%"):
                    # Percentage chance
                    survive_chance = float(formula_expr.rstrip("%")) / 100.0
                    character["survive_lethal_chance"] = survive_chance
            
            elif formula_key == "power_boost":
                # Boost attack power
                if formula_expr.endswith("%"):
                    # Percentage boost
                    boost = float(formula_expr.rstrip("%").lstrip("+")) / 100.0
                    if "power_boost" not in character:
                        character["power_boost"] = 0.0
                    character["power_boost"] += boost
            
            elif formula_key == "extra_move":
                # Set extra move chance
                if formula_expr.endswith("%"):
                    # Percentage chance
                    move_chance = float(formula_expr.rstrip("%")) / 100.0
                    character["extra_move_chance"] = move_chance
            
            elif formula_key == "confuse_opponent":
                # Set confusion chance
                if formula_expr.endswith("%"):
                    # Percentage chance
                    confuse_chance = float(formula_expr.rstrip("%")) / 100.0
                    character["confuse_opponent_chance"] = confuse_chance
            
            elif formula_key == "stat_boost":
                # Boost all stats
                if formula_expr.endswith("%"):
                    # Percentage boost
                    boost = float(formula_expr.rstrip("%").lstrip("+")) / 100.0
                    
                    # Apply to all stats
                    for stat in ["aSTR", "aSPD", "aFS", "aLDR", "aDUR", "aRES", "aWIL"]:
                        if stat in character:
                            # Store original value if not already stored
                            orig_key = f"original_{stat}"
                            if orig_key not in character:
                                character[orig_key] = character[stat]
                            
                            # Apply boost
                            character[stat] = character[orig_key] * (1 + boost)
            
            elif formula_key == "damage_negate":
                # Set damage negation
                if formula_expr == "100%":
                    character["damage_negate_next"] = True
            
            elif formula_key == "stat_share":
                # Set stat sharing
                if formula_expr.endswith("%"):
                    # Percentage shared
                    share_percent = float(formula_expr.rstrip("%")) / 100.0
                    character["stat_share_percent"] = share_percent
            
            elif formula_key == "power_gain":
                # Boost next move power
                if formula_expr.endswith("%"):
                    # Percentage boost
                    boost = float(formula_expr.rstrip("%").lstrip("+")) / 100.0
                    character["next_move_power_boost"] = boost
            
            elif formula_key == "zone_control":
                # Increase board control
                if formula_expr.endswith("%"):
                    # Percentage increase
                    control_boost = float(formula_expr.rstrip("%").lstrip("+")) / 100.0
                    character["zone_control_boost"] = control_boost
            
            elif formula_key == "power_conversion":
                # Convert stamina to power
                if formula_expr.endswith("%"):
                    # Percentage converted
                    conversion_percent = float(formula_expr.rstrip("%")) / 100.0
                    
                    # Calculate stamina to convert
                    current_stamina = character.get("stamina", 100)
                    stamina_to_convert = current_stamina * conversion_percent
                    
                    # Reduce stamina
                    new_stamina = current_stamina - stamina_to_convert
                    character["stamina"] = new_stamina
                    
                    # Add power boost
                    power_boost = stamina_to_convert / 100.0  # Scale to reasonable boost
                    if "power_boost" not in character:
                        character["power_boost"] = 0.0
                    character["power_boost"] += power_boost
            
            elif formula_key == "reduce_effects":
                # Reduce negative effects
                if formula_expr.endswith("%"):
                    # Percentage reduction
                    reduction = float(formula_expr.rstrip("%")) / 100.0
                    character["negative_effect_reduction"] = reduction
            
            elif formula_key == "combo_boost":
                # Set combo boost
                if formula_expr.endswith("%"):
                    # Percentage boost per combo
                    boost = float(formula_expr.rstrip("%").lstrip("+")) / 100.0
                    character["combo_boost_percent"] = boost
            
            elif formula_key == "position_advantage":
                # Set position advantage
                if formula_expr.endswith("%"):
                    # Percentage advantage
                    advantage = float(formula_expr.rstrip("%").lstrip("+")) / 100.0
                    character["position_advantage"] = advantage
            
            elif formula_key == "all_stats":
                # Boost all stats significantly
                if formula_expr.endswith("%"):
                    # Percentage boost
                    boost = float(formula_expr.rstrip("%").lstrip("+")) / 100.0
                    
                    # Apply to all stats
                    for stat in ["aSTR", "aSPD", "aFS", "aLDR", "aDUR", "aRES", "aWIL"]:
                        if stat in character:
                            # Store original value if not already stored
                            orig_key = f"original_{stat}"
                            if orig_key not in character:
                                character[orig_key] = character[stat]
                            
                            # Apply significant boost
                            character[stat] = character[orig_key] * (1 + boost)
            
            elif formula_key == "perfect_move":
                # Set perfect move chance
                if formula_expr.endswith("%"):
                    # Percentage chance
                    perfect_chance = float(formula_expr.rstrip("%")) / 100.0
                    character["perfect_move_chance"] = perfect_chance
            
            # If we got here, effect was applied
            return True
            
        except Exception as e:
            self.logger.error("Error applying trait effect {}: {}".format(formula_key, e))
            self._emit_error_event("apply_trait_effect", str(e), {
                "character_id": character.get("id", "unknown"),
                "trait_id": trait_id,
                "formula_key": formula_key
            })
            return False
    
    def _apply_stamina_regen(self, character: Dict[str, Any], trait_id: str,
                            trait_info: Dict[str, Any], event_data: Dict[str, Any]) -> bool:
        """
        Apply stamina regeneration from trait
        
        Args:
            character: Character dictionary
            trait_id: Trait ID
            trait_info: Trait info dictionary
            event_data: Event data
            
        Returns:
            True if regeneration was applied, False otherwise
        """
        try:
            formula_expr = trait_info.get("formula_expr")
            if not formula_expr:
                return False
                
            # Parse regen amount
            regen_amount = float(formula_expr.lstrip("+"))
            
            # Apply regeneration
            current_stamina = character.get("stamina", 0)
            new_stamina = min(100, current_stamina + regen_amount)
            character["stamina"] = new_stamina
            
            # Emit stamina_restored event
            self._emit_event("stamina_restored", {
                "character": character,
                "amount": regen_amount,
                "source_trait": trait_id,
                "old_stamina": current_stamina,
                "new_stamina": new_stamina,
                "match_context": event_data.get("match_context", {})
            })
            
            # Count as trait activation
            self.trait_activations[trait_id] += 1
            
            # Update character trait activation count
            if "traits" in character and trait_id in character["traits"]:
                if "activations" not in character["traits"][trait_id]:
                    character["traits"][trait_id]["activations"] = 0
                character["traits"][trait_id]["activations"] += 1
            
            # Update rStats
            if "rStats" in character:
                if "PASSIVE_TRAIT_ACTIVATIONS" not in character["rStats"]:
                    character["rStats"]["PASSIVE_TRAIT_ACTIVATIONS"] = 0
                character["rStats"]["PASSIVE_TRAIT_ACTIVATIONS"] += 1
            
            return True
            
        except Exception as e:
            self.logger.error("Error applying stamina regen: {}".format(e))
            self._emit_error_event("apply_stamina_regen", str(e), {
                "character_id": character.get("id", "unknown"),
                "trait_id": trait_id
            })
            return False
    
    def _apply_ko_resist(self, character: Dict[str, Any], trait_id: str,
                        trait_info: Dict[str, Any], event_data: Dict[str, Any]) -> bool:
        """
        Apply KO resistance
        
        Args:
            character: Character dictionary
            trait_id: Trait ID
            trait_info: Trait info dictionary
            event_data: Event data
            
        Returns:
            True if KO was resisted, False otherwise
        """
        try:
            formula_expr = trait_info.get("formula_expr")
            if not formula_expr or not formula_expr.endswith("%"):
                return False
                
            # Parse resist chance
            resist_chance = float(formula_expr.rstrip("%")) / 100.0
            
            # Roll for resistance
            if random.random() <= resist_chance:
                # Resist the KO
                character["is_ko"] = False
                character["HP"] = 1
                
                # Emit ko_resisted event
                self._emit_event("ko_resisted", {
                    "character": character,
                    "source_trait": trait_id,
                    "match_context": event_data.get("match_context", {})
                })
                
                # Count as trait activation
                self.trait_activations[trait_id] += 1
                
                # Update character trait activation count
                if "traits" in character and trait_id in character["traits"]:
                    if "activations" not in character["traits"][trait_id]:
                        character["traits"][trait_id]["activations"] = 0
                    character["traits"][trait_id]["activations"] += 1
                
                # Update rStats
                if "rStats" in character:
                    if "PASSIVE_TRAIT_ACTIVATIONS" not in character["rStats"]:
                        character["rStats"]["PASSIVE_TRAIT_ACTIVATIONS"] = 0
                    character["rStats"]["PASSIVE_TRAIT_ACTIVATIONS"] += 1
                
                return True
            
            return False
            
        except Exception as e:
            self.logger.error("Error applying KO resist: {}".format(e))
            self._emit_error_event("apply_ko_resist", str(e), {
                "character_id": character.get("id", "unknown"),
                "trait_id": trait_id
            })
            return False
    
    def _apply_consecutive_hit_effect(self, character: Dict[str, Any], trait_id: str,
                                     trait_info: Dict[str, Any], event_data: Dict[str, Any]) -> bool:
        """
        Apply consecutive hit effect
        
        Args:
            character: Character dictionary
            trait_id: Trait ID
            trait_info: Trait info dictionary
            event_data: Event data
            
        Returns:
            True if effect was applied, False otherwise
        """
        try:
            formula_expr = trait_info.get("formula_expr")
            if not formula_expr or not formula_expr.endswith("%"):
                return False
                
            # Parse boost percentage
            boost_percent = float(formula_expr.rstrip("%").lstrip("+")) / 100.0
            
            # Get hit counter
            hit_counter_key = f"{trait_id}_hit_counter"
            hit_counter = character.get(hit_counter_key, 0)
            
            # Apply boost based on hit counter
            if hit_counter > 0:
                # Calculate boost
                total_boost = boost_percent * hit_counter
                
                # Apply to attack power
                if "damage_boost_from_hits" not in character:
                    character["damage_boost_from_hits"] = 0.0
                
                # Clear previous boost and apply new one
                character["damage_boost_from_hits"] = total_boost
                
                # Count as trait activation
                self.trait_activations[trait_id] += 1
                
                # Update character trait activation count
                if "traits" in character and trait_id in character["traits"]:
                    if "activations" not in character["traits"][trait_id]:
                        character["traits"][trait_id]["activations"] = 0
                    character["traits"][trait_id]["activations"] += 1
                
                # Update rStats
                if "rStats" in character:
                    if "PASSIVE_TRAIT_ACTIVATIONS" not in character["rStats"]:
                        character["rStats"]["PASSIVE_TRAIT_ACTIVATIONS"] = 0
                    character["rStats"]["PASSIVE_TRAIT_ACTIVATIONS"] += 1
                
                return True
            
            return False
            
        except Exception as e:
            self.logger.error("Error applying consecutive hit effect: {}".format(e))
            self._emit_error_event("apply_consecutive_hit_effect", str(e), {
                "character_id": character.get("id", "unknown"),
                "trait_id": trait_id
            })
            return False
    
    def _apply_convergence_effect(self, character: Dict[str, Any], trait_id: str,
                                 trait_info: Dict[str, Any], event_data: Dict[str, Any]) -> bool:
        """
        Apply convergence effect
        
        Args:
            character: Character dictionary
            trait_id: Trait ID
            trait_info: Trait info dictionary
            event_data: Event data
            
        Returns:
            True if effect was applied, False otherwise
        """
        try:
            formula_expr = trait_info.get("formula_expr")
            if not formula_expr or not formula_expr.endswith("%"):
                return False
                
            # Parse boost percentage
            boost_percent = float(formula_expr.rstrip("%").lstrip("+")) / 100.0
            
            # Apply to convergence power
            if "convergence_power_boost" not in character:
                character["convergence_power_boost"] = 0.0
            character["convergence_power_boost"] += boost_percent
            
            # Count as trait activation
            self.trait_activations[trait_id] += 1
            
            # Update character trait activation count
            if "traits" in character and trait_id in character["traits"]:
                if "activations" not in character["traits"][trait_id]:
                    character["traits"][trait_id]["activations"] = 0
                character["traits"][trait_id]["activations"] += 1
            
            # Update rStats
            if "rStats" in character:
                if "PASSIVE_TRAIT_ACTIVATIONS" not in character["rStats"]:
                    character["rStats"]["PASSIVE_TRAIT_ACTIVATIONS"] = 0
                character["rStats"]["PASSIVE_TRAIT_ACTIVATIONS"] += 1
            
            return True
            
        except Exception as e:
            self.logger.error("Error applying convergence effect: {}".format(e))
            self._emit_error_event("apply_convergence_effect", str(e), {
                "character_id": character.get("id", "unknown"),
                "trait_id": trait_id
            })
            return False
    
    def _apply_morale_defense(self, character: Dict[str, Any], trait_id: str,
                             trait_info: Dict[str, Any], event_data: Dict[str, Any]) -> bool:
        """
        Apply morale defense effect
        
        Args:
            character: Character dictionary
            trait_id: Trait ID
            trait_info: Trait info dictionary
            event_data: Event data
            
        Returns:
            True if effect was applied, False otherwise
        """
        try:
            formula_expr = trait_info.get("formula_expr")
            if not formula_expr or not formula_expr.endswith("%"):
                return False
                
            # Parse reduction percentage
            reduction_percent = float(formula_expr.rstrip("%")) / 100.0
            
            # Check if morale is decreasing
            old_morale = event_data.get("old_morale", 100)
            new_morale = event_data.get("new_morale", 100)
            
            if new_morale < old_morale:
                # Calculate morale loss reduction
                morale_loss = old_morale - new_morale
                reduced_loss = morale_loss * (1 - reduction_percent)
                
                # Apply reduced morale loss
                adjusted_morale = old_morale - reduced_loss
                character["morale"] = adjusted_morale
                
                # Count as trait activation
                self.trait_activations[trait_id] += 1
                
                # Update character trait activation count
                if "traits" in character and trait_id in character["traits"]:
                    if "activations" not in character["traits"][trait_id]:
                        character["traits"][trait_id]["activations"] = 0
                    character["traits"][trait_id]["activations"] += 1
                
                # Update rStats
                if "rStats" in character:
                    if "PASSIVE_TRAIT_ACTIVATIONS" not in character["rStats"]:
                        character["rStats"]["PASSIVE_TRAIT_ACTIVATIONS"] = 0
                    character["rStats"]["PASSIVE_TRAIT_ACTIVATIONS"] += 1
                
                return True
            
            return False
            
        except Exception as e:
            self.logger.error("Error applying morale defense: {}".format(e))
            self._emit_error_event("apply_morale_defense", str(e), {
                "character_id": character.get("id", "unknown"),
                "trait_id": trait_id
            })
            return False
    
    def _apply_board_position_effect(self, character: Dict[str, Any], trait_id: str,
                                    trait_info: Dict[str, Any], event_data: Dict[str, Any]) -> bool:
        """
        Apply board position effect
        
        Args:
            character: Character dictionary
            trait_id: Trait ID
            trait_info: Trait info dictionary
            event_data: Event data
            
        Returns:
            True if effect was applied, False otherwise
        """
        try:
            formula_expr = trait_info.get("formula_expr")
            if not formula_expr or not formula_expr.endswith("%"):
                return False
                
            # Parse boost percentage
            boost_percent = float(formula_expr.rstrip("%").lstrip("+")) / 100.0
            
            # Apply to zone control
            if "zone_control_boost" not in character:
                character["zone_control_boost"] = 0.0
            character["zone_control_boost"] += boost_percent
            
            # Count as trait activation
            self.trait_activations[trait_id] += 1
            
            # Update character trait activation count
            if "traits" in character and trait_id in character["traits"]:
                if "activations" not in character["traits"][trait_id]:
                    character["traits"][trait_id]["activations"] = 0
                character["traits"][trait_id]["activations"] += 1
            
            # Update rStats
            if "rStats" in character:
                if "PASSIVE_TRAIT_ACTIVATIONS" not in character["rStats"]:
                    character["rStats"]["PASSIVE_TRAIT_ACTIVATIONS"] = 0
                character["rStats"]["PASSIVE_TRAIT_ACTIVATIONS"] += 1
            
            return True
            
        except Exception as e:
            self.logger.error("Error applying board position effect: {}".format(e))
            self._emit_error_event("apply_board_position_effect", str(e), {
                "character_id": character.get("id", "unknown"),
                "trait_id": trait_id
            })
            return False
    
    def _apply_adjacent_ally_effect(self, character: Dict[str, Any], trait_id: str,
                                   trait_info: Dict[str, Any], event_data: Dict[str, Any]) -> bool:
        """
        Apply adjacent ally effect
        
        Args:
            character: Character dictionary
            trait_id: Trait ID
            trait_info: Trait info dictionary
            event_data: Event data
            
        Returns:
            True if effect was applied, False otherwise
        """
        try:
            formula_expr = trait_info.get("formula_expr")
            if not formula_expr or not formula_expr.endswith("%"):
                return False
                
            # Parse share percentage
share_percent = float(formula_expr.rstrip("%")) / 100.0
            
            # Get board positions
            board_position = event_data.get("board_position")
            if not board_position:
                return False
                
            # Get adjacent ally positions
            match_context = event_data.get("match_context", {})
            team_data = match_context.get("team_data", {})
            
            if not team_data:
                return False
                
            # Get character's team
            character_id = character.get("id")
            character_team = None
            
            for team_id, team_chars in team_data.items():
                if character_id in team_chars:
                    character_team = team_id
                    break
            
            if not character_team:
                return False
                
            # Find adjacent allies
            adjacent_allies = []
            
            for team_char_id in team_data.get(character_team, []):
                if team_char_id == character_id:
                    continue  # Skip self
                    
                # Find the teammate character
                teammate = None
                for char in match_context.get("characters", []):
                    if char.get("id") == team_char_id:
                        teammate = char
                        break
                
                if not teammate or teammate.get("is_ko", False):
                    continue
                    
                # Check if adjacent on board
                teammate_position = teammate.get("board_position")
                if not teammate_position:
                    continue
                    
                # Check if adjacent (simplified - real implementation would use board coordinates)
                if self._is_adjacent(board_position, teammate_position):
                    adjacent_allies.append(teammate)
            
            # If no adjacent allies, no effect
            if not adjacent_allies:
                return False
                
            # Apply stat sharing with adjacent allies
            self._apply_stat_sharing(character, adjacent_allies, share_percent)
            
            # Count as trait activation
            self.trait_activations[trait_id] += 1
            
            # Update character trait activation count
            if "traits" in character and trait_id in character["traits"]:
                if "activations" not in character["traits"][trait_id]:
                    character["traits"][trait_id]["activations"] = 0
                character["traits"][trait_id]["activations"] += 1
            
            # Update rStats
            if "rStats" in character:
                if "PASSIVE_TRAIT_ACTIVATIONS" not in character["rStats"]:
                    character["rStats"]["PASSIVE_TRAIT_ACTIVATIONS"] = 0
                character["rStats"]["PASSIVE_TRAIT_ACTIVATIONS"] += 1
            
            return True
            
        except Exception as e:
            self.logger.error("Error applying adjacent ally effect: {}".format(e))
            self._emit_error_event("apply_adjacent_ally_effect", str(e), {
                "character_id": character.get("id", "unknown"),
                "trait_id": trait_id
            })
            return False
    
    def _is_adjacent(self, position1, position2):
        """
        Check if two positions are adjacent (simplified)
        
        Args:
            position1: First position
            position2: Second position
            
        Returns:
            True if adjacent, False otherwise
        """
        # Simplified implementation - real one would use board coordinates
        # This is just a placeholder for the actual adjacency check
        return True
    
    def _apply_stat_sharing(self, character: Dict[str, Any], allies: List[Dict[str, Any]], 
                           share_percent: float) -> None:
        """
        Apply stat sharing with allies
        
        Args:
            character: Character dictionary
            allies: List of ally character dictionaries
            share_percent: Percentage of stat to share
        """
        # Find highest stat
        highest_stat = ""
        highest_value = 0
        
        for stat in ["aSTR", "aSPD", "aFS", "aLDR", "aDUR", "aRES", "aWIL"]:
            if stat in character and character[stat] > highest_value:
                highest_stat = stat
                highest_value = character[stat]
        
        # If no valid stat found, return
        if not highest_stat:
            return
            
        # Share with allies
        for ally in allies:
            # Calculate shared value
            shared_value = highest_value * share_percent
            
            # Store original value if not already stored
            orig_key = f"original_{highest_stat}"
            if highest_stat in ally and orig_key not in ally:
                ally[orig_key] = ally[highest_stat]
            
            # Apply boost
            if highest_stat in ally:
                ally[highest_stat] += shared_value
    
    def _update_move_pattern(self, character: Dict[str, Any], trait_id: str,
                            trait_info: Dict[str, Any], event_data: Dict[str, Any]) -> bool:
        """
        Update move pattern tracking
        
        Args:
            character: Character dictionary
            trait_id: Trait ID
            trait_info: Trait info dictionary
            event_data: Event data
            
        Returns:
            True if pattern was updated, False otherwise
        """
        try:
            formula_expr = trait_info.get("formula_expr")
            if not formula_expr or not formula_expr.endswith("%"):
                return False
                
            # Parse boost percentage
            boost_percent = float(formula_expr.rstrip("%").lstrip("+")) / 100.0
            
            # Get move information
            move = event_data.get("move")
            if not move:
                return False
                
            # Get move pattern key
            pattern_key = f"{trait_id}_move_pattern"
            if pattern_key not in character:
                character[pattern_key] = []
            
            # Get current pattern
            current_pattern = character[pattern_key]
            
            # Add new move
            current_pattern.append(move)
            
            # Keep only the last 3 moves
            if len(current_pattern) > 3:
                current_pattern = current_pattern[-3:]
            
            # Save updated pattern
            character[pattern_key] = current_pattern
            
            # Check pattern length
            if len(current_pattern) < 2:
                return False
                
            # Check if moves follow a pattern
            has_pattern = self._check_move_pattern(current_pattern)
            
            if has_pattern:
                # Calculate boost based on pattern length
                pattern_boost = boost_percent * (len(current_pattern) - 1)
                
                # Apply to move effectiveness
                if "move_pattern_boost" not in character:
                    character["move_pattern_boost"] = 0.0
                character["move_pattern_boost"] = pattern_boost  # Replace previous boost
                
                # Count as trait activation
                self.trait_activations[trait_id] += 1
                
                # Update character trait activation count
                if "traits" in character and trait_id in character["traits"]:
                    if "activations" not in character["traits"][trait_id]:
                        character["traits"][trait_id]["activations"] = 0
                    character["traits"][trait_id]["activations"] += 1
                
                # Update rStats
                if "rStats" in character:
                    if "PASSIVE_TRAIT_ACTIVATIONS" not in character["rStats"]:
                        character["rStats"]["PASSIVE_TRAIT_ACTIVATIONS"] = 0
                    character["rStats"]["PASSIVE_TRAIT_ACTIVATIONS"] += 1
                
                return True
            
            return False
            
        except Exception as e:
            self.logger.error("Error updating move pattern: {}".format(e))
            self._emit_error_event("update_move_pattern", str(e), {
                "character_id": character.get("id", "unknown"),
                "trait_id": trait_id
            })
            return False
    
    def _check_move_pattern(self, moves: List) -> bool:
        """
        Check if moves follow a pattern
        
        Args:
            moves: List of moves
            
        Returns:
            True if pattern detected, False otherwise
        """
        # Simplified implementation - real one would analyze move patterns
        # This is just a placeholder for the actual pattern detection
        return len(moves) >= 2
    
    def update_cooldowns(self, characters: List[Dict[str, Any]]) -> None:
        """
        Update trait cooldowns for all characters
        
        Args:
            characters: List of character dictionaries
        """
        if not self.active:
            return
            
        try:
            for character in characters:
                character_id = character.get("id")
                if not character_id:
                    continue
                    
                # Skip if not in cooldown tracking
                if character_id not in self.trait_cooldowns:
                    continue
                    
                # Update each trait cooldown
                cooldowns = self.trait_cooldowns[character_id]
                traits_off_cooldown = []
                
                for trait_id, cooldown in cooldowns.items():
                    # Reduce cooldown
                    new_cooldown = max(0, cooldown - 1)
                    cooldowns[trait_id] = new_cooldown
                    
                    # Check if cooldown expired
                    if new_cooldown == 0:
                        traits_off_cooldown.append(trait_id)
                        
                        # Get trait info
                        trait_catalog = self._get_trait_catalog()
                        trait_info = trait_catalog.get(trait_id, {})
                        trait_name = trait_info.get("name", trait_id)
                        
                        # Emit trait_cooldown_expired event
                        self._emit_event("trait_cooldown_expired", {
                            "character": character,
                            "trait_id": trait_id,
                            "trait_name": trait_name
                        })
                        
                        self.logger.debug("Trait {} cooldown expired for character {}".format(
                            trait_name, character.get("name", character_id)))
                
                # Remove expired cooldowns
                for trait_id in traits_off_cooldown:
                    del cooldowns[trait_id]
                    
                # Remove character if no cooldowns left
                if not cooldowns:
                    del self.trait_cooldowns[character_id]
                    
        except Exception as e:
            self.logger.error("Error updating trait cooldowns: {}".format(e))
            self._emit_error_event("update_cooldowns", str(e))
    
    def get_trait_activations(self) -> Dict[str, int]:
        """Get trait activation counts"""
        return dict(self.trait_activations)
    
    def get_trait_cooldowns(self) -> Dict[str, Dict[str, int]]:
        """Get trait cooldown states"""
        return {char_id: dict(cooldowns) for char_id, cooldowns in self.trait_cooldowns.items()}
    
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
        """Save persistent data for trait reactor system"""
        try:
            # Save trait activation statistics
            data_dir = self.config.get("paths.data_dir", "data")
            stats_dir = os.path.join(data_dir, "statistics")
            os.makedirs(stats_dir, exist_ok=True)
            
            stats_file = os.path.join(stats_dir, "trait_statistics.json")
            with open(stats_file, 'w') as f:
                json.dump({
                    "trait_activations": dict(self.trait_activations),
                    "timestamp": datetime.datetime.now().isoformat()
                }, f, indent=2)
                
            self.logger.info("Trait statistics saved")
        except Exception as e:
            self.logger.error("Error saving persistent data: {}".format(e))
            self._emit_error_event("save_persistent_data", str(e))
    
    def export_state(self) -> Dict[str, Any]:
        """Export state for backup"""
        return {
            "trait_activations": dict(self.trait_activations),
            "trait_cooldowns": {char_id: dict(cooldowns) for char_id, cooldowns in self.trait_cooldowns.items()},
            "active": self.active
        }