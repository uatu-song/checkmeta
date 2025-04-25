# fl_substitution_engine.py
# Handles FL-only substitution logic when a Field Leader is knocked out mid-match

from typing import List, Dict, Optional


def find_fl_substitute(bench: List[dict]) -> Optional[dict]:
    """
    Finds the first FL-eligible unit on the bench.
    Assumes role or metadata includes 'FL_eligible': True
    """
    for unit in bench:
        if unit.get("FL_eligible", False):
            return unit
    return None


def apply_fl_substitution(match: dict, bench: List[dict]) -> Optional[dict]:
    """
    If an FL is marked dead, attempts to replace them with a valid bench substitute.
    """
    for side in ["white", "black"]:
        unit = match.get(side)
        if unit.get("role") == "FL" and unit.get("status") == "dead":
            substitute = find_fl_substitute(bench)
            if substitute:
                substitute["status"] = "active"
                bench.remove(substitute)
                match[side] = substitute
                return {
                    "replaced": unit["id"],
                    "substitute": substitute["id"],
                    "side": side
                }
    return None


# Example usage
if __name__ == "__main__":
    match = {
        "white": {"id": "unit_FL", "role": "FL", "status": "dead"},
        "black": {"id": "unit_VG", "role": "VG", "status": "active"}
    }
    bench = [
        {"id": "bench1", "role": "PO", "FL_eligible": False},
        {"id": "bench2", "role": "FL", "FL_eligible": True}
    ]

    result = apply_fl_substitution(match, bench)
    print("Substitution Result:", result)
    print("Updated Match:", match)
    print("Remaining Bench:", [u["id"] for u in bench])
