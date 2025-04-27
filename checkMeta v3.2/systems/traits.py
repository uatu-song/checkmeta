"""
META Fantasy League Simulator - Enhanced Trait System
Handles trait definitions, activation logic, and effects
"""

import os
import csv
import random
import json
from typing import Dict, List, Any, Optional

class TraitSystem:
    """Enhanced system for managing character traits with improved balance"""
    
    def __init__(self, trait_file="data/traits/SimEngine v2  full_trait_catalog_export.csv"):
        """Initialize trait system and load trait definitions
        
        Args:
            trait_file: Path to CSV file containing trait definitions
        """
        # Load traits
        self.traits = self._load_traits(trait_file)
        
        # Default traits if loading fails
        if not self.traits:
            self.traits = self._get_default_traits()
        
        # Track trait activations for balance analysis
        self.activation_counts = {}
    
    def _load_traits(self, trait_file):
        """Load trait definitions from CSV file
        
        Args:
            trait_file: Path to CSV file
            
        Returns:
            dict: Loaded trait definitions
        """
        traits = {}
        
        # Try to load from CSV
        try:
            if os.path.exists(trait_file):
                with open(trait_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # Extract key info
                        trait_id = row.get('trait_id', '').strip()
                        if not trait_id:
                            continue
                            
                        # Parse triggers
                        triggers_raw = row.get('triggers', '').strip()
                        triggers = [t.strip() for t in triggers_raw.split(',') if t.strip()]
                        
                        # Create trait definition
                        traits[trait_id] = {
                            'name': row.get('name', trait_id),
                            'type': row.get('type', '').lower(),
                            'triggers': triggers,
                            'formula_key': row.get('formula_key', ''),
                            'formula_expr': row.get('formula_expr', ''),
                            'value': int(row.get('value', 0)) if row.get('value', '').isdigit() else 10,
                            'stamina_cost': int(row.get('stamina_cost', 0)) if row.get('stamina_cost', '').isdigit() else 0,
                            'cooldown': int(row.get('cooldown', 0)) if row.get('cooldown', '').isdigit() else 0,
                            'description': row.get('description', '')
                        }
                
                print(f"Loaded {len(traits)} traits from {trait_file}")
                return traits
        except Exception as e:
            print(f"Error loading traits: {e}")
        
        return {}
    
    def _get_default_traits(self):
        """Get default trait definitions if loading fails
        
        Returns:
            dict: Default trait definitions
        """
        return {
            "genius": {
                "name": "Genius Intellect",
                "type": "combat",
                "triggers": ["convergence", "critical_hit"],
                "formula_key": "bonus_roll",
                "value": 15,
                "stamina_cost": 5,
                "cooldown": 1,
                "description": "Enhanced cognitive abilities provide combat advantages"
            },
            "armor": {
                "name": "Power Armor",
                "type": "defense",
                "triggers": ["damage_taken"],
                "formula_key": "damage_reduction",
                "value": 25,
                "stamina_cost": 0,
                "cooldown": 0,
                "description": "Advanced armor reduces incoming damage"
            },
            "tactical": {
                "name": "Tactical Mastery",
                "type": "leadership",
                "triggers": ["convergence", "team_boost"],
                "formula_key": "bonus_roll",
                "value": 20,
                "stamina_cost": 10,
                "cooldown": 2,
                "description": "Superior tactical thinking improves combat capabilities"
            },
            "shield": {
                "name": "Vibranium Shield",
                "type": "defense",
                "triggers": ["damage_taken", "convergence"],
                "formula_key": "damage_reduction",
                "value": 30,
                "stamina_cost": 5,
                "cooldown": 1,
                "description": "Near-indestructible shield provides exceptional protection"
            },
            "agile": {
                "name": "Enhanced Agility",
                "type": "mobility",
                "triggers": ["convergence", "evasion"],
                "formula_key": "bonus_roll",
                "value": 15,
                "stamina_cost": 3,
                "cooldown": 0,
                "description": "Superhuman agility improves combat capabilities"
            },
            "spider-sense": {
                "name": "Spider Sense",
                "type": "precognition",
                "triggers": ["combat", "danger"],
                "formula_key": "defense_bonus",
                "value": 20,
                "stamina_cost": 0,
                "cooldown": 0,
                "description": "Danger-sensing ability provides combat advantages"
            },
            "stretchy": {
                "name": "Polymorphic Body",
                "type": "mobility",
                "triggers": ["convergence", "positioning"],
                "formula_key": "bonus_roll",
                "value": 10,
                "stamina_cost": 5,
                "cooldown": 0,
                "description": "Malleable physiology allows for creative attacks"
            },
            "healing": {
                "name": "Rapid Healing",
                "type": "regeneration",
                "triggers": ["end_of_turn", "damage_taken"],
                "formula_key": "heal",
                "value": 5,
                "stamina_cost": 0,
                "cooldown": 0,
                "description": "Accelerated healing factor repairs injuries quickly"
            }
        }
    
    def check_trait_activation(self, character, trigger, context=None):
        """Check if a character's traits activate for a given trigger
        
        Args:
            character: Character to check traits for
            trigger: Trigger type to check
            context: Additional context for activation
            
        Returns:
            list: Activated traits
        """
        context = context or {}
        activated_traits = []
        
        # Get character traits
        traits = character.get("traits", [])
        
        # Check each trait
        for trait_id in traits:
            if trait_id not in self.traits:
                continue
                
            trait = self.traits[trait_id]
            
            # Check if this trait responds to this trigger
            if trigger not in trait.get("triggers", []):
                continue
                
            # Check if on cooldown
            char_cooldowns = character.get("trait_cooldowns", {})
            if trait_id in char_cooldowns and char_cooldowns[trait_id] > 0:
                continue
                
            # Calculate activation chance
            activation_chance = self._calculate_activation_chance(character, trait, context)
            
            # Roll for activation
            if random.random() <= activation_chance:
                # Apply stamina cost
                stamina_cost = trait.get("stamina_cost", 0)
                if stamina_cost > 0:
                    character["stamina"] = max(0, character.get("stamina", 100) - stamina_cost)
                
                # Apply cooldown
                cooldown = trait.get("cooldown", 0)
                if cooldown > 0:
                    if "trait_cooldowns" not in character:
                        character["trait_cooldowns"] = {}
                    character["trait_cooldowns"][trait_id] = cooldown
                
                # Add to activated traits
                activated_traits.append({
                    "trait_id": trait_id,
                    "trait_name": trait.get("name", trait_id),
                    "effect": trait.get("formula_key", ""),
                    "value": trait.get("value", 0),
                    "activation_chance": activation_chance
                })
                
                # Track activation for balance analysis
                if trait_id not in self.activation_counts:
                    self.activation_counts[trait_id] = 0
                self.activation_counts[trait_id] += 1
        
        return activated_traits
    
    def _calculate_activation_chance(self, character, trait, context):
        """Calculate trait activation chance with balanced factors
        
        Args:
            character: Character attempting trait activation
            trait: Trait definition
            context: Additional context
            
        Returns:
            float: Activation chance (0-1)
        """
        # Base chance (50%)
        base_chance = 0.5
        
        # Willpower impact
        wil = character.get("aWIL", 5)
        wil_modifier = (wil - 5) * 0.05  # +/- 5% per point away from 5
        
        # Morale impact
        morale = character.get("morale", 50)
        morale_modifier = 0
        if morale < 30:
            morale_modifier = -0.1  # -10% at very low morale
        elif morale > 70:
            morale_modifier = 0.1   # +10% at very high morale
        
        # Stamina impact
        stamina = character.get("stamina", 100)
        stamina_modifier = 0
        if stamina < 30:
            stamina_modifier = -0.1  # -10% at very low stamina
        
        # Momentum impact
        momentum_state = character.get("momentum_state", "stable")
        momentum_modifier = 0
        if momentum_state == "building":
            momentum_modifier = 0.1  # +10% in building momentum
        elif momentum_state == "crash":
            momentum_modifier = 0.05  # +5% in crash (comeback mechanic)
        
        # Combined chance
        final_chance = base_chance + wil_modifier + morale_modifier + stamina_modifier + momentum_modifier
        
        # Limit to reasonable range (20-90%)
        return max(0.2, min(final_chance, 0.9))
    
    def apply_trait_effect(self, character, trigger, context=None):
        """Apply trait effects for a given trigger
        
        Args:
            character: Character to apply effects to
            trigger: Trigger type
            context: Additional context
            
        Returns:
            list: Applied effects
        """
        context = context or {}
        effects = []
        
        # Check which traits activate
        activated_traits = self.check_trait_activation(character, trigger, context)
        
        # Process each activated trait
        for trait in activated_traits:
            trait_id = trait["trait_id"]
            trait_def = self.traits.get(trait_id, {})
            
            # Get effect type and value
            effect_type = trait_def.get("formula_key", "")
            effect_value = trait_def.get("value", 0)
            
            # Map effect type to standardized effect
            standardized_effect = self._map_effect_type(effect_type)
            
            # Add effect to list
            effects.append({
                "trait_id": trait_id,
                "trait_name": trait_def.get("name", trait_id),
                "effect": standardized_effect,
                "value": effect_value
            })
        
        return effects
    
    def _map_effect_type(self, effect_type):
        """Map trait effect types to standardized effects
        
        Args:
            effect_type: Original effect type
            
        Returns:
            str: Standardized effect type
        """
        # Map of formula keys to standardized effects
        effect_map = {
            "bonus_roll": "combat_bonus",
            "damage_reduction": "damage_reduction",
            "heal": "healing",
            "defense_bonus": "defense_bonus",
            "evasion": "evasion_bonus",
            "reroll": "reroll_dice",
            "trait_bonus": "trait_bonus"
        }
        
        return effect_map.get(effect_type, effect_type)
    
    def update_cooldowns(self, characters):
        """Update trait cooldowns at end of round
        
        Args:
            characters: List of characters to update
        """
        for character in characters:
            if "trait_cooldowns" in character:
                # Reduce all cooldowns by 1
                for trait_id in list(character["trait_cooldowns"].keys()):
                    character["trait_cooldowns"][trait_id] -= 1
                    
                    # Remove expired cooldowns
                    if character["trait_cooldowns"][trait_id] <= 0:
                        del character["trait_cooldowns"][trait_id]
    
    def assign_traits_to_character(self, character, division, role):
        """Assign appropriate traits to a character based on division and role
        
        Args:
            character: Character to assign traits to
            division: Character's division ('o' or 'i')
            role: Character's role
            
        Returns:
            list: Assigned traits
        """
        # Define trait sets by division and role
        operations_traits = {
            "FL": ["tactical", "shield", "armor"],
            "VG": ["agile", "shield", "stretchy"],
            "EN": ["armor", "agile", "tactical"]
        }
        
        intelligence_traits = {
            "RG": ["genius", "agile", "spider-sense"],
            "GO": ["spider-sense", "agile", "stretchy"],
            "PO": ["genius", "spider-sense", "tactical"],
            "SV": ["genius", "tactical", "shield"]
        }
        
        # Get appropriate trait pool
        if division == "o":
            trait_pool = operations_traits.get(role, ["tactical", "armor"])
        else:
            trait_pool = intelligence_traits.get(role, ["genius", "spider-sense"])
        
        # Add healing trait based on DUR
        if character.get("aDUR", 5) >= 7:
            trait_pool.append("healing")
        
        # Select 2-3 traits based on character stats
        num_traits = min(3, max(2, (character.get("aOP", 5) + character.get("aAM", 5)) // 4))
        
        # Select random traits from pool
        selected_traits = random.sample(trait_pool, min(num_traits, len(trait_pool)))
        
        # Set traits on character
        character["traits"] = selected_traits
        
        return selected_traits
    
    def export_trait_stats(self, output_file="results/trait_stats.json"):
        """Export trait activation statistics
        
        Args:
            output_file: File to save stats to
        """
        # Calculate total activations
        total = sum(self.activation_counts.values())
        
        # Calculate activation percentages
        stats = {
            "total_activations": total,
            "trait_counts": self.activation_counts,
            "trait_percentages": {
                trait_id: (count / total) * 100 if total > 0 else 0
                for trait_id, count in self.activation_counts.items()
            }
        }
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Save to file
        with open(output_file, 'w') as f:
            json.dump(stats, f, indent=2)
        
        print(f"Trait stats exported to {output_file}")
        
        return stats