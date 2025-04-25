# audit_trail_builder.py
# Records convergence events, dice rolls, trait effects, and substitutions

from typing import List, Dict


def build_audit_trail(match_results: List[Dict]) -> List[Dict]:
    """
    Generates an audit trail of all matchday events including:
    - Convergences
    - Dice rolls
    - Trait triggers
    - Substitutions
    """
    audit_log = []

    for entry in match_results:
        match = entry["match"]
        match_id = match["match_id"]

        white = match["white"]
        black = match["black"]
        conv_w = match["convergence"]["white"]
        conv_b = match["convergence"]["black"]

        audit_log.append({
            "match_id": match_id,
            "unit_id": white["id"],
            "side": "white",
            "convergence": conv_w,
            "rStats": match.get("rStats", {}).get("white", {}),
            "trait_triggers": white.get("traits", []),
            "roll": conv_w.get("roll"),
            "outcome": conv_w.get("outcome")
        })

        audit_log.append({
            "match_id": match_id,
            "unit_id": black["id"],
            "side": "black",
            "convergence": conv_b,
            "rStats": match.get("rStats", {}).get("black", {}),
            "trait_triggers": black.get("traits", []),
            "roll": conv_b.get("roll"),
            "outcome": conv_b.get("outcome")
        })

        # Substitution logs
        for tag in ["substitution_a", "substitution_b"]:
            if entry.get(tag):
                audit_log.append({
                    "match_id": match_id,
                    "event": "substitution",
                    "details": entry[tag]
                })

    return audit_log


# Example
if __name__ == "__main__":
    mock_result = [{
        "match": {
            "match_id": "match_01",
            "white": {"id": "A1", "traits": ["flanker"]},
            "black": {"id": "B1", "traits": ["tactician"]},
            "convergence": {
                "white": {"roll": 17, "outcome": "success"},
                "black": {"roll": 11, "outcome": "partial"}
            },
            "rStats": {
                "white": {"rDD": 3},
                "black": {"rDD": 1}
            }
        },
        "substitution_b": {"replaced": "B1", "substitute": "B9"}
    }]

    logs = build_audit_trail(mock_result)
    for l in logs:
        print(l)
