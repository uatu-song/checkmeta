"""
META Fantasy League Simulator - Morale and Momentum System
Handles team morale, momentum tracking, and comeback mechanics
"""

class MoraleSystem:
    """System for calculating and applying morale effects"""
    
    def __init__(self):
        """Initialize the morale system"""
        self.morale_thresholds = {
            'very_low': 20,
            'low': 40,
            'neutral': 60,
            'high': 80,
            'very_high': 100
        }
    
    def calculate_morale_modifiers(self, morale):
        """Calculate modifiers based on morale level
        
        Args:
            morale (int): Morale value (0-100)
            
        Returns:
            dict: Morale modifiers
        """
        # Default neutral modifiers
        modifiers = {
            'combat_bonus': 0.0,
            'defense_bonus': 0.0,
            'stamina_regen': 0.0,
            'trait_activation': 0.0
        }
        
        # Very low morale (0-20)
        if morale <= self.morale_thresholds['very_low']:
            modifiers['combat_bonus'] = -0.2
            modifiers['defense_bonus'] = -0.15
            modifiers['stamina_regen'] = -0.2
            modifiers['trait_activation'] = -0.1
        
        # Low morale (21-40)
        elif morale <= self.morale_thresholds['low']:
            modifiers['combat_bonus'] = -0.1
            modifiers['defense_bonus'] = -0.05
            modifiers['stamina_regen'] = -0.1
            modifiers['trait_activation'] = -0.05
        
        # High morale (61-80)
        elif morale <= self.morale_thresholds['high']:
            modifiers['combat_bonus'] = 0.1
            modifiers['defense_bonus'] = 0.05
            modifiers['stamina_regen'] = 0.1
            modifiers['trait_activation'] = 0.05
        
        # Very high morale (81-100)
        elif morale <= self.morale_thresholds['very_high']:
            modifiers['combat_bonus'] = 0.2
            modifiers['defense_bonus'] = 0.15
            modifiers['stamina_regen'] = 0.2
            modifiers['trait_activation'] = 0.1
        
        return modifiers
    
    def update_team_morale(self, team, match_result):
        """Update team morale based on match result
        
        Args:
            team: Team object or list of characters
            match_result (str): 'win', 'loss', or 'draw'
        """
        # Determine morale change based on result
        if match_result == 'win':
            morale_change = 10
        elif match_result == 'loss':
            morale_change = -5
        else:  # draw
            morale_change = 2
        
        # Apply to all characters
        characters = team.active_characters if hasattr(team, 'active_characters') else team
        
        for character in characters:
            if hasattr(character, 'morale'):
                character.morale = max(0, min(100, character.morale + morale_change))
            elif isinstance(character, dict):
                character['morale'] = max(0, min(100, character.get('morale', 50) + morale_change))


