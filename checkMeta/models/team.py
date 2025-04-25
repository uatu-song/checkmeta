import json
from typing import Dict, List, Any, Optional, Tuple
from ..models.character import Character
from ..models.team import Team

class CircuitSystem:
    """System for managing team circuits"""
    
    def __init__(self, trait_system=None):
        """Initialize the circuit system"""
        self.trait_system = trait_system
        self.circuits = self.load_team_circuits()
    
    def load_team_circuits(self) -> List[Dict[str, Any]]:
        """Load team circuits from the circuit catalog file"""
        try:
            with open("circuit_catalog.json", "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading team circuits: {e}")
            return []
    
    def check_team_circuit(self, team_chars: List[Tuple[int, Character]], context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check if a team can trigger a circuit based on their roles, traits, and conditions"""
        if not self.circuits:
            return None
            
        # Get character details
        chars = [char for _, char in team_chars]
        
        # Check each circuit
        for circuit in self.circuits:
            # Check if we have the required roles
            required_roles = circuit.get("requires_roles", [])
            
            # Count roles present
            role_count = {}
            for role in required_roles:
                role_count[role] = 0
            
            for char in chars:
                role = char.role
                if role in role_count:
                    role_count[role] += 1
            
            # Check if all required roles are present
            roles_satisfied = all(role_count.get(role, 0) > 0 for role in required_roles)
            if not roles_satisfied:
                continue
            
            # Check for required trait tags
            required_tags = circuit.get("trait_tags_required", [])
            
            # Count trait tags present
            tags_present = set()
            
            # Need trait system to check tags
            if not self.trait_system:
                continue
                
            for char in chars:
                char_tags = []
                for trait_name in char.traits:
                    if trait_name in self.trait_system.traits:
                        trait = self.trait_system.traits[trait_name]
                        # Add any tags from this trait
                        char_tags.extend(trait.get("tags", []))
                
                tags_present.update(char_tags)
            
            # Check if all required tags are present
            tags_satisfied = all(tag in tags_present for tag in required_tags)
            if not tags_satisfied:
                continue
            
            # Check trigger conditions
            conditions_satisfied = True
            for condition in circuit.get("trigger_conditions", []):
                # Parse and evaluate the condition
                # This is a simplified version - you may need a more complex parser
                if "momentum_state" in condition:
                    # Check team momentum
                    team_momentum = context.get("team_momentum", "stable")
                    if "building" in condition and team_momentum != "building":
                        conditions_satisfied = False
                        break
                
                if "FL_alive" in condition:
                    # Check if Field Leader is alive
                    fl_alive = any(char.role == "FL" and 
                                  not char.is_ko and 
                                  not char.is_dead 
                                  for char in chars)
                    if "true" in condition and not fl_alive:
                        conditions_satisfied = False
                        break
                
                if "round" in condition:
                    # Check round number
                    current_round = context.get("round", 1)
                    if ">=" in condition:
                        required_round = int(condition.split(">=")[1].strip())
                        if current_round < required_round:
                            conditions_satisfied = False
                            break
            
            # If all checks passed, return this circuit
            if conditions_satisfied:
                return circuit
        
        # No valid circuit found
        return None
    
    def apply_circuit_effects(self, team: Team, circuit: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply effects from an activated circuit to the team"""
        effects = circuit.get("effects", {})
        result = {
            "circuit_name": circuit.get("name", "Unknown Circuit"),
            "applied_effects": []
        }
        
        # Attribute bonuses
        if "attribute_bonus" in effects:
            for attr, bonus in effects["attribute_bonus"].items():
                for char in team.characters:
                    if attr in char.attributes:
                        char.attributes[attr] += bonus
                
                result["applied_effects"].append(f"+{bonus} to {attr} for all characters")
        
        # Combat multiplier
        if "damage_multiplier" in effects:
            multiplier = effects["damage_multiplier"]
            context["damage_multiplier"] = multiplier
            result["applied_effects"].append(f"Damage multiplier: x{multiplier}")
        
        # Morale boost
        if "morale_boost_team" in effects:
            boost = effects["morale_boost_team"]
            for char in team.characters:
                old_morale = char.morale
                char.morale = min(100, char.morale + boost)
                if char.morale_modifiers:
                    char.morale_modifiers = self.get_morale_system().calculate_morale_modifiers(char.morale)
            
            result["applied_effects"].append(f"+{boost} team morale")
        
        # Stamina recovery
        if "stamina_recovery" in effects:
            recovery = effects["stamina_recovery"]
            for char in team.active_characters:
                if not char.is_ko and not char.is_dead:
                    char.stamina = min(100, char.stamina + recovery)
            
            result["applied_effects"].append(f"+{recovery} stamina for active characters")
        
        # Special effects
        if "special_effects" in effects:
            special = effects["special_effects"]
            for effect_name, effect_data in special.items():
                result["applied_effects"].append(f"Special: {effect_name}")
                
                # Apply specific special effects
                if effect_name == "revive_ko":
                    # Chance to revive KO'd characters
                    chance = effect_data.get("chance", 0)
                    for char in team.active_characters:
                        if char.is_ko and not char.is_dead:
                            if random.random() < chance / 100.0:
                                char.is_ko = False
                                char.hp = max(20, char.hp)
                                result["applied_effects"].append(f"Revived {char.name}")
        
        return result
    
    def get_morale_system(self):
        """Get morale system - placeholder for proper dependency injection"""
        from ..systems.morale import MoraleSystem
        return MoraleSystem()