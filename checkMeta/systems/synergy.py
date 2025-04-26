"""
META Fantasy League Simulator - Synergy System
Handles team synergy calculations and effects
"""

class SynergySystem:
    """System for calculating and applying team synergy effects"""
    
    def __init__(self):
        """Initialize the synergy system"""
        self.synergy_thresholds = {
            'low': 30,
            'medium': 60,
            'high': 80,
            'perfect': 95
        }
    
    def calculate_team_synergy(self, team):
        """Calculate synergy score for a team
        
        Args:
            team: Team object with active_characters attribute
            
        Returns:
            float: Synergy score (0-100)
        """
        if not hasattr(team, 'active_characters') or not team.active_characters:
            return 0
        
        # Several factors contribute to synergy:
        
        # 1. Morale average
        avg_morale = sum(getattr(char, 'morale', 50) for char in team.active_characters) / len(team.active_characters)
        morale_factor = avg_morale / 100.0  # Normalize to 0-1
        
        # 2. Role coverage
        role_factor = self._calculate_role_coverage(team)
        
        # 3. Games played together
        games_factor = self._calculate_games_together(team)
        
        # 4. Division balance
        div_factor = self._calculate_division_balance(team)
        
        # Calculate final synergy score
        synergy_score = (
            morale_factor * 30 +  # 30% weight
            role_factor * 30 +     # 30% weight
            games_factor * 20 +    # 20% weight
            div_factor * 20        # 20% weight
        )
        
        # Store on team
        team.synergy_score = synergy_score
        
        # Apply synergy effects
        self._apply_synergy_effects(team, synergy_score)
        
        return synergy_score
    
    def _calculate_role_coverage(self, team):
        """Calculate role coverage factor
        
        Args:
            team: Team to calculate for
            
        Returns:
            float: Role coverage factor (0-1)
        """
        # Get all characters' roles
        roles = [getattr(char, 'role', 'FL') for char in team.active_characters]
        
        # Define ideal role composition
        ideal_roles = {
            'FL': 1,  # Field Leader
            'VG': 1,  # Vanguard
            'EN': 1,  # Enforcer
            'RG': 1,  # Ranger
            'GO': 1,  # Ghost Operative
            'PO': 1,  # Psi Operative
            'SV': 1   # Sovereign
        }
        
        # Count role occurrences
        role_counts = {}
        for role in roles:
            role_counts[role] = role_counts.get(role, 0) + 1
        
        # Calculate coverage
        coverage = 0
        for role, ideal_count in ideal_roles.items():
            actual_count = role_counts.get(role, 0)
            if actual_count >= ideal_count:
                coverage += 1
        
        return coverage / len(ideal_roles)
    
    def _calculate_games_together(self, team):
        """Calculate games played together factor
        
        Args:
            team: Team to calculate for
            
        Returns:
            float: Games together factor (0-1)
        """
        # Get number of games played with team
        games_with_team = []
        
        for char in team.active_characters:
            # Check if has games_with_team attribute, otherwise default to 0
            games = getattr(char, 'games_with_team', 0)
            games_with_team.append(games)
        
        # If no games recorded, return baseline value
        if not games_with_team or max(games_with_team) == 0:
            return 0.5
        
        # Calculate average games played
        avg_games = sum(games_with_team) / len(games_with_team)
        
        # Convert to factor with diminishing returns
        # 10 games -> 0.8 factor, 20 games -> 0.9 factor, 50 games -> 0.98 factor
        import math
        games_factor = 1.0 - (1.0 / (1.0 + avg_games / 5.0))
        
        return games_factor
    
    def _calculate_division_balance(self, team):
        """Calculate division balance factor
        
        Args:
            team: Team to calculate for
            
        Returns:
            float: Division balance factor (0-1)
        """
        # Count characters in each division
        ops_count = 0
        intel_count = 0
        
        for char in team.active_characters:
            div = getattr(char, 'division', 'o')
            if div == 'o':
                ops_count += 1
            else:
                intel_count += 1
        
        total_count = ops_count + intel_count
        
        # Calculate balance (difference from 50/50 split)
        if total_count == 0:
            return 0
        
        # Optimal is 60/40 split either way
        ops_pct = ops_count / total_count
        intel_pct = intel_count / total_count
        
        # Calculate how close we are to optimal
        if ops_pct > intel_pct:
            balance = min(ops_pct, 0.6) / 0.6
        else:
            balance = min(intel_pct, 0.6) / 0.6
        
        return balance
    
    def _apply_synergy_effects(self, team, synergy_score):
        """Apply synergy effects to team
        
        Args:
            team: Team to apply effects to
            synergy_score (float): Synergy score
        """
        # Determine synergy level
        synergy_level = "none"
        for level, threshold in sorted(self.synergy_thresholds.items(), key=lambda x: x[1]):
            if synergy_score >= threshold:
                synergy_level = level
        
        # Apply synergy bonuses based on level
        bonus_values = {
            'none': 0.0,
            'low': 0.05,
            'medium': 0.1,
            'high': 0.15,
            'perfect': 0.2
        }
        
        bonus = bonus_values.get(synergy_level, 0.0)
        
        # Apply bonus to each character
        for char in team.active_characters:
            char.synergy_modifiers = {
                'combat_bonus': bonus,
                'defense_bonus': bonus
            }