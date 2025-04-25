# checkMeta_core_engine.py
# Entry point for the checkMeta Tactical Simulation Engine

from life_state_scaffold import inject_life_meter, is_unit_dead


def initialize_unit_state(unit_profile: dict) -> dict:
    """
    Builds the full unit state object from profile.
    Injects HP, stamina, and life defaults.
    """
    state = {
        "id": unit_profile["id"],
        "role": unit_profile["role"],
        "traits": unit_profile.get("traits", []),
        "aStats": unit_profile.get("aStats", {}),
        "HP": unit_profile.get("HP", 100),
        "stamina": unit_profile.get("stamina", 100),
        "life": unit_profile.get("life", 10),
        "status": "active"
    }
    return inject_life_meter(state)


def evaluate_post_match(unit_state: dict) -> dict:
    """
    Apply end-of-match damage, stamina drain, and assess death condition.
    """
    # Placeholder logic for simulation result impact
    unit_state["HP"] -= 5
    unit_state["stamina"] -= 10
    unit_state["life"] -= 1

    if is_unit_dead(unit_state):
        unit_state["status"] = "dead"
    return unit_state


if __name__ == "__main__":
    example_unit = {
        "id": "unit_04",
        "role": "GO",
        "traits": ["regenerative_core"],
        "aStats": {"aINT": 0.8, "aESP": 0.7}
    }

    state = initialize_unit_state(example_unit)
    print("Initialized:", state)

    post_state = evaluate_post_match(state)
    print("After Match:", post_state)
