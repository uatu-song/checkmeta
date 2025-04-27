"""
META Fantasy League - Match Helper Utilities
Handles creating balanced team matchups and normalization functions
"""

import random
from typing import Dict, List, Any, Tuple

def create_team_matchups(teams: Dict, day_number: int = 1, randomize: bool = False) -> List[Tuple[str, str]]:
    """Create balanced team matchups for simulation
    
    Args:
        teams: Dictionary of teams by team_id
        day_number: Day number for scheduling
        randomize: Whether to randomize matchups
        
    Returns:
        List of matchup tuples (team_a_id, team_b_id)
    """
    # Get all team IDs
    all_team_ids = list(teams.keys())
    
    print(f"Available teams for matchups: {all_team_ids}")
    
    if len(all_team_ids) < 2:
        print("Not enough teams for matchups (minimum 2 required)")
        return []
    
    # Use appropriate matchup creation method
    if randomize:
        return create_random_matchups(all_team_ids)
    else:
        # Try day-based matchups first
        matchups = create_day_matchups(all_team_ids, day_number)
        
        # Fall back to round-robin if day matchups don't work
        if not matchups:
            matchups = create_round_robin_matchups(all_team_ids, day_number)
        
        # Fall back to random if no valid matchups
        if not matchups:
            print("Scheduled matchups failed, falling back to random matchups")
            return create_random_matchups(all_team_ids)
        
        return matchups

def create_random_matchups(team_ids: List[str]) -> List[Tuple[str, str]]:
    """Create random matchups from team IDs
    
    Args:
        team_ids: List of team IDs
        
    Returns:
        List of matchup tuples (team_a_id, team_b_id)
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

def create_day_matchups(team_ids: List[str], day_number: int) -> List[Tuple[str, str]]:
    """Create matchups based on predefined day schedule
    
    Args:
        team_ids: List of team IDs
        day_number: Day number (1-5)
        
    Returns:
        List of matchup tuples (team_a_id, team_b_id)
    """
    # Define standard 10-team league matchups
    all_matchups = {
        # Day 1: Standard pairing
        1: [
            ("tT001", "t002"),
            ("tT004", "t003"),
            ("tT005", "t006"),
            ("tT008", "t007"),
            ("tT009", "t010")
        ],
        # Day 2: Rotate for different matchups
        2: [
            ("tT001", "t003"),
            ("tT004", "t006"),
            ("tT005", "t007"),
            ("tT008", "t010"),
            ("tT009", "t002")
        ],
        # Day 3: Another rotation
        3: [
            ("tT001", "t006"),
            ("tT004", "t007"),
            ("tT005", "t010"),
            ("tT008", "t002"),
            ("tT009", "t003")
        ],
        # Day 4
        4: [
            ("tT001", "t007"),
            ("tT004", "t010"),
            ("tT005", "t002"),
            ("tT008", "t003"),
            ("tT009", "t006")
        ],
        # Day 5
        5: [
            ("tT001", "t010"),
            ("tT004", "t002"),
            ("tT005", "t003"),
            ("tT008", "t006"),
            ("tT009", "t007")
        ]
    }
    
    # Default to day 1 if the requested day isn't defined
    if day_number not in all_matchups:
        print(f"Warning: No predefined matchups for day {day_number}, using day 1 matchups")
        day_matches = all_matchups[1]
    else:
        day_matches = all_matchups[day_number]
    
    # Normalize provided team IDs for consistent comparison
    normalized_team_ids = [normalize_team_id(tid) for tid in team_ids]
    
    # Validate matchups against available teams
    valid_matchups = []
    for team_a, team_b in day_matches:
        team_a_norm = normalize_team_id(team_a)
        team_b_norm = normalize_team_id(team_b)
        
        # Find corresponding actual team IDs (preserving case)
        actual_team_a = None
        actual_team_b = None
        
        for i, tid in enumerate(normalized_team_ids):
            if tid == team_a_norm:
                actual_team_a = team_ids[i]
            if tid == team_b_norm:
                actual_team_b = team_ids[i]
        
        if actual_team_a and actual_team_b:
            valid_matchups.append((actual_team_a, actual_team_b))
        else:
            print(f"Skipping matchup ({team_a} vs {team_b}) - one or both teams not available")
    
    print(f"Created {len(valid_matchups)} day-based matchups for day {day_number}")
    return valid_matchups

def create_round_robin_matchups(team_ids: List[str], day_number: int) -> List[Tuple[str, str]]:
    """Create round-robin style matchups based on team IDs
    
    Args:
        team_ids: List of team IDs
        day_number: Day number for scheduling rotation
        
    Returns:
        List of matchup tuples (team_a_id, team_b_id)
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
        team_a = rotating_teams[i]
        team_b = rotating_teams[n - 1 - i]
        
        # Skip matchups involving the dummy team
        if not using_dummy or (team_a != "BYE" and team_b != "BYE"):
            matchups.append((team_a, team_b))
    
    # Limit to 5 matches
    if len(matchups) > 5:
        print(f"Limiting from {len(matchups)} to 5 matches")
        matchups = matchups[:5]
    
    print(f"Created {len(matchups)} round-robin matchups for day {day_number}")
    return matchups

