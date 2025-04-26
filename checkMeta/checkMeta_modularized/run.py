# run.py
from simulator.meta_league_simulator import MetaLeagueSimulator

if __name__ == "__main__":
    simulator = MetaLeagueSimulator(stockfish_path=None)
    lineups_file = "path_to_your_lineups.xlsx"
    simulator.run_matchday(lineups_file)
