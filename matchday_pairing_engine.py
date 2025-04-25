# matchday_pairing_engine.py
# Assigns 8v8 team matchups and determines sides (White/Black), handling 12-unit rosters with FL-aware bench

from typing import List, Dict


def pair_teams(team_a: List[dict], team_b: List[dict]) -> Dict[str, List[dict]]:
    """
    Pairs two teams (up to 12 units each) into 8 matches.
    Match index parity determines which unit plays White.
    Returns matchups and preserved benches.
    """
    assert len(team_a) >= 8 and len(team_b) >= 8, "Each team must have at least 8 units."

    starters_a = team_a[:8]
    bench_a = team_a[8:]
    starters_b = team_b[:8]
    bench_b = team_b[8:]

    matchups = []
    for i in range(8):
        white = starters_a[i] if i % 2 == 0 else starters_b[i]
        black = starters_b[i] if i % 2 == 0 else starters_a[i]

        matchups.append({
            "match_id": f"match_{i+1:02d}",
            "white": white,
            "black": black
        })

    return {
        "matches": matchups,
        "benches": {
            "team_a": bench_a,
            "team_b": bench_b
        }
    }


# Example
if __name__ == "__main__":
    team_a = [{"id": f"A{i+1}"} for i in range(12)]
    team_b = [{"id": f"B{i+1}"} for i in range(12)]

    result = pair_teams(team_a, team_b)

    print("Matchups:")
    for match in result["matches"]:
        print(match)

    print("\nBenches:")
    print("Team A:", [u["id"] for u in result["benches"]["team_a"]])
    print("Team B:", [u["id"] for u in result["benches"]["team_b"]])
