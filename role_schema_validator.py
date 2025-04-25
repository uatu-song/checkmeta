# role_schema_validator.py
# Validates that all units use approved roles and division designations (intel or ops)

from typing import List, Dict

# Canonical role definitions (based on reference docs)
CANON_ROLES = {
    "FL": "o",  # Field Leader
    "RG": "o",  # Ranger
    "VG": "o",  # Vanguard
    "EN": "o",  # Enforcer
    "GO": "i",  # Ghost Operative
    "PO": "i",  # Psi Operative
    "SV": "i"   # Sovereign
}


def validate_unit_roles(units: List[Dict]) -> List[str]:
    """
    Validates that all units have known roles and correct division assignment.
    """
    errors = []
    for u in units:
        role = u.get("role")
        division = u.get("division")
        if role not in CANON_ROLES:
            errors.append(f"Unit {u.get('id')} has unknown role: {role}")
            continue

        expected_div = CANON_ROLES[role]
        if division != expected_div:
            errors.append(f"Unit {u.get('id')} has mismatched division: {division} (expected {expected_div})")

    return errors


# Example
if __name__ == "__main__":
    test_units = [
        {"id": "A1", "role": "FL", "division": "o"},
        {"id": "B1", "role": "GO", "division": "o"}  # invalid
    ]
    issues = validate_unit_roles(test_units)
    print("Role Validation Errors:", issues)
