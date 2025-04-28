# gatekeeper_v2.py

import os
import glob
import chess
import datetime

class Gatekeeper:
    def __init__(self, config, data_loader):
        self.config = config
        self.data_loader = data_loader
        self.errors = []

    def validate_directories(self):
        required_dirs = [
            self.config.DATA_DIR,
            self.config.RESULTS_DIR,
            self.config.LOG_DIR,
            self.config.PGN_DIR,
            self.config.BACKUP_DIR
        ]
        for directory in required_dirs:
            if not os.path.exists(directory):
                self.errors.append(f"Missing required directory: {directory}")

    def validate_stockfish(self):
        if self.config.USE_STOCKFISH:
            if not os.path.exists(self.config.STOCKFISH_PATH):
                self.errors.append("Stockfish engine required but not found at specified path.")

    def validate_team_data(self):
        teams = self.data_loader.load_teams()
        if not teams:
            self.errors.append("No team data loaded. Check /data/lineups or team ID files.")
        for team in teams:
            if len(team.get("players", [])) != 8:
                self.errors.append(f"Team {team['team_id']} does not have exactly 8 players.")

    def validate_division_rules(self):
        divisions = self.data_loader.load_divisions()
        if not divisions:
            self.errors.append("Divisions data missing. Check divisions.csv.")

    def validate_pgn_generation(self):
        today = datetime.datetime.now().strftime("%Y%m%d")
        todays_pgns = glob.glob(os.path.join(self.config.PGN_DIR, f"*{today}*.pgn"))
        if not todays_pgns:
            self.errors.append("No PGN files found for today's matches. PGN generation failed.")

    def validate_naming_conventions(self):
        # Example simple naming rule check for team IDs, filenames, etc.
        allowed_prefixes = ("t0", "overlay", "undercurrent")
        files = os.listdir(self.config.DATA_DIR)
        for file in files:
            if not file.startswith(allowed_prefixes):
                self.errors.append(f"File naming violation detected: {file}")

    def run_all_checks(self):
        self.validate_directories()
        self.validate_stockfish()
        self.validate_team_data()
        self.validate_division_rules()
        self.validate_pgn_generation()
        self.validate_naming_conventions()

        if self.errors:
            print("\n[Gatekeeper V2 BLOCKED Simulation]\n")
            for err in self.errors:
                print(f"- {err}")
            raise Exception("\nGatekeeper V2 detected fatal issues. Simulation cannot continue.")
        else:
            print("\n✅ Gatekeeper V2 Passed: Simulation is safe to proceed!\n")


# Example usage
if __name__ == "__main__":
    from meta_simulator_monolith import CONFIG, DataLoader

    data_loader = DataLoader(CONFIG)
    gatekeeper = Gatekeeper(CONFIG, data_loader)
    gatekeeper.run_all_checks()
