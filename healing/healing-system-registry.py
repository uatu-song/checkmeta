"""
META Fantasy League Simulator v5.0
Healing System Registry Integration

This module initializes and registers the healing system and its stamina integration
with the system registry.
"""

import os
import logging
from typing import Dict, Any, Optional

# Import required systems
from system_registry import SystemRegistry
from healing_mechanics import HealingMechanics
from healing_stamina_integrator import HealingStaminaIntegrator

# Import base systems that healing depends on
from injury_system import InjurySystem
from stamina_system import StaminaSystem

logger = logging.getLogger("HEALING_SYSTEM_REGISTRY")

def register_healing_system(registry: SystemRegistry, config: Dict[str, Any]) -> bool:
    """
    Register the healing system and its stamina integration with the system registry.
    
    Args:
        registry: System registry
        config: Configuration dictionary
        
    Returns:
        bool: Success of registration
    """
    logger.info("Registering healing system and integrations...")
    
    # Check if healing is enabled in config
    if not config.get("features", {}).get("healing_enabled", False):
        logger.info("Healing system is disabled in configuration. Skipping registration.")
        return False
    
    # Check for required dependencies
    injury_system = registry.get("injury_system")
    if not injury_system:
        logger.error("Healing system requires injury system, but it is not registered.")
        return False
    
    stamina_system = registry.get("stamina_system")
    if not stamina_system:
        logger.warning("Healing system requires stamina system for full functionality, but it is not registered.")
        # Continue anyway, will have reduced functionality
    
    try:
        # Create healing mechanics system
        healing_mechanics = HealingMechanics(injury_system=injury_system, config=config)
        
        # Register healing mechanics in registry
        registry.register("healing_mechanics", healing_mechanics, dependencies=["injury_system"])
        logger.info("Healing mechanics registered successfully.")
        
        # If stamina system is available, register the integrator
        if stamina_system:
            # Create healing-stamina integrator
            healing_stamina_integrator = HealingStaminaIntegrator(config, registry)
            
            # Register healing-stamina integrator in registry
            registry.register(
                "healing_stamina_integrator", 
                healing_stamina_integrator, 
                dependencies=["healing_mechanics", "stamina_system"]
            )
            logger.info("Healing-stamina integrator registered successfully.")
        
        return True
    except Exception as e:
        logger.error(f"Error registering healing system: {e}")
        return False

def initialize_healing_system(registry: SystemRegistry) -> bool:
    """
    Initialize and activate the healing system and its stamina integration.
    
    Args:
        registry: System registry
        
    Returns:
        bool: Success of initialization
    """
    logger.info("Initializing healing system and integrations...")
    
    try:
        # Activate healing mechanics
        if registry.is_active("healing_mechanics"):
            logger.info("Healing mechanics already active.")
        else:
            success = registry.activate("healing_mechanics")
            if not success:
                logger.error("Failed to activate healing mechanics.")
                return False
            logger.info("Healing mechanics activated successfully.")
        
        # Activate healing-stamina integrator if available
        if "healing_stamina_integrator" in registry._systems:
            if registry.is_active("healing_stamina_integrator"):
                logger.info("Healing-stamina integrator already active.")
            else:
                success = registry.activate("healing_stamina_integrator")
                if not success:
                    logger.error("Failed to activate healing-stamina integrator.")
                    # Continue anyway, healing will work without stamina integration
                else:
                    logger.info("Healing-stamina integrator activated successfully.")
        
        return True
    except Exception as e:
        logger.error(f"Error initializing healing system: {e}")
        return False

def healing_system_status(registry: SystemRegistry) -> Dict[str, Any]:
    """
    Get status report for healing system and its integrations.
    
    Args:
        registry: System registry
        
    Returns:
        dict: Status report
    """
    status = {
        "healing_mechanics_registered": "healing_mechanics" in registry._systems,
        "healing_mechanics_active": registry.is_active("healing_mechanics"),
        "healing_stamina_integration_registered": "healing_stamina_integrator" in registry._systems,
        "healing_stamina_integration_active": registry.is_active("healing_stamina_integrator"),
        "injury_system_available": registry.get("injury_system") is not None,
        "stamina_system_available": registry.get("stamina_system") is not None
    }
    
    # Add capabilities info
    capabilities = []
    
    if status["healing_mechanics_active"]:
        capabilities.append("Basic healing")
        capabilities.append("Injury treatment")
        
        if status["healing_stamina_integration_active"]:
            capabilities.append("Stamina-based healing success")
            capabilities.append("Healing stamina costs")
            capabilities.append("Post-healing stamina effects")
            capabilities.append("Enhanced overnight recovery")
    
    status["capabilities"] = capabilities
    
    return status

def add_healing_to_simulator(simulator):
    """
    Add healing system to an existing simulator instance.
    
    Args:
        simulator: Simulator instance
        
    Returns:
        bool: Success of addition
    """
    try:
        # Get registry from simulator
        registry = simulator.registry
        
        # Register healing system
        success = register_healing_system(registry, simulator.config)
        if not success:
            return False
        
        # Initialize healing system
        success = initialize_healing_system(registry)
        if not success:
            return False
        
        # Add healing methods to simulator for convenience
        simulator.heal_character = lambda healer, injured: registry.get("healing_mechanics").attempt_healing(healer, injured)
        simulator.heal_team = lambda team: registry.get("healing_mechanics").heal_team_injuries(team)
        simulator.identify_healers = lambda team: registry.get("healing_mechanics").identify_healers(team)
        
        # Add stamina-aware overnight simulation if available
        if registry.is_active("healing_stamina_integrator"):
            simulator.simulate_overnight_healing = lambda team: registry.get("healing_stamina_integrator").simulate_overnight_healing_recovery(team)
        
        return True
    except Exception as e:
        logger.error(f"Error adding healing to simulator: {e}")
        return False
