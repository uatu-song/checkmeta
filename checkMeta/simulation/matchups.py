###############################
# simulation/matchups.py
###############################
"""
Team matchup generation for META League Simulator
"""

from typing import Dict, List, Tuple, Any
from ..models.team import Team

def create_team_matchups(teams: Dict[str, List], day_number: int = 1) -> List[Tuple[str, str]]:
    """Create matchups for the META League based on team numbers"""
    # Get all team IDs and sort them numerically
    all_team_ids = list(teams.keys())
    
    # Sort by team number
    all_team_ids.sort(key=lambda x: int(x[1:]) if x[1:].isdigit() else 999)
    
    print(f"All team IDs: {all_team_ids}")
    
    # Calculate number of active teams
    total_teams = len(all_team_ids)
    
    # Implement a round-robin scheduling algorithm
    # Keep first team fixed, rotate all others based on day number
    if total_teams <= 1:
        print("Not enough teams for matchups")
        return []
    
    # For odd number of teams, add a dummy team (represents a bye)
    if total_teams % 2 == 1:
        all_team_ids.append("dummy")
        total_teams += 1
    
    # Calculate rotation for current day
    rotation = (day_number - 1) % (total_teams - 1)
    
    # Create the rotated schedule
    # First team stays fixed, others rotate
    remaining_teams = all_team_ids[1:]
    
    if rotation > 0:
        remaining_teams = remaining_teams[-(rotation):] + remaining_teams[:-(rotation)]
    
    # Create schedule
    schedule = []
    fixed_team = all_team_ids[0]
    
    # Combine fixed team with first rotated team
    if remaining_teams[0] != "dummy" and fixed_team != "dummy":
        schedule.append((fixed_team, remaining_teams[0]))
    
    # Pair up the rest of the teams
    for i in range(1, len(remaining_teams) // 2):
        team_a = remaining_teams[i]
        team_b = remaining_teams[total_teams - 1 - i]
        
        if team_a != "dummy" and team_b != "dummy":
            schedule.append((team_a, team_b))
    
    print(f"Generated {len(schedule)} matchups for day {day_number}")
    
    # Ensure we have exactly 5 matches if possible
    while len(schedule) > 5:
        schedule.pop()  # Remove excess matches
    
    return schedule