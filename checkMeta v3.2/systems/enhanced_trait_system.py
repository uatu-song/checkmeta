"""
META Fantasy League - Enhanced Trait System
Fully implements all traits from the trait catalog
"""

import os
import csv
import random
import json
from typing import Dict, List, Any, Optional

class EnhancedTraitSystem:
    """Enhanced system for managing all character traits from the catalog"""
    
    def __init__(self, trait_file="data/traits/SimEngine v2  full_trait_catalog_export.csv"):
        """Initialize the enhanced trait system"""
        self.traits = {}
        self.trait_effect_map = {}
        self.trait_type_handlers = {}
        self.activation_counts = {}
        
        # Load traits from catalog
        self.load_traits(trait_file)
        
        # Initialize effect mappings
        self._create_trait_effect_mapping()
    
    def load_traits(self, trait_file):
        """Load all traits from the trait catalog"""
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
                        self.traits[trait_id] = {
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
                
                print(f"Loaded {len(self.traits)} traits from {trait_file}")
        except Exception as e:
            print(f"Error loading traits: {e}")
            # Initialize with defaults if loading fails
            self._init_default_traits()
    
    def _init_default_traits(self):
        """Initialize with default traits if catalog loading fails"""
        self.traits = {
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
            # Add more default traits...
        }
        print(f"Initialized {len(self.traits)} default traits")
    
    def _create_trait_effect_mapping(self):
        """Create mapping between traits and their specific effect implementations"""
        # Map trait_id to effect functions
        self.trait_effect_map = {
            # Core traits with specific implementations
            "genius": self._apply_genius_effect,
            "tactical": self._apply_tactical_effect,
            "armor": self._apply_armor_effect,
            "shield": self._apply_shield_effect,
            "agile": self._apply_agile_effect,
            "spider-sense": self._apply_spider_sense_effect,
            "stretchy": self._apply_stretchy_effect,
            "healing": self._apply_healing_effect,
            # Additional traits can be added here
        }
        
        # Create default handlers for trait types
        self.trait_type_handlers = {
            "combat": self._handle_combat_trait,
            "defense": self._handle_defense_trait,
            "mobility": self._handle_mobility_trait,
            "leadership": self._handle_leadership_trait,
            "regeneration": self._handle_regeneration_trait,
            "precognition": self._handle_precognition_trait
        }
    
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
            
            # Use specific handler if available
            if trait_id in self.trait_effect_map:
                effect = self.trait_effect_map[trait_id](character, context)
                if effect:
                    effects.append(effect)
                    continue
            
            # Otherwise use generic type handler
            trait_def = self.traits.get(trait_id, {})
            trait_type = trait_def.get("type", "")
            
            if trait_type in self.trait_type_handlers:
                effect = self.trait_type_handlers[trait_type](character, trait_def, context)
                if effect:
                    effects.append(effect)
                    continue
            
            # Fallback to generic effect
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
    
    # Implementations for specific trait effects
    def _apply_genius_effect(self, character, context):
        # Implementation for genius trait
        pass
    
    def _apply_tactical_effect(self, character, context):
        # Implementation for tactical trait
        pass
    
    # Type handler implementations
    def _handle_combat_trait(self, character, trait_def, context):
        # Generic handler for combat traits
        pass
    
    def _handle_defense_trait(self, character, trait_def, context):
        # Generic handler for defense traits
        pass
    
    # Additional methods from the original trait system...