"""
META Fantasy League Simulator - Team Helpers
Provides utilities for team identification and management
"""

from typing import Dict, List, Any, Optional, Tuple
from config import get_config

def normalize_team_id(team_id):
    """Normalize team ID for consistent comparison
    
    Args:
        team_id: Team ID in any format
        
    Returns:
        str: Normalized team ID
    """
    # Ensure string type
    team_id = str(team_id)
    
    # Remove non-alphanumeric characters
    team_id = ''.join(c for c in team_id if c.isalnum())
    
    # Ensure it starts with 't' (case insensitive)
    if not team_id.lower().startswith('t'):
        team_id = 't' + team_id
    
    # Convert to lowercase for consistent comparison
    return team_id.lower()

def get_team_name(team_id):
    """Get friendly team name from team ID
    
    Args:
        team_id: Team ID
        
    Returns:
        str: Team name
    """
    config = get_config()
    
    # Normalize team ID
    norm_id = normalize_team_id(team_id)
    
    # Look up in config
    return config.get_team_name(norm_id)

def get_matchups_for_day(day_number):
    """Get matchups for a specific day
    
    Args:
        day_number: Day number
        
    Returns:
        List: List of matchup tuples
    """
    config = get_config()
    
    # Get raw matchups from config
    raw_matchups = config.get_matchups_for_day(day_number)
    
    # Normalize team IDs in matchups
    normalized_matchups = []
    for team_a, team_b in raw_matchups:
        normalized_matchups.append((
            normalize_team_id(team_a),
            normalize_team_id(team_b)
        ))
    
    return normalized_matchups

def format_team_display(team_id, include_id=False):
    """Format team name for display
    
    Args:
        team_id: Team ID
        include_id: Whether to include team ID in output
        
    Returns:
        str: Formatted team name
    """
    team_name = get_team_name(team_id)
    
    if include_id:
        return f"{team_name} ({team_id})"
    else:
        return team_name

def get_team_color(team_id):
    """Get team color based on team ID
    
    Args:
        team_id: Team ID
        
    Returns:
        str: Team color
    """
    # Normalize team ID
    norm_id = normalize_team_id(team_id)
    
    # Color map based on team ID's numeric part
    num_part = ''.join(c for c in norm_id if c.isdigit())
    
    # Default colors for teams
    colors = {
        "001": "#0000FF",  # Blue
        "002": "#800080",  # Purple
        "003": "#FF0000",  # Red
        "004": "#0000FF",  # Blue
        "005": "#800080",  # Purple
        "006": "#FFA500",  # Orange
        "007": "#000000",  # Black
        "008": "#008000",  # Green
        "009": "#FF0000",  # Red
        "010": "#800000"   # Maroon
    }
    
    # Return color or default
    return colors.get(num_part, "#333333")