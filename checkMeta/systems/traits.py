"""
Trait system for META League Simulator
"""

from typing import Dict, List, Any, Optional
import random
from ..models.character import Character

class TraitSystem:
    """System for managing traits and their effects"""
    
    def __init__(self):
        """Initialize the trait system with definitions"""
        self.traits = self._load_traits()
    
    def _load_traits(self) -> Dict[str, Dict[str, Any]]:
        """Load trait definitions"""
        return {
            # Original traits
            "genius": {
                "name": "Genius Intellect",
                "type": "combat",
                "triggers": ["convergence", "critical_hit"],
                "formula_key": "bonus_roll",
                "value": 15
            },
            "armor": {
                "name": "Power Armor",
                "type": "defense",
                "triggers": ["damage_taken"],
                "formula_key": "damage_reduction",
                "value": 25
            },
            "tactical": {
                "name": "Tactical Mastery",
                "type": "leadership",
                "triggers": ["convergence", "team_boost"],
                "formula_key": "bonus_roll",
                "value": 20
            },
            "shield": {
                "name": "Vibranium Shield",
                "type": "defense",
                "triggers": ["damage_taken", "convergence"],
                "formula_key": "damage_reduction",
                "value": 30
            },
            "agile": {
                "name": "Enhanced Agility",
                "type": "mobility",
                "triggers": ["convergence", "evasion"],
                "formula_key": "bonus_roll",
                "value": 15
            },
            "spider-sense": {
                "name": "Spider Sense",
                "type": "precognition",
                "triggers": ["combat", "danger"],
                "formula_key": "defense_bonus",
                "value": 20
            },
            "stretchy": {
                "name": "Polymorphic Body",
                "type": "mobility",
                "triggers": ["convergence", "positioning"],
                "formula_key": "bonus_roll",
                "value": 10
            },
            "healing": {
                "name": "Rapid Healing",
                "type": "regeneration",
                "triggers": ["end_of_turn", "damage_taken"],
                "formula_key": "heal",
                "value": 5
            },
            
            # New traits
            "luck": {
                "name": "Extraordinary Luck",
                "type": "probability",
                "triggers": ["combat_roll", "critical_hit", "evasion"],
                "formula_key": "reroll_chance",
                "value": 20
            },
            "telekinetic": {
                "name": "Telekinesis",
                "type": "psionic",
                "triggers": ["convergence", "board_control"],
                "formula_key": "positioning_bonus",
                "value": 15
            },
            "magnetic": {
                "name": "Magnetic Control",
                "type": "energy",
                "triggers": ["piece_capture", "board_control"],
                "formula_key": "capture_bonus",
                "value": 20
            },
            "phasing": {
                "name": "Phasing",
                "type": "defense",
                "triggers": ["damage_taken", "evasion"],
                "formula_key": "damage_reduction",
                "value": 25
            },
            "time_manipulation": {
                "name": "Time Manipulation",
                "type": "tactical",
                "triggers": ["critical_danger", "team_support"],
                "formula_key": "second_chance",
                "value": 10
            },
            "energy_absorption": {
                "name": "Energy Absorption",
                "type": "defense",
                "triggers": ["damage_taken", "counter_attack"],
                "formula_key": "reflect_damage",
                "value": 15
            },
            "teleportation": {
                "name": "Teleportation",
                "type": "mobility",
                "triggers": ["positioning", "escape"],
                "formula_key": "position_change",
                "value": 20
            },
            "invisibility": {
                "name": "Invisibility",
                "type": "stealth",
                "triggers": ["evasion", "surprise_attack"],
                "formula_key": "stealth_bonus",
                "value": 15
            },
            "precognition": {
                "name": "Precognition",
                "type": "sensing",
                "triggers": ["danger", "planning"],
                "formula_key": "anticipation",
                "value": 20
            },
            "super_strength": {
                "name": "Super Strength",
                "type": "physical",
                "triggers": ["melee_combat", "board_pressure"],
                "formula_key": "power_bonus",
                "value": 25
            },
            "adaptive_mutation": {
                "name": "Adaptive Mutation",
                "type": "evolution",
                "triggers": ["end_of_turn", "critical_situation"],
                "formula_key": "stat_boost",
                "value": 10
            },
            "energy_projection": {
                "name": "Energy Projection",
                "type": "ranged",
                "triggers": ["long_range_attack", "area_effect"],
                "formula_key": "range_bonus",
                "value": 20
            },
            "mental_shield": {
                "name": "Mental Shield",
                "type": "psionic_defense",
                "triggers": ["mental_attack", "morale_boost"],
                "formula_key": "mental_resistance",
                "value": 15
            }
        }
    
    def apply_trait_effect(self, character: Character, trigger: str, context: Dict = None) -> List[Dict[str, Any]]:
        """Apply trait effects for a specific trigger"""
        if context is None:
            context = {}
            
        results = []
        
        for trait_name in character.traits:
            if trait_name not in self.traits:
                continue
                
            trait = self.traits[trait_name]
            if trigger not in trait.get("triggers", []):
                continue
            
            # Apply trait effect based on formula_key
            effect = self._calculate_trait_effect(trait, character, trigger, context)
            
            if effect["applied"]:
                results.append({
                    "trait": trait_name,
                    "trait_name": trait["name"],
                    "trigger": trigger,
                    "effect": effect["effect"],
                    "value": effect["value"]
                })
        
        return results
    
    def _calculate_trait_effect(self, trait: Dict[str, Any], character: Character, 
                               trigger: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate the effect of a trait"""
        formula_key = trait.get("formula_key")
        value = trait.get("value", 0)
        
        result = {
            "applied": False,
            "effect": None,
            "value": 0
        }
        
        if formula_key == "bonus_roll":
            result["applied"] = True
            result["effect"] = "combat_bonus"
            result["value"] = value
            
        elif formula_key == "damage_reduction":
            result["applied"] = True
            result["effect"] = "damage_reduction"
            result["value"] = value
            
        elif formula_key == "heal":
            result["applied"] = True
            result["effect"] = "healing"
            result["value"] = value
            
        elif formula_key == "reroll_chance":
            # Implementation for luck trait
            if "roll" in context:
                original_roll = context["roll"]
                
                # Only apply for poor rolls
                if original_roll < 40:
                    # Luck chance
                    luck_threshold = value
                    
                    # Add LCK attribute bonus
                    luck_stat_bonus = max(0, character.get_attribute('LCK') - 5) * 2
                    luck_threshold += luck_stat_bonus
                    
                    # Check if luck triggers
                    if random.random() * 100 < luck_threshold:
                        result["applied"] = True
                        result["effect"] = "reroll"
                        result["value"] = luck_threshold
            
        elif formula_key == "reflect_damage":
            if "damage" in context and "attacker" in context:
                # Reflect damage back to attacker
                reflect_amount = context["damage"] * (value / 100.0)
                result["applied"] = True
                result["effect"] = "damage_reflect"
                result["value"] = reflect_amount
        
        elif formula_key == "second_chance":
            # Time manipulation - chance for a second move
            if "critical_health" in context and context["critical_health"]:
                chance = value + (character.get_attribute('LCK') - 5)
                if random.random() * 100 < chance:
                    result["applied"] = True
                    result["effect"] = "extra_move"
                    result["value"] = chance
        
        # Add other trait formulas as needed
        
        return result
    
    def assign_traits_from_attributes(self, character: Character) -> List[str]:
        """Assign traits based on character attributes"""
        from ..config.game_config import MAX_TRAITS_PER_CHARACTER
        traits = []
        
        # Get attribute values
        str_val = character.get_attribute('STR')
        spd_val = character.get_attribute('SPD')
        int_val = character.get_attribute('INT') 
        dur_val = character.get_attribute('DUR')
        lck_val = character.get_attribute('LCK')
        wil_val = character.get_attribute('WIL')
        ep_val = character.get_attribute('EP')   # Energy Potential
        esp_val = character.get_attribute('ESP') # Extrasensory Perception
        
        # Assign traits based on exceptional attributes (8+)
        if str_val >= 8:
            traits.append("super_strength")
        
        if spd_val >= 8:
            traits.append("agile")
        
        if int_val >= 8:
            traits.append("genius")
        
        if dur_val >= 8:
            traits.append("healing")
        
        if lck_val >= 8:
            traits.append("luck")
        
        if wil_val >= 8:
            traits.append("mental_shield")
        
        if ep_val >= 8:
            traits.append("energy_projection")
        
        if esp_val >= 8:
            traits.append("precognition")
        
        # Limit to maximum traits per character
        if len(traits) > MAX_TRAITS_PER_CHARACTER:
            # Prioritize highest attributes
            attributes = {
                "STR": str_val,
                "SPD": spd_val,
                "INT": int_val,
                "DUR": dur_val,
                "LCK": lck_val,
                "WIL": wil_val,
                "EP": ep_val,
                "ESP": esp_val
            }
            
            # Sort attributes by value (descending)
            sorted_attrs = sorted(attributes.items(), key=lambda x: x[1], reverse=True)
            
            # Select traits based on top attributes
            traits_map = {
                "STR": "super_strength",
                "SPD": "agile",
                "INT": "genius",
                "DUR": "healing",
                "LCK": "luck",
                "WIL": "mental_shield",
                "EP": "energy_projection",
                "ESP": "precognition"
            }
            
            top_traits = []
            for attr, _ in sorted_attrs[:MAX_TRAITS_PER_CHARACTER]:
                if attr in traits_map:
                    top_traits.append(traits_map[attr])
            
            traits = top_traits
        
        # Add custom traits if available
        custom_traits = character.custom_traits
        if custom_traits:
            # Add custom traits (ensure we don't exceed max)
            remaining_slots = MAX_TRAITS_PER_CHARACTER - len(traits)
            if remaining_slots > 0:
                traits.extend(custom_traits[:remaining_slots])
        
        return traits


