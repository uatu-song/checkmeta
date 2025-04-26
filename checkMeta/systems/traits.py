"""
META Fantasy League Simulator - Trait System
Handles trait definitions, activation checks, and effect application
"""

import random

class TraitSystem:
    """System for managing character traits and their effects"""
    
    def __init__(self, trait_definitions=None):
        """Initialize the trait system
        
        Args:
            trait_definitions (dict, optional): Dictionary of trait definitions. Defaults to None.
        """
        self.trait_definitions = trait_definitions or {}
        print(f"Trait system initialized with {len(self.trait_definitions)} trait definitions")
    
    def get_trait_definition(self, trait_id):
        """Get the definition for a trait
        
        Args:
            trait_id (str): ID of the trait
        
        Returns:
            dict: Trait definition or empty dict if not found
        """
        return self.trait_definitions.get(trait_id, {})
    
    def check_trait_activation(self, character, trigger_type, context=None):
        """Check if a character's traits activate based on a trigger
        
        Args:
            character: The character object
            trigger_type (str): The type of trigger (e.g., "convergence", "damage_taken")
            context (dict, optional): Additional context for the trigger. Defaults to None.
        
        Returns:
            list: List of activated traits and their effects
        """
        activated_traits = []
        context = context or {}
        
        # Skip if character has no traits attribute
        if not hasattr(character, 'traits'):
            return activated_traits
        
        for trait_id in character.traits:
            # Get trait definition
            trait_def = self.get_trait_definition(trait_id)
            
            # Skip if trait not found
            if not trait_def:
                continue
            
            # Check if this trigger activates the trait
            triggers = trait_def.get('triggers', [])
            if not isinstance(triggers, list):
                # Handle comma-separated string
                if isinstance(triggers, str):
                    triggers = [t.strip() for t in triggers.split(',')]
                else:
                    triggers = []
            
            if trigger_type in triggers:
                # Calculate activation chance
                chance = 1.0  # Default 100%
                
                # Apply character modifiers
                if hasattr(character, 'trait_activation_bonus'):
                    chance *= (1 + character.trait_activation_bonus)
                
                # Random roll for activation
                if random.random() <= chance:
                    # Get trait values
                    formula_key = trait_def.get('formula_key', '')
                    
                    # Create activation record
                    activation = {
                        'trait_id': trait_id,
                        'name': trait_def.get('name', trait_id),
                        'effect_type': formula_key,
                        'value': trait_def.get('value', 0),
                        'formula': trait_def.get('formula_expr', ''),
                    }
                    
                    # Apply any context-specific modifications
                    if 'combat' in context and formula_key:
                        # Handle combat-specific trait effects
                        if formula_key == 'bonus_roll':
                            activation['applied_value'] = trait_def.get('value', 0)
                        elif formula_key == 'damage_reduction':
                            damage = context.get('damage', 0)
                            reduction = trait_def.get('value', 0) / 100.0
                            activation['applied_value'] = damage * reduction
                    
                    activated_traits.append(activation)
                    print(f"Trait '{trait_def.get('name', trait_id)}' activated for {character.name}")
        
        return activated_traits
    
    def apply_trait_effects(self, character, activated_traits, context=None):
        """Apply the effects of activated traits to a character
        
        Args:
            character: The character object
            activated_traits (list): List of activated traits from check_trait_activation
            context (dict, optional): Additional context. Defaults to None.
        
        Returns:
            dict: Effects that were applied
        """
        context = context or {}
        applied_effects = {}
        
        for trait in activated_traits:
            effect_type = trait.get('effect_type', '')
            value = trait.get('value', 0)
            
            # Apply effect based on type
            if effect_type == 'bonus_roll':
                # Add to combat roll
                if 'combat_roll' in context:
                    context['combat_roll'] += value
                    applied_effects['bonus_roll'] = value
            
            elif effect_type == 'damage_reduction':
                # Reduce damage
                if 'damage' in context:
                    reduction = min(context['damage'], value)
                    context['damage'] -= reduction
                    applied_effects['damage_reduction'] = reduction
            
            elif effect_type == 'heal':
                # Heal character
                if hasattr(character, 'HP'):
                    old_hp = character.HP
                    character.HP = min(100, character.HP + value)
                    applied_effects['heal'] = character.HP - old_hp
                    print(f"{character.name} healed for {character.HP - old_hp} HP from {trait.get('name', 'trait')}")
            
            # Apply formula-based effects if 'formula_expr' is provided
            formula = trait.get('formula', '')
            if formula:
                try:
                    # Simple formula evaluation (this could be expanded)
                    result = eval(formula, {"x": value, "context": context})
                    applied_effects[f'formula_{effect_type}'] = result
                except Exception as e:
                    print(f"Error evaluating trait formula: {e}")
        
        return applied_effects
    
    def assign_traits_from_attributes(self, character):
        """Assign traits to a character based on their attributes
        
        Args:
            character: Character to assign traits to
            
        Returns:
            list: List of assigned trait IDs
        """
        traits = []
        
        # Check each attribute value to determine appropriate traits
        str_val = getattr(character, 'aSTR', 5) if hasattr(character, 'aSTR') else 5
        if str_val >= 8:
            traits.append('shield')
        
        int_val = getattr(character, 'aINT', 5) if hasattr(character, 'aINT') else 5
        if int_val >= 8:
            traits.append('genius')
        
        # Leadership trait
        ldr_val = getattr(character, 'aLDR', 5) if hasattr(character, 'aLDR') else 5
        if ldr_val >= 8:
            traits.append('tactical')
        
        # Speed-based traits
        spd_val = getattr(character, 'aSPD', 5) if hasattr(character, 'aSPD') else 5
        if spd_val >= 8:
            traits.append('agile')
        
        # Durability-based traits
        dur_val = getattr(character, 'aDUR', 5) if hasattr(character, 'aDUR') else 5
        if dur_val >= 8:
            traits.append('healing')
        
        # Make sure character has at least one trait
        if not traits:
            role = character.role if hasattr(character, 'role') else 'FL'
            
            # Default traits based on role
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