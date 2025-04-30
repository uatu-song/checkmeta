"""
META Fantasy League Simulator - Stamina System Integration Example
=================================================================

This file demonstrates how to integrate the stamina system with the META League Simulator's
other systems, including combat, traits, and convergence.
"""

import json
import logging
from typing import Dict, List, Any

# Import required system components
from system_registry import SystemRegistry
from config_manager import ConfigurationManager
from stamina_system import StaminaSystem
from trait_system import TraitSystem  # Hypothetical trait system
from combat_system import CombatSystem  # Hypothetical combat system
from convergence_system import ConvergenceSystem  # Hypothetical convergence system

# Set up logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("StaminaIntegration")

def integrate_stamina_with_simulator():
    """Example of integrating stamina system with the simulator"""
    # Create configuration manager
    config = ConfigurationManager("config/config.json")
    
    # Create system registry
    registry = SystemRegistry()
    
    # Initialize and register stamina system
    stamina_system = StaminaSystem(config, registry)
    registry.register("stamina_system", stamina_system)
    
    # Initialize and register trait system (with stamina integration)
    trait_system = TraitSystemWithStamina(config, registry)
    registry.register("trait_system", trait_system)
    
    # Initialize and register combat system (with stamina integration)
    combat_system = CombatSystemWithStamina(config, registry)
    registry.register("combat_system", combat_system)
    
    # Initialize and register convergence system (with stamina integration)
    convergence_system = ConvergenceSystemWithStamina(config, registry)
    registry.register("convergence_system", convergence_system)
    
    # Activate all systems
    registry.activate("stamina_system")
    registry.activate("trait_system")
    registry.activate("combat_system")
    registry.activate("convergence_system")
    
    logger.info("All systems initialized and activated")
    
    return registry

# Example extension of trait system with stamina integration
class TraitSystemWithStamina(TraitSystem):
    """Extension of TraitSystem with stamina integration"""
    
    def activate_trait(self, character, trait_name, match_context):
        """Activate a trait with stamina cost
        
        Args:
            character: The character activating the trait
            trait_name: The name of the trait
            match_context: The current match context
            
        Returns:
            (bool, str): Whether the trait was activated and a message
        """
        # Get trait details
        trait = self.get_trait(trait_name)
        if not trait:
            return False, f"Trait {trait_name} not found"
        
        # Get stamina system
        stamina_system = self.registry.get("stamina_system")
        if not stamina_system:
            logger.warning("Stamina system not available for trait activation")
            return super().activate_trait(character, trait_name, match_context)
        
        # Check if character has enough stamina
        stamina_cost = trait.get("stamina_cost", 5.0)  # Default cost
        can_use, reason = stamina_system.can_use_trait(character, trait_name, stamina_cost)
        
        if not can_use:
            logger.info(f"Trait {trait_name} activation failed: {reason}")
            return False, reason
        
        # Adjust activation chance based on stamina
        base_chance = trait.get("activation_chance", 0.8)
        modified_chance = stamina_system.calculate_trait_chance_modifier(character, base_chance)
        
        # Attempt to activate with modified chance
        activated, message = self._roll_trait_activation(modified_chance)
        
        if activated:
            # Apply stamina cost if trait activated
            stamina_system.apply_stamina_cost(
                character,
                stamina_cost,
                f"trait_activation:{trait_name}",
                match_context
            )
            
            # Apply trait effects
            return self._apply_trait_effects(character, trait, match_context)
        else:
            return False, message
    
    def _roll_trait_activation(self, chance):
        """Roll for trait activation based on chance"""
        import random
        
        roll = random.random()
        if roll <= chance:
            return True, "Trait activated successfully"
        else:
            return False, "Trait activation failed (random chance)"
    
    def _apply_trait_effects(self, character, trait, match_context):
        """Apply trait effects (placeholder implementation)"""
        logger.info(f"Applying effects for trait {trait['name']}")
        return True, f"Trait {trait['name']} activated successfully"
    
    def get_trait_cost_category(self, trait_name):
        """Get the cost category of a trait
        
        Args:
            trait_name: The name of the trait
            
        Returns:
            str: Cost category ('low', 'medium', 'high', 'extreme')
        """
        trait = self.get_trait(trait_name)
        if not trait:
            return "medium"  # Default
        
        return trait.get("cost_category", "medium")
    
    def get_trait(self, trait_name):
        """Get trait details (placeholder implementation)"""
        # In a real implementation, this would retrieve from a catalog
        # For this example, return dummy data
        return {
            "name": trait_name,
            "activation_chance": 0.8,
            "stamina_cost": 5.0,
            "cost_category": "medium",
            "effects": []
        }

