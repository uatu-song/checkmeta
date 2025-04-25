"""
Team synergy system for META League Simulator
"""

from typing import Dict, List, Any, Optional
from ..models.team import Team
from ..models.character import Character

class SynergySystem:
    """System for managing team synergy effects"""
    
    def __init__(self):
        """Initialize the synergy system"""
        self.team_bonuses = self._load_team_bonuses()
    
    def _load_team_bonuses(self) -> Dict[str, Dict[str, Any]]:
        """Load team-specific bonuses"""
        return {
            "avengers": {
                "attributes": {"aLDR": 1, "aFS": 1},
                "combat_bonus": 5,
                "recovery_boost": 10,
                "special_ability": "avengers_assemble"
            },
            "x-men": {
                "attributes": {"aESP": 1, "aWIL": 1},
                "combat_bonus": 0,
                "recovery_boost": 15,
                "special_ability": "teamwork"
            },
            "fantastic": {
                "attributes": {"aINT": 1, "aDUR": 1},
                "combat_bonus": 0,
                "recovery_boost": 15,
                "special_ability": "family_bond"
            },
            "guardians": {
                "attributes": {"aLCK": 1, "aOP": 1},
                "combat_bonus": 10,
                "recovery_boost": 5,
                "special_ability": "unpredictable"
            },
            "defenders": {
                "attributes": {"aDUR": 2},
                "combat_bonus": 0,
                "recovery_boost": 20,
                "special_ability": "endurance"
            },
            "illuminati": {
                "attributes": {"aINT": 2},
                "combat_bonus": 5,
                "recovery_boost": 5,
                "special_ability": "strategic_planning"
            },
            "champions": {
                "attributes": {"aSPD": 1, "aAM": 1},
                "combat_bonus": 5,
                "recovery_boost": 10,
                "special_ability": "youthful_energy"
            }
        }
    
    def apply_team_bonuses(self, team: Team) -> Team:
        """Apply synergy bonuses based on team affiliation"""
        team_name = team.team_name.lower() if team.team_name else ""
        
        # Base synergy bonuses for all teams
        morale_boost = 5
        stamina_recover = 2
        
        # Find matching team bonus
        matched_bonus = None
        for team_key, bonus in self.team_bonuses.items():
            if team_key in team_name:
                matched_bonus = bonus
                break
        
        # Apply standard bonuses to all team members
        for character in team.characters:
            # Standard morale boost
            character.morale = min(100, character.morale + morale_boost)
            
            # Apply team-specific bonuses if available
            if matched_bonus:
                # Attribute bonuses
                for attr, boost in matched_bonus["attributes"].items():
                    if attr in character.attributes:
                        character.attributes[attr] += boost
                
                # Track that these synergy bonuses were applied
                character.team_affiliation_bonuses = {
                    "team": team_name,
                    "attribute_bonuses": matched_bonus["attributes"],
                    "combat_bonus": matched_bonus["combat_bonus"],
                    "recovery_boost": matched_bonus["recovery_boost"],
                    "special_ability": matched_bonus["special_ability"]
                }
        
        return team
    
    def calculate_team_synergy(self, team: Team) -> Team:
        """Calculate and apply team synergy level"""
        # Base factors affecting synergy
        avg_morale = sum(char.morale for char in team.characters) / len(team.characters)
        avg_games_together = sum(char.games_with_team for char in team.characters) / len(team.characters)
        
        # Find leader bonus if available
        leader_bonus = 0
        for char in team.characters:
            if char.is_leader:
                leader_bonus = char.get_attribute('LDR') - 5
                break
        
        # Calculate synergy score (0-100)
        synergy_score = min(100, (
            (avg_morale * 0.5) +          # 50% influence from morale
            (avg_games_together * 2) +    # Games played together builds synergy
            (leader_bonus * 5)            # Strong leader improves synergy
        ))
        
        # Apply synergy bonuses based on score
        if synergy_score >= 80:  # Excellent synergy
            synergy_tier = 4
            combat_bonus = 15
            damage_reduction = 15
            convergence_bonus = 15
            healing_bonus = 8
        elif synergy_score >= 60:  # Good synergy
            synergy_tier = 3
            combat_bonus = 10
            damage_reduction = 10
            convergence_bonus = 10
            healing_bonus = 5
        elif synergy_score >= 40:  # Decent synergy
            synergy_tier = 2
            combat_bonus = 5
            damage_reduction = 5
            convergence_bonus = 5
            healing_bonus = 3
        elif synergy_score >= 20:  # Basic synergy
            synergy_tier = 1
            combat_bonus = 2
            damage_reduction = 2
            convergence_bonus = 2
            healing_bonus = 1
        else:  # Poor synergy
            synergy_tier = 0
            combat_bonus = 0
            damage_reduction = 0
            convergence_bonus = 0
            healing_bonus = 0
        
        # Apply leadership bonus if applicable
        for char in team.characters:
            if hasattr(char, 'leadership_bonuses') and char.leadership_bonuses:
                synergy_boost = char.leadership_bonuses.get("synergy_boost", 0)
                combat_bonus += combat_bonus * synergy_boost
                damage_reduction += damage_reduction * synergy_boost
                convergence_bonus += convergence_bonus * synergy_boost
                healing_bonus += healing_bonus * synergy_boost
        
        # Store team synergy info
        team_synergy = {
            "score": synergy_score,
            "tier": synergy_tier,
            "combat_bonus": combat_bonus,
            "damage_reduction": damage_reduction,
            "convergence_bonus": convergence_bonus,
            "healing_bonus": healing_bonus
        }
        
        # Apply to all team members
        for character in team.characters:
            character.team_synergy = team_synergy
            
            # Increment games with team counter
            character.games_with_team += 1
        
        return team
    
    def get_special_ability_effect(self, character: Character, situation: str) -> Dict[str, Any]:
        """Get effect from team special ability for a specific situation"""
        if not hasattr(character, 'team_affiliation_bonuses') or not character.team_affiliation_bonuses:
            return {}
            
        special_ability = character.team_affiliation_bonuses.get("special_ability")
        
        if not special_ability:
            return {}
            
        effect = {}
        
        # Avengers get stronger when backed into a corner
        if special_ability == "avengers_assemble" and situation == "critical_health" and character.hp < 30:
            effect = {
                "combat_bonus": 15,
                "message": "Avengers Assemble! Combat bonus activated due to critical health."
            }
            
        # X-Men work better in larger teams
        elif special_ability == "teamwork" and situation == "team_size" and character.team_id:
            # Would need to check team size here
            effect = {
                "combat_bonus": 10,
                "message": "X-Men Teamwork! Combat bonus activated due to large team size."
            }
            
        # Fantastic Four rally when a member is in danger
        elif special_ability == "family_bond" and situation == "teammate_danger":
            effect = {
                "combat_bonus": 15,
                "recovery_boost": 10,
                "message": "Family Bond! Bonus activated to help endangered teammate."
            }
            
        # Add other special abilities as needed
            
        return effect

###############################
