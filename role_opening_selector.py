# role_opening_selector.py
# Assigns unit-specific opening sequences based on role profile JSON

import random
import json
from typing import Dict, List

# Load role-based openings from profile JSON
with open("/mnt/data/role_profiles_structured.json") as f:
    ROLE_OPENINGS = json.load(f)


def select_role_opening(role: str, variation: bool = True) -> List[str]:
    """
    Selects a list of opening moves based on role (e.g. FL, GO, VG).
    Optional variation chooses randomly from available sequences.
    """
    role_data = ROLE_OPENINGS.get(role)
    if not role_data or "openings" not in role_data:
        return ["e4", "Nf3", "Bc4"]  # fallback generic

    openings = role_data["openings"]
    if isinstance(openings, list) and variation:
        return random.choice(openings)
    elif isinstance(openings, list):
        return openings[0]

    return ["e4"]


def inject_opening_to_pgn(opening_moves: List[str], max_turns: int = 3) -> str:
    """
    Builds a minimal PGN header with the opening injected.
    """
    pgn = ["[Event \"checkMeta Opening\"]"]
    turns = []
    for i in range(0, min(len(opening_moves), max_turns * 2), 2):
        move_pair = opening_moves[i:i+2]
        turn_number = i // 2 + 1
        turn = f"{turn_number}. {' '.join(move_pair)}"
        turns.append(turn)
    return "\n".join(pgn + turns)


# Example
if __name__ == "__main__":
    opening = select_role_opening("FL")
    print("Selected Opening:", opening)
    print("\nPGN Injected:\n", inject_opening_to_pgn(opening))
