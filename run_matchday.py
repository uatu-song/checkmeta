# run_matchday.py
# Orchestrates a full matchday: pairing, simulating, evaluating, substituting, updating state, and generating report

from matchday_pairing_engine import pair_teams
from simulate_match_stub import simulate_match
from fl_substitution_engine import apply_fl_substitution
from team_state_updater import update_team_state
from matchday_report_generator import generate_matchday_report


def run_matchday(team_a: list, team_b: list, pgn_bank: list) -> dict:
    """
    Simulates a full 8v8 matchday between two 12-unit teams.
    Uses PGNs from pgn_bank.
    Applies FL substitutions if needed.
    Updates team state and produces final matchday report.
    """
    paired = pair_teams(team_a, team_b)
    match_results = []
    bench_a = paired["benches"]["team_a"]
    bench_b = paired["benches"]["team_b"]

    for i, match in enumerate(paired["matches"]):
        pgn = pgn_bank[i % len(pgn_bank)]  # cycle PGNs
        sim_result = simulate_match(match, pgn)

        sub_a = apply_fl_substitution(sim_result, bench_a)
        sub_b = apply_fl_substitution(sim_result, bench_b)

        match_results.append({
            "match": sim_result,
            "substitution_a": sub_a,
            "substitution_b": sub_b
        })

    # Update persistent team states
    updated_team_a = update_team_state(team_a, match_results, side="white")
    updated_team_b = update_team_state(team_b, match_results, side="black")

    # Generate report
    report = generate_matchday_report(match_results)

    return {
        "results": match_results,
        "updated_teams": {
            "team_a": updated_team_a,
            "team_b": updated_team_b
        },
        "remaining_bench": {
            "team_a": bench_a,
            "team_b": bench_b
        },
        "report": report
    }


# Example usage
if __name__ == "__main__":
    dummy_team = lambda prefix: [
        {"id": f"{prefix}{i+1}", "role": "FL" if i == 0 else "VG", "traits": [], "aStats": {"aINT": 0.5, "aLCK": 0.3}, "FL_eligible": i >= 8}
        for i in range(12)
    ]

    dummy_pgns = ["""[Event \"Test\"]\n1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Bxc6 dxc6 5. Nxe5 Qd4\n"""] * 8

    output = run_matchday(dummy_team("A"), dummy_team("B"), dummy_pgns)
    print("Final Report:", output["report"])