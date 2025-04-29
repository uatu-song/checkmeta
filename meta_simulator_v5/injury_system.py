#!/usr/bin/env python3
import os
import fileinput
import sys

# First, fix the file name
old_path = "data/SimEngine v3 - Divisions.csv"
new_path = "data/SimEngine v3  Divisions.csv"
if os.path.exists(old_path) and not os.path.exists(new_path):
    os.rename(old_path, new_path)
    print(f"Renamed file: {old_path} → {new_path}")

# Now let's fix the DataLoader._process_lineup_data method
simulator_path = "meta_simulator_v4_1.py"

# Find the line right before we return teams
line_to_find = "        self.logger.info(f\"Processed {sum(len(chars) for chars in teams.values())} characters across {len(teams)} teams\")"
new_code = """
        # STRICT ENFORCEMENT: Trim active characters to exactly 8 per team
        teams_per_match = self.config.get("simulation.teams_per_match")
        for team_id, chars in teams.items():
            active_chars = [c for c in chars if c.get("is_active", True)]
            if len(active_chars) > teams_per_match:
                # Mark excess characters as inactive
                active_count = 0
                for char in chars:
                    if char.get("is_active", True):
                        if active_count >= teams_per_match:
                            char["is_active"] = False
                        active_count += 1
                self.logger.info(f"Team {team_id} trimmed from {len(active_chars)} to {teams_per_match} active characters")
"""

found = False
with fileinput.FileInput(simulator_path, inplace=True) as file:
    for line in file:
        print(line, end='')
        if line.strip() == line_to_find.strip():
            found = True
            print(new_code)

if found:
    print("Successfully patched the file to enforce 8v8 teams")
else:
    print("Could not find the target line to patch. Manual intervention required.")