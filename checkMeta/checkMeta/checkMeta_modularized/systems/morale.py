# systems/morale.py

def adjust_morale(unit: dict, won_match: bool) -> None:
    morale = unit.get("morale", 50)
    morale += 10 if won_match else -5
    morale = max(0, min(100, morale))
    unit["morale"] = morale
