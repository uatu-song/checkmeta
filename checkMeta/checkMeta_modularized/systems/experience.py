# systems/experience.py

def award_xp(unit: dict, match_outcome: str) -> None:
    xp = unit.get("xp", 0)
    if match_outcome == "win":
        xp += 50
    elif match_outcome == "draw":
        xp += 20
    else:
        xp += 10
    unit["xp"] = xp
