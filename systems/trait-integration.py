"""
TraitStaminaIntegrator

This module implements the integration between the Stamina System and the Trait System
for the META Fantasy League Simulator v5.0.

It provides functions for:
- Checking if traits can be activated based on stamina
- Calculating stamina costs for trait activation
- Applying stamina-based modifiers to trait effectiveness
"""

import logging
from typing import Dict, Any, Tuple, Optional, List
from system_base import SystemBase


class TraitStaminaIntegrator(SystemBase):
    """
    Integration class between Trait System and Stamina System.
    
    This class handles all interactions between traits and stamina:
    - Determining stamina costs for trait activation
    - Checking if traits can be activated based on current stamina
    - Applying stamina-based modifiers to trait effectiveness
    """
    
    def __init__(self, config, registry):
        """Initialize the trait-stamina integrator"""
        super().__init__("trait_stamina_integrator", registry, config)
        self.logger = logging.getLogger("TRAIT_STAMINA_INTEGRATOR")
        self.trait_system = None
        self.stamina_system = None
        
    def _activate_implementation(self):
        """Activate the integrator by connecting to required systems"""
        # Get required systems from registry
        self.trait_system = self.registry.get("trait_system")
        if not self.trait_system:
            raise ValueError("Trait system is required but not available in the registry")
            
        self.stamina_system = self.registry.get("stamina_system")
        if not self.stamina_system:
            raise ValueError("Stamina system is required but not available in the registry")
            
        # Load trait stamina costs configuration
        self._load_trait_stamina_config()
        
        # Register with trait system's hooks
        if hasattr(self.trait_system, "register_activation_check"):
            self.trait_system.register_activation_check(self.can_activate_trait)
            
        if hasattr(self.trait_system, "register_post_activation_hook"):
            self.trait_system.register_post_activation_hook(self.apply_trait_stamina_cost)
            
        self.logger.info("Trait-Stamina integrator activated successfully")
        
    def _load_trait_stamina_config(self):
        """Load trait stamina cost configuration"""
        # Get trait catalog from configuration or trait system
        if hasattr(self.trait_system, "get_trait_catalog"):
            self.trait_catalog = self.trait_system.get_trait_catalog()
        else:
            # Default path for trait catalog
            catalog_path = self.config.get("paths.trait_catalog", "data/traits/trait_catalog.json")
            import json
            with open(catalog_path, 'r') as f:
                self.trait_catalog = json.load(f)
                
        # Load stamina configuration
        stamina_config_path = self.config.get(
            "paths.stamina_integration_config", 
            "config/stamina_integration_config.json"
        )
        
        try:
            import json
            with open(stamina_config_path, 'r') as f:
                self.stamina_config = json.load(f)
        except Exception as e:
            self.logger.warning(f"Failed to load stamina integration config: {e}")
            # Use default configuration
            self.stamina_config = {
                "trait_costs": {
                    "default": 5.0,
                    "low": 2.0,
                    "medium": 5.0,
                    "high": 10.0,
                    "extreme": 15.0
                },
                "threshold_restrictions": {
                    "60": ["extreme"],  # At 60% stamina, restrict extreme cost traits
                    "40": ["extreme", "high"],  # At 40%, restrict high and extreme
                    "20": ["extreme", "high", "medium"]  # At 20%, only allow low cost traits
                },
                "fatigue_effectiveness": {
                    "60": 0.9,  # 90% effectiveness at minor fatigue
                    "40": 0.75,  # 75% effectiveness at moderate fatigue
                    "20": 0.5   # 50% effectiveness at severe fatigue
                }
            }
            
    def can_activate_trait(self, character: Dict[str, Any], trait_id: str, 
                          match_context: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Check if a trait can be activated based on character's current stamina.
        
        Args:
            character: Character data dictionary
            trait_id: ID of the trait to check
            match_context: Current match context
            
        Returns:
            Tuple of (can_activate, reason)
            - can_activate: Boolean indicating if trait can be activated
            - reason: Optional string explaining why trait cannot be activated
        """
        # Get trait data
        trait_data = self._get_trait_data(trait_id)
        if not trait_data:
            return False, f"Trait {trait_id} not found in catalog"
            
        # Get current stamina
        current_stamina = character.get("stamina", 0)
        
        # Get stamina cost
        stamina_cost = self.calculate_trait_stamina_cost(character, trait_id, trait_data)
        
        # Check if character has enough stamina
        if current_stamina < stamina_cost:
            return False, f"Insufficient stamina ({current_stamina:.1f}/{stamina_cost:.1f})"
            
        # Check threshold restrictions
        trait_cost_level = trait_data.get("stamina_cost", "medium")
        
        # Check each threshold from highest to lowest
        thresholds = sorted([int(t) for t in self.stamina_config["threshold_restrictions"].keys()], 
                           reverse=False)
        
        for threshold in thresholds:
            if current_stamina <= threshold:
                restricted_levels = self.stamina_config["threshold_restrictions"][str(threshold)]
                if trait_cost_level in restricted_levels:
                    return False, f"Trait {trait_id} ({trait_cost_level}) restricted at stamina {current_stamina:.1f}"
        
        # If we got here, trait can be activated
        return True, None
        
    def calculate_trait_stamina_cost(self, character: Dict[str, Any], trait_id: str, 
                                    trait_data: Optional[Dict[str, Any]] = None) -> float:
        """
        Calculate the stamina cost for activating a specific trait.
        
        Args:
            character: Character data dictionary
            trait_id: ID of the trait
            trait_data: Optional trait data (if already fetched)
            
        Returns:
            Calculated stamina cost
        """
        if not trait_data:
            trait_data = self._get_trait_data(trait_id)
            if not trait_data:
                # Use default cost for unknown traits
                self.logger.warning(f"Trait {trait_id} not found, using default cost")
                return self.stamina_config["trait_costs"]["default"]
        
        # Get base cost by trait cost level
        cost_level = trait_data.get("stamina_cost", "medium")
        base_cost = self.stamina_config["trait_costs"].get(cost_level, 
                                                         self.stamina_config["trait_costs"]["medium"])
        
        # Apply character's willpower modifier if available
        if "aWIL" in character:
            # Higher willpower reduces stamina cost
            willpower_mod = 1.0 - (max(0, character["aWIL"] - 50) / 200.0)
            base_cost *= max(0.5, willpower_mod)  # Cap at 50% reduction
            
        # Apply any trait-specific modifiers
        if "stamina_cost_mod" in trait_data:
            base_cost *= trait_data["stamina_cost_mod"]
            
        # Round to 1 decimal place
        return round(base_cost, 1)
        
    def apply_trait_stamina_cost(self, character: Dict[str, Any], trait_id: str, 
                                activation_result: Dict[str, Any], match_context: Dict[str, Any]) -> None:
        """
        Apply stamina cost after a trait is activated.
        
        Args:
            character: Character data dictionary
            trait_id: ID of the activated trait
            activation_result: Result data from trait activation
            match_context: Current match context
        """
        # Calculate stamina cost
        trait_data = self._get_trait_data(trait_id)
        stamina_cost = self.calculate_trait_stamina_cost(character, trait_id, trait_data)
        
        # Apply the cost using stamina system
        self.stamina_system.apply_stamina_cost(
            character, 
            stamina_cost, 
            f"trait_activation:{trait_id}", 
            match_context
        )
        
        # Log the cost
        self.logger.debug(f"Applied stamina cost {stamina_cost} for trait {trait_id} to {character.get('name', 'Unknown')}")
        
    def calculate_trait_effectiveness(self, character: Dict[str, Any], trait_id: str) -> float:
        """
        Calculate effectiveness modifier for trait based on current stamina level.
        
        Args:
            character: Character data dictionary
            trait_id: ID of the trait
            
        Returns:
            Effectiveness modifier (1.0 = 100% effective)
        """
        # Get current stamina
        current_stamina = character.get("stamina", 0)
        
        # Default effectiveness = 100%
        effectiveness = 1.0
        
        # Apply stamina-based effectiveness modifiers
        thresholds = sorted([int(t) for t in self.stamina_config["fatigue_effectiveness"].keys()], 
                           reverse=False)
        
        for threshold in thresholds:
            if current_stamina <= threshold:
                effectiveness = self.stamina_config["fatigue_effectiveness"][str(threshold)]
        
        return effectiveness
        
    def _get_trait_data(self, trait_id: str) -> Optional[Dict[str, Any]]:
        """Get trait data from catalog"""
        # Try trait system first if available
        if hasattr(self.trait_system, "get_trait"):
            return self.trait_system.get_trait(trait_id)
            
        # Fall back to catalog lookup
        for trait in self.trait_catalog:
            if trait.get("trait_id") == trait_id:
                return trait
                
        return None
