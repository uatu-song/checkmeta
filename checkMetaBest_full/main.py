
# main.py

from systems.simulator import Simulator
from utils.data_loader import load_teams

def main():
    teams = load_teams("data/teams.xlsx")
    sim = Simulator()
    sim.run_season(teams)

if __name__ == "__main__":
    main()
