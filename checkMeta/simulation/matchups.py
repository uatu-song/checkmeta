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
    
    if randomize:
        # Simple random pairing
        return create_random_matchups(all_team_ids)
    else:
        # Use round-robin scheduling
        return create_round_robin_matchups(all_team_ids, day_number)

def create_random_matchups(team_ids: List[str]) -> List[Tuple[str, str]]:
    """Create random matchups from a list of team IDs
    
    Args:
        team_ids (list): List of team IDs
        
    Returns:
        list: List of matchup tuples (team_a_id, team_b_id)
    """
    # Shuffle team IDs
    shuffled_ids = team_ids.copy()
    random.shuffle(shuffled_ids)
    
    # Create pairings
    matchups = []
    
    # Handle odd number of teams
    if len(shuffled_ids) % 2 == 1:
        # Add a bye
        shuffled_ids.append("BYE")
    
    # Create pairs
    for i in range(0, len(shuffled_ids), 2):
        if i + 1 < len(shuffled_ids):
            # Skip byes
            if shuffled_ids[i] != "BYE" and shuffled_ids[i+1] != "BYE":
                matchups.append((shuffled_ids[i], shuffled_ids[i+1]))
    
    # Limit to 5 matches
    return matchups[:5]

def create_round_robin_matchups(team_ids: List[str], day_number: int) -> List[Tuple[str, str]]:
    """Create round-robin matchups based on team IDs and day number
    
    Args:
        team_ids (list): List of team IDs
        day_number (int): Day number (1-based) for scheduling
        
    Returns:
        list: List of matchup tuples (team_a_id, team_b_id)
    """
    # Sort team IDs for consistency
    sorted_ids = sorted(team_ids, key=lambda x: int(x[1:]) if x[1:].isdigit() else 999)
    
    # Total number of teams
    total_teams = len(sorted_ids)
    
    # Handle cases with too few teams
    if total_teams <= 1:
        print("Not enough teams for matchups")
        return []
    
    # For odd number of teams, add a dummy team (represents a bye)
    if total_teams % 2 == 1:
        sorted_ids.append("BYE")
        total_teams += 1
    
    # Implement round-robin scheduling (circle method)
    
    # Calculate rotation for current day
    rotation = (day_number - 1) % (total_teams - 1)
    
    # Fixed team (stays in place)
    fixed_team = sorted_ids[0]
    
    # Rotating teams (all except the first)
    rotating_teams = sorted_ids[1:]
    
    # Apply rotation based on day number
    if rotation > 0:
        rotating_teams = rotating_teams[-(rotation):] + rotating_teams[:-(rotation)]
    
    # Create matchups
    matchups = []
    

    def create_round_robin_matchups(team_ids: List[str], day_number: int) -> List[Tuple[str, str]]:
        """Create round-robin matchups based on team IDs and day number
        
        Args:
            team_ids (list): List of team IDs
            day_number (int): Day number (1-based) for scheduling
            
        Returns:
            list: List of matchup tuples (team_a_id, team_b_id)
        """
        # Sort team IDs for consistency
        sorted_ids = sorted(team_ids, key=lambda x: int(x[1:]) if x[1:].isdigit() else 999)
        
        # Total number of teams
        total_teams = len(sorted_ids)
        
        # Handle cases with too few teams
        if total_teams <= 1:
            print("Not enough teams for matchups")
            return []
        
        # For odd number of teams, add a dummy team (represents a bye)
        if total_teams % 2 == 1:
            sorted_ids.append("BYE")
            total_teams += 1
        
        # Implement round-robin scheduling (circle method)
        
        # Calculate rotation for current day
        rotation = (day_number - 1) % (total_teams - 1)
        
        # Fixed team (stays in place)
        fixed_team = sorted_ids[0]
        
        # Rotating teams (all except the first)
        rotating_teams = sorted_ids[1:]
        
        # Apply rotation based on day number
        if rotation > 0:
            rotating_teams = rotating_teams[-(rotation):] + rotating_teams[:-(rotation)]
        
        # Create matchups
        matchups = []
        
        # Match fixed team with first rotating team (unless it's a bye)
        if fixed_team != "BYE" and rotating_teams[0] != "BYE":
            matchups.append((fixed_team, rotating_teams[0]))
        
        # Pair up the rest of the teams
        for i in range(1, len(rotating_teams) // 2):
            team_a = rotating_teams[i]
            team_b = rotating_teams[total_teams - 1 - i]
            
            if team_a != "BYE" and team_b != "BYE":
                matchups.append((team_a, team_b))
        
        # Ensure we have exactly 5 matches if possible
        while len(matchups) > 5:
            matchups.pop()  # Remove excess matches
        
        print(f"Generated {len(matchups)} matchups for day {day_number}")
        return matchups


    def create_balanced_matchups(team_ids: List[str], team_info: Dict[str, Any]) -> List[Tuple[str, str]]:
        """Create matchups based on division or other team attributes
        
        Args:
            team_ids (list): List of team IDs
            team_info (dict): Dictionary of team information
            
        Returns:
            list: List of matchup tuples (team_a_id, team_b_id)
        """
        # Group teams by division if available
        divisions = {}
        
        for team_id in team_ids:
            # Get team division from team_info or default to "unknown"
            team_division = "unknown"
            if team_id in team_info:
                team_division = team_info[team_id].get("division", "unknown")
            
            if team_division not in divisions:
                divisions[team_division] = []
            
            divisions[team_division].append(team_id)
        
        # Create matchups, prioritizing inter-division matchups
        matchups = []
        
        # Create matchups between divisions
        used_teams = set()
        for div1 in divisions:
            for div2 in divisions:
                if div1 == div2:
                    continue  # Skip intra-division matchups for now
                
                # Create matchups between teams in different divisions
                for team1 in divisions[div1]:
                    if team1 in used_teams:
                        continue
                    
                    for team2 in divisions[div2]:
                        if team2 in used_teams:
                            continue
                        
                        matchups.append((team1, team2))
                        used_teams.add(team1)
                        used_teams.add(team2)
                        break
                    
                    if team1 in used_teams:
                        break
        
        # Fill remaining with intra-division matchups if needed
        remaining_teams = [t for t in team_ids if t not in used_teams]
        
        # Sort remaining teams by division for consistency
        remaining_teams.sort(key=lambda x: team_info.get(x, {}).get("division", "unknown"))
        
        # Create pairings from remaining teams
        for i in range(0, len(remaining_teams), 2):
            if i + 1 < len(remaining_teams):
                matchups.append((remaining_teams[i], remaining_teams[i+1]))
        
        # Limit to 5 matches
        return matchups[:5]


    def get_team_power_level(team_id: str, team_info: Dict[str, Any]) -> float:
        """Calculate a team's power level based on members' stats
        
        Args:
            team_id (str): Team ID
            team_info (dict): Dictionary of team information
            
        Returns:
            float: Team power level score
        """
        # Default power level if no info found
        if team_id not in team_info:
            return 50.0
        
        # Get team's character stats, if available
        chars = team_info[team_id].get("characters", [])
        if not chars:
            return 50.0
        
        # Calculate power level based on character attributes
        total_power = 0
        for char in chars:
            # Sum up relevant attributes
            power = 0
            for stat in ["aSTR", "aSPD", "aOP", "aLDR", "aDUR"]:
                power += char.get(stat, 5)
            
            # Average and normalize to 0-100 scale
            char_power = (power / 5) * 10
            total_power += char_power
        
        # Average team power
        return total_power / len(chars)