class MomentumSystem:
    """System for tracking and applying team momentum effects"""
    
    def __init__(self):
        """Initialize the momentum system"""
        self.momentum_states = ['crash', 'stable', 'building']
        self.momentum_thresholds = {
            'crash': -3,
            'building': 3
        }
    
    def get_initial_momentum(self):
        """Get initial momentum state"""
        return {
            "state": "stable",
            "value": 0
        }
    
    def update_momentum(self, team_a_status, team_b_status, context=None):
        """Update momentum for both teams based on battle status
        
        Args:
            team_a_status (dict): Status of team A (active/KO counts)
            team_b_status (dict): Status of team B (active/KO counts)
            context (dict, optional): Match context
            
        Returns:
            tuple: (team_a_momentum, team_b_momentum)
        """
        context = context or {}
        
        # Get current momentum or initialize
        team_a_momentum = context.get("team_a_momentum", self.get_initial_momentum())
        team_b_momentum = context.get("team_b_momentum", self.get_initial_momentum())
        
        # Calculate relative team strengths
        team_a_percentage = self._calculate_team_strength(team_a_status)
        team_b_percentage = self._calculate_team_strength(team_b_status)
        
        # Update momentum values based on relative strength
        momentum_shift = self._calculate_momentum_shift(team_a_percentage, team_b_percentage)
        
        # Apply momentum shift
        team_a_momentum["value"] += momentum_shift
        team_b_momentum["value"] -= momentum_shift
        
        # Cap momentum values
        team_a_momentum["value"] = max(-5, min(5, team_a_momentum["value"]))
        team_b_momentum["value"] = max(-5, min(5, team_b_momentum["value"]))
        
        # Update momentum states
        team_a_momentum["state"] = self._determine_momentum_state(team_a_momentum["value"])
        team_b_momentum["state"] = self._determine_momentum_state(team_b_momentum["value"])
        
        return team_a_momentum, team_b_momentum
    
    def _calculate_team_strength(self, team_status):
        """Calculate team strength percentage
        
        Args:
            team_status (dict): Team status (active/KO counts)
            
        Returns:
            float: Team strength percentage (0-1)
        """
        active_count = team_status.get("active", 0)
        total_count = team_status.get("total", 0)
        
        if total_count == 0:
            return 0
            
        return active_count / total_count
    
    def _calculate_momentum_shift(self, team_a_strength, team_b_strength):
        """Calculate momentum shift based on team strengths
        
        Args:
            team_a_strength (float): Team A strength (0-1)
            team_b_strength (float): Team B strength (0-1)
            
        Returns:
            int: Momentum shift value (-1, 0, or 1)
        """
        # Significant advantage (30% difference)
        if team_a_strength > team_b_strength + 0.3:
            return 1
        elif team_b_strength > team_a_strength + 0.3:
            return -1
        
        # Moderate advantage (10-30% difference)
        if team_a_strength > team_b_strength + 0.1:
            return 0.5
        elif team_b_strength > team_a_strength + 0.1:
            return -0.5
            
        # Balanced (less than 10% difference)
        return 0
    
    def _determine_momentum_state(self, momentum_value):
        """Determine momentum state based on value
        
        Args:
            momentum_value (int): Momentum value (-5 to 5)
            
        Returns:
            str: Momentum state ('crash', 'stable', or 'building')
        """
        if momentum_value <= self.momentum_thresholds['crash']:
            return 'crash'
        elif momentum_value >= self.momentum_thresholds['building']:
            return 'building'
        else:
            return 'stable'
    
    def apply_momentum_effects(self, characters, momentum):
        """Apply effects based on team momentum
        
        Args:
            characters (list): List of characters
            momentum (dict): Team momentum state and value
            
        Returns:
            dict: Applied effects
        """
        effects = {}
        
        # Apply effects based on momentum state
        if momentum["state"] == "building":
            # Building momentum grants offensive bonuses
            effects["combat_bonus"] = 0.1
            effects["trait_activation_bonus"] = 0.05
            
            # Apply to characters
            for character in characters:
                if hasattr(character, 'momentum_state'):
                    character.momentum_state = 'building'
                    character.momentum_value = momentum["value"]
                elif isinstance(character, dict):
                    character['momentum_state'] = 'building'
                    character['momentum_value'] = momentum["value"]
        
        elif momentum["state"] == "crash":
            # Crash momentum activates comeback mechanics
            effects["damage_reduction"] = 0.15
            effects["recovery_bonus"] = 0.2
            effects["trait_activation_bonus"] = 0.15
            
            # Apply to characters
            for character in characters:
                if hasattr(character, 'momentum_state'):
                    character.momentum_state = 'crash'
                    character.momentum_value = momentum["value"]
                elif isinstance(character, dict):
                    character['momentum_state'] = 'crash'
                    character['momentum_value'] = momentum["value"]
        
        else:  # stable
            # Stable has no special effects
            effects = {}
            
            # Reset character momentum states
            for character in characters:
                if hasattr(character, 'momentum_state'):
                    character.momentum_state = 'stable'
                    character.momentum_value = momentum["value"]
                elif isinstance(character, dict):
                    character['momentum_state'] = 'stable'
                    character['momentum_value'] = momentum["value"]
        
        return effects


