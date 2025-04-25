# convergence_detector.py
# Identifies convergences (ally or enemy) based on shared move notations per turn across all PGNs

from typing import List, Dict
import re


def extract_moves_by_turn(pgn: str) -> Dict[int, str]:
    """
    Parses PGN and extracts a map of turn_number → white move (ignores black).
    """
    move_map = {}
    for match in re.finditer(r"(\d+)\.\s+(\S+)", pgn):
        turn = int(match.group(1))
        move = match.group(2)
        move_map[turn] = move
    return move_map


def detect_convergences(pgns: Dict[str, str]) -> List[Dict]:
    """
    Detects turn-by-turn overlaps of move notations.
    Returns convergence logs with involved units, turn, and type.
    """
    turn_index: Dict[int, Dict[str, List[str]]] = {}
    for unit_id, pgn in pgns.items():
        turn_map = extract_moves_by_turn(pgn)
        for turn, move in turn_map.items():
            turn_index.setdefault(turn, {}).setdefault(move, []).append(unit_id)

    convergences = []
    for turn, move_sets in turn_index.items():
        for move, units in move_sets.items():
            if len(units) > 1:
                convergences.append({
                    "turn": turn,
                    "move": move,
                    "units": units,
                    "type": "enemy" if _is_cross_team(units) else "ally"
                })

    return convergences


def _is_cross_team(unit_ids: List[str]) -> bool:
    """
    Placeholder: assumes unit IDs prefixed with team letter (A1, B5, etc.)
    """
    return len({uid[0] for uid in unit_ids}) > 1


# Example
if __name__ == "__main__":
    fake_pgns = {
        "A1": "1. e4 e5\n2. Nf3 Nc6\n3. Bc4 Bc5",
        "B1": "1. e4 c5\n2. Nf3 d6\n3. Bc4 Nc6",
        "A2": "1. d4 d5\n2. Nf3 Nf6\n3. Bc4 e6"
    }
    result = detect_convergences(fake_pgns)
    print("Detected Convergences:")
    for r in result:
        print(r)