def normalize_team_id(team_id: str) -> str:
    """Normalize team ID format
    
    Args:
        team_id: Team ID in any format
        
    Returns:
        Normalized team ID
    """
    # Handle None or empty string
    if not team_id:
        return ""
        
    # Convert to string if not already
    team_id = str(team_id)
    
    # Remove any non-alphanumeric characters
    team_id = ''.join(c for c in team_id if c.isalnum())
    
    # Ensure it starts with 't' (lowercase)
    if not team_id.lower().startswith('t'):
        team_id = 't' + team_id
    
    # Lowercase the entire ID for consistent comparison
    return team_id.lower()

def create_balanced_matchups(teams: Dict, team_info: Dict = None) -> List[Tuple[str, str]]:
    """Create matchups based on team balance factors
    
    Args:
        teams: Dictionary of teams by team_id
        team_info: Additional team information for balancing
        
    Returns:
        List of matchup tuples (team_a_id, team_b_id)
    """
    # Get team IDs
    team_ids = list(teams.keys())
    
    # Calculate team power levels
    power_levels = {}
    for team_id in team_ids:
        team_chars = teams[team_id]
        
        # Calculate average of key stats
        total_power = 0
        for char in team_chars:
            # Sum of key attributes
            power = (
                char.get("aSTR", 5) + 
                char.get("aSPD", 5) + 
                char.get("aOP", 5) + 
                char.get("aLDR", 5)
            ) / 4.0
            
            # Weight by role importance
            role = char.get("role", "")
            if role == "FL":
                power *= 1.3  # Field Leader is 30% more important
            elif role == "SV":
                power *= 1.2  # Sovereign is 20% more important
            
            total_power += power
        
        # Calculate average power level for team
        power_levels[team_id] = total_power / len(team_chars) if team_chars else 0
    
    # Sort teams by power level
    sorted_teams = sorted(team_ids, key=lambda x: power_levels.get(x, 0))
    
    # Create balanced matchups by pairing teams with similar power levels
    matchups = []
    while len(sorted_teams) >= 2:
        # Create matchup with teams from opposite ends of the list
        # This ensures more balanced matchups
        team_a = sorted_teams.pop(0)  # Lower power team
        team_b = sorted_teams.pop(-1)  # Higher power team
        matchups.append((team_a, team_b))
    
    # Limit to 5 matches
    if len(matchups) > 5:
        matchups = matchups[:5]
    
    return matchups

def get_team_pairing_stats(team_a, team_b):
    """Calculate comparative stats for a team pairing
    
    Args:
        team_a: List of team A characters
        team_b: List of team B characters
        
    Returns:
        dict: Comparative statistics
    """
    stats = {
        "team_a_size": len(team_a),
        "team_b_size": len(team_b),
        "team_a_roles": {},
        "team_b_roles": {},
        "team_a_avg_power": 0,
        "team_b_avg_power": 0,
        "team_a_avg_hp": 0,
        "team_b_avg_hp": 0
    }
    
    # Count roles
    for team, role_dict in [(team_a, stats["team_a_roles"]), (team_b, stats["team_b_roles"])]:
        for char in team:
            role = char.get("role", "Unknown")
            role_dict[role] = role_dict.get(role, 0) + 1
    
    # Calculate average power and HP
    for team, power_key, hp_key in [
        (team_a, "team_a_avg_power", "team_a_avg_hp"),
        (team_b, "team_b_avg_power", "team_b_avg_hp")
    ]:
        if not team:
            continue
            
        total_power = 0
        total_hp = 0
        
        for char in team:
            # Calculate power
            power = (
                char.get("aSTR", 5) + 
                char.get("aSPD", 5) + 
                char.get("aOP", 5) + 
                char.get("aLDR", 5)
            ) / 4.0
            
            total_power += power
            total_hp += char.get("HP", 100)
        
        stats[power_key] = total_power / len(team)
        stats[hp_key] = total_hp / len(team)
    
    # Calculate overall balance factor (0-100%, higher is more balanced)
    power_ratio = min(stats["team_a_avg_power"], stats["team_b_avg_power"]) / max(stats["team_a_avg_power"], stats["team_b_avg_power"]) if max(stats["team_a_avg_power"], stats["team_b_avg_power"]) > 0 else 1
    size_ratio = min(stats["team_a_size"], stats["team_b_size"]) / max(stats["team_a_size"], stats["team_b_size"]) if max(stats["team_a_size"], stats["team_b_size"]) > 0 else 1
    
    stats["balance_factor"] = (power_ratio * 0.7 + size_ratio * 0.3) * 100
    
    return stats