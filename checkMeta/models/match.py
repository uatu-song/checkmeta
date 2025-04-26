"""
META Fantasy League Simulator - Matchup Generation
Handles creating balanced team matchups for simulation
"""

import random
from typing import Dict, List, Tuple, Any

def create_team_matchups(teams: Dict, day_number: int = 1, randomize: bool = False) -> List[Tuple[str, str]]:
    """Create matchups for the META League based on team numbers with improved fairness
    
    Args:
        teams (dict): Dictionary of teams by team_id
        day_number (int): Day number for scheduling pattern
        randomize (bool): Whether to randomize matchups instead of using round-robin
        
    Returns:
        list: List of matchup tuples (team_a_id, team_b_id)
    """
    # Get all team IDs
    all_team_ids = list(teams.keys())
    
    # Print available teams for debugging
    print(f"Available teams for matchups: {all_team_ids}")
    
    if len(all_team_ids) < 2:
        print("Not enough teams for matchups (minimum 2 required)")
        return []
    
    # Force pairing if we're having issues
    if randomize:
        return create_random_matchups(all_team_ids)
    else:
        # Try round-robin first
        matchups = create_round_robin_matchups(all_team_ids, day_number)
        
        # If no valid matchups, fall back to random
        if not matchups:
            print("Round-robin matchup failed, falling back to random matchups")
            return create_random_matchups(all_team_ids)
        
        return matchups

def create_random_matchups(team_ids: List[str]) -> List[Tuple[str, str]]:
    """Create random matchups from a list of team IDs
    
    Args:
        team_ids (list): List of team IDs
        
    Returns:
        list: List of matchup tuples (team_a_id, team_b_id)
    """
    # Verify we have teams
    if len(team_ids) < 2:
        print("Not enough teams for random matchups")
        return []
    
    # Make a copy to avoid modifying the original
    available_teams = team_ids.copy()
    
    # Shuffle team IDs
    random.shuffle(available_teams)
    
    # Create pairings
    matchups = []
    while len(available_teams) >= 2:
        team_a = available_teams.pop(0)
        team_b = available_teams.pop(0)
        matchups.append((team_a, team_b))
    
    # Limit to 5 matches
    if len(matchups) > 5:
        print(f"Limiting from {len(matchups)} to 5 matches")
        matchups = matchups[:5]
    
    print(f"Created {len(matchups)} random matchups")
    return matchups

def create_round_robin_matchups(team_ids: List[str], day_number: int) -> List[Tuple[str, str]]:
    """Create round-robin matchups based on team IDs and day number
    
    Args:
        team_ids (list): List of team IDs
        day_number (int): Day number (1-based) for scheduling
        
    Returns:
        list: List of matchup tuples (team_a_id, team_b_id)
    """
    # Handle edge cases
    if len(team_ids) < 2:
        print("Not enough teams for round-robin matchups")
        return []
    
    # Make a copy to avoid modifying the original
    teams = team_ids.copy()
    
    # For odd number of teams, add a dummy team (represents a bye)
    using_dummy = False
    if len(teams) % 2 == 1:
        teams.append("BYE")
        using_dummy = True
        print("Added a BYE team to handle odd number of teams")
    
    # Calculate number of rounds and rotation
    n = len(teams)
    rounds = n - 1
    rotation = (day_number - 1) % rounds
    
    # Create a basic round-robin schedule (circle method)
    # In this method, one team stays fixed and others rotate around it
    fixed_team = teams[0]
    rotating_teams = teams[1:]
    
    # Apply rotation based on day number
    if rotation > 0:
        rotating_teams = rotating_teams[-rotation:] + rotating_teams[:-rotation]
    
    # Create matchups for this rotation
    matchups = []
    
    # Match fixed team with first rotating team
    if fixed_team != "BYE" and rotating_teams[0] != "BYE":
        matchups.append((fixed_team, rotating_teams[0]))
    
    # Pair up the rest of the teams
    for i in range(1, n // 2):
        team_a = rotating_teams[i-1]
        team_b = rotating_teams[n-1-i]
        
        # Skip matchups involving the dummy team
        if not using_dummy or (team_a != "BYE" and team_b != "BYE"):
            matchups.append((team_a, team_b))
    
    # Limit to 5 matches
    if len(matchups) > 5:
        print(f"Limiting from {len(matchups)} to 5 matches")
        matchups = matchups[:5]
    
    print(f"Created {len(matchups)} round-robin matchups for day {day_number}")
    
    # Check if we successfully created matchups
    if not matchups:
        print("WARNING: Failed to create any valid matchups with round-robin scheduling")
    
    return matchups

def create_fixed_matchups() -> List[Tuple[str, str]]:
    """Create a set of hardcoded matchups as a fallback
    
    Returns:
        list: List of matchup tuples (team_a_id, team_b_id)
    """
    # These are hardcoded team IDs that should match your data
    matchups = [
        ("tT001", "tT002"),
        ("tT003", "tT004"),
        ("tT005", "tT006"),
        ("tT007", "tT008"),
        ("tT009", "tT010")
    ]
    
    print("Created 5 fixed matchups as a fallback")
    return matchups

def normalize_team_id(team_id: str) -> str:
    """Normalize team ID format to handle potential format differences
    
    Args:
        team_id (str): Team ID in any format
        
    Returns:
        str: Normalized team ID
    """
    # Remove any non-alphanumeric characters
    team_id = ''.join(c for c in team_id if c.isalnum())
    
    # Ensure it starts with 't' or 'T'
    if not team_id.lower().startswith('t'):
        team_id = 't' + team_id
    
    return team_id