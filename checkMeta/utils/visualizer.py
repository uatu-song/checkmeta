"""
META Fantasy League Simulator - Match Visualization & Reporting
Generates visualizations and reports from match results
"""

import os
import json
import random
import datetime
from typing import Dict, List, Any, Optional

def generate_match_summary(result: Dict[str, Any]) -> str:
    """
    Generate a text summary of a match result
    
    Args:
        result: Match result data
        
    Returns:
        str: Formatted match summary
    """
    # Extract key information
    team_a_name = result.get("team_a_name", "Team A")
    team_b_name = result.get("team_b_name", "Team B")
    team_a_wins = result.get("team_a_wins", 0)
    team_b_wins = result.get("team_b_wins", 0)
    winner = result.get("winner", "Draw")
    winning_team = result.get("winning_team", "None")
    convergence_count = result.get("convergence_count", 0)
    trait_activations = result.get("trait_activations", 0)
    
    # Get character results
    character_results = result.get("character_results", [])
    
    # Find key performers
    top_damage_dealer = {"name": "Unknown", "damage": 0, "team": None}
    top_knockouts = {"name": "Unknown", "kos": 0, "team": None}
    
    for char in character_results:
        # Check damage dealt
        damage = 0
        if "rStats" in char:
            # Check different damage stats
            damage += char["rStats"].get("rDD", 0)
            damage += char["rStats"].get("rDDo", 0)
            damage += char["rStats"].get("rDDi", 0)
        
        if damage > top_damage_dealer["damage"]:
            top_damage_dealer = {
                "name": char["character_name"],
                "damage": damage,
                "team": char["team"]
            }
        
        # Check knockouts
        kos = 0
        if "rStats" in char:
            kos = char["rStats"].get("rOTD", 0)
        
        if kos > top_knockouts["kos"]:
            top_knockouts = {
                "name": char["character_name"],
                "kos": kos,
                "team": char["team"]
            }
    
    # Generate summary
    summary = f"""
=== MATCH SUMMARY ===
{team_a_name} vs {team_b_name}

RESULT: {team_a_name} {team_a_wins} - {team_b_wins} {team_b_name}
WINNER: {winning_team}

KEY STATISTICS:
- Convergences: {convergence_count}
- Trait Activations: {trait_activations}

TOP PERFORMERS:
- Damage Dealer: {top_damage_dealer["name"]} ({team_a_name if top_damage_dealer["team"] == "A" else team_b_name})
- Knockouts: {top_knockouts["name"]} ({team_a_name if top_knockouts["team"] == "A" else team_b_name})

TEAM SUMMARIES:
"""
    
    # Add team A summary
    team_a_active = [c for c in character_results if c["team"] == "A" and c["was_active"]]
    team_a_ko = [c for c in team_a_active if c["is_ko"]]
    
    summary += f"{team_a_name}: {len(team_a_active) - len(team_a_ko)}/{len(team_a_active)} characters active\n"
    
    # Add team B summary
    team_b_active = [c for c in character_results if c["team"] == "B" and c["was_active"]]
    team_b_ko = [c for c in team_b_active if c["is_ko"]]
    
    summary += f"{team_b_name}: {len(team_b_active) - len(team_b_ko)}/{len(team_b_active)} characters active\n"
    
    # Add momentum summary if available
    if "team_a_momentum_final" in result:
        team_a_momentum = result["team_a_momentum_final"]
        team_b_momentum = result["team_b_momentum_final"]
        
        summary += f"\nMOMENTUM STATES:\n"
        summary += f"{team_a_name}: {team_a_momentum['state'].upper()} ({team_a_momentum['value']})\n"
        summary += f"{team_b_name}: {team_b_momentum['state'].upper()} ({team_b_momentum['value']})\n"
    
    # Add injuries summary if any
    injured = [c for c in character_results if c["is_ko"] and c["was_active"]]
    if injured:
        summary += f"\nINJURIES:\n"
        for char in injured:
            team_name = team_a_name if char["team"] == "A" else team_b_name
            summary += f"- {char['character_name']} ({team_name}): Knocked Out\n"
    
    return summary

