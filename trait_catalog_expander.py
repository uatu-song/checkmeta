# trait_catalog_expander.py
# Trait payload expander for HP, stamina, life, morale, XP impact, and behavioral hooks

from typing import Dict, List

# Example schema for expanding a trait into its active simulation effects
TRAIT_EFFECTS = {
    "regenerative_core": {"stamina_regen": 5, "hp_regen": 2},
    "berserker": {"stamina_cost": 10, "hp_boost": 5, "life_cost": 1},
    "tactician": {"xp_gain_multiplier": 1.5, "morale_boost": 1},
    "coward": {"morale_loss_on_damage": 2, "escape_roll_bonus": 3},
    "shield_wall": {"damage_reduction": 0.25, "stamina_drain_reduction": 0.2}
}


def expand_trait_payloads(traits: List[str]) -> Dict[str, float]:
    """
    Expands traits into cumulative effect dictionary.
    """
    effects = {}
    for trait in traits:
        modifiers = TRAIT_EFFECTS.get(trait, {})
        for key, val in modifiers.items():
            effects[key] = effects.get(key, 0) + val
    return effects


# Example usage
if __name__ == "__main__":
    test_traits = ["regenerative_core", "tactician"]
    expanded = expand_trait_payloads(test_traits)
    print("Expanded Trait Effects:", expanded)
