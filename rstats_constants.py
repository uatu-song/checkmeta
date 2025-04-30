"""
rStats System Constants for META Fantasy League
Defines all available stats that can be tracked for characters and teams
"""

# Character Stats
CHARACTER_STATS = {
    # Match and Game Stats
    "MATCHES_PLAYED": {"default": 0, "display_name": "Matches Played", "category": "general"},
    "WINS": {"default": 0, "display_name": "Wins", "category": "general"},
    "LOSSES": {"default": 0, "display_name": "Losses", "category": "general"},
    "DRAWS": {"default": 0, "display_name": "Draws", "category": "general"},
    "WIN_STREAK": {"default": 0, "display_name": "Winning Streak", "category": "general"},
    "LONGEST_WIN_STREAK": {"default": 0, "display_name": "Longest Winning Streak", "category": "general"},
    
    # Chess Stats
    "CHECKMATES_GIVEN": {"default": 0, "display_name": "Checkmates Given", "category": "chess"},
    "CHECKMATES_RECEIVED": {"default": 0, "display_name": "Checkmates Received", "category": "chess"},
    "MOVES_PLAYED": {"default": 0, "display_name": "Moves Played", "category": "chess"},
    "CAPTURES_MADE": {"default": 0, "display_name": "Captures Made", "category": "chess"},
    "PIECES_LOST": {"default": 0, "display_name": "Pieces Lost", "category": "chess"},
    "MATERIAL_ADVANTAGE_GAINED": {"default": 0, "display_name": "Material Advantage Gained", "category": "chess"},
    "MATERIAL_ADVANTAGE_LOST": {"default": 0, "display_name": "Material Advantage Lost", "category": "chess"},
    
    # Combat Stats
    "DAMAGE_DEALT": {"default": 0, "display_name": "Damage Dealt", "category": "combat"},
    "DAMAGE_TAKEN": {"default": 0, "display_name": "Damage Taken", "category": "combat"},
    "KOS_DEALT": {"default": 0, "display_name": "KOs Dealt", "category": "combat"},
    "TIMES_KOD": {"default": 0, "display_name": "Times KO'd", "category": "combat"},
    "CRITICAL_HITS": {"default": 0, "display_name": "Critical Hits", "category": "combat"},
    "ROUNDS_SURVIVED": {"default": 0, "display_name": "Rounds Survived", "category": "combat"},
    
    # Convergence Stats
    "CONVERGENCES_INITIATED": {"default": 0, "display_name": "Convergences Initiated", "category": "convergence"},
    "CONVERGENCES_RECEIVED": {"default": 0, "display_name": "Convergences Received", "category": "convergence"},
    "ASSISTS": {"default": 0, "display_name": "Assists Given", "category": "convergence"},
    "ASSIST_DAMAGE": {"default": 0, "display_name": "Assist Damage", "category": "convergence"},
    "TEAM_DAMAGE_PREVENTED": {"default": 0, "display_name": "Team Damage Prevented", "category": "convergence"},
    
    # Trait Stats
    "TRAIT_ACTIVATIONS": {"default": 0, "display_name": "Trait Activations", "category": "traits"},
    "OFFENSIVE_TRAIT_ACTIVATIONS": {"default": 0, "display_name": "Offensive Trait Activations", "category": "traits"},
    "DEFENSIVE_TRAIT_ACTIVATIONS": {"default": 0, "display_name": "Defensive Trait Activations", "category": "traits"},
    "SUPPORT_TRAIT_ACTIVATIONS": {"default": 0, "display_name": "Support Trait Activations", "category": "traits"},
    "UTILITY_TRAIT_ACTIVATIONS": {"default": 0, "display_name": "Utility Trait Activations", "category": "traits"},
    
    # Development Stats
    "XP_EARNED": {"default": 0, "display_name": "XP Earned", "category": "development"},
    "LEVEL_UPS": {"default": 0, "display_name": "Level Ups", "category": "development"},
    
    # Stamina/Morale/Injury Stats
    "STAMINA_DEPLETED": {"default": 0, "display_name": "Times Stamina Depleted", "category": "condition"},
    "MORALE_COLLAPSED": {"default": 0, "display_name": "Morale Collapses", "category": "condition"},
    "INJURIES_SUSTAINED": {"default": 0, "display_name": "Injuries Sustained", "category": "condition"},
    "DAYS_INJURED": {"default": 0, "display_name": "Days Injured", "category": "condition"},
    
    # Team Stats
    "TEAM_WINS_CONTRIBUTED": {"default": 0, "display_name": "Team Wins Contributed", "category": "team"},
    "TEAM_SYNERGY_ACTIVATIONS": {"default": 0, "display_name": "Team Synergy Activations", "category": "team"},
    "TEAM_CARRYING": {"default": 0, "display_name": "Team Carrying", "category": "team"},
}

