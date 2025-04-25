# rstat_logger.py
# Applies post-match rStats based on match data and convergence outcomes, using canonical validator

from typing import Dict
from rstat_validator import validate_rstats


def log_rstats(unit: dict, convergence: dict, material_loss: int) -> Dict[str, int]:
    """
    Determines rStat outputs based on convergence result and material loss.
    Returns a dict of rStat name → value, validated against role division.
    """
    raw_rstats = {}
    outcome = convergence.get("outcome", "none")

    # Damage Dealt (DD) — scaled by opponent material loss
    if material_loss > 0:
        raw_rstats["rDD"] = material_loss

    # Ultimate Move Impact (ULT) — on critical convergence
    if outcome == "critical_success":
        raw_rstats["rULT"] = 1

    # Disruption Effect (DSRi) — on success or higher
    if outcome in ("success", "critical_success"):
        raw_rstats["rDSRi"] = 1

    # Mind Break (MBi) — if major material swing occurred
    if material_loss >= 12:
        raw_rstats["rMBi"] = 1

    return validate_rstats(unit, raw_rstats)


# Example usage
if __name__ == "__main__":
    unit = {"id": "unit_X", "division": "i"}
    convergence = {"outcome": "critical_success"}
    loss = 13

    result = log_rstats(unit, convergence, loss)
    print("Validated rStats:", result)