# xp_progression_engine.py
# Tracks XP gain, handles level-up thresholds, and unlockable traits/stat buffs

from typing import Dict

LEVEL_THRESHOLDS = [0, 50, 120, 200, 300, 450]  # Level 0 to 5+
LEVEL_REWARDS = {
    1: {"unlock": "trait_slot_2"},
    2: {"bonus_stat": "aINT", "amount": 0.1},
    3: {"unlock": "trait_slot_3"},
    4: {"bonus_stat": "aLCK", "amount": 0.1},
    5: {"unlock": "elite_mode"}
}


def evaluate_xp(unit: Dict, gained_xp: int) -> Dict:
    """
    Applies XP to a unit and handles level-up logic.
    Returns updated unit with XP and rewards.
    """
    current_xp = unit.get("XP", 0)
    current_level = unit.get("level", 0)
    new_xp = current_xp + gained_xp

    unit["XP"] = new_xp
    new_level = current_level

    for i in range(len(LEVEL_THRESHOLDS)):
        if new_xp >= LEVEL_THRESHOLDS[i]:
            new_level = i

    if new_level > current_level:
        unit["level"] = new_level
        rewards = LEVEL_REWARDS.get(new_level, {})
        if "unlock" in rewards:
            unit.setdefault("unlocks", []).append(rewards["unlock"])
        if "bonus_stat" in rewards:
            stat = rewards["bonus_stat"]
            unit.setdefault("aStats", {})[stat] = unit["aStats"].get(stat, 0) + rewards["amount"]

    return unit


# Example usage
if __name__ == "__main__":
    unit = {"id": "U12", "XP": 110, "level": 1, "aStats": {"aINT": 0.5}, "unlocks": []}
    result = evaluate_xp(unit, gained_xp=25)
    print("Updated Unit:", result)
