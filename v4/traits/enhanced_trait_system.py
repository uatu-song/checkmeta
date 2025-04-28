"""
META Fantasy League Simulator - Enhanced Trait System
Fully implements traits from the trait catalog with robust loading
"""

import os
import logging
from typing import Dict, List, Any, Optional, Set
import random
from enhanced_trait_loader import TraitLoader

logger = logging.getLogger("TraitSystem")

class EnhancedTraitSystem:
    """Enhanced system for managing all character traits from the catalog"""
    
    def __init__(self, config=None, trait_file=None):
        """Initialize the enhanced trait system
        
        Args:
            config: Optional configuration object
            trait_file: Optional path to trait catalog file
        """
        self.config = config
        self.trait_file = trait_file
        
        # Initialize trait loader
        self.trait_loader = TraitLoader(config)
        
        # Load traits
        self.traits = self.trait_loader.load_traits()
        
        # Validate traits
        self.validation_report = self.trait_loader.validate_traits()
        
        # Track trait activations
        self.activation_counts = {}
        
        # Map trait effects
        self.trait_effect_map = self._create_trait_effect_mapping()
        self.trait_type_handlers = self._create_trait_type_handlers()
        
        logger.info(f"Enhanced Trait System initialized with {len(self.traits)} traits")
        
        # If verbose logging is enabled, print trait summary
        if logger.level <= logging.DEBUG:
            self.trait_loader.print_trait_summary()
    
    def _create_trait_effect_mapping(self) -> Dict[str, Any]:
        """Create mapping between traits and their specific effect implementations
        
        Returns:
            dict: Mapping of trait IDs to effect functions
        """
        # Map trait_id to effect functions
        return {
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
    
    def _create_trait_type_handlers(self) -> Dict[str, Any]:
        """Create handlers for trait types
        
        Returns:
            dict: Mapping of trait types to handler functions
        """
        # Create default handlers for trait types
        return {
            "combat": self._handle_combat_trait,
            "defense": self._handle_defense_trait,
            "mobility": self._handle_mobility_trait,
            "leadership": self._handle_leadership_trait,
            "regeneration": self._handle_regeneration_trait,
            "precognition": self._handle_precognition_trait
        }
    
    def check_trait_activation(self, character: Dict[str, Any], trigger: str, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
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
                logger.warning(f"Trait '{trait_id}' not found in trait catalog. Skipping.")
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
            
            # Apply synergy bonuses to activation chance
            activation_bonus = 0
            if "synergy_bonuses" in character:
                # Get trait activation bonus from synergies
                trait_activation_bonus = character["synergy_bonuses"].get("trait_activation", 0)
                dynamic_bonus = character["synergy_bonuses"].get("dynamic_trait_activation", 0)
                
                activation_bonus = trait_activation_bonus + dynamic_bonus
            
            # Apply bonus from context if present
            if "activation_bonus" in context:
                activation_bonus += context["activation_bonus"]
                
            # Apply total bonus
            if activation_bonus > 0:
                activation_chance += activation_bonus
                activation_chance = max(0.2, min(activation_chance, 0.95))  # Cap between 20-95%
            
            # Roll for activation
            roll = random.random()
            success = roll <= activation_chance
            
            # Log roll details at debug level
            logger.debug(f"Trait activation roll: {trait_id}, roll={roll:.2f}, chance={activation_chance:.2f}, success={success}")
            
            if success:
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
    
    def _calculate_activation_chance(self, character: Dict[str, Any], trait: Dict[str, Any], context: Dict[str, Any]) -> float:
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
        
        # Trait type modifiers
        trait_type = trait.get("type", "").lower()
        type_modifier = 0
        
        # Some trait types are naturally more likely to activate
        if trait_type == "precognition":
            type_modifier = 0.1  # +10% for precognition traits
        elif trait_type == "regeneration":
            type_modifier = 0.15  # +15% for regeneration traits
        
        # Combined chance
        final_chance = base_chance + wil_modifier + morale_modifier + stamina_modifier + type_modifier
        
        # Limit to reasonable range (20-90%)
        return max(0.2, min(final_chance, 0.9))
    
    def update_cooldowns(self, characters: List[Dict[str, Any]]) -> None:
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
    
    def apply_trait_effect(self, character: Dict[str, Any], trigger: str, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
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
    
    def _map_effect_type(self, effect_type: str) -> str:
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
    
    def assign_traits_to_character(self, character: Dict[str, Any], division: str, role: str) -> List[str]:
        """Assign appropriate traits to a character based on division and role
        
        Args:
            character: Character to assign traits to
            division: Character's division ('o' or 'i')
            role: Character's role
            
        Returns:
            list: Assigned traits
        """
        # Get traits by type to ensure we have a variety of traits
        trait_types = self.trait_loader.get_trait_types()
        
        # Define trait pools by division and role
        operations_traits = {
            "FL": ["tactical", "leadership", "command"],
            "VG": ["agile", "shield", "stretchy"],
            "EN": ["armor", "strength", "endurance"]
        }
        
        intelligence_traits = {
            "RG": ["genius", "agile", "precision"],
            "GO": ["spider-sense", "stealth", "infiltration"],
            "PO": ["mental", "telepathy", "telekinesis"],
            "SV": ["genius", "tactical", "reality"]
        }
        
        # Start with preferred traits for this role
        preferred_traits = []
        
        if division == "o":
            preferred_traits = operations_traits.get(role, ["tactical", "armor"])
        else:
            preferred_traits = intelligence_traits.get(role, ["genius", "spider-sense"])
        
        # Always add healing trait based on DUR
        if character.get("aDUR", 5) >= 7:
            preferred_traits.append("healing")
        
        # Filter to traits that actually exist in our catalog
        valid_traits = [t for t in preferred_traits if t in self.traits]
        
        # If we don't have enough valid traits, add some from each type
        if len(valid_traits) < 2:
            # Add a combat trait
            if "combat" in trait_types and trait_types["combat"]:
                combat_trait = random.choice(trait_types["combat"])
                if combat_trait not in valid_traits:
                    valid_traits.append(combat_trait)
            
            # Add a defense trait
            if "defense" in trait_types and trait_types["defense"]:
                defense_trait = random.choice(trait_types["defense"])
                if defense_trait not in valid_traits:
                    valid_traits.append(defense_trait)
        
        # Select 2-3 traits based on character stats
        num_traits = min(3, max(2, (character.get("aOP", 5) + character.get("aAM", 5)) // 4))
        
        # If we have more valid traits than needed, select randomly
        if len(valid_traits) > num_traits:
            selected_traits = random.sample(valid_traits, num_traits)
        else:
            # Use all valid traits
            selected_traits = valid_traits
            
            # If we still need more, add random traits from catalog
            if len(selected_traits) < num_traits:
                # Get all trait IDs
                all_traits = list(self.traits.keys())
                
                # Remove already selected traits
                available_traits = [t for t in all_traits if t not in selected_traits]
                
                # Add random traits to reach desired count
                additional_count = num_traits - len(selected_traits)
                if available_traits and additional_count > 0:
                    additional_traits = random.sample(available_traits, min(additional_count, len(available_traits)))
                    selected_traits.extend(additional_traits)
        
        # Set traits on character
        character["traits"] = selected_traits
        
        return selected_traits
    
    def get_all_trait_ids(self) -> List[str]:
        """Get all available trait IDs
        
        Returns:
            list: List of all trait IDs
        """
        return list(self.traits.keys())
    
    def get_trait_count(self) -> int:
        """Get number of loaded traits
        
        Returns:
            int: Number of traits
        """
        return len(self.traits)
    
    def get_most_activated_traits(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most frequently activated traits
        
        Args:
            limit: Maximum number of traits to return
            
        Returns:
            list: Most activated traits with counts
        """
        # Sort traits by activation count
        sorted_traits = sorted(self.activation_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Return top N traits
        result = []
        for trait_id, count in sorted_traits[:limit]:
            if trait_id in self.traits:
                result.append({
                    "trait_id": trait_id,
                    "name": self.traits[trait_id].get("name", trait_id),
                    "activations": count
                })
        
        return result
    
    def print_trait_catalog_summary(self) -> None:
        """Print a summary of the trait catalog"""
        self.trait_loader.print_trait_summary()
    
    # Implementations for specific trait effects (placeholder implementations)
    def _apply_genius_effect(self, character: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply Genius Intellect trait effect
        
        Args:
            character: Character with trait
            context: Effect context
            
        Returns:
            dict: Effect details
        """
        # Provide combat bonus
        return {
            "trait_id": "genius",
            "trait_name": "Genius Intellect",
            "effect": "combat_bonus",
            "value": 15
        }
    
    def _apply_tactical_effect(self, character: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply Tactical Mastery trait effect
        
        Args:
            character: Character with trait
            context: Effect context
            
        Returns:
            dict: Effect details
        """
        # Provide combat bonus
        return {
            "trait_id": "tactical",
            "trait_name": "Tactical Mastery",
            "effect": "combat_bonus",
            "value": 20
        }
    
    def _apply_armor_effect(self, character: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply Power Armor trait effect
        
        Args:
            character: Character with trait
            context: Effect context
            
        Returns:
            dict: Effect details
        """
        # Provide damage reduction
        return {
            "trait_id": "armor",
            "trait_name": "Power Armor",
            "effect": "damage_reduction",
            "value": 25
        }
    
    def _apply_shield_effect(self, character: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply Vibranium Shield trait effect
        
        Args:
            character: Character with trait
            context: Effect context
            
        Returns:
            dict: Effect details
        """
        # Provide damage reduction
        return {
            "trait_id": "shield",
            "trait_name": "Vibranium Shield",
            "effect": "damage_reduction",
            "value": 30
        }
    
    def _apply_agile_effect(self, character: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply Enhanced Agility trait effect
        
        Args:
            character: Character with trait
            context: Effect context
            
        Returns:
            dict: Effect details
        """
        # Provide combat bonus
        return {
            "trait_id": "agile",
            "trait_name": "Enhanced Agility",
            "effect": "combat_bonus",
            "value": 15
        }
    
    def _apply_spider_sense_effect(self, character: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply Spider Sense trait effect
        
        Args:
            character: Character with trait
            context: Effect context
            
        Returns:
            dict: Effect details
        """
        # Provide defense bonus
        return {
            "trait_id": "spider-sense",
            "trait_name": "Spider Sense",
            "effect": "defense_bonus",
            "value": 20
        }
    
    def _apply_stretchy_effect(self, character: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply Polymorphic Body trait effect
        
        Args:
            character: Character with trait
            context: Effect context
            
        Returns:
            dict: Effect details
        """
        # Provide combat bonus
        return {
            "trait_id": "stretchy",
            "trait_name": "Polymorphic Body",
            "effect": "combat_bonus",
            "value": 10
        }
    
    def _apply_healing_effect(self, character: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply Rapid Healing trait effect
        
        Args:
            character: Character with trait
            context: Effect context
            
        Returns:
            dict: Effect details
        """
        # Provide healing
        return {
            "trait_id": "healing",
            "trait_name": "Rapid Healing",
            "effect": "healing",
            "value": 5
        }
    
    # Generic trait type handlers
    def _handle_combat_trait(self, character: Dict[str, Any], trait_def: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle generic combat trait
        
        Args:
            character: Character with trait
            trait_def: Trait definition
            context: Effect context
            
        Returns:
            dict: Effect details
        """
        return {
            "trait_id": trait_def.get("id", "unknown"),
            "trait_name": trait_def.get("name", "Unknown Combat Trait"),
            "effect": "combat_bonus",
            "value": trait_def.get("value", 10)
        }
    
    def _handle_defense_trait(self, character: Dict[str, Any], trait_def: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle generic defense trait
        
        Args:
            character: Character with trait
            trait_def: Trait definition
            context: Effect context
            
        Returns:
            dict: Effect details
        """
        return {
            "trait_id": trait_def.get("id", "unknown"),
            "trait_name": trait_def.get("name", "Unknown Defense Trait"),
            "effect": "damage_reduction",
            "value": trait_def.get("value", 15)
        }
    
    def _handle_mobility_trait(self, character: Dict[str, Any], trait_def: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle generic mobility trait
        
        Args:
            character: Character with trait
            trait_def: Trait definition
            context: Effect context
            
        Returns:
            dict: Effect details
        """
        return {
            "trait_id": trait_def.get("id", "unknown"),
            "trait_name": trait_def.get("name", "Unknown Mobility Trait"),
            "effect": "evasion_bonus",
            "value": trait_def.get("value", 15)
        }
    
    def _handle_leadership_trait(self, character: Dict[str, Any], trait_def: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle generic leadership trait
        
        Args:
            character: Character with trait
            trait_def: Trait definition
            context: Effect context
            
        Returns:
            dict: Effect details
        """
        return {
            "trait_id": trait_def.get("id", "unknown"),
            "trait_name": trait_def.get("name", "Unknown Leadership Trait"),
            "effect": "team_bonus",
            "value": trait_def.get("value", 10)
        }
    
    def _handle_regeneration_trait(self, character: Dict[str, Any], trait_def: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle generic regeneration trait
        
        Args:
            character: Character with trait
            trait_def: Trait definition
            context: Effect context
            
        Returns:
            dict: Effect details
        """
        return {
            "trait_id": trait_def.get("id", "unknown"),
            "trait_name": trait_def.get("name", "Unknown Regeneration Trait"),
            "effect": "healing",
            "value": trait_def.get("value", 5)
        }
    
    def _handle_precognition_trait(self, character: Dict[str, Any], trait_def: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle generic precognition trait
        
        Args:
            character: Character with trait
            trait_def: Trait definition
            context: Effect context
            
        Returns:
            dict: Effect details
        """
        return {
            "trait_id": trait_def.get("id", "unknown"),
            "trait_name": trait_def.get("name", "Unknown Precognition Trait"),
            "effect": "defense_bonus",
            "value": trait_def.get("value", 15)
        }