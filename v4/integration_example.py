"""
META Fantasy League Simulator - Integration Example
Example of integrating SynergyEngine into the MetaLeagueSimulator
"""

from meta_simulator_v4 import MetaLeagueSimulator
from synergy_integration import SynergyIntegration

def integrate_synergy_system():
    """
    Example function showing how to integrate the synergy system
    into the existing MetaLeagueSimulator
    """
    # Initialize simulator
    simulator = MetaLeagueSimulator()
    
    # Initialize and activate synergy integration
    synergy_integration = SynergyIntegration(simulator)
    result = synergy_integration.activate()
    
    if result:
        print("✅ Synergy system successfully integrated!")
    else:
        print("❌ Failed to integrate synergy system")
    
    return simulator

def enhance_existing_simulator(simulator):
    """
    Example function showing how to enhance an existing simulator instance
    with the synergy system
    
    Args:
        simulator: Existing MetaLeagueSimulator instance
    
    Returns:
        bool: Success status
    """
    # Initialize and activate synergy integration
    synergy_integration = SynergyIntegration(simulator)
    result = synergy_integration.activate()
    
    if result:
        print("✅ Synergy system successfully integrated into existing simulator!")
    else:
        print("❌ Failed to integrate synergy system")
    
    return result

# Example usage:
if __name__ == "__main__":
    # Create a new simulator with synergy system
    simulator = integrate_synergy_system()
    
    # Run a simulation with synergy effects
    # This will now automatically detect and apply synergies
    # and track character dynamics throughout the match
    day_number = 1
    simulator.run_matchday(day_number=day_number, show_details=True)
    
    print(f"Completed day {day_number} with synergy system active!")