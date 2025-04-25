###############################
# utils/helpers.py
###############################
"""
Helper functions for META League Simulator
"""

from typing import Dict, List, Any, Optional
from ..config.game_config import POSITION_MAP, VALID_ROLES, OPERATIONS_ROLES, INTELLIGENCE_ROLES

def get_division_from_role(role: str) -> str:
    """Map role codes to divisions (operations or intelligence)"""
    if role in OPERATIONS_ROLES:
        return "o"
    elif role in INTELLIGENCE_ROLES:
        return "i"
    else:
        return "o"  # Default to operations

def map_position_to_role(position: str) -> str:
    """Map position names to standardized role codes"""
    position = str(position).upper().strip()
    
    # Check for exact matches in the position map
    if position in POSITION_MAP:
        return POSITION_MAP[position]
    
    # Check for partial matches
    for key, value in POSITION_MAP.items():
        if key in position:
            return value
    
    # Check if already a valid role code
    if position in VALID_ROLES:
        return position
    
    # Default
    return "FL"

def calculate_win_loss_record(character_results: List[Dict[str, Any]]) -> Dict[str, int]:
    """Calculate win/loss/draw record from character results"""
    record = {
        "wins": 0,
        "losses": 0,
        "draws": 0,
        "bench": 0
    }
    
    for result in character_results:
        if result["result"] == "win":
            record["wins"] += 1
        elif result["result"] == "loss":
            record["losses"] += 1
        elif result["result"] == "draw":
            record["draws"] += 1
        elif result["result"] == "bench":
            record["bench"] += 1
    
    return record

def format_damage_amount(damage: float) -> str:
    """Format damage amount with appropriate units"""
    if damage >= 1000:
        return f"{damage/1000:.1f}k"
    else:
        return f"{int(damage)}"

def has_role_in_active_roster(team: List[Dict[str, Any]], role: str, active_roster_size: int = 8) -> bool:
    """Check if team has a specific role in the active roster"""
    active_roster = team[:active_roster_size]
    return any(char["role"] == role for char in active_roster)