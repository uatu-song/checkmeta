"""
META Fantasy League Simulator - Common Helper Functions
Provides role mapping and division logic helper functions
"""

from typing import Dict, List, Any, Optional, Union, Tuple

def map_position_to_role(position: str) -> str:
    """Map position names to standardized role codes
    
    Args:
        position: Position name or code
        
    Returns:
        str: Standardized role code
    """
    position = str(position).upper().strip()
    
    # Standard position mappings
    position_map = {
        "FIELD LEADER": "FL",
        "VANGUARD": "VG",
        "ENFORCER": "EN",
        "RANGER": "RG",
        "GHOST OPERATIVE": "GO",
        "PSI OPERATIVE": "PO",
        "SOVEREIGN": "SV"
    }
    
    # Check for exact matches
    if position in position_map:
        return position_map[position]
    
    # Check for partial matches
    for key, value in position_map.items():
        if key in position:
            return value
    
    # Check if already a valid role code
    valid_roles = ["FL", "VG", "EN", "RG", "GO", "PO", "SV"]
    if position in valid_roles:
        return position
    
    # Default
    return "FL"

def get_division_from_role(role: str) -> str:
    """Map role codes to divisions (operations or intelligence)
    
    Args:
        role: Role code
        
    Returns:
        str: Division code ('o' or 'i')
    """
    operations_roles = ["FL", "VG", "EN"]
    intelligence_roles = ["RG", "GO", "PO", "SV"]
    
    if role in operations_roles:
        return "o"
    elif role in intelligence_roles:
        return "i"
    else:
        return "o"  # Default to operations

def get_role_name(role: str) -> str:
    """Get full name for a role code
    
    Args:
        role: Role code
        
    Returns:
        str: Full role name
    """
    role_names = {
        "FL": "Field Leader",
        "VG": "Vanguard",
        "EN": "Enforcer",
        "RG": "Ranger",
        "GO": "Ghost Operative",
        "PO": "Psi Operative",
        "SV": "Sovereign"
    }
    
    return role_names.get(role, role)

def get_division_name(division: str) -> str:
    """Get full name for a division code
    
    Args:
        division: Division code
        
    Returns:
        str: Full division name
    """
    division_names = {
        "o": "Operations",
        "i": "Intelligence"
    }
    
    return division_names.get(division, division)

def get_trait_display_name(trait_id: str) -> str:
    """Get display name for a trait ID
    
    Args:
        trait_id: Raw trait ID
        
    Returns:
        str: Formatted trait display name
    """
    # Replace hyphens with spaces
    name = trait_id.replace('-', ' ')
    
    # Capitalize words
    return ' '.join(word.capitalize() for word in name.split())

def format_hp_display(hp: float, max_hp: float = 100.0) -> str:
    """Format HP value for display with color coding
    
    Args:
        hp: Current HP value
        max_hp: Maximum HP value
        
    Returns:
        str: Formatted HP display
    """
    # Calculate percentage
    percentage = hp / max_hp * 100
    
    # Format with color indicator
    if percentage > 60:
        indicator = "+"  # Good
    elif percentage > 30:
        indicator = "~"  # Medium
    else:
        indicator = "!"  # Critical
    
    return f"{indicator}{hp:.1f}/{max_hp:.1f}"

def format_time(seconds: float) -> str:
    """Format seconds into human readable time
    
    Args:
        seconds: Time in seconds
        
    Returns:
        str: Formatted time string
    """
    minutes, seconds = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

def calculate_win_percentage(wins: int, losses: int, draws: int = 0) -> float:
    """Calculate win percentage
    
    Args:
        wins: Number of wins
        losses: Number of losses
        draws: Number of draws
        
    Returns:
        float: Win percentage (0-100)
    """
    total_matches = wins + losses + draws
    
    if total_matches == 0:
        return 0.0
    
    # Count draws as half a win
    win_equiv = wins + (draws / 2)
    
    return (win_equiv / total_matches) * 100

def sanitize_filename(filename: str) -> str:
    """Sanitize a string to use as a filename
    
    Args:
        filename: Input string to sanitize
        
    Returns:
        str: Sanitized filename
    """
    # Replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove leading/trailing spaces
    filename = filename.strip()
    
    # Ensure not empty
    if not filename:
        filename = "unnamed"
    
    return filename

def parse_stat_modifiers(modifier_string: str) -> Dict[str, int]:
    """Parse a stat modifier string into a dictionary
    
    Args:
        modifier_string: Stat modifier string (e.g., "STR+2,SPD-1")
        
    Returns:
        dict: Dictionary of stat modifiers
    """
    modifiers = {}
    
    if not modifier_string:
        return modifiers
    
    # Split by commas
    parts = modifier_string.split(',')
    
    for part in parts:
        part = part.strip()
        
        # Find the modifier symbol (+ or -)
        plus_pos = part.find('+')
        minus_pos = part.find('-')
        
        if plus_pos > 0:
            stat = part[:plus_pos].strip().upper()
            try:
                value = int(part[plus_pos:])
                modifiers[stat] = value
            except ValueError:
                continue
        elif minus_pos > 0:
            stat = part[:minus_pos].strip().upper()
            try:
                value = int(part[minus_pos:])
                modifiers[stat] = value
            except ValueError:
                continue
    
    return modifiers