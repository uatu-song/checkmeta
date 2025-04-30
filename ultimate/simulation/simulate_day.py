
import json
import random
from datetime import datetime

teams = [f"Team_{i}" for i in range(1, 11)]
players = [f"Player_{i}" for i in range(1, 81)]
lineups = [{"team": teams[i // 8], "player": players[i]} for i in range(80)]

def simulate_stamina(player_id):
    stamina = 100
    stamina_log = []
    effects = []
    for turn in range(1, random.randint(10, 20)):
        cost = random.randint(1, 6)
        stamina = max(0, stamina - cost)
        stamina_log.append({
            "turn": turn,
            "cost": cost,
            "reason": random.choice(["standard_move", "trait_activation:Overclock", "synergy_assist"]),
            "stamina_remaining": stamina
        })
        if stamina < 20:
            effects.append("resignation_risk")
        elif stamina < 40:
            effects.append("trait_failure_possible")
        elif stamina < 60:
            effects.append("-5% accuracy")
    return {
        "player_id": player_id,
        "start_stamina": 100,
        "stamina_remaining": stamina,
        "stamina_log": stamina_log,
        "current_effects": list(set(effects))
    }

def simulate_day():
    summary = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "teams": [],
        "global_summary": {
            "total_games": 0,
            "total_wins": 0,
            "total_losses": 0,
            "total_draws": 0
        }
    }

    stamina_events = []

    for team in teams:
        team_entry = {
            "team_id": team,
            "players": [],
            "team_result": {"boards_won": 0, "boards_lost": 0, "boards_drawn": 0}
        }
        team_players = [p["player"] for p in lineups if p["team"] == team]
        for pid in team_players:
            result = random.choices(["win", "loss", "draw"], weights=[4, 4, 2])[0]
            if result == "win":
                team_entry["team_result"]["boards_won"] += 1
            elif result == "loss":
                team_entry["team_result"]["boards_lost"] += 1
            else:
                team_entry["team_result"]["boards_drawn"] += 1

            stamina_data = simulate_stamina(pid)
            stamina_events.append({
                "event_type": "stamina_analytics",
                "player_id": pid,
                "team_id": team,
                "stamina_remaining": stamina_data["stamina_remaining"],
                "effects": stamina_data["current_effects"]
            })

            team_entry["players"].append({
                "player_id": pid,
                "result": result,
                "stamina": stamina_data
            })

        summary["teams"].append(team_entry)

    summary["global_summary"]["total_games"] = 80
    summary["global_summary"]["total_wins"] = sum(t["team_result"]["boards_won"] for t in summary["teams"])
    summary["global_summary"]["total_losses"] = sum(t["team_result"]["boards_lost"] for t in summary["teams"])
    summary["global_summary"]["total_draws"] = sum(t["team_result"]["boards_drawn"] for t in summary["teams"])

    return summary, stamina_events

if __name__ == "__main__":
    match_summary, stamina_event_log = simulate_day()

    with open("day1_match_summary.json", "w") as f:
        json.dump(match_summary, f, indent=2)

    with open("day1_stamina_events.jsonl", "w") as f:
        for event in stamina_event_log:
            f.write(json.dumps(event) + "\n")
