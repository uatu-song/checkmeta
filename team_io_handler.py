# team_io_handler.py
# Handles loading and saving of team JSON files for matchday simulation

import json
from typing import List


def load_team(filepath: str) -> List[dict]:
    """
    Loads a team from a JSON file.
    Expects a list of unit dicts.
    """
    with open(filepath, "r") as f:
        return json.load(f)


def save_team(filepath: str, team_data: List[dict]) -> None:
    """
    Saves updated team data to a JSON file.
    """
    with open(filepath, "w") as f:
        json.dump(team_data, f, indent=2)


# Example usage
if __name__ == "__main__":
    dummy_team = [{"id": "unit_1", "HP": 100, "stamina": 100, "life": 10, "status": "active", "XP": 0}]
    path = "team_example.json"

    save_team(path, dummy_team)
    print("Team saved.")

    loaded = load_team(path)
    print("Loaded Team:", loaded)
