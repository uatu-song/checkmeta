from models.character import Character
from models.team import Team
from systems.traits import TraitSystem
from systems.morale import MoraleSystem
from systems.leadership import LeadershipSystem
from systems.synergy import SynergySystem
from simulation.combat import CombatSystem
from simulation.convergence import ConvergenceSystem
from data.loaders import load_lineups_from_excel

class MetaLeagueSimulator:
    """Main simulator class integrating all systems"""
    
    def __init__(self, stockfish_path="/usr/local/bin/stockfish"):
        """Initialize the simulator and all subsystems"""
        # Game state
        self.current_day = 1
        
        # Initialize subsystems
        self.trait_system = TraitSystem()
        self.morale_system = MoraleSystem()
        self.leadership_system = LeadershipSystem()
        self.synergy_system = SynergySystem()
        self.combat_system = CombatSystem(stockfish_path)
        self.convergence_system = ConvergenceSystem(self.trait_system)
        
        # Create results directory
        os.makedirs("results", exist_ok=True)
    
    def simulate_match(self, team_a, team_b, show_details=True):
        """Simulate a match between two teams"""
        # Convert dict data to Character objects
        team_a_characters = [Character(char_data) for char_data in team_a]
        team_b_characters = [Character(char_data) for char_data in team_b]
        
        # Create Team objects
        team_a_obj = Team(team_a_characters)
        team_b_obj = Team(team_b_characters)
        
        # Apply leadership bonuses
        self.leadership_system.apply_leadership_bonuses(team_a_obj)
        self.leadership_system.apply_leadership_bonuses(team_b_obj)
        
        # Calculate team synergy
        self.synergy_system.calculate_team_synergy(team_a_obj)
        self.synergy_system.calculate_team_synergy(team_b_obj)
        
        # Apply morale effects
        for character in team_a_obj.active_characters + team_b_obj.active_characters:
            character.morale_modifiers = self.morale_system.calculate_morale_modifiers(character.morale)
        
        # Simulation logic would go here, calling the appropriate systems
        # ...
        
        # Convert results back to dictionaries for output
        results = {
            # Match results
        }
        
        return results