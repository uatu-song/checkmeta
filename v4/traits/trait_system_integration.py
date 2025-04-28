"""
META Fantasy League Simulator - Trait System Integration
Instructions and example for integrating the enhanced trait system
"""

import os
import logging
from typing import Dict, List, Any, Optional

# Import enhanced classes
from enhanced_trait_loader import TraitLoader
from enhanced_trait_system import EnhancedTraitSystem

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TraitSystemIntegration")

def integrate_enhanced_trait_system(simulator):
    """
    Integrate enhanced trait system into the simulator
    
    Args:
        simulator: MetaLeagueSimulator instance
        
    Returns:
        bool: Success status
    """
    try:
        # Create enhanced trait system
        enhanced_system = EnhancedTraitSystem(config=getattr(simulator, "config", None))
        
        # Log trait loading results
        trait_count = enhanced_system.get_trait_count()
        logger.info(f"Enhanced Trait System loaded {trait_count} traits")
        
        # Store reference to old system for fallback
        simulator._old_trait_system = simulator.trait_system
        
        # Replace trait system
        simulator.trait_system = enhanced_system
        
        # Update combat system to use new trait system
        if hasattr(simulator, "combat_system") and simulator.combat_system:
            simulator.combat_system.trait_system = enhanced_system
        
        # Update convergence system to use new trait system
        if hasattr(simulator, "convergence_system") and simulator.convergence_system:
            simulator.convergence_system.trait_system = enhanced_system
        
        logger.info("Enhanced Trait System successfully integrated")
        return True
        
    except Exception as e:
        logger.error(f"Error integrating Enhanced Trait System: {e}")
        
        # Restore old trait system if available
        if hasattr(simulator, "_old_trait_system"):
            simulator.trait_system = simulator._old_trait_system
            
            # Restore references in other systems
            if hasattr(simulator, "combat_system") and simulator.combat_system:
                simulator.combat_system.trait_system = simulator._old_trait_system
            
            if hasattr(simulator, "convergence_system") and simulator.convergence_system:
                simulator.convergence_system.trait_system = simulator._old_trait_system
                
            delattr(simulator, "_old_trait_system")
            
        return False

def add_trait_verification_to_simulator(simulator):
    """
    Add trait verification to the simulator's run_matchday method
    to ensure traits are properly loaded and applied
    
    Args:
        simulator: MetaLeagueSimulator instance
        
    Returns:
        bool: Success status
    """
    try:
        # Store reference to original method
        original_run_matchday = simulator.run_matchday
        
        # Create enhanced method
        def enhanced_run_matchday(day_number=1, lineup_file=None, show_details=True):
            """Enhanced run_matchday with trait verification"""
            # Verify traits are loaded
            if hasattr(simulator.trait_system, "get_trait_count"):
                trait_count = simulator.trait_system.get_trait_count()
                logger.info(f"Trait System has {trait_count} traits loaded")
                
                # Print summary if detailed logging
                if show_details and hasattr(simulator.trait_system, "print_trait_catalog_summary"):
                    simulator.trait_system.print_trait_catalog_summary()
                
                # Verify against expected count
                expected_count = 41  # Expected from full catalog
                if trait_count < expected_count:
                    logger.warning(f"Only {trait_count}/{expected_count} traits loaded. This may affect gameplay.")
            
            # Run original method
            return original_run_matchday(day_number, lineup_file, show_details)
        
        # Replace method
        simulator.run_matchday = enhanced_run_matchday
        simulator._original_run_matchday = original_run_matchday
        
        logger.info("Trait verification successfully added to simulator")
        return True
        
    except Exception as e:
        logger.error(f"Error adding trait verification: {e}")
        return False

# Example usage
if __name__ == "__main__":
    # This would be used in your main script
    try:
        from meta_simulator_v4 import MetaLeagueSimulator
        
        # Initialize simulator
        simulator = MetaLeagueSimulator()
        
        # Integrate enhanced trait system
        success = integrate_enhanced_trait_system(simulator)
        
        if success:
            # Add trait verification
            add_trait_verification_to_simulator(simulator)
            
            # Run simulation
            simulator.run_matchday(day_number=1, show_details=True)
        else:
            print("Failed to integrate enhanced trait system")
            
    except ImportError:
        print("This is an example script. Import the necessary modules in your project.")

# INTEGRATION INSTRUCTIONS
"""
To integrate the enhanced trait system into your META Fantasy League Simulator:

1. Add the following files to your project:
   - enhanced_trait_loader.py
   - enhanced_trait_system.py
   - trait_system_integration.py

2. In your main script, add the following code:

   ```python
   from trait_system_integration import integrate_enhanced_trait_system, add_trait_verification_to_simulator
   
   # Initialize your simulator
   simulator = MetaLeagueSimulator()
   
   # Integrate enhanced trait system
   success = integrate_enhanced_trait_system(simulator)
   
   if success:
       # Add trait verification
       add_trait_verification_to_simulator(simulator)
       
       # Run simulation
       simulator.run_matchday(day_number=1, show_details=True)
   else:
       print("Failed to integrate enhanced trait system")
   ```

3. Verify that traits are being loaded by checking the logs.
   You should see a message like: "Trait System has X traits loaded"

4. If you want to see a full trait summary, run with show_details=True

5. To revert to the original trait system, you can do:
   
   ```python
   simulator.trait_system = simulator._old_trait_system
   simulator.combat_system.trait_system = simulator._old_trait_system
   simulator.convergence_system.trait_system = simulator._old_trait_system
   simulator.run_matchday = simulator._original_run_matchday
   ```

This integration method allows you to:
1. Load all 41 traits from the catalog CSV
2. Reliably parse traits even if the CSV format varies
3. Validate that traits are being loaded correctly
4. Provide detailed logging and debugging information
5. Easily revert to the original system if needed
"""