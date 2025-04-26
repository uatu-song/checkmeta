# config/game_config.py
###############################
"""
Game configuration constants and settings
"""

# Game constants
MAX_ACTIVE_ROSTER_SIZE = 8  # 8 active players, rest on bench
MAX_MOVES_TO_SIMULATE = 30  # Maximum chess moves to simulate per match
MAX_TRAITS_PER_CHARACTER = 3  # Maximum number of traits a character can have
MAX_CONVERGENCES_PER_CHAR = 3  # Maximum convergences per character per round

# Starting values
DEFAULT_HP = 100
DEFAULT_STAMINA = 100
DEFAULT_LIFE = 100
DEFAULT_MORALE = 50
DEFAULT_ATTRIBUTE_VALUE = 5  # Default value for attributes if not specified

# Damage and recovery settings
BASE_HP_REGEN = 5
BASE_STAMINA_REGEN = 5
DAMAGE_REDUCTION_CAP = 85  # Maximum damage reduction percentage
MATERIAL_DAMAGE_FACTOR = 3  # Multiplier for damage based on material loss

# Division codes
OPERATIONS_ROLES = ["FL", "VG", "EN"]
INTELLIGENCE_ROLES = ["RG", "GO", "PO", "SV"]

# Position mappings
POSITION_MAP = {
    "FIELD LEADER": "FL",
    "VANGUARD": "VG",
    "ENFORCER": "EN",
    "RANGER": "RG",
    "GHOST OPERATIVE": "GO",
    "PSI OPERATIVE": "PO",
    "SOVEREIGN": "SV"
}

# Valid role codes
VALID_ROLES = ["FL", "VG", "EN", "RG", "GO", "PO", "SV"]