# Example extension of combat system with stamina integration
class CombatSystemWithStamina(CombatSystem):
    """Extension of CombatSystem with stamina integration"""
    
    def update_character_metrics(self, character, material_change, match_context):
        """Update character metrics based on material change
        
        Args:
            character: The character to update
            material_change: The change in material value
            match_context: The current match context
        """
        # Get stamina system
        stamina_system = self.registry.get("stamina_system")
        
        # Calculate stamina cost based on material change magnitude
        # Capturing pieces (positive material change) costs stamina
        if material_change > 0:
            base_cost = abs(material_change) * 0.5  # 0.5 stamina per material point
            
            if stamina_system:
                stamina_system.apply_stamina_cost(
                    character,
                    base_cost,
                    "capturing_piece",
                    match_context
                )
        
        # Call parent implementation
        super().update_character_metrics(character, material_change, match_context)
    
    def apply_damage(self, target_character, damage_amount, source, match_context):
        """Apply damage to a character with stamina factors
        
        Args:
            target_character: The character taking damage
            damage_amount: The base damage amount
            source: The source of the damage
            match_context: The current match context
            
        Returns:
            The actual damage applied
        """
        # Get stamina system
        stamina_system = self.registry.get("stamina_system")
        
        # Apply low stamina penalty if available
        if stamina_system:
            damage_multiplier = stamina_system.get_low_stamina_penalty(target_character)
            damage_amount *= damage_multiplier
            
            if damage_multiplier > 1.0:
                logger.info(f"Character {target_character['name']} takes +{(damage_multiplier-1)*100:.0f}% damage due to low stamina")
        
        # Apply damage
        actual_damage = super().apply_damage(target_character, damage_amount, source, match_context)
        
        # Counterattacking or defending also costs stamina
        if stamina_system and "counter" in source:
            stamina_system.apply_stamina_cost(
                target_character,
                2.0,  # Base cost for counter
                "counter_attack",
                match_context
            )
        
        return actual_damage

# Example extension of convergence system with stamina integration
class ConvergenceSystemWithStamina(ConvergenceSystem):
    """Extension of ConvergenceSystem with stamina integration"""
    
    def process_convergences(self, team_a, team_a_boards, team_b, team_b_boards, match_context, max_per_char=3):
        """Process convergences between boards with stamina costs
        
        Args:
            team_a: Team A characters
            team_a_boards: Team A chess boards
            team_b: Team B characters
            team_b_boards: Team B chess boards
            match_context: The current match context
            max_per_char: Maximum convergences per character
            
        Returns:
            List of processed convergences
        """
        # Get stamina system
        stamina_system = self.registry.get("stamina_system")
        
        # Find potential convergences
        convergences = super().process_convergences(
            team_a, team_a_boards, 
            team_b, team_b_boards, 
            match_context, max_per_char
        )
        
        # Apply stamina costs for convergences
        if stamina_system and convergences:
            for convergence in convergences:
                # Apply cost to initiator
                initiator = convergence.get("initiator")
                if initiator:
                    # Higher leadership reduces stamina cost
                    base_cost = 3.0
                    stamina_system.apply_stamina_cost(
                        initiator,
                        base_cost,
                        "convergence_assist",
                        match_context
                    )
                
                # Apply cost to target
                target = convergence.get("target")
                if target:
                    # Being target costs more stamina
                    base_cost = 5.0
                    stamina_system.apply_stamina_cost(
                        target,
                        base_cost,
                        "convergence_target",
                        match_context
                    )
        
        return convergences
    
    def can_initiate_convergence(self, character, match_context):
        """Check if a character can initiate a convergence based on stamina
        
        Args:
            character: The character who wants to initiate
            match_context: The current match context
            
        Returns:
            (bool, str): Whether convergence can be initiated and reason if not
        """
        # Get stamina system
        stamina_system = self.registry.get("stamina_system")
        if not stamina_system:
            return super().can_initiate_convergence(character, match_context)
        
        # Check if character has enough stamina
        base_cost = 3.0
        current_stamina = character.get("stamina", 0)
        
        if current_stamina < base_cost:
            return False, f"Insufficient stamina: {current_stamina} < {base_cost}"
        
        # Check for severe fatigue effect
        if any(effect.startswith("stamina:severe_fatigue") for effect in character.get("effects", [])):
            return False, "Too fatigued to initiate convergence"
        
        # Call parent implementation for other checks
        return super().can_initiate_convergence(character, match_context)

