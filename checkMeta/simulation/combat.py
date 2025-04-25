###############################
# simulation/combat.py
###############################
"""
Combat calculations for META League Simulator
"""

import random
import math
from typing import Dict, Any, Optional, List
from ..models.character import Character

class CombatSystem:
    """System for handling combat calculations"""
    
    def __init__(self, trait_system=None, morale_system=None):
        """Initialize the combat system"""
        self.trait_system = trait_system
        self.morale_system = morale_system
    
    def calculate_combat_roll(self, attacker: Character, defender: Character, 
                            context: Dict[str, Any] = None) -> int:
        """Calculate a combat roll for a character"""
        if context is None:
            context = {}
            
        # Base roll (1-100)
        roll = random.randint(1, 100)
        
        # Add attacker's attributes
        roll += attacker.get_attribute('STR') + attacker.get_attribute('FS')
        
        # Apply Operation Potential scaling
        op_factor = attacker.get_attribute('OP') / 5.0
        roll = int(roll * op_factor)
        
        # Add morale modifier
        if hasattr(attacker, 'morale_modifiers') and attacker.morale_modifiers:
            roll += attacker.morale_modifiers.get("combat_bonus", 0)
        
        # Add synergy modifier
        if hasattr(attacker, 'team_synergy') and attacker.team_synergy:
            roll += attacker.team_synergy.get("combat_bonus", 0)
        
        # Apply special abilities based on situation
        if hasattr(attacker, 'team_affiliation_bonuses') and attacker.team_affiliation_bonuses:
            special_ability = attacker.team_affiliation_bonuses.get("special_ability")
            
            # Avengers get stronger when backed into a corner
            if special_ability == "avengers_assemble" and attacker.hp < 30:
                roll += 15
                context["special_ability_triggered"] = "avengers_assemble"
        
        # Apply trait effects if trait system is available
        if self.trait_system:
            trait_context = {"roll": roll, "opponent": defender}
            trait_context.update(context)
            
            trait_effects = self.trait_system.apply_trait_effect(
                attacker, "combat_roll", trait_context
            )
            
            # Process trait effects
            for effect in trait_effects:
                if effect.get("effect") == "combat_bonus":
                    roll += effect.get("value", 0)
                elif effect.get("effect") == "reroll" and "reroll" not in context:
                    # Prevent recursive rerolls by checking context
                    reroll_context = trait_context.copy()
                    reroll_context["reroll"] = True
                    
                    # Generate new roll
                    new_roll = self.calculate_combat_roll(attacker, defender, reroll_context)
                    
                    # Take better roll
                    roll = max(roll, new_roll)
        
        return roll
    
    def calculate_damage(self, base_damage: float, attacker: Character, defender: Character) -> Dict[str, Any]:
        """Calculate damage after all modifiers"""
        # Start with base damage
        damage = base_damage
        damage_reduction = 0
        
        # Get damage reduction from defender's traits
        if self.trait_system:
            trait_effects = self.trait_system.apply_trait_effect(
                defender, "damage_taken", {"damage": damage, "attacker": attacker}
            )
            
            for effect in trait_effects:
                if effect.get("effect") == "damage_reduction":
                    damage_reduction += effect.get("value", 0)
        
        # Apply morale modifier to damage reduction
        if hasattr(defender, 'morale_modifiers') and defender.morale_modifiers:
            damage_reduction += defender.morale_modifiers.get("damage_reduction", 0)
        
        # Apply team synergy to damage reduction
        if hasattr(defender, 'team_synergy') and defender.team_synergy:
            damage_reduction += defender.team_synergy.get("damage_reduction", 0)
        
        # Apply DUR/RES stat bonuses
        dur_bonus = (defender.get_attribute('DUR') - 5) * 10  # 10% per point
        res_bonus = (defender.get_attribute('RES') - 5) * 8   # 8% per point
        
        # Base reduction for all characters
        base_reduction = 30
        total_reduction = min(85, max(0, damage_reduction + dur_bonus + res_bonus + base_reduction))
        
        # Apply damage to defender
        actual_damage = max(1, damage * (1 - total_reduction/100.0))
        result = defender.take_damage(actual_damage)
        
        # Add additional information to result
        result.update({
            "attacker": attacker.name,
            "defender": defender.name,
            "base_damage": damage,
            "damage_reduction_percent": total_reduction,
            "dur_bonus": dur_bonus,
            "res_bonus": res_bonus,
            "trait_reduction": damage_reduction
        })
        
        return result
    
    def calculate_convergence_damage(self, winner_roll: int, loser_roll: int) -> float:
        """Calculate damage from a convergence with diminishing returns"""
        diff = winner_roll - loser_roll
        # Use a logarithmic scale to reduce extreme differences
        damage = max(0, 3 * math.log(1 + diff/10))
        return damage
    
    def _update_character_metrics(self, character: Character, material_change: int, show_details: bool = False) -> None:
    """Update character metrics based on material change"""
    # Material loss = damage
    if material_change < 0:
        # BALANCE: Reduce damage scaling from material loss
        damage = abs(material_change) * 3  # Reduced from 5 to 3
        
        # Get damage reduction from traits
        damage_reduction = 0
        for trait_name in character.traits:
            if trait_name in self.trait_system.traits:
                trait = self.trait_system.traits[trait_name]
                if trait.get("formula_key") == "damage_reduction":
                    damage_reduction += trait.get("value", 0)
        
        # Apply damage
        damage_result = character.take_damage(damage, damage_reduction)
        
        # Update rStats for damage sustained
        character.r_stats.setdefault("rDSo" if character.division == "o" else "rDSi", 0)
        character.r_stats["rDSo" if character.division == "o" else "rDSi"] += damage_result["reduced_damage"]
        
        if show_details:
            print(f"  {character.name} HP: {character.hp}, Stamina: {character.stamina}, Life: {character.life}")
    
    # Material gain = damage dealt to opponent
    elif material_change > 0:
        # BALANCE: Reduce damage scaling for stats
        damage_dealt = material_change * 3  # Reduced from 5 to 3
        
        # Update rStats for damage dealt
        character.r_stats.setdefault("rDDo" if character.division == "o" else "rDDi", 0)
        character.r_stats["rDDo" if character.division == "o" else "rDDi"] += damage_dealt
    
    # Higher stamina cost with aStats influence
    base_stamina_cost = 1.5  # Increased from 0.5 to 1.5
    
    # Apply aStats modifiers to stamina cost
    dur_factor = max(0.7, 1.0 - (character.get_attribute('DUR') - 5) * 0.05)  # 5% reduction per DUR above 5, min 30% cost
    res_factor = max(0.7, 1.0 - (character.get_attribute('RES') - 5) * 0.03)  # 3% reduction per RES above 5, min 30% cost
    wil_factor = max(0.7, 1.0 - (character.get_attribute('WIL') - 5) * 0.08)  # 8% reduction per WIL above 5, min 30% cost
    
    # Combined factor - multiply all factors together
    combined_factor = dur_factor * res_factor * wil_factor
    
    # Apply stamina cost with aStats influence
    stamina_cost = base_stamina_cost * combined_factor
    
    character.stamina = max(0, character.stamina - stamina_cost)