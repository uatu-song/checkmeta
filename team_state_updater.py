# team_state_updater.py
# Applies simulation results to persistent team state: HP, stamina, life, status, XP, and rStats

from typing import List, Dict

def update_team_state(team: List[dict], match_results: List[dict], side: str) -> List[dict]:
    """
    Applies match results to units on one side ("white" or "black").
    Updates HP, stamina, life, status, and logs rStats.
    """
    unit_map = {unit["id"]: unit for unit in team}

    for match in match_results:
        unit = match["match"][side]
        uid = unit["id"]
        if uid in unit_map:
            team_unit = unit_map[uid]
            team_unit.update({
                "HP": unit.get("HP"),
                "stamina": unit.get("stamina"),
                "life": unit.get("life"),
                "status": unit.get("status", "active")
            })

            # Apply rStats
            if "rStats" not in team_unit:
                team_unit["rStats"] = {}
            for stat, val in match["rStats"][side].items():
                team_unit["rStats"][stat] = team_unit["rStats"].get(stat, 0) + val

            # Simple XP bump (placeholder logic)
            team_unit["XP"] = team_unit.get("XP", 0) + 10

    return list(unit_map.values())


# Example test call
if __name__ == "__main__":
    team = [{"id": "unit_1", "HP": 100, "stamina": 100, "life": 10, "rStats": {}, "XP": 0}]
    result = {
        "match": {"white": {"id": "unit_1", "HP": 90, "stamina": 85, "life": 9, "status": "active"}},
        "rStats": {"white": {"rDD": 3, "rULT": 1}}
    }
    updated = update_team_state(team, [result], side="white")
    print("Updated Team:", updated)
