# matchday_report_generator.py
# Compiles matchday results into a readable structured report for audit/export

from typing import List, Dict

CANONICAL_RSTATS = [
    "rDD", "rDS", "rOTD", "rAST", "rULT", "rLVS", "rLLS", "rDFS", "rKNB", "rCTT",
    "rEVS", "rFFD", "rFFI", "rHLG", "rRTOo", "rCQTo", "rBRXo", "rHWIo", "rMOTo",
    "rAMBo", "rMBi", "rILSi", "rFEi", "rDSRi", "rINFi", "rRSPi"
]


def fill_missing_rstats(rstats: Dict[str, int]) -> Dict[str, int]:
    """
    Ensures all canonical rStats are present in the dict.
    Fills missing ones with 0.
    """
    return {k: rstats.get(k, 0) for k in CANONICAL_RSTATS}


def generate_matchday_report(match_results: List[dict]) -> Dict:
    """
    Summarizes match results, convergence rolls, and rStats.
    Returns a dict report suitable for export or UI rendering.
    """
    report = {
        "matches": [],
        "summary": {
            "total_matches": len(match_results),
            "FL_replacements": 0,
            "total_rStats": {k: 0 for k in CANONICAL_RSTATS}
        }
    }

    for match_entry in match_results:
        match = match_entry["match"]
        rstats = match.get("rStats", {})

        white_stats = fill_missing_rstats(rstats.get("white", {}))
        black_stats = fill_missing_rstats(rstats.get("black", {}))

        report["matches"].append({
            "match_id": match["match_id"],
            "white_id": match["white"]["id"],
            "black_id": match["black"]["id"],
            "white_status": match["white"].get("status"),
            "black_status": match["black"].get("status"),
            "white_rStats": white_stats,
            "black_rStats": black_stats,
            "white_convergence": match["convergence"]["white"],
            "black_convergence": match["convergence"]["black"]
        })

        # Count substitutions
        if match_entry.get("substitution_a") or match_entry.get("substitution_b"):
            report["summary"]["FL_replacements"] += 1

        # Aggregate rStats
        for stat in CANONICAL_RSTATS:
            report["summary"]["total_rStats"][stat] += white_stats[stat] + black_stats[stat]

    return report


# Example usage
if __name__ == "__main__":
    mock_results = [{
        "match": {
            "match_id": "match_01",
            "white": {"id": "unit1", "status": "active"},
            "black": {"id": "unit2", "status": "dead"},
            "rStats": {"white": {"rDD": 3, "rULT": 1}, "black": {}}
        },
        "substitution_b": {"replaced": "unit2", "substitute": "unit9", "side": "black"}
    }]

    report = generate_matchday_report(mock_results)
    print("Matchday Report:", report)