# Example usage in a match simulation
def simulate_match_with_stamina():
    """Simulate a match with stamina integration"""
    # Set up systems
    registry = integrate_stamina_with_simulator()
    
    # Get systems
    stamina_system = registry.get("stamina_system")
    trait_system = registry.get("trait_system")
    combat_system = registry.get("combat_system")
    convergence_system = registry.get("convergence_system")
    
    # Create test characters
    team_a = [
        {
            "id": "char_a1",
            "name": "Alice",
            "team_id": "team_a",
            "aDUR": 60,  # Above average durability
            "aSTR": 70,  # High strength
            "aLDR": 80   # High leadership
        },
        {
            "id": "char_a2",
            "name": "Bob",
            "team_id": "team_a",
            "aDUR": 50,  # Average durability
            "aSTR": 60,  # Above average strength
            "aLDR": 50   # Average leadership
        }
    ]
    
    team_b = [
        {
            "id": "char_b1",
            "name": "Charlie",
            "team_id": "team_b",
            "aDUR": 70,  # High durability
            "aSTR": 50,  # Average strength
            "aLDR": 60   # Above average leadership
        },
        {
            "id": "char_b2",
            "name": "Diana",
            "team_id": "team_b",
            "aDUR": 40,  # Below average durability
            "aSTR": 80,  # High strength
            "aLDR": 60   # Above average leadership
        }
    ]
    
    # Create test boards (placeholders)
    team_a_boards = [None, None]
    team_b_boards = [None, None]
    
    # Create match context
    match_context = {
        "match_id": "test_match",
        "round": 1,
        "day": 1
    }
    
    # Initialize stamina for all characters
    for character in team_a + team_b:
        stamina_system.initialize_character_stamina(character)
        logger.info(f"Initial stamina for {character['name']}: {character['stamina']}")
    
    # Simulate several rounds
    for round_num in range(1, 11):
        logger.info(f"\n--- Round {round_num} ---")
        match_context["round"] = round_num
        
        # Simulate actions for team A
        for i, character in enumerate(team_a):
            # Attempt to activate a trait
            if round_num % 3 == 1:  # Every 3rd round
                trait_result, message = trait_system.activate_trait(
                    character, "power_strike", match_context
                )
                logger.info(f"{character['name']} trait activation: {message}")
            
            # Simulate material change (capturing a piece)
            if round_num % 2 == 0:  # Even rounds
                material_change = 3  # Captured a piece worth 3 points
                combat_system.update_character_metrics(
                    character, material_change, match_context
                )
                logger.info(f"{character['name']} captured piece: +{material_change} material")
        
        # Simulate actions for team B
        for i, character in enumerate(team_b):
            # Attempt to activate a trait
            if round_num % 3 == 2:  # Different rounds than team A
                trait_result, message = trait_system.activate_trait(
                    character, "defensive_stance", match_context
                )
                logger.info(f"{character['name']} trait activation: {message}")
            
            # Simulate taking damage
            if round_num % 2 == 1:  # Odd rounds
                damage = 10  # Base damage
                actual_damage = combat_system.apply_damage(
                    character, damage, "attack", match_context
                )
                logger.info(f"{character['name']} took {actual_damage} damage")
        
        # Simulate convergence every 5 rounds
        if round_num % 5 == 0:
            # Check if can initiate convergence
            initiator = team_a[0]
            can_converge, reason = convergence_system.can_initiate_convergence(
                initiator, match_context
            )
            
            if can_converge:
                # Process a convergence
                convergences = convergence_system.process_convergences(
                    team_a, team_a_boards,
                    team_b, team_b_boards,
                    match_context
                )
                logger.info(f"Processed {len(convergences)} convergences")
            else:
                logger.info(f"Convergence failed: {reason}")
        
        # Apply end of round effects
        stamina_system.apply_end_of_round_effects(team_a + team_b, match_context)
        
        # Log current stamina
        for character in team_a + team_b:
            logger.info(f"{character['name']} stamina: {character['stamina']:.1f}")
            
            # Log active effects
            if "effects" in character and character["effects"]:
                logger.info(f"{character['name']} effects: {', '.join(character['effects'])}")
    
    # End of match - persist stamina
    for character in team_a + team_b:
        stamina_system.process_match_end(character, "win" if character in team_a else "loss", match_context)
    
    logger.info("Match complete - stamina persisted for future matches")
    
    # Return final state for analysis
    return {
        "team_a": team_a,
        "team_b": team_b,
        "match_context": match_context
    }

if __name__ == "__main__":
    # Run integration example
    result = simulate_match_with_stamina()
    
    # Display final stats
    print("\nFinal Character Stats:")
    print("=====================")
    
    for team_name, team in [("Team A", result["team_a"]), ("Team B", result["team_b"])]:
        print(f"\n{team_name}:")
        for character in team:
            print(f"  {character['name']}:")
            print(f"    - Stamina: {character['stamina']:.1f}")
            print(f"    - Effects: {', '.join(character.get('effects', []))}")
            print(f"    - Stamina Log: {len(character.get('stamina_log', []))} entries")