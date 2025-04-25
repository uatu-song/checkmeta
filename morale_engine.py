# morale_engine.py
# Tracks and modifies unit and team morale based on match events and traits

from typing import Dict, List


def update_unit_morale(unit: Dict, events: Dict) -> Dict:
    """
    Modifies morale based on match events and traits.
    """
    morale = unit.get("morale", 5)

    # Morale effects
    if events.get("won_match"):
        morale += 1
    if events.get("lost_match"):
        morale -= 1
    if events.get("ally_FL_died"):
        morale -= 2

    # Clamp to 0–10
    unit["morale"] = max(0, min(10, morale))
    return unit


def teamwide_morale_shift(team: List[Dict], team_events: Dict) -> List[Dict]:
    """
    Applies team-level morale changes to all members.
    """
    for unit in team:
        unit = update_unit_morale(unit, team_events)
    return team


# Example
if __name__ == "__main__":
    team = [
        {"id": "U1", "morale": 6},
        {"id": "U2", "morale": 7}
    ]
    result = teamwide_morale_shift(team, {"lost_match": True, "ally_FL_died": True})
    print("Team Morale Post-Match:", result)
