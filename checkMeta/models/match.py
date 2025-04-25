"""
Match results model for META League Simulator
"""

from typing import Dict, List, Any
from .team import Team

class MatchResult:
    """Match result model for META League Simulator"""
    
    def __init__(self, team_a: Team, team_b: Team, day: int = 1):
        """Initialize match result with teams"""
        self.day = day
        self.team_a_id = team_a.team_id
        self.team_b_id = team_b.team_id
        self.team_a_name = team_a.team_name
        self.team_b_name = team_b.team_name
        self.team_a_wins = 0
        self.team_b_wins = 0
        self.winner = None
        self.winning_team = None
        self.character_results = []
        self.convergence_logs = []
        self.trait_logs = []
    
    def add_character_result(self, character, team: str, result: str, was_active: bool = True) -> None:
        """Add a character result to the match"""
        self.character_results.append({
            "team": team,
            "character_id": character.id,
            "character_name": character.name,
            "result": result,
            "final_hp": character.hp,
            "final_stamina": character.stamina,
            "final_life": character.life,
            "is_ko": character.is_ko,
            "is_dead": character.is_dead,
            "was_active": was_active
        })
        
        # Update win counters
        if result == "win":
            if team == "A":
                self.team_a_wins += 1
            elif team == "B":
                self.team_b_wins += 1
    
    def add_convergence_log(self, log_entry: Dict[str, Any]) -> None:
        """Add a convergence log entry"""
        self.convergence_logs.append(log_entry)
    
    def add_trait_log(self, log_entry: Dict[str, Any]) -> None:
        """Add a trait activation log entry"""
        self.trait_logs.append(log_entry)
    
    def finalize(self) -> None:
        """Determine match winner"""
        if self.team_a_wins > self.team_b_wins:
            self.winner = "Team A"
            self.winning_team = self.team_a_name
        elif self.team_b_wins > self.team_a_wins:
            self.winner = "Team B"
            self.winning_team = self.team_b_name
        else:
            self.winner = "Draw"
            self.winning_team = "None"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert match result to dictionary for serialization"""
        return {
            "team_a_name": self.team_a_name,
            "team_b_name": self.team_b_name,
            "team_a_wins": self.team_a_wins,
            "team_b_wins": self.team_b_wins,
            "winner": self.winner,
            "winning_team": self.winning_team,
            "character_results": self.character_results,
            "convergence_count": len(self.convergence_logs),
            "trait_activations": len(self.trait_logs),
            "convergence_logs": self.convergence_logs,
            "trait_logs": self.trait_logs
        }

###############################
