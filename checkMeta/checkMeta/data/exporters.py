###############################
# data/exporters.py
###############################
"""
Result exporting functions for META League Simulator
"""

import json
import os
import pandas as pd
from typing import Dict, List, Any

def export_results_to_json(results: List[Dict[str, Any]], file_path: str) -> None:
    """Export match results to a JSON file"""
    with open(file_path, "w") as f:
        json.dump(results, f, indent=2)

def export_results_to_csv(results: List[Dict[str, Any]], file_path: str) -> None:
    """Export match results to a CSV file"""
    # Extract main match data
    match_data = []
    for match in results:
        match_data.append({
            "Team A": match["team_a_name"],
            "Team B": match["team_b_name"],
            "Team A Wins": match["team_a_wins"],
            "Team B Wins": match["team_b_wins"],
            "Winner": match["winning_team"],
            "Convergences": match["convergence_count"],
            "Trait Activations": match["trait_activations"]
        })
    
    # Create DataFrame and save
    df = pd.DataFrame(match_data)
    df.to_csv(file_path, index=False)

def export_character_stats(results: List[Dict[str, Any]], file_path: str) -> None:
    """Export character stats from match results"""
    # Extract character data
    character_data = []
    
    for match in results:
        for char_result in match["character_results"]:
            character_data.append({
                "Character": char_result["character_name"],
                "Team": match["team_a_name"] if char_result["team"] == "A" else match["team_b_name"],
                "Result": char_result["result"],
                "Final HP": char_result["final_hp"],
                "Final Stamina": char_result["final_stamina"],
                "KO'd": char_result["is_ko"],
                "Active": char_result["was_active"]
            })
    
    # Create DataFrame and save
    df = pd.DataFrame(character_data)
    df.to_csv(file_path, index=False)