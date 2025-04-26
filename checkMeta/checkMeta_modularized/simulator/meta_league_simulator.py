# simulator/meta_league_simulator.py
from systems.traits import load_traits
from systems.chess_engine import apply_opening_moves, select_move
from systems.morale import adjust_morale
from systems.experience import award_xp
from systems.convergence import detect_convergences
from utils.data_loader import load_teams
from utils.match_helpers import calculate_material
import chess
import random
import json

class MetaLeagueSimulator:
    def __init__(self, stockfish_path=None):
        self.stockfish_path = stockfish_path
        self.stockfish_available = bool(stockfish_path)
        self.current_day = 1
        self.role_openings = {}
        self.traits = load_traits()

    def simulate_match(self, team_a, team_b, show_details=True):
        boards = {}
        for unit in team_a + team_b:
            board = chess.Board()
            role = unit["role"]
            opening_moves = self.role_openings.get(role, ["e4"])
            apply_opening_moves(board, opening_moves)
            boards[unit["id"]] = board

        for _ in range(20):
            movers = random.choice([team_a + team_b, team_b + team_a])
            for mover in movers:
                board = boards[mover["id"]]
                if board.is_game_over():
                    continue
                move = select_move(board, mover, self.stockfish_path)
                if move:
                    board.push(move)

        result = self._calculate_match_result(team_a, team_b, boards)
        return result

    def _calculate_match_result(self, team_a, team_b, boards):
        result = {}
        for unit in team_a + team_b:
            board = boards[unit["id"]]
            material = calculate_material(board)
            result[unit["id"]] = {
                "final_material": material,
                "is_ko": False,
                "is_dead": False
            }
        return result

    def run_matchday(self, lineups_path):
        teams = load_teams(lineups_path)
        schedule = self._generate_matchups()
        all_results = {}

        for match in schedule:
            team_a, team_b = teams[match[0]], teams[match[1]]
            match_result = self.simulate_match(team_a, team_b)
            all_results[f"{match[0]}_vs_{match[1]}"] = match_result

        with open(f"day_{self.current_day}_results.json", "w") as f:
            json.dump(all_results, f, indent=2)

    def _generate_matchups(self):
        return [("T001", "T002"), ("T003", "T004"), ("T005", "T006"), ("T007", "T008"), ("T009", "T010")]
