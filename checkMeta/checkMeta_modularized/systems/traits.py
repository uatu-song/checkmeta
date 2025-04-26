# systems/traits.py

def load_traits():
    return {
        "genius": {"name": "Genius", "type": "combat", "triggers": ["convergence", "critical_hit"], "formula_key": "bonus_roll", "value": 15},
        "armor": {"name": "Armor", "type": "defense", "triggers": ["damage_taken"], "formula_key": "damage_reduction", "value": 0.25},
        "tactical": {"name": "Tactical", "type": "combat", "triggers": ["convergence", "team_boost"], "formula_key": "bonus_roll", "value": 20},
        "shield": {"name": "Shield", "type": "defense", "triggers": ["damage_taken", "convergence"], "formula_key": "damage_reduction", "value": 0.30},
        "agile": {"name": "Agile", "type": "mobility", "triggers": ["convergence", "evasion"], "formula_key": "bonus_roll", "value": 15},
        "spider-sense": {"name": "Spider-Sense", "type": "precognition", "triggers": ["combat", "danger"], "formula_key": "defense_bonus", "value": 20},
        "stretchy": {"name": "Stretchy", "type": "mobility", "triggers": ["convergence", "positioning"], "formula_key": "bonus_roll", "value": 10},
        "healing": {"name": "Healing", "type": "regeneration", "triggers": ["damage_taken", "end_of_turn"], "formula_key": "hp_regen", "value": 5}
    }
