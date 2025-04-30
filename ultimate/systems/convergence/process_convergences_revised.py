"""
Convergence System for META Fantasy League Simulator
Handles board-to-board convergences and character interactions

Version: 5.1.0 - Guardian Compliant
"""

import random
import datetime
import logging
import chess
from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict

from system_base import SystemBase

class ConvergenceSystem(SystemBase):
    """
    Handles convergences between chess boards and characters
    
    Compliant with Guardian standards:
    - Event emissions via EventEmitter
    - External configuration
    - Structured logging
    - Error handling
    - System registration
    """
    
    def __init__(self, config, trait_system=None, combat_system=None):
        """Initialize the convergence system"""
        super().__init__(config)
        self.name = "convergence_system"
        self.logger = logging.getLogger("META_SIMULATOR.ConvergenceSystem")
        
        # Store dependencies
        self.trait_system = trait_system
        self.combat_system = combat_system
        
        # Cache for commonly used systems and configurations
        self._event_system = None
        self._registry = None
        self._base_convergence_chance = self.config.get("simulation.convergence_base_chance", 0.15)
        self._ldr_factor = self.config.get("simulation.convergence_ldr_factor", 0.005)
        self._esp_factor = self.config.get("simulation.convergence_esp_factor", 0.01)
        self._damage_multiplier = self.config.get("convergence_settings.convergence_damage_multiplier", 2.0)
        
        # Initialize state
        self.active = False
        self.convergence_history = []
        
        self.logger.info("Convergence system initialized with damage_multiplier={:.2f}".format(self._damage_multiplier))
    
    def activate(self):
        """Activate the convergence system"""
        self.active = True
        self.logger.info("Convergence system activated")
        return True
    
    def deactivate(self):
        """Deactivate the convergence system"""
        self.active = False
        self.logger.info("Convergence system deactivated")
        return True
    
    def is_active(self):
        """Check if the convergence system is active"""
        return self.active
    
    def _get_event_system(self):
        """Get event system from registry (lazy loading)"""
        if not self._event_system:
            if not self._registry:
                from system_registry import SystemRegistry
                self._registry = SystemRegistry()
            self._event_system = self._registry.get("event_system")
            if not self._event_system:
                self.logger.warning("Event system not available, events will not be emitted")
        return self._event_system
    
    def set_damage_multiplier(self, multiplier: float) -> None:
        """Set the convergence damage multiplier"""
        try:
            if multiplier <= 0:
                self.logger.error("Invalid damage multiplier: {}, must be positive".format(multiplier))
                return
            
            self._damage_multiplier = multiplier
            self.logger.info("Convergence damage multiplier set to {:.2f}".format(multiplier))
            
            # Emit configuration changed event
            event_system = self._get_event_system()
            if event_system:
                event_system.emit("config_changed", {
                    "system": self.name,
                    "parameter": "damage_multiplier",
                    "old_value": None,  # Cannot track previous value in this context
                    "new_value": multiplier,
                    "source": "set_damage_multiplier"
                })
        except Exception as e:
            self.logger.error("Error setting damage multiplier: {}".format(e))
            # Emit error event
            self._emit_error_event("set_damage_multiplier", str(e))
    
    def process_convergences(self, team_a: List[Dict[str, Any]], team_a_boards: List[chess.Board],
                          team_b: List[Dict[str, Any]], team_b_boards: List[chess.Board],
                          match_context: Dict[str, Any], max_per_char: int = 3) -> List[Dict[str, Any]]:
        """
        Process convergences between boards
        
        Args:
            team_a: Team A characters
            team_a_boards: Team A chess boards
            team_b: Team B characters
            team_b_boards: Team B chess boards
            match_context: Match context data
            max_per_char: Maximum convergences per character
            
        Returns:
            List of convergence records
        """
        if not self.active:
            self.logger.warning("Convergence system not active, skipping convergence processing")
            return []
        
        try:
            self.logger.info("Processing convergences for round {}".format(match_context.get('round', 0)))
            
            # Emit process_start event
            self._emit_event("process_convergences_start", {
                "match_id": match_context.get("match_id", "unknown"),
                "round": match_context.get("round", 0),
                "team_a_count": len(team_a),
                "team_b_count": len(team_b),
                "max_per_char": max_per_char
            })
            
            # Track convergences by character to enforce max_per_char
            convergence_counts = defaultdict(int)
            
            # Track all convergences for reporting
            all_convergences = []
            
            # Process team A convergences
            team_a_convergences = self._process_team_convergences(
                team_a, team_a_boards, "A", convergence_counts, max_per_char, match_context
            )
            all_convergences.extend(team_a_convergences)
            
            # Process team B convergences
            team_b_convergences = self._process_team_convergences(
                team_b, team_b_boards, "B", convergence_counts, max_per_char, match_context
            )
            all_convergences.extend(team_b_convergences)
            
            # Update convergence history
            self.convergence_history.extend(all_convergences)
            
            # Update match context with convergence logs
            if "convergence_logs" in match_context:
                match_context["convergence_logs"].extend(all_convergences)
            else:
                match_context["convergence_logs"] = all_convergences
            
            # Emit process_complete event
            self._emit_event("process_convergences_complete", {
                "match_id": match_context.get("match_id", "unknown"),
                "round": match_context.get("round", 0),
                "convergence_count": len(all_convergences),
                "team_a_count": len(team_a_convergences),
                "team_b_count": len(team_b_convergences)
            })
            
            self.logger.info("Processed {} convergences (Team A: {}, Team B: {})".format(
                len(all_convergences), len(team_a_convergences), len(team_b_convergences)
            ))
            
            # Return all convergences processed
            return all_convergences
            
        except Exception as e:
            self.logger.error("Error processing convergences: {}".format(e))
            # Emit error event
            self._emit_error_event("process_convergences", str(e))
            return []
    
    def _process_team_convergences(self, team: List[Dict[str, Any]], team_boards: List[chess.Board],
                                  team_id: str, convergence_counts: Dict[str, int],
                                  max_per_char: int, match_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Process convergences for a single team
        
        Args:
            team: Team characters
            team_boards: Team chess boards
            team_id: Team identifier (A or B)
            convergence_counts: Dictionary tracking convergences per character
            max_per_char: Maximum convergences per character
            match_context: Match context data
            
        Returns:
            List of convergence records for this team
        """
        team_convergences = []
        
        for i, (char, board) in enumerate(zip(team, team_boards)):
            try:
                # Skip knocked out or inactive characters
                if char.get("is_ko", False) or not char.get("is_active", True):
                    continue
                
                # Skip if already at max convergences
                if convergence_counts.get(char.get("id")) >= max_per_char:
                    continue
                
                # Check for pre-convergence traits
                if self.trait_system:
                    self.trait_system.check_pre_convergence_traits(char, board, match_context)
                
                # Calculate convergence chance
                convergence_chance = self._calculate_convergence_chance(char)
                
                # Roll for convergence
                if random.random() <= convergence_chance:
                    # Attempt to find a convergence target
                    convergence_result = self._attempt_convergence(
                        char, i, team, team_boards, team_id, convergence_counts, max_per_char, match_context
                    )
                    
                    if convergence_result:
                        team_convergences.append(convergence_result)
            
            except Exception as e:
                self.logger.error("Error processing convergence for character {}: {}".format(
                    char.get("id", "unknown"), e
                ))
                # Emit error event
                self._emit_error_event("process_team_convergences", str(e), {
                    "character_id": char.get("id", "unknown"),
                    "character_name": char.get("name", "Unknown"),
                    "team": team_id
                })
        
        return team_convergences
    
    def _calculate_convergence_chance(self, char: Dict[str, Any]) -> float:
        """Calculate the chance of a character initiating a convergence"""
        try:
            # Start with base chance from config
            base_chance = self._base_convergence_chance
            
            # Apply LDR bonus
            ldr_bonus = char.get("aLDR", 0) * self._ldr_factor
            
            # Apply ESP bonus
            esp_bonus = char.get("aESP", 0) * self._esp_factor
            
            # Calculate total chance
            convergence_chance = base_chance + ldr_bonus + esp_bonus
            
            # Apply convergence traits if any
            if self.trait_system:
                convergence_chance = self.trait_system.apply_convergence_chance_traits(char, convergence_chance)
            
            # Ensure chance is within valid range [0, 1]
            convergence_chance = max(0.0, min(1.0, convergence_chance))
            
            return convergence_chance
            
        except Exception as e:
            self.logger.error("Error calculating convergence chance: {}".format(e))
            # Emit error event
            self._emit_error_event("calculate_convergence_chance", str(e), {
                "character_id": char.get("id", "unknown"),
                "character_name": char.get("name", "Unknown")
            })
            
            # Return default chance on error
            return self._base_convergence_chance
    
    def _attempt_convergence(self, initiator: Dict[str, Any], initiator_idx: int,
                            team: List[Dict[str, Any]], team_boards: List[chess.Board],
                            team_id: str, convergence_counts: Dict[str, int],
                            max_per_char: int, match_context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Attempt to find a valid target and execute a convergence
        
        Args:
            initiator: Character initiating the convergence
            initiator_idx: Index of initiator in team list
            team: Team characters
            team_boards: Team chess boards
            team_id: Team identifier (A or B)
            convergence_counts: Dictionary tracking convergences per character
            max_per_char: Maximum convergences per character
            match_context: Match context data
            
        Returns:
            Convergence record if successful, None otherwise
        """
        try:
            # Select a valid target for convergence
            valid_targets = []
            
            for j, (target, board_b) in enumerate(zip(team, team_boards)):
                # Cannot converge with self
                if initiator_idx == j:
                    continue
                
                # Cannot converge with KO'd or inactive characters
                if target.get("is_ko", False) or not target.get("is_active", True):
                    continue
                
                # Cannot converge with characters already at max
                if convergence_counts.get(target.get("id")) >= max_per_char:
                    continue
                
                # Check for compatibility
                if self._check_convergence_compatibility(initiator, target):
                    valid_targets.append((j, target, board_b))
            
            # If no valid targets found, return None
            if not valid_targets:
                return None
            
            # Select a random target from valid targets
            target_idx, target_char, target_board = random.choice(valid_targets)
            
            # Apply convergence effect
            convergence_effect = self._calculate_convergence_effect(initiator, target_char)
            self._apply_convergence(initiator, target_char, convergence_effect, match_context)
            
            # Increment convergence counts
            convergence_counts[initiator.get("id")] = convergence_counts.get(initiator.get("id"), 0) + 1
            convergence_counts[target_char.get("id")] = convergence_counts.get(target_char.get("id"), 0) + 1
            
            # Create convergence record
            convergence_record = {
                "round": match_context.get("round", 0),
                "initiator_id": initiator.get("id", "unknown"),
                "initiator_name": initiator.get("name", "Unknown"),
                "target_id": target_char.get("id", "unknown"),
                "target_name": target_char.get("name", "Unknown"), 
                "team": team_id,
                "effect": convergence_effect,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            self.logger.info("Convergence: {} -> {}, effect: {}".format(
                initiator.get("name", "Unknown"),
                target_char.get("name", "Unknown"),
                convergence_effect
            ))
            
            # Emit convergence events
            self._emit_convergence_events(initiator, target_char, convergence_effect, match_context)
            
            # Check for post-convergence traits
            if self.trait_system:
                self.trait_system.check_post_convergence_traits(initiator, target_char, match_context)
            
            return convergence_record
            
        except Exception as e:
            self.logger.error("Error attempting convergence: {}".format(e))
            # Emit error event
            self._emit_error_event("attempt_convergence", str(e), {
                "initiator_id": initiator.get("id", "unknown"),
                "initiator_name": initiator.get("name", "Unknown"),
                "team": team_id
            })
            return None
    
    def _check_convergence_compatibility(self, char_a: Dict[str, Any], char_b: Dict[str, Any]) -> bool:
        """Check if two characters are compatible for convergence"""
        try:
            # Basic compatibility check (can be extended with more rules)
            # For now, just ensure they have compatible types or roles
            
            # Example: Check primary_type compatibility
            type_a = char_a.get("primary_type", "").lower()
            type_b = char_b.get("primary_type", "").lower()
            
            # Example compatible types (can be moved to configuration)
            compatible_types = {
                "fire": ["air", "fire"],
                "water": ["earth", "water"],
                "air": ["fire", "air"],
                "earth": ["water", "earth"],
                "light": ["light", "cosmic"],
                "dark": ["dark", "void"],
                "cosmic": ["light", "cosmic"],
                "void": ["dark", "void"],
                # Default compatibility with same type
                "": [""]
            }
            
            # Check if types are compatible
            if type_b in compatible_types.get(type_a, []) or type_a in compatible_types.get(type_b, []):
                return True
            
            # Check role compatibility if type compatibility fails
            role_a = char_a.get("role", "").lower()
            role_b = char_b.get("role", "").lower()
            
            # Example compatible roles (can be moved to configuration)
            compatible_roles = {
                "tank": ["support", "damage"],
                "damage": ["tank", "control"],
                "support": ["tank", "control"],
                "control": ["damage", "support"],
                # Default compatibility with same role
                "": [""]
            }
            
            # Check if roles are compatible
            if role_b in compatible_roles.get(role_a, []) or role_a in compatible_roles.get(role_b, []):
                return True
            
            # If all checks fail, return False
            return False
            
        except Exception as e:
            self.logger.error("Error checking convergence compatibility: {}".format(e))
            # Emit error event
            self._emit_error_event("check_convergence_compatibility", str(e), {
                "char_a_id": char_a.get("id", "unknown"),
                "char_b_id": char_b.get("id", "unknown")
            })
            
            # Default to False on error
            return False
    
    def _calculate_convergence_effect(self, initiator: Dict[str, Any], target: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate the effect of a convergence between two characters"""
        try:
            # Base effect
            effect = {
                "type": "healing",  # Default to healing
                "value": 0,
                "stat_buffs": {},
                "duration": 1  # Default duration in rounds
            }
            
            # Determine effect type based on character roles
            initiator_role = initiator.get("role", "").lower()
            target_role = target.get("role", "").lower()
            
            # Support to Tank = Healing
            if initiator_role == "support" and target_role == "tank":
                effect["type"] = "healing"
                effect["value"] = 10 + (initiator.get("aWIL", 0) * 0.2)
                
            # Support to Damage = Damage Buff
            elif initiator_role == "support" and target_role == "damage":
                effect["type"] = "stat_buff"
                effect["stat_buffs"]["aSTR"] = 5 + (initiator.get("aLDR", 0) * 0.1)
                effect["duration"] = 2
                
            # Damage to Tank = Protection Buff
            elif initiator_role == "damage" and target_role == "tank":
                effect["type"] = "stat_buff"
                effect["stat_buffs"]["aDUR"] = 5 + (initiator.get("aFS", 0) * 0.1)
                effect["duration"] = 2
                
            # Tank to Support = Stamina Regen
            elif initiator_role == "tank" and target_role == "support":
                effect["type"] = "stamina_regen"
                effect["value"] = 15 + (initiator.get("aDUR", 0) * 0.2)
                
            # Default effect based on initiator stats
            else:
                effect["type"] = "healing"
                effect["value"] = 5 + (initiator.get("aWIL", 0) * 0.1)
            
            # Apply convergence damage multiplier for damage effects
            if effect["type"] == "damage":
                effect["value"] *= self._damage_multiplier
            
            # Round numeric values
            effect["value"] = round(effect["value"], 1)
            for stat, value in effect["stat_buffs"].items():
                effect["stat_buffs"][stat] = round(value, 1)
            
            return effect
            
        except Exception as e:
            self.logger.error("Error calculating convergence effect: {}".format(e))
            # Emit error event
            self._emit_error_event("calculate_convergence_effect", str(e), {
                "initiator_id": initiator.get("id", "unknown"),
                "target_id": target.get("id", "unknown")
            })
            
            # Return minimal effect on error
            return {
                "type": "healing",
                "value": 5,
                "stat_buffs": {},
                "duration": 1
            }
    
    def _apply_convergence(self, initiator: Dict[str, Any], target: Dict[str, Any], 
                          effect: Dict[str, Any], match_context: Dict[str, Any]) -> None:
        """Apply convergence effect to target character"""
        try:
            effect_type = effect.get("type", "healing")
            effect_value = effect.get("value", 0)
            stat_buffs = effect.get("stat_buffs", {})
            effect_duration = effect.get("duration", 1)
            
            # Apply effect based on type
            if effect_type == "healing":
                # Add HP to target
                target_hp = target.get("HP", 100)
                new_hp = min(100, target_hp + effect_value)
                target["HP"] = new_hp
                
                self.logger.debug("Applied healing effect: {} -> {}, +{} HP".format(
                    initiator.get("name", "Unknown"),
                    target.get("name", "Unknown"),
                    effect_value
                ))
                
            elif effect_type == "stat_buff":
                # Apply stat buffs to target
                for stat, value in stat_buffs.items():
                    if stat in target:
                        # Store original value if not already stored
                        orig_key = f"original_{stat}"
                        if orig_key not in target:
                            target[orig_key] = target[stat]
                        
                        # Apply buff
                        target[stat] += value
                        
                        # Store buff duration
                        target[f"{stat}_buff_duration"] = effect_duration
                        
                        self.logger.debug("Applied stat buff: {} -> {}, +{} {}".format(
                            initiator.get("name", "Unknown"),
                            target.get("name", "Unknown"),
                            value,
                            stat
                        ))
                
            elif effect_type == "stamina_regen":
                # Add stamina to target
                target_stamina = target.get("stamina", 100)
                new_stamina = min(100, target_stamina + effect_value)
                target["stamina"] = new_stamina
                
                self.logger.debug("Applied stamina regen: {} -> {}, +{} stamina".format(
                    initiator.get("name", "Unknown"),
                    target.get("name", "Unknown"),
                    effect_value
                ))
            
            # Additional effects can be added here
            
        except Exception as e:
            self.logger.error("Error applying convergence effect: {}".format(e))
            # Emit error event
            self._emit_error_event("apply_convergence", str(e), {
                "initiator_id": initiator.get("id", "unknown"),
                "target_id": target.get("id", "unknown"),
                "effect_type": effect.get("type", "unknown")
            })
    
    def _emit_convergence_events(self, initiator: Dict[str, Any], target: Dict[str, Any],
                               effect: Dict[str, Any], match_context: Dict[str, Any]) -> None:
        """Emit events related to convergence"""
        event_system = self._get_event_system()
        if not event_system:
            return
        
        try:
            # Emit convergence_triggered event for the initiator
            event_system.emit("convergence_triggered", {
                "character": initiator,
                "target": target,
                "match_context": match_context,
                "effect": effect,
                "result": "success"
            })
            
            # Emit assist_given event for the initiator
            event_system.emit("assist_given", {
                "character": initiator,
                "target": target,
                "match_context": match_context,
                "effect": effect,
                "type": "convergence"
            })
            
            # Emit convergence_received event for the target
            event_system.emit("convergence_received", {
                "character": target,
                "source": initiator,
                "match_context": match_context,
                "effect": effect
            })
            
            # Emit specialized events based on effect type
            effect_type = effect.get("type")
            if effect_type == "healing":
                event_system.emit("healing_received", {
                    "character": target,
                    "source": initiator,
                    "match_context": match_context,
                    "amount": effect.get("value", 0),
                    "type": "convergence"
                })
            elif effect_type == "stat_buff":
                event_system.emit("buff_applied", {
                    "character": target,
                    "source": initiator,
                    "match_context": match_context,
                    "buffs": effect.get("stat_buffs", {}),
                    "duration": effect.get("duration", 1),
                    "type": "convergence"
                })
            elif effect_type == "stamina_regen":
                event_system.emit("stamina_restored", {
                    "character": target,
                    "source": initiator,
                    "match_context": match_context,
                    "amount": effect.get("value", 0),
                    "type": "convergence"
                })
                
        except Exception as e:
            self.logger.error("Error emitting convergence events: {}".format(e))
            # Emit error event
            self._emit_error_event("emit_convergence_events", str(e), {
                "initiator_id": initiator.get("id", "unknown"),
                "target_id": target.get("id", "unknown")
            })
    
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
        """Save persistent data for the convergence system"""
        # No persistent data needed for convergence system
        pass
    
    def export_state(self) -> Dict[str, Any]:
        """Export state for backup"""
        return {
            "damage_multiplier": self._damage_multiplier,
            "active": self.active,
            "convergence_history_count": len(self.convergence_history)
        }
