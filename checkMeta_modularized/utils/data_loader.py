# utils/data_loader.py
import pandas as pd

def load_teams(filepath: str) -> dict:
    df = pd.read_excel(filepath)
    teams = {}
    for _, row in df.iterrows():
        team_id = row.get("team_id")
        if team_id not in teams:
            teams[team_id] = []
        unit = {
            "id": row.get("id"),
            "role": row.get("role"),
            "morale": row.get("morale", 50),
            "xp": row.get("xp", 0)
        }
        teams[team_id].append(unit)
    return teams

def generate_sample_teams() -> dict:
    return {
        "T001": [{"id": "IronMan", "role": "FL"}, {"id": "SpiderMan", "role": "RG"}],
        "T002": [{"id": "Wolverine", "role": "VG"}, {"id": "Cyclops", "role": "EN"}]
    }