def generate_narrative_report(result: Dict[str, Any]) -> str:
    """
    Generate a narrative report for a match
    
    Args:
        result: Match result data
        
    Returns:
        str: Narrative match report
    """
    # Extract key information
    team_a_name = result.get("team_a_name", "Team A")
    team_b_name = result.get("team_b_name", "Team B")
    team_a_wins = result.get("team_a_wins", 0)
    team_b_wins = result.get("team_b_wins", 0)
    winner = result.get("winner", "Draw")
    winning_team = result.get("winning_team", "None")
    
    # Get character results for key stories
    character_results = result.get("character_results", [])
    
    # Get convergences for storytelling
    convergences = result.get("convergence_logs", [])
    
    # Determine if this was a close match or a blowout
    match_type = "close" if abs(team_a_wins - team_b_wins) <= 2 else "decisive"
    
    # Generate narrative opening
    if match_type == "close":
        opening = random.choice([
            f"In a thrilling contest that came down to the wire, {winning_team} narrowly defeated their rivals.",
            f"The arena fell silent as {winning_team} secured a hard-fought victory in the closing moments.",
            f"Neither team gave an inch in a back-and-forth battle that {winning_team} ultimately won."
        ])
    else:
        opening = random.choice([
            f"{winning_team} dominated from the opening bell, securing a decisive victory.",
            f"It was a showcase of tactical superiority as {winning_team} overwhelmed their opponents.",
            f"The outcome was never in doubt as {winning_team} controlled every aspect of the match."
        ])
    
    # Find key performers for storylines
    top_performers = []
    for char in character_results:
        if not char["was_active"]:
            continue
            
        # Calculate performance score
        score = 0
        if "rStats" in char:
            # Damage is a factor
            damage = char["rStats"].get("rDD", 0) + char["rStats"].get("rDDo", 0) + char["rStats"].get("rDDi", 0)
            score += damage / 100
            
            # Knockouts are valuable
            kos = char["rStats"].get("rOTD", 0)
            score += kos * 5
            
            # Ultimate moves are impressive
            ults = char["rStats"].get("rULT", 0)
            score += ults * 3
            
            # Healing and support counts
            healing = char["rStats"].get("rHLG", 0)
            score += healing / 50
            
            # Convergence victories matter
            cvs = char["rStats"].get("rCVo", 0) + char["rStats"].get("rMBi", 0)
            score += cvs * 2
        
        if score > 0:
            top_performers.append({
                "name": char["character_name"],
                "team": char["team"],
                "score": score,
                "role": char["role"],
                "is_ko": char["is_ko"]
            })
    
    # Sort by performance score
    top_performers.sort(key=lambda x: x["score"], reverse=True)
    
    # Generate narrative body
    body = ""
    
    # Add key performer narratives
    if top_performers:
        mvp = top_performers[0]
        mvp_team = team_a_name if mvp["team"] == "A" else team_b_name
        
        body += f"\n{mvp['name']} was the standout performer for {mvp_team}, "
        
        if mvp["role"] == "FL":
            body += "leading the team with tactical brilliance. "
        elif mvp["role"] == "VG":
            body += "breaking through enemy lines with devastating efficiency. "
        elif mvp["role"] == "EN":
            body += "enforcing dominance with raw power and determination. "
        elif mvp["role"] == "SV":
            body += "controlling reality with unmatched strategic awareness. "
        else:
            body += "showcasing exceptional skill throughout the match. "
        
        # Add a secondary performer if available
        if len(top_performers) > 1:
            second = top_performers[1]
            second_team = team_a_name if second["team"] == "A" else team_b_name
            
            body += f"\n\n{second['name']} of {second_team} also made a significant impact, "
            
            if second["is_ko"]:
                body += "despite being knocked out in the later stages. "
            else:
                body += "remaining a threat until the final moments. "
    
    # Add notable convergences if available
    if convergences:
        # Pick a notable convergence
        notable = random.choice(convergences)
        
        body += f"\n\nA pivotal moment came when {notable['winner']} triumphed over {notable['loser']} "
        body += f"in a convergence at {notable['square']}, dealing significant damage. "
        
        # If there was a critical success, highlight it
        critical = next((c for c in convergences if c.get("outcome") == "critical_success"), None)
        if critical:
            body += f"\n\n{critical['winner']} executed a breathtaking ultimate move that shifted the momentum of the match. "
    
    # Add substitution narratives if any occurred
    substitutions = result.get("substitutions", [])
    if substitutions:
        sub = substitutions[0]
        body += f"\n\nThe match saw a critical Field Leader substitution when {sub['replacement']} "
        body += f"stepped in for the knocked out {sub['ko_character']}, changing team dynamics. "
    
    # Generate narrative closing
    if match_type == "close":
        closing = random.choice([
            f"As the dust settled, {winning_team} emerged victorious, but both teams earned respect for their performance.",
            f"The match will be remembered as one of the season's most competitive, with {winning_team} barely edging out the win.",
            f"Analysts will debate the strategic decisions that ultimately gave {winning_team} the narrow victory."
        ])
    else:
        closing = random.choice([
            f"The dominant performance from {winning_team} sends a message to all other teams in the league.",
            f"Questions will be asked about tactical preparation after {winning_team} secured such a one-sided victory.",
            f"The coaching staff of {winning_team} deserves credit for a perfectly executed game plan."
        ])
    
    # Combine all sections
    report = f"""
=== MATCH NARRATIVE REPORT ===
{team_a_name} vs {team_b_name}
Final Score: {team_a_wins}-{team_b_wins}

{opening}
{body}

{closing}
"""
    
    return report

