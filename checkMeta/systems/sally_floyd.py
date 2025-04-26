# sally_floyd_report.py

import datetime
import random

# Friendly name map for teams
friendly_name_map = {
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

    # Extract key performers
    top_damage_dealer = None
    top_damage = 0
    top_ko = None
    most_kos = 0

    for result in match_data.get("character_results", []):
        # Track damage dealers
        damage = result.get("rDD", 0)
        if damage > top_damage:
            top_damage = damage
            top_damage_dealer = result

        # Track KOs
        kos = result.get("rOTD", 0)
        if kos > most_kos:
            most_kos = kos
            top_ko = result

    # Generate narrative sections
    team_dd = friendly_name_map.get(
        top_damage_dealer.get("team_id", "unknown") if top_damage_dealer else "unknown",
        "an unnamed team"
    )

    cinematic = (
        f"{top_damage_dealer['character_name']} of {team_dd} unleashed {top_damage}00 damage — most of the league froze just watching."
        if top_damage_dealer else
        "The battlefield was surprisingly quiet today."
    )

    tragedy = (
        f"{top_ko['character_name']} dropped opponents like they were practice dummies. {most_kos} confirmed takedowns."
        if top_ko else
        "No standout performers today."
    )

    broken = random.choice([
        "Magik and Deadpool triggered simultaneous MBi flashes — no one's sure what the Overlay saw, but the Undercurrent twitched.",
        "Reality stuttered twice during the third quarter. Logs show a temporal anomaly that repaired itself.",
        "Three separate convergence points froze mid-calculation. The system thinks it's normal. It's not normal."
    ])

    traits = random.choice([
        "Godmode, Diamond Conversion, and Phoenix Fire all triggered ULTs today. The grid burned like it was finals.",
        "Someone went full Ultimate. The logs claim it was authorized. Half the spectators disagree.",
        "Trait cascades rippled across four separate engagements. This shouldn't be possible with current tech."
    ])

    overlays = random.choice([
        "One sim log shows Nova KO'd. Another shows him KO'ing. Sally can't verify either.",
        "The official log and what spectators saw don't match up. Again.",
        "Multiple timeline threads detected, but admin tools insist everything is fine."
    ])

    return {
        "date": match_date.strftime("%Y-%m-%d"),
        "cinematic": cinematic,
        "tragedy": tragedy,
        "broken": broken,
        "traits": traits,
        "overlays": overlays
    }