"""
META Fantasy League Simulator - Trait System
Handles trait definitions, activation checks, and effect application
"""

import random
import json
import os
from typing import Dict, List, Any, Optional

class TraitSystem:
    """System for managing character traits and their effects"""
    
    def __init__(self, trait_definitions=None):
        """Initialize the trait system
        
        Args:
            trait_definitions (dict, optional): Dictionary of trait definitions. Defaults to None.
        """
        self.traits = trait_definitions or self._load_default_traits()
    
    def _load_default_traits(self) -> Dict[str, Dict[str, Any]]:
        """Load default trait definitions"""
        return {
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
            }
        }
    
    def load_traits_from_file(self, file_path: str) -> bool:
        """Load traits from a JSON file
        
        Args:
            file_path (str): Path to the traits JSON file
            
        Returns:
            bool: Success flag
        """
        try:
            if not os.path.exists(file_path):
                print(f"Traits file not found: {file_path}")
                return False
                
            with open(file_path, 'r') as f:
                self.traits = json.load(f)
                
            print(f"Successfully loaded {len(self.traits)} traits from {file_path}")
            return True
        except Exception as e:
            print(f"Error loading traits from file: {e}")
            return False
    
    def check_trait_activation(self, character, trigger_type, context=None):
        """Check if a character's traits activate based on a trigger
        
        Args:
            character: The character object or dictionary
            trigger_type (str): The type of trigger (e.g., "convergence", "damage_taken")
            context (dict, optional): Additional context for the trigger. Defaults to None.
        
        Returns:
            list: List of activated traits and their effects
        """
        activated_traits = []
        context = context or {}
        
        # Skip if character has no traits
        if not self._has_traits(character):
            return activated_traits
        
        # Get traits from character
        traits = self._get_traits(character)
        
        # Check each trait for activation
        for trait_id in traits:
            # Skip if trait not found in definitions
            if trait_id not in self.traits:
                continue
                
            trait_def = self.traits[trait_id]
            
            # Check if this trigger activates the trait
            triggers = trait_def.get('triggers', [])
            if not isinstance(triggers, list):
                # Handle comma-separated string
                triggers = [t.strip() for t in triggers.split(',')] if isinstance(triggers, str) else []
            
            if trigger_type in triggers:
                # Calculate activation chance
                activation_chance = self._calculate_activation_chance(character, trait_def, context)
                
                # Roll for activation
                if random.random() <= activation_chance:
                    # Create activation record
                    activated_traits.append({
                        "trait_id": trait_id,
                        "name": trait_def.get("name", trait_id),
                        "formula_key": trait_def.get("formula_key", ""),
                        "value": trait_def.get("value", 0),
                        "activation_chance": activation_chance
                    })
        
        return activated_traits
    
    def _calculate_activation_chance(self, character, trait_def, context=None):
        """Calculate trait activation chance based on character stats and context
        
        Args:
            character: Character object or dictionary
            trait_def: Trait definition
            context: Additional context
            
        Returns:
            float: Activation chance (0-1)
        """
        # Base chance (50%)
        base_chance = 0.5
        
        # Apply character stat modifiers (use willpower or focus)
        wil_bonus = 0
        if hasattr(character, 'aWIL'):
            wil_bonus = (character.aWIL - 5) * 0.05
        elif isinstance(character, dict) and 'aWIL' in character:
            wil_bonus = (character['aWIL'] - 5) * 0.05
        
        # Apply morale modifier
        morale_mod = 0
        morale = 50  # Default
        if hasattr(character, 'morale'):
            morale = character.morale
        elif isinstance(character, dict) and 'morale' in character:
            morale = character['morale']
        
        if morale < 30:
            morale_mod = -0.1
        elif morale > 70:
            morale_mod = 0.1
        
        # Apply momentum modifier
        momentum_mod = 0
        if context and 'team_momentum' in context:
            momentum = context['team_momentum']
            if momentum['state'] == 'crash':
                momentum_mod = 0.15  # Boost for comeback mechanics
        
        # Final activation chance
        activation_chance = base_chance + wil_bonus + morale_mod + momentum_mod
        
        # Cap between 30% and 85%
        return max(0.3, min(0.85, activation_chance))
    
    def apply_trait_effects(self, character, activated_traits, context=None):
        """Apply the effects of activated traits to a character
        
        Args:
            character: The character object or dictionary
            activated_traits (list): List of activated traits from check_trait_activation
            context (dict, optional): Additional context. Defaults to None.
        
        Returns:
            dict: Effects that were applied
        """
        context = context or {}
        applied_effects = {}
        
        for trait in activated_traits:
            formula_key = trait.get('formula_key', '')
            value = trait.get('value', 0)
            
            # Apply effect based on formula key
            if formula_key == 'bonus_roll':
                # Add to combat roll
                applied_effects['bonus_roll'] = value
                
            elif formula_key == 'damage_reduction':
                # Reduce damage
                applied_effects['damage_reduction'] = value
                
            elif formula_key == 'heal':
                # Heal HP
                applied_effects['heal'] = value
                
            elif formula_key == 'defense_bonus':
                # Defense bonus
                applied_effects['defense_bonus'] = value
            
            # Update character's trait activation counter
            if hasattr(character, 'combat_stats') and isinstance(character.combat_stats, dict):
                character.combat_stats['special_ability_uses'] = character.combat_stats.get('special_ability_uses', 0) + 1
            elif isinstance(character, dict) and 'combat_stats' in character:
                character['combat_stats']['special_ability_uses'] = character['combat_stats'].get('special_ability_uses', 0) + 1
        
        return applied_effects
    
    def _has_traits(self, character) -> bool:
        """Check if character has traits
        
        Args:
            character: Character object or dictionary
            
        Returns:
            bool: True if has traits
        """
        if hasattr(character, 'traits'):
            return bool(character.traits)
        elif isinstance(character, dict) and 'traits' in character:
            return bool(character['traits'])
        return False
    
    def _get_traits(self, character) -> List[str]:
        """Get traits from character
        
        Args:
            character: Character object or dictionary
            
        Returns:
            list: List of trait IDs
        """
        if hasattr(character, 'traits'):
            return character.traits
        elif isinstance(character, dict) and 'traits' in character:
            return character['traits']
        return []
    
    def assign_traits_from_attributes(self, character):
        """Assign traits to a character based on their attributes
        
        Args:
            character: Character to assign traits to
            
        Returns:
            list: List of assigned trait IDs
        """
        traits = []
        
        # Get attribute values
        attributes = {}
        if hasattr(character, 'aSTR'):
            # Character is an object with attributes
            for stat in ['STR', 'INT', 'SPD', 'FS', 'DUR', 'RES', 'WIL', 'LDR', 'OP']:
                attr_name = f'a{stat}'
                if hasattr(character, attr_name):
                    attributes[stat] = getattr(character, attr_name)
                else:
                    attributes[stat] = 5  # Default
        elif isinstance(character, dict):
            # Character is a dictionary
            for stat in ['STR', 'INT', 'SPD', 'FS', 'DUR', 'RES', 'WIL', 'LDR', 'OP']:
                attr_name = f'a{stat}'
                attributes[stat] = character.get(attr_name, 5)
        
        # Assign traits based on high stats
        if attributes.get('INT', 5) >= 7:
            traits.append('genius')
        
        if attributes.get('DUR', 5) >= 7:
            traits.append('shield')
        
        if attributes.get('LDR', 5) >= 7:
            traits.append('tactical')
        
        if attributes.get('SPD', 5) >= 7:
            traits.append('agile')
        
        if attributes.get('RES', 5) >= 7:
            traits.append('healing')
        
        # Get role for default trait assignment
        role = "FL"  # Default
        if hasattr(character, 'role'):
            role = character.role
        elif isinstance(character, dict) and 'role' in character:
            role = character['role']
        
        # If no traits assigned yet, give default by role
        if not traits:
            role_traits = {
                'FL': ['tactical', 'shield'],
                'VG': ['agile', 'shield'],
                'EN': ['shield', 'healing'],
                'RG': ['genius', 'agile'],
                'GO': ['agile', 'genius'],
                'PO': ['genius', 'tactical'],
                'SV': ['tactical', 'healing']
            }
            
            if role in role_traits:
                traits = role_traits[role]
            else:
                # Default fallback
                traits = ['genius', 'tactical']
        
        return traits
    
    def auto_assign_traits(self, characters):
        """Auto-assign traits to a list of characters based on attributes
        
        Args:
            characters: List of character objects or dictionaries
            
        Returns:
            int: Number of characters assigned traits
        """
        assigned_count = 0
        
        for character in characters:
            # Skip if already has traits
            if self._has_traits(character) and self._get_traits(character):
                continue
                
            # Assign traits
            traits = self.assign_traits_from_attributes(character)
            
            # Set traits on character
            if hasattr(character, 'traits'):
                character.traits = traits
            elif isinstance(character, dict):
                character['traits'] = traits
                
            assigned_count += 1
        
        return assigned_count
    
    def export_traits_to_file(self, file_path="traits.json"):
        """Export current trait definitions to a JSON file
        
        Args:
            file_path (str, optional): Path to save the file. Defaults to "traits.json".
            
        Returns:
            bool: Success flag
        """
        try:
            # Create directory if not exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w') as f:
                json.dump(self.traits, f, indent=2)
                
            print(f"Successfully exported {len(self.traits)} traits to {file_path}")
            return True
        except Exception as e:
            print(f"Error exporting traits to file: {e}")
            return False