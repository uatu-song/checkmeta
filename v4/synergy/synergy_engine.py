"""
META Fantasy League Simulator - Synergy Engine
Handles team synergies, character dynamics, and relationship effects
"""

import os
import json
import random
import csv
import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from collections import defaultdict

logger = logging.getLogger("SynergyEngine")

class SynergyEngine:
    """System for managing team synergies, trait interactions, and character dynamics"""
    
    def __init__(self, trait_system=None, config=None):
        """Initialize the synergy engine
        
        Args:
            trait_system: Optional reference to trait system
            config: Optional configuration
        """
        self.trait_system = trait_system
        self.config = config
        
        # Dictionary of defined synergies
        self.synergies = self._load_synergies()
        
        # Track synergy activations
        self.activation_counts = defaultdict(int)
        
        # Track active team synergies
        self.active_synergies = {}
        
        # Track convergence relationships between characters
        self.convergence_history = defaultdict(list)
        
        # Track dynamic bonuses between characters
        self.dynamic_bonuses = {}
        
        logger.info(f"SynergyEngine initialized with {len(self.synergies)} synergy definitions")
    
    def _load_synergies(self) -> Dict[str, Dict[str, Any]]:
        """Load synergy definitions
        
        Returns:
            dict: Dictionary of synergy definitions
        """
        synergies = {}
        
        # Try to load from file if config is available
        if self.config and hasattr(self.config, "paths"):
            synergy_file = self.config.paths.get("synergy_file")
            if synergy_file and os.path.exists(synergy_file):
                try:
                    with open(synergy_file, 'r') as f:
                        synergies = json.load(f)
                    logger.info(f"Loaded {len(synergies)} synergies from {synergy_file}")
                    return synergies
                except Exception as e:
                    logger.error(f"Error loading synergies from file: {e}")
        
        # Define default synergies programmatically
        synergies = {
            # Role combinations (Operations)
            "vanguard_enforcer": {
                "name": "Frontline Dominance",
                "type": "role_combo",
                "requirements": {
                    "roles": ["VG", "EN"],
                    "count": 2
                },
                "effects": [
                    {"target": "role", "roles": ["VG", "EN"], "stat": "aSTR", "bonus": 1},
                    {"target": "role", "roles": ["VG", "EN"], "stat": "damage_reduction", "bonus": 5}
                ],
                "description": "Vanguard and Enforcer units gain +1 Strength and 5% damage reduction"
            },
            
            "leaders_command": {
                "name": "Leader's Command",
                "type": "role_combo",
                "requirements": {
                    "roles": ["FL", "VG"],
                    "count": 2
                },
                "effects": [
                    {"target": "role", "roles": ["FL"], "stat": "aLDR", "bonus": 1},
                    {"target": "role", "roles": ["VG"], "stat": "aSTR", "bonus": 1}
                ],
                "description": "Field Leader gains +1 Leadership and Vanguard gains +1 Strength"
            },
            
            # Role combinations (Intelligence)
            "ranger_ghost": {
                "name": "Stealth Operations",
                "type": "role_combo",
                "requirements": {
                    "roles": ["RG", "GO"],
                    "count": 2
                },
                "effects": [
                    {"target": "role", "roles": ["RG", "GO"], "stat": "aSPD", "bonus": 1},
                    {"target": "role", "roles": ["RG", "GO"], "stat": "evasion", "bonus": 10}
                ],
                "description": "Ranger and Ghost Operative units gain +1 Speed and 10% evasion chance"
            },
            
            "psi_sovereign": {
                "name": "Mental Dominance",
                "type": "role_combo",
                "requirements": {
                    "roles": ["PO", "SV"],
                    "count": 2
                },
                "effects": [
                    {"target": "role", "roles": ["PO", "SV"], "stat": "aWIL", "bonus": 1},
                    {"target": "role", "roles": ["PO", "SV"], "stat": "aOP", "bonus": 1}
                ],
                "description": "Psi Operative and Sovereign gain +1 Willpower and +1 Operant Potential"
            },
            
            # Character trait synergies
            "tactical_genius": {
                "name": "Strategic Brilliance",
                "type": "trait_combo",
                "requirements": {
                    "traits": ["genius", "tactical"],
                    "count": 1,  # Number of characters that need both traits
                    "character_count": 1
                },
                "effects": [
                    {"target": "character", "stat": "aFS", "bonus": 2},
                    {"target": "character", "stat": "combat_bonus", "bonus": 15}
                ],
                "description": "Characters with both Tactical and Genius traits gain +2 Focus/Speed and +15 to combat rolls"
            },
            
            "defense_specialists": {
                "name": "Defense Specialists",
                "type": "trait_combo",
                "requirements": {
                    "traits": ["armor", "shield"],
                    "count": 1,
                    "character_count": 1
                },
                "effects": [
                    {"target": "character", "stat": "aDUR", "bonus": 1},
                    {"target": "character", "stat": "damage_reduction", "bonus": 15}
                ],
                "description": "Characters with both Armor and Shield traits gain +1 Durability and 15% damage reduction"
            },
            
            "mobility_masters": {
                "name": "Mobility Masters",
                "type": "trait_combo",
                "requirements": {
                    "traits": ["agile", "stretchy"],
                    "count": 1,
                    "character_count": 1
                },
                "effects": [
                    {"target": "character", "stat": "aSPD", "bonus": 2},
                    {"target": "character", "stat": "evasion", "bonus": 20}
                ],
                "description": "Characters with both Agile and Stretchy traits gain +2 Speed and 20% evasion chance"
            },
            
            "prescient_defense": {
                "name": "Prescient Defense",
                "type": "trait_combo",
                "requirements": {
                    "traits": ["spider-sense", "shield"],
                    "count": 1,
                    "character_count": 1
                },
                "effects": [
                    {"target": "character", "stat": "aFS", "bonus": 1},
                    {"target": "character", "stat": "damage_reduction", "bonus": 10}
                ],
                "description": "Characters with both Spider-Sense and Shield traits gain +1 Focus/Speed and 10% damage reduction"
            },
            
            # Division synergies
            "balanced_forces": {
                "name": "Balanced Forces",
                "type": "division_balance",
                "requirements": {
                    "operations_min": 3,
                    "intelligence_min": 3
                },
                "effects": [
                    {"target": "team", "stat": "morale_regen", "bonus": 5},
                    {"target": "team", "stat": "trait_activation", "bonus": 0.1}
                ],
                "description": "Teams with at least 3 characters from each division gain increased morale regeneration and trait activation chance"
            },
            
            "operations_specialists": {
                "name": "Operations Specialists",
                "type": "division_focus",
                "requirements": {
                    "operations_min": 5
                },
                "effects": [
                    {"target": "division", "division": "o", "stat": "aSTR", "bonus": 1},
                    {"target": "division", "division": "o", "stat": "aDUR", "bonus": 1}
                ],
                "description": "Teams with at least 5 Operations division characters gain +1 Strength and +1 Durability for all Operations characters"
            },
            
            "intelligence_specialists": {
                "name": "Intelligence Specialists",
                "type": "division_focus",
                "requirements": {
                    "intelligence_min": 5
                },
                "effects": [
                    {"target": "division", "division": "i", "stat": "aFS", "bonus": 1},
                    {"target": "division", "division": "i", "stat": "aWIL", "bonus": 1}
                ],
                "description": "Teams with at least 5 Intelligence division characters gain +1 Focus/Speed and +1 Willpower for all Intelligence characters"
            },
            
            # Field Leader synergies
            "inspiring_leader": {
                "name": "Inspiring Leadership",
                "type": "leader_aura",
                "requirements": {
                    "role": "FL",
                    "stat": "aLDR",
                    "min_value": 7
                },
                "effects": [
                    {"target": "aura", "range": "all", "stat": "morale", "bonus": 10},
                    {"target": "aura", "range": "all", "stat": "trait_activation", "bonus": 0.05}
                ],
                "description": "Field Leaders with 7+ Leadership provide morale and trait activation bonuses to all team members"
            },
            
            "tactical_coordination": {
                "name": "Tactical Coordination",
                "type": "leader_trait",
                "requirements": {
                    "role": "FL",
                    "traits": ["tactical"]
                },
                "effects": [
                    {"target": "aura", "range": "all", "stat": "combat_bonus", "bonus": 10}
                ],
                "description": "Field Leaders with the Tactical trait provide +10 combat bonus to all team members"
            }
        }
        
        logger.info(f"Using {len(synergies)} default synergy definitions")
        return synergies
    
    def detect_team_synergies(self, team: List[Dict[str, Any]], team_id: str) -> List[Dict[str, Any]]:
        """Detect active synergies for a team
        
        Args:
            team: List of team characters
            team_id: Team identifier
            
        Returns:
            list: Active synergies and their effects
        """
        active_synergies = []
        
        # Check each synergy definition
        for synergy_id, synergy in self.synergies.items():
            if self._check_synergy_requirements(team, synergy):
                # Add to active synergies
                active_synergies.append({
                    "id": synergy_id,
                    "name": synergy["name"],
                    "type": synergy["type"],
                    "effects": synergy["effects"]
                })
                
                # Track activation
                self.activation_counts[synergy_id] += 1
        
        # Store active synergies
        self.active_synergies[team_id] = active_synergies
        
        logger.info(f"Team {team_id}: Detected {len(active_synergies)} active synergies")
        return active_synergies
    
    def _check_synergy_requirements(self, team: List[Dict[str, Any]], synergy: Dict[str, Any]) -> bool:
        """Check if a team meets synergy requirements
        
        Args:
            team: List of team characters
            synergy: Synergy definition
            
        Returns:
            bool: True if requirements are met
        """
        req = synergy["requirements"]
        synergy_type = synergy["type"]
        
        if synergy_type == "role_combo":
            # Count characters with required roles
            role_counts = defaultdict(int)
            for char in team:
                if char.get("role") in req["roles"]:
                    role_counts[char.get("role")] += 1
            
            # Check if we have enough of each required role
            for role in req["roles"]:
                if role_counts[role] < req.get("count", 1):
                    return False
            
            return True
            
        elif synergy_type == "trait_combo":
            # Count characters with all required traits
            char_count = 0
            for char in team:
                has_all_traits = all(trait in char.get("traits", []) for trait in req["traits"])
                if has_all_traits:
                    char_count += 1
            
            return char_count >= req.get("character_count", 1)
            
        elif synergy_type == "division_balance":
            # Count characters in each division
            operations_count = sum(1 for char in team if char.get("division") == "o")
            intelligence_count = sum(1 for char in team if char.get("division") == "i")
            
            return (operations_count >= req.get("operations_min", 0) and 
                    intelligence_count >= req.get("intelligence_min", 0))
            
        elif synergy_type == "division_focus":
            # Check if we have minimum required characters in a specific division
            if "operations_min" in req:
                operations_count = sum(1 for char in team if char.get("division") == "o")
                return operations_count >= req["operations_min"]
            elif "intelligence_min" in req:
                intelligence_count = sum(1 for char in team if char.get("division") == "i")
                return intelligence_count >= req["intelligence_min"]
            
            return False
                    
        elif synergy_type == "leader_aura":
            # Find Field Leaders meeting stat requirements
            for char in team:
                if char.get("role") == req.get("role") and char.get(req.get("stat"), 0) >= req.get("min_value", 0):
                    return True
            
            return False
            
        elif synergy_type == "leader_trait":
            # Check if Field Leader has required traits
            for char in team:
                if char.get("role") == req.get("role"):
                    # Check traits
                    if "traits" in req:
                        has_traits = all(trait in char.get("traits", []) for trait in req["traits"])
                        return has_traits
            
            return False
            
        # Unknown synergy type
        return False
    
    def apply_synergy_effects(self, team: List[Dict[str, Any]], team_id: str) -> None:
        """Apply synergy effects to team characters
        
        Args:
            team: List of team characters
            team_id: Team identifier
        """
        # Get active synergies
        if team_id not in self.active_synergies:
            # Detect synergies if not already done
            self.detect_team_synergies(team, team_id)
        
        active_synergies = self.active_synergies.get(team_id, [])
        
        # Process each synergy
        for synergy in active_synergies:
            for effect in synergy["effects"]:
                target_type = effect["target"]
                
                if target_type == "role":
                    # Apply to characters with specific roles
                    roles = effect.get("roles", [])
                    for char in team:
                        if char.get("role") in roles:
                            self._apply_effect_to_character(char, effect, synergy["name"])
                
                elif target_type == "character":
                    # Apply to characters that triggered the synergy
                    if "trait_combo" in synergy["type"]:
                        # For trait combos, apply to characters with all required traits
                        required_traits = self.synergies[synergy["id"]]["requirements"]["traits"]
                        for char in team:
                            if all(trait in char.get("traits", []) for trait in required_traits):
                                self._apply_effect_to_character(char, effect, synergy["name"])
                
                elif target_type == "team":
                    # Apply to all team members
                    for char in team:
                        self._apply_effect_to_character(char, effect, synergy["name"])
                
                elif target_type == "division":
                    # Apply to characters in a specific division
                    division = effect.get("division", "")
                    for char in team:
                        if char.get("division") == division:
                            self._apply_effect_to_character(char, effect, synergy["name"])
                
                elif target_type == "aura":
                    # Find the leader first
                    leaders = [char for char in team if char.get("role") == "FL"]
                    if not leaders:
                        continue
                    
                    # Apply aura based on range
                    effect_range = effect.get("range", "all")
                    if effect_range == "all":
                        for char in team:
                            self._apply_effect_to_character(char, effect, synergy["name"])
        
        logger.debug(f"Applied synergy effects for team {team_id}")
    
    def _apply_effect_to_character(self, character: Dict[str, Any], effect: Dict[str, Any], synergy_name: str) -> None:
        """Apply a synergy effect to a character
        
        Args:
            character: Character to apply effect to
            effect: Effect definition
            synergy_name: Name of the synergy (for logging)
        """
        stat = effect.get("stat", "")
        bonus = effect.get("bonus", 0)
        
        # Initialize synergy bonuses if not present
        if "synergy_bonuses" not in character:
            character["synergy_bonuses"] = {}
        
        # Record synergy source
        if "synergy_sources" not in character:
            character["synergy_sources"] = {}
        
        # Handle different stat types
        if stat.startswith("a"):  # Attribute
            # For attributes, we record the bonus but don't directly modify the base attribute
            # The combat system will apply these bonuses when needed
            character["synergy_bonuses"][stat] = character["synergy_bonuses"].get(stat, 0) + bonus
            character["synergy_sources"][stat] = synergy_name
            
        elif stat == "damage_reduction":
            character["synergy_bonuses"]["damage_reduction"] = character["synergy_bonuses"].get("damage_reduction", 0) + bonus
            character["synergy_sources"]["damage_reduction"] = synergy_name
            
        elif stat == "evasion":
            character["synergy_bonuses"]["evasion"] = character["synergy_bonuses"].get("evasion", 0) + bonus
            character["synergy_sources"]["evasion"] = synergy_name
            
        elif stat == "combat_bonus":
            character["synergy_bonuses"]["combat_bonus"] = character["synergy_bonuses"].get("combat_bonus", 0) + bonus
            character["synergy_sources"]["combat_bonus"] = synergy_name
            
        elif stat == "morale":
            # Directly apply morale bonus (capped at 100)
            character["morale"] = min(100, character.get("morale", 50) + bonus)
            
        elif stat == "trait_activation":
            character["synergy_bonuses"]["trait_activation"] = character["synergy_bonuses"].get("trait_activation", 0) + bonus
            character["synergy_sources"]["trait_activation"] = synergy_name
            
        elif stat == "morale_regen":
            character["synergy_bonuses"]["morale_regen"] = character["synergy_bonuses"].get("morale_regen", 0) + bonus
            character["synergy_sources"]["morale_regen"] = synergy_name
    
    def record_convergence_interaction(self, char_a: Dict[str, Any], char_b: Dict[str, Any], 
                                    result: str, damage: float = 0) -> None:
        """Record a convergence interaction between characters
        
        Args:
            char_a: First character
            char_b: Second character
            result: Interaction result ('win', 'loss', 'draw')
            damage: Amount of damage dealt
        """
        # Get character IDs
        char_a_id = char_a.get("id", "unknown")
        char_b_id = char_b.get("id", "unknown")
        
        # Record interaction for both characters
        interaction = {
            "a_id": char_a_id,
            "b_id": char_b_id,
            "result": result,
            "damage": damage,
            "a_team": char_a.get("team_id", "unknown"),
            "b_team": char_b.get("team_id", "unknown")
        }
        
        self.convergence_history[char_a_id].append(interaction)
        self.convergence_history[char_b_id].append(interaction)
        
        # Update dynamic relationship
        self._update_dynamic_relationship(char_a, char_b, result, damage)
    
    def _update_dynamic_relationship(self, char_a: Dict[str, Any], char_b: Dict[str, Any], 
                                    result: str, damage: float) -> None:
        """Update dynamic relationship bonuses between characters
        
        Args:
            char_a: First character
            char_b: Second character
            result: Interaction result
            damage: Amount of damage
        """
        # Get character IDs
        char_a_id = char_a.get("id", "unknown")
        char_b_id = char_b.get("id", "unknown")
        
        # Same team bonuses
        if char_a.get("team_id") == char_b.get("team_id"):
            # Initialize relationship if not exists
            key = f"{char_a_id}_{char_b_id}"
            if key not in self.dynamic_bonuses:
                self.dynamic_bonuses[key] = {
                    "combat_bonus": 0,
                    "trait_activation": 0,
                    "interactions": 0
                }
            
            # Increment interaction count
            self.dynamic_bonuses[key]["interactions"] += 1
            
            # Cap at 3 interactions for bonuses
            if self.dynamic_bonuses[key]["interactions"] <= 3:
                # Increase bonuses (small increments)
                self.dynamic_bonuses[key]["combat_bonus"] += 5
                self.dynamic_bonuses[key]["trait_activation"] += 0.02
        
        # Enemy team - track for future versions
        else:
            # This could track rivalries, nemesis relationships, etc.
            pass
    
    def apply_dynamic_bonuses(self, character: Dict[str, Any], team: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Apply dynamic relationship bonuses to a character
        
        Args:
            character: Character to apply bonuses to
            team: List of team characters
            
        Returns:
            dict: Applied bonuses
        """
        char_id = character.get("id", "unknown")
        applied_bonuses = {
            "combat_bonus": 0,
            "trait_activation": 0
        }
        
        # Apply bonuses from team relationships
        for teammate in team:
            # Skip self
            if teammate.get("id") == char_id:
                continue
                
            teammate_id = teammate.get("id", "unknown")
            
            # Check relationship in both directions
            key1 = f"{char_id}_{teammate_id}"
            key2 = f"{teammate_id}_{char_id}"
            
            relationship = None
            if key1 in self.dynamic_bonuses:
                relationship = self.dynamic_bonuses[key1]
            elif key2 in self.dynamic_bonuses:
                relationship = self.dynamic_bonuses[key2]
            
            # Apply bonuses if relationship exists
            if relationship:
                applied_bonuses["combat_bonus"] += relationship.get("combat_bonus", 0)
                applied_bonuses["trait_activation"] += relationship.get("trait_activation", 0)
        
        # Add to character's synergy bonuses
        if "synergy_bonuses" not in character:
            character["synergy_bonuses"] = {}
        
        character["synergy_bonuses"]["dynamic_combat_bonus"] = applied_bonuses["combat_bonus"]
        character["synergy_bonuses"]["dynamic_trait_activation"] = applied_bonuses["trait_activation"]
        
        return applied_bonuses
    
    def get_active_synergies_report(self, team_id: str) -> Dict[str, Any]:
        """Get a report of active synergies for a team
        
        Args:
            team_id: Team ID
            
        Returns:
            dict: Report of active synergies
        """
        if team_id not in self.active_synergies:
            return {"team_id": team_id, "synergies": []}
            
        active = self.active_synergies[team_id]
        
        return {
            "team_id": team_id,
            "synergies": [
                {
                    "name": synergy["name"],
                    "type": synergy["type"],
                    "description": self.synergies[synergy["id"]]["description"]
                }
                for synergy in active
            ]
        }
    
    def get_character_synergy_report(self, character: Dict[str, Any]) -> Dict[str, Any]:
        """Get a report of synergy effects for a character
        
        Args:
            character: Character to report on
            
        Returns:
            dict: Report of synergy effects
        """
        # Get synergy bonuses
        bonuses = character.get("synergy_bonuses", {})
        sources = character.get("synergy_sources", {})
        
        # Format report
        report = {
            "character_id": character.get("id", "unknown"),
            "character_name": character.get("name", "Unknown"),
            "active_bonuses": []
        }
        
        # Add each bonus with its source
        for stat, bonus in bonuses.items():
            source = sources.get(stat, "Unknown")
            
            # Format bonus description
            if stat.startswith("a"):  # Attribute
                attr_name = stat[1:]  # Remove 'a' prefix
                description = f"+{bonus} to {attr_name}"
            elif stat == "damage_reduction":
                description = f"{bonus}% damage reduction"
            elif stat == "evasion":
                description = f"{bonus}% evasion chance"
            elif stat == "combat_bonus":
                description = f"+{bonus} to combat rolls"
            elif stat == "trait_activation":
                description = f"+{bonus*100:.1f}% trait activation chance"
            elif stat.startswith("dynamic_"):
                base_stat = stat[8:]  # Remove 'dynamic_' prefix
                if base_stat == "combat_bonus":
                    description = f"+{bonus} to combat rolls (team dynamics)"
                elif base_stat == "trait_activation":
                    description = f"+{bonus*100:.1f}% trait activation chance (team dynamics)"
                source = "Team Dynamics"
            else:
                description = f"+{bonus} to {stat}"
            
            report["active_bonuses"].append({
                "stat": stat,
                "bonus": bonus,
                "description": description,
                "source": source
            })
        
        return report
    
    def get_team_dynamics_report(self, team: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get a report of team dynamics
        
        Args:
            team: List of team characters
            
        Returns:
            dict: Team dynamics report
        """
        # Group characters by role
        roles = defaultdict(list)
        for char in team:
            roles[char.get("role", "Unknown")].append(char.get("name", "Unknown"))
        
        # Count divisions
        operations_count = sum(1 for char in team if char.get("division") == "o")
        intelligence_count = sum(1 for char in team if char.get("division") == "i")
        
        # Get field leader
        field_leaders = [char for char in team if char.get("role") == "FL"]
        
        # Calculate team synergy score
        synergy_score = len(self.active_synergies.get(team[0].get("team_id", "unknown"), []))
        
        # Generate report
        report = {
            "team_name": team[0].get("team_name", "Unknown Team"),
            "team_id": team[0].get("team_id", "unknown"),
            "team_size": len(team),
            "roles": dict(roles),
            "operations_count": operations_count,
            "intelligence_count": intelligence_count,
            "field_leader": field_leaders[0].get("name", "Unknown") if field_leaders else "None",
            "synergy_score": synergy_score,
            "active_synergy_count": synergy_score
        }
        
        return report
    
    def reset(self) -> None:
        """Reset the synergy engine state"""
        self.active_synergies = {}
        self.convergence_history = defaultdict(list)
        self.dynamic_bonuses = {}


# Character Dynamics System (Placeholder Stub for Future Implementation)
class CharacterDynamicsSystem:
    """STUB: System for managing character dynamics and relationships
    For future implementation in v4.0+
    """
    
    def __init__(self):
        """Initialize the character dynamics system"""
        self.character_relationships = {}
        self.team_dynamics = {}
        self.dynamic_effects = {}
        
    def initialize_relationships(self, characters):
        """Initialize relationship values between characters
        
        Args:
            characters: List of characters
        """
        # Placeholder for future implementation
        pass
        
    def update_relationship(self, character_a, character_b, event_type, value=None):
        """Update relationship between two characters based on an event
        
        Args:
            character_a: First character
            character_b: Second character
            event_type: Type of interaction event
            value: Optional direct value modifier
        """
        # Placeholder for future implementation
        pass
        
    def get_relationship_effects(self, character_a, character_b):
        """Get effects based on relationship between characters
        
        Args:
            character_a: First character
            character_b: Second character
            
        Returns:
            dict: Effects based on relationship
        """
        # Placeholder for future implementation
        return {}