def save_match_report(result: Dict[str, Any], output_dir="results/reports"):
    """
    Save match reports to files
    
    Args:
        result: Match result data
        output_dir: Directory to save reports
        
    Returns:
        tuple: Paths to saved report files
    """
    # Create directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Create timestamp and match identifier
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    team_a_id = result.get("team_a_id", "unknown")
    team_b_id = result.get("team_b_id", "unknown")
    match_id = f"{team_a_id}_vs_{team_b_id}"
    
    # Generate reports
    summary = generate_match_summary(result)
    narrative = generate_narrative_report(result)
    
    # Save summary report
    summary_path = os.path.join(output_dir, f"{match_id}_{timestamp}_summary.txt")
    with open(summary_path, "w") as f:
        f.write(summary)
    
    # Save narrative report
    narrative_path = os.path.join(output_dir, f"{match_id}_{timestamp}_narrative.txt")
    with open(narrative_path, "w") as f:
        f.write(narrative)
    
    print(f"Reports saved to {summary_path} and {narrative_path}")
    
    return summary_path, narrative_path

def generate_match_visualization(result: Dict[str, Any]) -> str:
    """
    Generate a text-based visualization of the match
    
    Args:
        result: Match result data
        
    Returns:
        str: Text visualization of the match
    """
    # Extract character results
    character_results = result.get("character_results", [])
    
    # Get team names
    team_a_name = result.get("team_a_name", "Team A")
    team_b_name = result.get("team_b_name", "Team B")
    
    # Filter for active characters
    team_a_active = [c for c in character_results if c["team"] == "A" and c["was_active"]]
    team_b_active = [c for c in character_results if c["team"] == "B" and c["was_active"]]
    
    # Generate team rosters with status
    team_a_roster = []
    for char in team_a_active:
        status = "KO" if char["is_ko"] else ("DEAD" if char.get("is_dead", False) else "OK")
        hp = char["final_hp"]
        stam = char["final_stamina"]
        role = char["role"]
        
        # Format entry
        entry = f"{char['character_name']} ({role}): {status} | HP: {hp:.1f} | STAM: {stam:.1f}"
        team_a_roster.append(entry)
    
    team_b_roster = []
    for char in team_b_active:
        status = "KO" if char["is_ko"] else ("DEAD" if char.get("is_dead", False) else "OK")
        hp = char["final_hp"]
        stam = char["final_stamina"]
        role = char["role"]
        
        # Format entry
        entry = f"{char['character_name']} ({role}): {status} | HP: {hp:.1f} | STAM: {stam:.1f}"
        team_b_roster.append(entry)
    
    # Calculate team health percentages
    team_a_health = sum(c["final_hp"] for c in team_a_active) / (len(team_a_active) * 100) * 100
    team_b_health = sum(c["final_hp"] for c in team_b_active) / (len(team_b_active) * 100) * 100
    
    # Generate health bars
    a_health_bar = generate_health_bar(team_a_health)
    b_health_bar = generate_health_bar(team_b_health)
    
    # Generate visualization
    viz = f"""
==========================================
            MATCH VISUALIZATION            
==========================================

{team_a_name} ({result.get('team_a_wins', 0)} wins)
{a_health_bar} {team_a_health:.1f}%
"""
    
    # Add team A roster
    for entry in team_a_roster:
        viz += f"  {entry}\n"
    
    viz += f"\nvs.\n\n"
    
    # Add team B roster
    viz += f"{team_b_name} ({result.get('team_b_wins', 0)} wins)\n"
    viz += f"{b_health_bar} {team_b_health:.1f}%\n"
    
    for entry in team_b_roster:
        viz += f"  {entry}\n"
    
    viz += "\n==========================================\n"
    
    # Add convergence map if available
    convergences = result.get("convergence_logs", [])
    if convergences:
        viz += "\nNOTABLE CONVERGENCE POINTS:\n"
        
        # Take up to 5 most significant convergences
        significant = sorted(convergences, key=lambda x: abs(x.get("a_roll", 0) - x.get("b_roll", 0)), reverse=True)[:5]
        
        for conv in significant:
            viz += f"  {conv['square']}: {conv['winner']} defeated {conv['loser']} (Damage: {conv.get('reduced_damage', 0):.1f})\n"
    
    return viz

def generate_health_bar(percentage, width=20):
    """
    Generate a text-based health bar
    
    Args:
        percentage: Health percentage (0-100)
        width: Width of the bar
        
    Returns:
        str: Text-based health bar
    """
    # Ensure percentage is within range
    percentage = max(0, min(100, percentage))
    
    # Calculate filled positions
    filled = int(width * percentage / 100)
    
    # Generate bar
    if percentage > 60:
        # Green for high health
        bar = f"[{'#' * filled}{' ' * (width - filled)}]"
    elif percentage > 30:
        # Yellow for medium health
        bar = f"[{'!' * filled}{' ' * (width - filled)}]"
    else:
        # Red for low health
        bar = f"[{'*' * filled}{' ' * (width - filled)}]"
    
    return bar