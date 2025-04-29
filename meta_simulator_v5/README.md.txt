META Fantasy League Simulator v5.0
The META Fantasy League Simulator is an advanced system for simulating matches between teams of characters who play chess games that impact their combat capabilities.

Overview
This simulation system combines chess gameplay with combat mechanics to create a unique fantasy league experience. Characters play individual chess games, and their moves impact both the chess board and their combat statistics. Characters can also use special traits, experience stamina fatigue, and interact with each other through convergences.

Core Features
Chess-based Combat: Characters play chess games that determine combat outcomes
8v8 Team Battles: Each team fields exactly 8 players (non-negotiable rule)
Cross-Division Matches: Teams from different divisions must play each other
Trait System: Characters have unique traits that provide special abilities
Stamina Management: Characters experience fatigue that affects performance
Injury System: Characters can be injured and require recovery time
PGN Generation: Records chess games in standard PGN format
Comprehensive Reporting: Detailed match, day, week, and season reports
Data Structure
The simulator requires the following data files in the data directory:

teams.csv: Team information, including division and home court advantage
players.csv: Player stats and attributes
traits.csv: Trait definitions, effects, and cooldowns
divisions.csv: Division properties and bonuses
player_traits.csv: Assignment of traits to players
lineups_day1.csv: Starting lineup for day 1
matchups.csv: Predefined matchups for each day
Non-Negotiable Rules
8v8 Team Lineups: Every team fields exactly 8 players
No Inner Division Matches: Teams from the same division cannot play each other
Alternate Home/Away: Teams alternate home field advantage each day
Independent Chess Matches: Each player plays their own independent game
5 Matches per Day: Exactly 5 matches simulated each day
5 Days per Week: Monday through Friday only
Calendar Anchoring: Day 1 is 4/7/25 (Monday)
Combat Calibration
The v5.0 update includes enhanced combat mechanics:

Base HP: Remains stable at default values
Base Damage: +25% increase (moves are more meaningful)
Stamina Decay: +15% increase (fatigue is a real constraint)
Morale Loss: +10% increase per KO (KO swings have bigger effects)
Convergence Damage: 2x multiplier (convergences are decisive)
Extra Damage at Low Stamina: +20% (exhausted characters are vulnerable)
Morale Collapse: Enabled at Morale < 30% (risk of psychological collapse)
Injury Triggers: Enabled at Stamina < 35% (fatigue causes injuries)
Requirements
Python 3.8+
Required libraries:
pandas
python-chess
matplotlib (for charts)
Setup
Run the setup script to create the necessary directory structure:
python setup_meta_league.py
Ensure all data files are placed in the data directory.
Configure the simulator settings in config.json.
Running the Simulator
Run a single day:

python meta_simulator_v5.py --config config.json --day 1
Run a full week:

python meta_simulator_v5.py --config config.json --week 1
Run a full season:

python meta_simulator_v5.py --config config.json --season
Output
The simulator generates various output files:

PGN Files: Chess game records in standard PGN format (in results/pgn/)
Match Reports: Detailed reports of each match (in results/reports/)
Day/Week/Season Reports: Summary reports (in results/reports/)
Log Files: Detailed logs of the simulation (in logs/)
Backups: Automatic backups at configurable intervals (in backups/)
Credits
META Fantasy League Simulator v5.0 - A comprehensive simulation system for chess-based team combat.

