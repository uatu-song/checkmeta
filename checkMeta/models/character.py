"""
META Fantasy League Simulator - Character Model
Defines the Character class for representing in-game characters
"""

class Character:
    """Model representing a character in the META Fantasy League"""
    
    def __init__(self, data=None):
        """Initialize a character from a data dictionary
        
        Args:
            data (dict, optional): Dictionary containing character data. Defaults to None.
        """
        # Basic information
        self.id = data.get('id', '') if data else ''
        self.name = data.get('name', 'Unknown') if data else 'Unknown'
        self.team_id = data.get('team_id', '') if data else ''
        self.team_name = data.get('team_name', '') if data else ''
        self.role = data.get('role', 'FL') if data else 'FL'
        self.division = data.get('division', 'o') if data else 'o'
        
        # Status
        self.HP = data.get('HP', 100) if data else 100
        self.stamina = data.get('stamina', 100) if data else 100
        self.life = data.get('life', 100) if data else 100
        self.morale = data.get('morale', 50) if data else 50
        self.is_ko = data.get('is_ko', False) if data else False
        self.is_dead = data.get('is_dead', False) if data else False
        
        # Traits
        self.traits = data.get('traits', []) if data else []
        
        # Stats (copy all stats starting with 'a')
        self.stats = {}
        if data:
            for key, value in data.items():
                if key.startswith('a'):
                    setattr(self, key, value)
                    self.stats[key] = value
        
        # Result stats
        self.rStats = data.get('rStats', {}) if data else {}
        self.xp_total = data.get('xp_total', 0) if data else 0
        self.xp_earned = 0
        
        # Runtime modifiers
        self.morale_modifiers = {}
        self.leadership_modifiers = {}
        self.synergy_modifiers = {}
        self.trait_activation_bonus = 0
    
    def to_dict(self):
        """Convert character to dictionary for serialization
        
        Returns:
            dict: Dictionary representation of the character
        """
        data = {
            'id': self.id,
            'name': self.name,
            'team_id': self.team_id,
            'team_name': self.team_name,
            'role': self.role,
            'division': self.division,
            'HP': self.HP,
            'stamina': self.stamina,
            'life': self.life,
            'morale': self.morale,
            'is_ko': self.is_ko,
            'is_dead': self.is_dead,
            'traits': self.traits,
            'rStats': self.rStats,
            'xp_total': self.xp_total,
            'xp_earned': self.xp_earned
        }
        
        # Add stats
        for key, value in self.stats.items():
            data[key] = value
        
        return data
    
    def is_active(self):
        """Check if the character is active (not KO'd or dead)
        
        Returns:
            bool: True if active, False otherwise
        """
        return not (self.is_ko or self.is_dead)
    
    def get_stat(self, stat_name, default=5):
        """Get a character stat with fallback
        
        Args:
            stat_name (str): Stat name (without 'a' prefix)
            default (int, optional): Default value. Defaults to 5.
        
        Returns:
            float: Stat value
        """
        key = f"a{stat_name}"
        
        # First try the attribute
        if hasattr(self, key):
            return getattr(self, key)
        
        # Then try the stats dictionary
        return self.stats.get(key, default)
    
    def take_damage(self, damage):
        """Apply damage to the character
        
        Args:
            damage (float): Amount of damage to take
        
        Returns:
            dict: Effects of the damage
        """
        old_hp = self.HP
        old_stamina = self.stamina
        old_life = self.life
        
        # Apply to HP first
        self.HP = max(0, self.HP - damage)
        hp_damage = old_hp - self.HP
        remaining_damage = damage - hp_damage
        
        stamina_damage = 0
        life_damage = 0
        
        # Overflow to stamina if HP is depleted
        if self.HP == 0 and remaining_damage > 0:
            self.stamina = max(0, self.stamina - remaining_damage * 0.4)
            stamina_damage = old_stamina - self.stamina
            remaining_damage = remaining_damage - (stamina_damage / 0.4)
            
            # Overflow to life with threshold
            if self.stamina == 0 and remaining_damage > 0:
                life_threshold = 100
                if remaining_damage > life_threshold:
                    self.life = max(0, self.life - 0.5)
                    life_damage = old_life - self.life
        
        # Update KO/dead status
        if self.HP <= 0 and self.stamina <= 0:
            self.is_ko = True
            
            if self.life <= 0:
                self.is_dead = True
        
        return {
            'hp_damage': hp_damage,
            'stamina_damage': stamina_damage,
            'life_damage': life_damage,
            'is_ko': self.is_ko,
            'is_dead': self.is_dead
        }