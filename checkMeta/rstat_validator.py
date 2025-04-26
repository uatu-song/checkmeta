# rstat_validator.py
# Validates rStats against canonical list and domain restrictions (ops/intel)

from typing import Dict

# Canonical rStats with allowed domains: 'o' = ops, 'i' = intel, 'b' = both
CANONICAL_RSTATS = {
    "DD": "b", "DS": "b", "OTD": "o", "AST": "b", "ULT": "b", "LVS": "b", "LLS": "b",
    "DFS": "o", "KNB": "o", "CTT": "b", "EVS": "b", "FFD": "b", "FFI": "b", "HLG": "b",
    "RTOo": "o", "CQTo": "o", "BRXo": "o", "HWIo": "o", "MOTo": "o", "AMBo": "o",
    "MBi": "i", "ILSi": "i", "FEi": "i", "DSRi": "i", "INFi": "i", "RSPi": "i"
}


def get_allowed_rstats(role_division: str) -> set:
    """
    Returns the set of allowed rStats for a role division ('o', 'i').
    """
    return {
        stat for stat, domain in CANONICAL_RSTATS.items()
        if domain == role_division or domain == 'b'
    }


def validate_rstats(unit: dict, rstats: Dict[str, int]) -> Dict[str, int]:
    """
    Filters rStats to only include valid, canonical codes for the unit's division.
    """
    division = unit.get("division", "b")  # assume fallback to 'both'
    allowed = get_allowed_rstats(division)

    validated = {}
    for stat, val in rstats.items():
        stat_clean = stat.replace("r", "", 1) if stat.startswith("r") else stat
        if stat_clean in allowed:
            validated[f"r{stat_clean}"] = val
    return validated


# Example test
if __name__ == "__main__":
    unit = {"id": "U01", "division": "i"}
    attempted_stats = {
        "rMBi": 1,   # allowed
        "rBRXo": 1,  # illegal for intel
        "rXPBoost": 999  # non-canonical
    }

    print("Validated rStats:", validate_rstats(unit, attempted_stats))