# Team Stats
TEAM_STATS = {
    # Match Stats
    "MATCHES_PLAYED": {"default": 0, "display_name": "Matches Played", "category": "general"},
    "WINS": {"default": 0, "display_name": "Wins", "category": "general"},
    "LOSSES": {"default": 0, "display_name": "Losses", "category": "general"},
    "DRAWS": {"default": 0, "display_name": "Draws", "category": "general"},
    "WIN_STREAK": {"default": 0, "display_name": "Winning Streak", "category": "general"},
    "LONGEST_WIN_STREAK": {"default": 0, "display_name": "Longest Winning Streak", "category": "general"},
    "POINTS": {"default": 0, "display_name": "League Points", "category": "general"},
    
    # Combat Stats
    "TOTAL_DAMAGE_DEALT": {"default": 0, "display_name": "Total Damage Dealt", "category": "combat"},
    "TOTAL_DAMAGE_TAKEN": {"default": 0, "display_name": "Total Damage Taken", "category": "combat"},
    "KOS_DEALT": {"default": 0, "display_name": "KOs Dealt", "category": "combat"},
    "TIMES_KOD": {"default": 0, "display_name": "Times KO'd", "category": "combat"},
    
    # Tactical Stats
    "CONVERGENCES": {"default": 0, "display_name": "Convergences", "category": "tactics"},
    "CHECKMATES_GIVEN": {"default": 0, "display_name": "Checkmates Given", "category": "tactics"},
    "CHECKMATES_RECEIVED": {"default": 0, "display_name": "Checkmates Received", "category": "tactics"},
    "TRAIT_ACTIVATIONS": {"default": 0, "display_name": "Trait Activations", "category": "tactics"},
    "SYNERGY_ACTIVATIONS": {"default": 0, "display_name": "Synergy Activations", "category": "tactics"},
    
    # Condition Stats  
    "INJURIES_SUSTAINED": {"default": 0, "display_name": "Injuries Sustained", "category": "condition"},
    "MORALE_COLLAPSES": {"default": 0, "display_name": "Morale Collapses", "category": "condition"},
    
    # Home/Away Stats
    "HOME_WINS": {"default": 0, "display_name": "Home Wins", "category": "location"},
    "HOME_LOSSES": {"default": 0, "display_name": "Home Losses", "category": "location"},
    "AWAY_WINS": {"default": 0, "display_name": "Away Wins", "category": "location"},
    "AWAY_LOSSES": {"default": 0, "display_name": "Away Losses", "category": "location"},
}

# Team Stat Contribution Thresholds
TEAM_CONTRIBUTION_THRESHOLDS = {
    "CARRYING": 0.5,  # 50% of team's output comes from one character
    "KEY_CONTRIBUTOR": 0.3,  # 30% of team's output
    "SUPPORTER": 0.15,  # 15% of team's output
}

# Event to Stat Mapping
EVENT_TO_STAT_MAP = {
    "checkmate_given": "CHECKMATES_GIVEN",
    "checkmate_received": "CHECKMATES_RECEIVED",
    "piece_captured": "CAPTURES_MADE",
    "piece_lost": "PIECES_LOST",
    "damage_dealt": "DAMAGE_DEALT",
    "damage_taken": "DAMAGE_TAKEN",
    "ko_dealt": "KOS_DEALT",
    "ko_received": "TIMES_KOD",
    "critical_hit": "CRITICAL_HITS",
    "round_survived": "ROUNDS_SURVIVED",
    "convergence_triggered": "CONVERGENCES_INITIATED",
    "convergence_received": "CONVERGENCES_RECEIVED",
    "assist_given": "ASSISTS",
    "trait_activated": "TRAIT_ACTIVATIONS",
    "offensive_trait_activated": "OFFENSIVE_TRAIT_ACTIVATIONS",
    "defensive_trait_activated": "DEFENSIVE_TRAIT_ACTIVATIONS",
    "support_trait_activated": "SUPPORT_TRAIT_ACTIVATIONS",
    "utility_trait_activated": "UTILITY_TRAIT_ACTIVATIONS",
    "xp_earned": "XP_EARNED",
    "level_up": "LEVEL_UPS",
    "stamina_depleted": "STAMINA_DEPLETED",
    "morale_collapsed": "MORALE_COLLAPSED",
    "injury_sustained": "INJURIES_SUSTAINED",
}