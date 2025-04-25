"""
Character model for META League Simulator
"""

from typing import Dict, List, Any, Optional
from ..utils.helpers import get_division_from_role

class Character:
    """Character model representing a superhero in the META League"""
    
    def __init__(self, character_data: Dict = None):
        """Initialize a character from dictionary data"""
        if character_data is None:
            character_data = {}
            
        self.id = character_data.get('id', None)
        self.name = character_data.get('name', 'Unknown')
        self.team_id = character_data.get('team_id', None)
        self.team_name = character_data.get('team_name', None)
        self.role = character_data.get('role', 'FL')
        self.division = character_data.get('division', get_division_from_role(self.role))
        
        # Stats
        self.hp = character_data.get('HP', 100)
        self.stamina = character_data.get('stamina', 100)
        self.life = character_data.get('life', 100)
        self.morale = character_data.get('morale', 50)
        
        # Attributes
        self.attributes = {}
        for stat in ['STR', 'SPD', 'FS', 'LDR', 'DUR', 'RES', 'WIL', 'OP', 'AM', 'SBY', 'INT', 'LCK', 'ESP', 'EP']:
            attr_key = f'a{stat}'
            self.attributes[attr_key] = character_data.get(attr_key, 5)
        
        # Traits
        self.traits = character_data.get('traits', [])
        self.custom_traits = character_data.get('custom_traits', [])
        
        # Game state
        self.is_ko = character_data.get('is_ko', False)
        self.is_dead = character_data.get('is_dead', False)
        self.is_leader = character_data.get('is_leader', False)
        
        # Stats tracking
        self.r_stats = character_data.get('rStats', {})
        self.xp_total = character_data.get('xp_total', 0)
        self.xp_earned = character_data.get('xp_earned', 0)
        self.games_with_team = character_data.get('games_with_team', 0)
        
        # Modifiers
        self.morale_modifiers = {}
        self.team_synergy = {}
        self.leadership_bonuses = {}
    
    def get_attribute(self, attr_name: str) -> float:
        """Get an attribute value with proper key formatting"""
        # Handle both aSTR and STR format
        if not attr_name.startswith('a'):
            attr_name = f'a{attr_name}'
            
        return self.attributes.get(attr_name, 5)
    
    def set_attribute(self, attr_name: str, value: float) -> None:
        """Set an attribute value with proper key formatting"""
        # Handle both aSTR and STR format
        if not attr_name.startswith('a'):
            attr_name = f'a{attr_name}'
            
        self.attributes[attr_name] = value
    
    def take_damage(self, damage: float, damage_reduction: float = 0) -> Dict[str, Any]:
        """Apply damage to the character"""
        result = {
            "original_damage": damage,
            "reduced_damage": 0,
            "hp_damage": 0,
            "stamina_damage": 0,
            "life_damage": 0,
            "hp_before": self.hp,
            "stamina_before": self.stamina,
            "life_before": self.life
        }
        
        # Apply damage reduction
        reduction = damage_reduction
        
        # Apply DUR/RES stat bonuses
        dur_bonus = (self.get_attribute('DUR') - 5) * 10  # 10% per point
        res_bonus = (self.get_attribute('RES') - 5) * 8   # 8% per point
        
        # Base reduction for all characters
        base_reduction = 30
        total_reduction = min(85, max(0, reduction + dur_bonus + res_bonus + base_reduction))
        
        actual_damage = max(1, damage * (1 - total_reduction/100.0))
        result["reduced_damage"] = actual_damage
        
        # Apply to HP first
        current_hp = self.hp
        new_hp = max(0, current_hp - actual_damage)
        self.hp = new_hp
        result["hp_damage"] = current_hp - new_hp
        
        # Overflow to stamina if HP is depleted
        stamina_damage = 0
        if new_hp == 0:
            # Reduced stamina damage
            stamina_damage = (actual_damage - current_hp) * 0.4
            
            current_stamina = self.stamina
            new_stamina = max(0, current_stamina - stamina_damage)
            self.stamina = new_stamina
            result["stamina_damage"] = current_stamina - new_stamina
            
            # Overflow to life with higher threshold
            if new_stamina == 0:
                life_threshold = 100
                if stamina_damage > current_stamina + life_threshold:
                    life_damage = 0.5  # Fractional life loss
                    self.life = max(0, self.life - life_damage)
                    result["life_damage"] = life_damage
        
        # Update character state
        if self.hp <= 0 and self.stamina <= 0:
            if self.life <= 0:
                self.is_dead = True
            else:
                self.is_ko = True
        
        result["hp_after"] = self.hp
        result["stamina_after"] = self.stamina
        result["life_after"] = self.life
        result["is_ko"] = self.is_ko
        result["is_dead"] = self.is_dead
        
        return result
    
    def recover(self, base_hp_regen: float = 5, base_stamina_regen: float = 5, trait_heal: float = 0) -> Dict[str, Any]:
        """Apply end of round recovery effects"""
        result = {
            "hp_before": self.hp,
            "stamina_before": self.stamina,
            "hp_regen": 0,
            "stamina_regen": 0,
            "recovered_from_ko": False
        }
        
        # Skip dead characters
        if self.is_dead:
            return result
            
        # Calculate HP regeneration
        total_heal = base_hp_regen + trait_heal
        
        # Apply morale modifier to healing
        if hasattr(self, 'morale_modifiers') and self.morale_modifiers:
            heal_modifier = self.morale_modifiers.get('healing_modifier', 1.0)
            total_heal *= heal_modifier
            
        # Apply team synergy to healing
        if hasattr(self, 'team_synergy') and self.team_synergy:
            synergy_heal = self.team_synergy.get('healing_bonus', 0)
            total_heal += synergy_heal
            
        # Only heal if not at full HP
        if self.hp < 100:
            old_hp = self.hp
            self.hp = min(100, old_hp + total_heal)
            result["hp_regen"] = self.hp - old_hp
            
        # Calculate stamina regeneration
        wil_bonus = max(0, self.get_attribute('WIL') - 5)
        wil_regen = wil_bonus * 0.8
        
        regen_rate = base_stamina_regen + wil_regen
        
        # Apply morale modifier to stamina regen
        if hasattr(self, 'morale_modifiers') and self.morale_modifiers:
            stamina_modifier = self.morale_modifiers.get('stamina_regen', 1.0)
            regen_rate *= stamina_modifier
            
        # Faster recovery from KO
        if self.is_ko:
            regen_rate *= 3
            
            # Chance to recover from KO
            stamina = self.stamina
            if stamina > 20:
                recovery_chance = stamina / 150
                import random
                if random.random() < recovery_chance:
                    self.is_ko = False
                    self.hp = max(20, self.hp)
                    result["recovered_from_ko"] = True
        
        # Apply stamina regeneration
        old_stamina = self.stamina
        self.stamina = min(100, old_stamina + regen_rate)
        result["stamina_regen"] = self.stamina - old_stamina
        
        return result
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert character to dictionary for storage/serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'team_id': self.team_id,
            'team_name': self.team_name,
            'role': self.role,
            'division': self.division,
            'HP': self.hp,
            'stamina': self.stamina,
            'life': self.life,
            'morale': self.morale,
            'traits': self.traits,
            **self.attributes,
            'rStats': self.r_stats,
            'xp_total': self.xp_total,
            'xp_earned': self.xp_earned,
            'is_ko': self.is_ko,
            'is_dead': self.is_dead,
            'is_leader': self.is_leader,
            'games_with_team': self.games_with_team
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Character':
        """Create a Character instance from a dictionary"""
        return cls(data)

    def recover(self, base_hp_regen: float = 3, base_stamina_regen: float = 2, trait_heal: float = 0) -> Dict[str, Any]:
    """Apply end of round recovery effects with slower stamina regen"""
    result = {
        "hp_before": self.hp,
        "stamina_before": self.stamina,
        "hp_regen": 0,
        "stamina_regen": 0,
        "recovered_from_ko": False
    }
    
    # Skip dead characters
    if self.is_dead:
        return result
        
    # Calculate HP regeneration
    total_heal = base_hp_regen + trait_heal  # Reduced base_hp_regen to 3 (from 5)
    
    # Apply morale modifier to healing
    if hasattr(self, 'morale_modifiers') and self.morale_modifiers:
        heal_modifier = self.morale_modifiers.get('healing_modifier', 1.0)
        total_heal *= heal_modifier
        
    # Apply team synergy to healing
    if hasattr(self, 'team_synergy') and self.team_synergy:
        synergy_heal = self.team_synergy.get('healing_bonus', 0)
        total_heal += synergy_heal
        
    # Only heal if not at full HP
    if self.hp < 100:
        old_hp = self.hp
        self.hp = min(100, old_hp + total_heal)
        result["hp_regen"] = self.hp - old_hp
        
    # BALANCE: Slower stamina regeneration
    # Reduced base_stamina_regen from 5 to 2
    
    # Apply WIL bonus to stamina regen, but more limited
    wil_bonus = max(0, self.get_attribute('WIL') - 5)
    wil_regen = wil_bonus * 0.5  # Reduced from 0.8 to 0.5
    
    regen_rate = base_stamina_regen + wil_regen
    
    # Knocked out characters no longer recover - they stay knocked out
    if self.is_ko:
        # No recovery for knocked out characters
        return result
    
    # Apply stamina regeneration
    old_stamina = self.stamina
    self.stamina = min(100, old_stamina + regen_rate)
    result["stamina_regen"] = self.stamina - old_stamina
    
    return result


###############################
