# convergence_trait_engine.py
# Evaluates convergence conditions and applies trait-driven effects via d20 rolls

import random

D20_BASE = 20


def roll_d20(skew: int = 0) -> int:
    """
    Rolls a d20 with optional skew. Positive skew favors higher rolls.
    """
    raw = random.randint(1, D20_BASE)
    adjusted = min(max(raw + skew, 1), D20_BASE)
    return adjusted


def evaluate_convergence(unit: dict, material_loss: int) -> dict:
    """
    Evaluates convergence events triggered by material loss.
    Applies trait effects via d20 roll results.
    Returns convergence summary.
    """
    traits = unit.get("traits", [])
    aStats = unit.get("aStats", {})

    # Basic convergence trigger condition (tunable)
    triggered = material_loss >= 5
    result = {
        "triggered": triggered,
        "roll": None,
        "outcome": "none",
        "modifiers": []
    }

    if not triggered:
        return result

    # Apply aStats-based modifier (e.g., intelligence, focus, luck)
    skew = int((aStats.get("aINT", 0) + aStats.get("aLCK", 0)) * 4)
    roll = roll_d20(skew)
    result["roll"] = roll
    result["modifiers"] = [
        {"source": "aINT+aLCK", "value": skew, "reason": "convergence modifier"}
    ]

    if roll >= 18:
        result["outcome"] = "critical_success"
    elif roll >= 10:
        result["outcome"] = "success"
    elif roll >= 5:
        result["outcome"] = "partial"
    else:
        result["outcome"] = "failure"

    return result


# Example run
if __name__ == "__main__":
    unit = {
        "id": "unit_77",
        "aStats": {"aINT": 0.8, "aLCK": 0.4},
        "traits": ["flanking"]
    }
    outcome = evaluate_convergence(unit, material_loss=6)
    print("Convergence Result:", outcome)