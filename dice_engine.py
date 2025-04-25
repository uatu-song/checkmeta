# dice_engine.py
# Centralized probability engine for trait-based d20 rolls, contested rolls, and chance-based triggers

import random
from typing import Dict

D20 = 20


def roll_d20(modifier: int = 0, floor: int = 1, ceiling: int = D20) -> int:
    """
    Rolls a d20 with optional additive modifier.
    Clamped between floor and ceiling.
    """
    base = random.randint(1, D20)
    return max(floor, min(base + modifier, ceiling))


def contested_roll(attacker_mod: int, defender_mod: int) -> Dict[str, int]:
    """
    Performs a contested d20 roll between two parties.
    Returns detailed result with winner.
    """
    roll_att = roll_d20(modifier=attacker_mod)
    roll_def = roll_d20(modifier=defender_mod)

    result = {
        "attacker": roll_att,
        "defender": roll_def,
        "winner": "attacker" if roll_att > roll_def else "defender" if roll_def > roll_att else "draw"
    }
    return result


def probability_trigger(chance_percent: float) -> bool:
    """
    Simple percent-based probability trigger.
    """
    return random.uniform(0, 100) <= chance_percent


# Example roll outputs
if __name__ == "__main__":
    print("d20 Roll (mod +2):", roll_d20(modifier=2))
    print("Contested Roll:", contested_roll(3, 1))
    print("Trigger 30% Chance:", probability_trigger(30.0))