# status_metric_engine.py
# Central engine for processing and modifying HP, stamina, life, and morale based on traits and match effects

from typing import Dict
from trait_catalog_expander import expand_trait_payloads

DEFAULTS = {
    "HP": 100,
    "stamina": 100,
    "life": 10,
    "morale": 5
}


def apply_status_modifiers(unit: Dict, events: Dict = None) -> Dict:
    """
    Applies trait-driven effects and event-driven drains or gains.
    Returns updated unit object.
    """
    events = events or {}
    traits = unit.get("traits", [])
    status = unit.copy()
    effects = expand_trait_payloads(traits)

    # Regen / Recovery
    status["HP"] = min(DEFAULTS["HP"], status.get("HP", 0) + effects.get("hp_regen", 0))
    status["stamina"] = min(DEFAULTS["stamina"], status.get("stamina", 0) + effects.get("stamina_regen", 0))
    status["morale"] = min(10, status.get("morale", 5) + effects.get("morale_boost", 0))

    # Event-Driven Losses
    if events.get("damage_taken"):
        dmg = events["damage_taken"]
        status["HP"] = max(0, status["HP"] - dmg)
        if "morale_loss_on_damage" in effects:
            status["morale"] = max(0, status["morale"] - effects["morale_loss_on_damage"])

    if events.get("stamina_cost"):
        status["stamina"] = max(0, status["stamina"] - events["stamina_cost"])

    if events.get("life_cost"):
        status["life"] = max(0, status["life"] - events["life_cost"])

    # Death check
    if status["HP"] <= 5 or status["stamina"] == 0 or status["life"] == 0:
        status["status"] = "dead"

    return status


# Example
if __name__ == "__main__":
    unit = {"id": "U23", "HP": 90, "stamina": 50, "life": 8, "morale": 4, "traits": ["regenerative_core", "coward"]}
    events = {"damage_taken": 10, "stamina_cost": 15}
    updated = apply_status_modifiers(unit, events)
    print("Updated Status:", updated)