class CombatMomentumTracker:
    """Combined system for tracking morale, momentum, and applying effects"""
    
    def __init__(self):
        """Initialize the combat momentum tracker"""
        self.morale_system = MoraleSystem()
        self.momentum_system = MomentumSystem()
    
    def initialize_match_context(self, context, team_a, team_b):
        """Initialize the match context with morale and momentum tracking
        
        Args:
            context (dict): Match context
            team_a (list): Team A characters
            team_b (list): Team B characters
            
        Returns:
            dict: Updated context
        """
        # Initialize momentum
        context["team_a_momentum"] = self.momentum_system.get_initial_momentum()
        context["team_b_momentum"] = self.momentum_system.get_initial_momentum()
        
        # Calculate initial morale modifiers
        context["team_a_morale_mods"] = {}
        context["team_b_morale_mods"] = {}
        
        for char in team_a:
            morale = char.get('morale', 50) if isinstance(char, dict) else getattr(char, 'morale', 50)
            char_id = char.get('id', '') if isinstance(char, dict) else getattr(char, 'id', '')
            context["team_a_morale_mods"][char_id] = self.morale_system.calculate_morale_modifiers(morale)
        
        for char in team_b:
            morale = char.get('morale', 50) if isinstance(char, dict) else getattr(char, 'morale', 50)
            char_id = char.get('id', '') if isinstance(char, dict) else getattr(char, 'id', '')
            context["team_b_morale_mods"][char_id] = self.morale_system.calculate_morale_modifiers(morale)
        
        return context
    
    def update_round_state(self, context, team_a, team_b):
        """Update state for a new round
        
        Args:
            context (dict): Match context
            team_a (list): Team A characters
            team_b (list): Team B characters
            
        Returns:
            dict: Updated context
        """
        # Calculate team status
        team_a_status = self._calculate_team_status(team_a)
        team_b_status = self._calculate_team_status(team_b)
        
        # Update momentum
        context["team_a_momentum"], context["team_b_momentum"] = self.momentum_system.update_momentum(
            team_a_status, team_b_status, context
        )
        
        # Apply momentum effects
        context["team_a_momentum_effects"] = self.momentum_system.apply_momentum_effects(
            team_a, context["team_a_momentum"]
        )
        
        context["team_b_momentum_effects"] = self.momentum_system.apply_momentum_effects(
            team_b, context["team_b_momentum"]
        )
        
        return context
    
    def _calculate_team_status(self, team):
        """Calculate team status (active/KO counts)
        
        Args:
            team (list): Team characters
            
        Returns:
            dict: Team status
        """
        active_count = 0
        ko_count = 0
        
        for char in team:
            is_ko = False
            is_dead = False
            
            if isinstance(char, dict):
                is_ko = char.get('is_ko', False)
                is_dead = char.get('is_dead', False)
            else:
                is_ko = getattr(char, 'is_ko', False)
                is_dead = getattr(char, 'is_dead', False)
            
            if not is_ko and not is_dead:
                active_count += 1
            elif is_ko:
                ko_count += 1
        
        return {
            "active": active_count,
            "ko": ko_count,
            "total": len(team)
        }
    
    def get_character_modifiers(self, character, context):
        """Get combined morale and momentum modifiers for a character
        
        Args:
            character: Character object or dictionary
            context (dict): Match context
            
        Returns:
            dict: Combined modifiers
        """
        modifiers = {
            'combat_bonus': 0.0,
            'defense_bonus': 0.0,
            'stamina_regen': 0.0,
            'trait_activation': 0.0
        }
        
        # Get character ID and team
        if isinstance(character, dict):
            char_id = character.get('id', '')
            team = 'A' if character.get('team', '') == 'A' else 'B'
        else:
            char_id = getattr(character, 'id', '')
            team = 'A' if getattr(character, 'team', '') == 'A' else 'B'
        
        # Apply morale modifiers
        morale_mods = {}
        if team == 'A' and char_id in context.get("team_a_morale_mods", {}):
            morale_mods = context["team_a_morale_mods"][char_id]
        elif team == 'B' and char_id in context.get("team_b_morale_mods", {}):
            morale_mods = context["team_b_morale_mods"][char_id]
        
        # Apply momentum effects
        momentum_effects = {}
        if team == 'A' and "team_a_momentum_effects" in context:
            momentum_effects = context["team_a_momentum_effects"]
        elif team == 'B' and "team_b_momentum_effects" in context:
            momentum_effects = context["team_b_momentum_effects"]
        
        # Combine modifiers
        for key in modifiers:
            modifiers[key] += morale_mods.get(key, 0.0)
            
            # Map momentum effects to modifier keys
            if key == 'combat_bonus' and 'combat_bonus' in momentum_effects:
                modifiers[key] += momentum_effects['combat_bonus']
            elif key == 'defense_bonus' and 'damage_reduction' in momentum_effects:
                modifiers[key] += momentum_effects['damage_reduction']
            elif key == 'stamina_regen' and 'recovery_bonus' in momentum_effects:
                modifiers[key] += momentum_effects['recovery_bonus']
            elif key == 'trait_activation' and 'trait_activation_bonus' in momentum_effects:
                modifiers[key] += momentum_effects['trait_activation_bonus']
        
        return modifiers