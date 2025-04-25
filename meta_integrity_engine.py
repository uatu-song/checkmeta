# meta_integrity_engine.py
# Ensures simulation components follow current schemas and shared structures

from typing import Dict, List

# Canonical rStats
REQUIRED_RSTATS = [
    "rDD", "rDS", "rOTD", "rAST", "rULT", "rLVS", "rLLS", "rDFS", "rKNB", "rCTT",
    "rEVS", "rFFD", "rFFI", "rHLG", "rRTOo", "rCQTo", "rBRXo", "rHWIo", "rMOTo",
    "rAMBo", "rMBi", "rILSi", "rFEi", "rDSRi", "rINFi", "rRSPi"
]

REQUIRED_UNIT_FIELDS = ["HP", "stamina", "life", "status", "traits", "aStats"]

REQUIRED_TRAIT_FIELDS = ["id", "name", "type", "applies"]


# ---- CHECKERS ----

def check_unit_schema(unit: Dict) -> List[str]:
    errors = []
    for field in REQUIRED_UNIT_FIELDS:
        if field not in unit:
            errors.append(f"Unit {unit.get('id', '?')} missing field: {field}")
    return errors


def check_rstats_schema(rstats: Dict[str, int]) -> List[str]:
    errors = []
    for key in rstats:
        if key not in REQUIRED_RSTATS:
            errors.append(f"Non-canonical rStat detected: {key}")
    return errors


def check_trait_schema(trait: Dict) -> List[str]:
    errors = []
    for field in REQUIRED_TRAIT_FIELDS:
        if field not in trait:
            errors.append(f"Trait {trait.get('id', '?')} missing field: {field}")
    return errors


# ---- RUNNER ----

def run_integrity_check(team_a: List[dict], team_b: List[dict], trait_catalog: List[dict]) -> List[str]:
    errors = []

    for unit in team_a + team_b:
        errors.extend(check_unit_schema(unit))
        if "rStats" in unit:
            errors.extend(check_rstats_schema(unit["rStats"]))

    for trait in trait_catalog:
        errors.extend(check_trait_schema(trait))

    return errors


# Example only
if __name__ == "__main__":
    team_a = [{"id": "A1", "HP": 100, "stamina": 90, "life": 10, "status": "active", "traits": [], "aStats": {}}]
    team_b = [{"id": "B1", "HP": 95, "stamina": 80, "life": 9, "status": "active", "traits": [], "aStats": {}, "rStats": {"rDD": 5, "rXYZ": 2}}]
    trait_catalog = [{"id": "reckless", "name": "Reckless", "type": "active"}]  # missing 'applies'

    errs = run_integrity_check(team_a, team_b, trait_catalog)
    print("\nIntegrity Errors:")
    for err in errs:
        print("-", err)
