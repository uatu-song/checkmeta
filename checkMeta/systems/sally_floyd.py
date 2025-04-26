# sally_floyd.py

import datetime
import random
import pandas as pd
import os

def load_team_name_map(csv_path='data/teams/SimEngine v3 teamIDs 1.csv'):
    """
    Load team name mapping from CSV file
    
    Returns:
        Dictionary with team_ids as keys and teamName as values
    """
    try:
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            return dict(zip(df['team_ids'], df['teamName']))
    except Exception as e:
        print(f"Error loading team names: {e}")
    
    # Fallback mapping if CSV cannot be loaded
    return {
        'T001': "Xavier's School", 
        'T002': 'Brotherhood', 
        'T003': 'Avengers', 
        'T004': 'Fantastic Four', 
        'T005': 'Hellfire Club', 
        'T006': 'Asgardians', 
        'T007': 'Shield Ops', 
        'T008': 'Mutant Underground', 
        'T009': 'X-Force', 
        'T010': 'The Illuminati'
    }

def generate_sally_report(match_data, match_date=None):
    """
    Generate a narrative report based on match data.

    Parameters:
    - match_data: Dictionary containing match results
    - match_date: Date of the match (default: today)

    Returns:
    - Dictionary with narrative report sections
    """
    if match_date is None:
        match_date = datetime.datetime.now()
    
    # Load team names
    friendly_name_map = load_team_name_map()

    # Extract key performers
    top_damage_dealer = None
    top_damage = 0
    top_ko = None
    most_kos = 0
    
    for result in match_data.get("character_results", []):
        # Extract character stats
        char_damage = 0
        if 'rStats' in result:
            char_damage = result['rStats'].get('rDDo', 0) + result['rStats'].get('rDDi', 0)
        
        # Track damage dealers
        if char_damage > top_damage:
            top_damage = char_damage
            top_damage_dealer = result
        
        # Track KOs - look for KO stats or check is_ko status
        ko_count = 0
        if 'rStats' in result:
            ko_count = result['rStats'].get('rOTD', 0) + result['rStats'].get('rKO', 0)
        
        if ko_count > most_kos:
            most_kos = ko_count
            top_ko = result

    # Extract convergence data
    convergence_count = match_data.get("convergence_count", 0)
    trait_activations = match_data.get("trait_activations", 0)
    
    # Get team names
    team_a_name = match_data.get("team_a_name", "Unknown Team A")
    team_b_name = match_data.get("team_b_name", "Unknown Team B")
    winner_name = match_data.get("winning_team", "None")
    
    # Get team id from character if available
    team_id = None
    if top_damage_dealer and 'team_id' in top_damage_dealer:
        team_id = top_damage_dealer['team_id']
    
    # Get friendly team name
    team_dd = friendly_name_map.get(team_id, team_a_name if team_id == "A" else team_b_name)
    
    # Generate narrative sections
    top_char_name = top_damage_dealer.get('character_name', 'Unknown') if top_damage_dealer else 'Unknown'
    ko_char_name = top_ko.get('character_name', 'Unknown') if top_ko else 'Unknown'
    
    cinematic = (
        f"{top_char_name} of {team_dd} unleashed {top_damage}00 damage — most of the league froze just watching."
        if top_damage_dealer and top_damage > 0 else
        "The battlefield was surprisingly quiet today."
    )

    tragedy = (
        f"{ko_char_name} dropped opponents like they were practice dummies. {most_kos} confirmed takedowns."
        if top_ko and most_kos > 0 else
        "No standout performers today."
    )

    # Generate random observations based on match data
    convergence_comments = [
        f"The grid lit up with {convergence_count} convergence points. Techs said it looked like constellations.",
        f"{convergence_count} convergences triggered — way above baseline for a standard match.",
        f"Reality stuttered {convergence_count} times during convergences. Each one left a temporal wake."
    ]
    
    trait_comments = [
        f"{trait_activations} trait activations rippled across four separate engagements.",
        f"Trackers counted {trait_activations} trait activations. Half of them shouldn't be possible.",
        f"{trait_activations} power signatures went beyond the measurement threshold today."
    ]
    
    match_anomalies = [
        "One sim log shows a hero KO'd. Another shows them KO'ing. Sally can't verify either.",
        f"{winner_name} won, but the overlay flickered to show {team_a_name if winner_name != team_a_name else team_b_name} as champions for 3 seconds.",
        "Multiple timeline threads detected, but admin tools insist everything is fine."
    ]
    
    broken = random.choice(convergence_comments) if convergence_count > 0 else "The system ran perfectly today. That's suspicious in itself."
    traits = random.choice(trait_comments) if trait_activations > 0 else "No trait activations registered. That's statistically impossible."
    overlays = random.choice(match_anomalies)

    return {
        "date": match_date.strftime("%Y-%m-%d"),
        "match": f"{team_a_name} vs {team_b_name}",
        "winner": winner_name,
        "cinematic": cinematic,
        "tragedy": tragedy,
        "broken": broken,
        "traits": traits,
        "overlays": overlays
    }

def format_report(report):
    """
    Format the report for display
    """
    return f"""
SALLY FLOYD REPORT: {report['date']}
=======================================================
MATCH: {report['match']}
WINNER: {report['winner']}

STANDOUT MOMENT:
{report['cinematic']}

CASUALTIES & TAKEDOWNS:
{report['tragedy']}

SYSTEM ANOMALIES:
{report['broken']}

TRAIT ANALYSIS:
{report['traits']}

OVERLAY INCONSISTENCIES:
{report['overlays']}
=======================================================
// Transcript authorized by Sally Floyd - Admin Level 5
// These logs are encrypted. Distribution is restricted.
"""

if __name__ == "__main__":
    # Example usage with sample data
    sample_match = {
        "team_a_name": "Xavier's School",
        "team_b_name": "Brotherhood",
        "winning_team": "Xavier's School",
        "convergence_count": 12,
        "trait_activations": 8,
        "character_results": [
            {
                "character_name": "Wolverine",
                "team_id": "T001",
                "team": "A",
                "rStats": {"rDDo": 150, "rKO": 2}
            },
            {
                "character_name": "Magneto",
                "team_id": "T002",
                "team": "B",
                "rStats": {"rDDo": 80, "rKO": 1}
            }
        ]
    }
    
    # Generate and print sample report
    report = generate_sally_report(sample_match)
    print(format_report(report))