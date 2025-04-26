###############################
# data/loaders.py
###############################
"""
Data loading functions for META League Simulator
"""

import os
import pandas as pd
import random
import json
from typing import Dict, List, Any, Optional
from models.character import Character
from models.team import Team
from utils.helpers import map_position_to_role, get_division_from_role
from systems.traits import TraitSystem

def load_traits(filename=None, use_csv=True):
    """Load trait definitions
    
    Args:
        filename (str, optional): Name of the file to load. Defaults to None.
        use_csv (bool, optional): Whether to use CSV or JSON. Defaults to True.
    
    Returns:
        dict: Dictionary of trait definitions
    """
    # Default filenames
    csv_filename = "SimEngine v2 - full_trait_catalog_export.csv"
    json_filename = "traits.json"
    
    # Default paths
    traits_dir = os.path.join("data", "traits")
    
    # If filename is explicitly provided, use that
    if filename:
        if filename.endswith('.csv'):
            return load_traits_from_csv(filename)
        elif filename.endswith('.json'):
            filepath = os.path.join(traits_dir, filename)
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    return json.load(f)
            else:
                print(f"Traits file not found: {filepath}")
                return {}
    
    # Otherwise use the preferred format
    if use_csv:
        return load_traits_from_csv(csv_filename)
    else:
        # Try to load JSON
        filepath = os.path.join(traits_dir, json_filename)
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)
        else:
            print(f"Traits file not found: {filepath}")
            return {}

def load_traits_from_csv(filename="SimEngine v2 - full_trait_catalog_export.csv"):
    """Load traits from a CSV file
    
    Args:
        filename (str): Name of the CSV file
    
    Returns:
        dict: Dictionary of traits by trait_id
    """
    traits_dir = os.path.join("data", "traits")
    filepath = os.path.join(traits_dir, filename)
    
    try:
        if not os.path.exists(filepath):
            print(f"Traits CSV not found at {filepath}")
            return {}
        
        # Load the CSV file
        df = pd.read_csv(filepath)
        
        # Print column names for debugging
        print(f"Columns in traits file: {df.columns.tolist()}")
        
        # Create traits dictionary
        traits = {}
        
        for _, row in df.iterrows():
            trait_id = row.get('trait_id', f"trait_{len(traits)}")
            
            # Handle triggers (may be a comma-separated string)
            triggers = []
            if 'triggers' in df.columns:
                trigger_str = row.get('triggers', '')
                if isinstance(trigger_str, str):
                    triggers = [t.strip() for t in trigger_str.split(',')]
            
            # Create trait dictionary
            trait = {
                'name': row.get('name', f"Trait {trait_id}"),
                'type': row.get('type', 'unknown'),
                'triggers': triggers,
                'formula_key': row.get('formula_key', ''),
                'formula_expr': row.get('formula_expr', ''),
                'value': row.get('stamina_cost', 0),  # Use stamina_cost as value for compatibility
                'cooldown': row.get('cooldown', ''),
                'description': row.get('description', ''),
                'bound_nbid': row.get('bound_nbid', '')
            }
            
            # Add to traits dictionary
            traits[trait_id] = trait
        
        print(f"Loaded {len(traits)} traits from CSV")
        return traits
        
    except Exception as e:
        print(f"Error loading traits from CSV: {e}")
        return {}

def load_team_ids(filename="SimEngine v3 - teamIDs (1).csv"):
    """Load team IDs and roster information
    
    Args:
        filename (str): Name of the CSV file
    
    Returns:
        dict: Dictionary of team information
    """
    teams_dir = os.path.join("data", "teams")
    filepath = os.path.join(teams_dir, filename)
    
    try:
        if not os.path.exists(filepath):
            print(f"Team IDs file not found at {filepath}")
            return {}
        
        # Load the CSV file
        df = pd.read_csv(filepath)
        
        # Print column names for debugging
        print(f"Columns in team IDs file: {df.columns.tolist()}")
        
        # Create teams dictionary
        teams_info = {}
        
        for _, row in df.iterrows():
            team_id = str(row.get('team_ids', ''))
            
            # Skip if team_id is empty
            if not team_id or pd.isna(team_id):
                continue
                
            # Ensure team_id starts with 't'
            if not team_id.startswith('t'):
                team_id = f"t{team_id}"
            
            # Get roster and bench information
            deploy_roster = row.get('deployRoster', '')
            bench = row.get('Bench', '')
            
            # Process deploy roster (may be comma-separated list)
            active_roster = []
            if isinstance(deploy_roster, str) and deploy_roster.strip():
                active_roster = [name.strip() for name in deploy_roster.split(',')]
            
            # Process bench (may be comma-separated list)
            bench_roster = []
            if isinstance(bench, str) and bench.strip():
                bench_roster = [name.strip() for name in bench.split(',')]
            
            # Create team info dictionary
            teams_info[team_id] = {
                'team_id': team_id,
                'team_name': row.get('teamName', f"Team {team_id}"),
                'active_roster': active_roster,
                'bench_roster': bench_roster
            }
        
        print(f"Loaded information for {len(teams_info)} teams")
        return teams_info
        
    except Exception as e:
        print(f"Error loading team IDs: {e}")
        return {}

def load_divisions_from_csv(filename="SimEngine v3 - Divisions.csv"):
    """Load division information from CSV
    
    Args:
        filename (str): Name of the CSV file
    
    Returns:
        dict: Dictionary of division information
    """
    divisions_dir = os.path.join("data", "divisions")
    filepath = os.path.join(divisions_dir, filename)
    
    try:
        if not os.path.exists(filepath):
            print(f"Divisions CSV not found at {filepath}")
            return {}
        
        # Load the CSV file
        df = pd.read_csv(filepath)
        
        # Print column names for debugging
        print(f"Columns in divisions file: {df.columns.tolist()}")
        
        # Create divisions dictionary based on available columns
        divisions_info = {
            "divisions": {},
            "teams": {}
        }
        
        # Process each row in the CSV
        for _, row in df.iterrows():
            # Extract available information based on column names
            # (This will need to be adjusted based on the actual CSV structure)
            if 'division_id' in df.columns:
                div_id = row.get('division_id', '')
                div_name = row.get('division_name', f"Division {div_id}")
                
                divisions_info["divisions"][div_id] = {
                    "name": div_name,
                    "teams": []
                }
            
            # If the CSV contains team-to-division mappings
            if 'team_id' in df.columns and 'division_id' in df.columns:
                team_id = row.get('team_id', '')
                div_id = row.get('division_id', '')
                
                if team_id and div_id:
                    divisions_info["teams"][team_id] = div_id
                    
                    if div_id in divisions_info["divisions"]:
                        if "teams" not in divisions_info["divisions"][div_id]:
                            divisions_info["divisions"][div_id]["teams"] = []
                        
                        divisions_info["divisions"][div_id]["teams"].append(team_id)
        
        print(f"Loaded division information from CSV")
        return divisions_info
        
    except Exception as e:
        print(f"Error loading divisions from CSV: {e}")
        return {}

def load_attributes(filename="Attribute Stats.csv"):
    """Load character attributes from CSV file
    
    Args:
        filename (str): Name of the CSV file
    
    Returns:
        dict: Dictionary of character attributes by name
    """
    # Use the main data directory directly
    filepath = os.path.join("data", filename)
    
    try:
        if not os.path.exists(filepath):
            print(f"Attributes CSV not found at {filepath}")
            return {}
        
        print(f"Found attributes file at: {filepath}")
        
        # Load the CSV file
        df = pd.read_csv(filepath)
        
        # Print column names for debugging
        print(f"Columns in attributes file: {df.columns.tolist()}")
        
        # Find character name column
        name_columns = ['Friendly Name', 'Name', 'Character Name', 'Character']
        name_column = None
        for col in name_columns:
            if col in df.columns:
                name_column = col
                break
        
        if not name_column:
            print("Could not find character name column in attributes file!")
            return {}
        
        # Mapping of potential column names to stat keys
        stat_mapping = {
            'INT': ['INT', 'Intelligence'],
            'STR': ['STR', 'Strength'],
            'SPD': ['SPD', 'Speed'],
            'DUR': ['DUR', 'Durability'],
            'EP': ['EP', 'Energy Potential'],
            'FS': ['FS', 'Focus/Speed'],
            'LDR': ['LDR', 'Leadership'],
            'RES': ['RES', 'Resistance'],
            'WIL': ['WIL', 'Willpower'],
            'LCK': ['LCK', 'Luck'],
            'ESP': ['ESP', 'Extrasensory Perception'],
            'OP': ['OP', 'Operations Potential'],
            'AM': ['AM', 'Adaptive Mastery'],
            'SBY': ['SBY', 'Situational Awareness']
        }
        
        # Find column names for each stat
        stat_columns = {}
        for stat, possible_names in stat_mapping.items():
            for name in possible_names:
                if name in df.columns:
                    stat_columns[stat] = name
                    break
        
        # Create attribute dictionary
        attribute_stats = {}
        for _, row in df.iterrows():
            char_name = str(row[name_column]).strip()
            
            # Create attribute dictionary with default fallback
            char_attrs = {}
            for stat, col in stat_columns.items():
                value = row.get(col, 5)
                # Ensure it's a number, default to 5 if not
                try:
                    char_attrs[f'a{stat}'] = float(value)
                except (ValueError, TypeError):
                    char_attrs[f'a{stat}'] = 5
            
            attribute_stats[char_name] = char_attrs
        
        print(f"Loaded attributes for {len(attribute_stats)} characters")
        
        return attribute_stats
            
    except Exception as e:
        print(f"Error loading attributes from CSV: {e}")
        return {}

def apply_attributes_to_teams(teams, attribute_stats=None):
    """Apply attribute stats to teams
    
    Args:
        teams (dict): Dictionary of teams
        attribute_stats (dict, optional): Dictionary of attribute stats. Defaults to None.
    
    Returns:
        dict: Updated teams dictionary
    """
    if attribute_stats is None:
        attribute_stats = load_attributes()
    
    if not attribute_stats:
        print("No attribute stats available to apply")
        return teams
    
    for team_id, team_chars in teams.items():
        for i, character in enumerate(team_chars):
            # Get character name
            if isinstance(character, Character):
                char_name = character.name
            else:
                char_name = character.get('name', '')
            
            # Try to find matching attributes
            char_attrs = attribute_stats.get(char_name, {})
            
            if not char_attrs:
                continue
            
            # Update attributes
            if isinstance(character, Character):
                # For Character objects
                for stat, value in char_attrs.items():
                    setattr(character, stat, value)
                    character.stats[stat] = value
            else:
                # For dictionary data
                for stat, value in char_attrs.items():
                    character[stat] = value
    
    return teams

def load_complete_teams(lineup_file="All Lineups (1).xlsx", 
                       day_sheet="4/7/25",
                       attribute_file="Attribute Stats.csv"):
    """Load teams with all data integrated
    
    Args:
        lineup_file (str): Name of the lineup Excel file
        day_sheet (str): Name of the sheet in the Excel file
        attribute_file (str): Name of the attributes CSV file
    
    Returns:
        dict: Dictionary of teams with all data integrated
    """
    # Create file paths
    lineups_dir = os.path.join("data", "lineups")
    lineup_path = os.path.join(lineups_dir, lineup_file)
    
    # Load base teams from lineup file
    teams = load_lineups_from_excel(lineup_path, day_sheet)
    
    # Load attributes
    attribute_stats = load_attributes(attribute_file)
    
    # Apply attributes to teams
    teams = apply_attributes_to_teams(teams, attribute_stats)
    
    return teams

def load_lineups_from_excel(file_path: str, day_sheet: str = "4/7/25") -> Dict[str, List[Character]]:
    """Load character lineups from an Excel file"""
    try:
        print(f"Attempting to load from: {file_path}")
        
        # First check if file exists
        if not os.path.exists(file_path):
            print(f"Error: File '{file_path}' does not exist")
            raise FileNotFoundError(f"File '{file_path}' does not exist")
        
        # Get all sheet names to debug
        xls = pd.ExcelFile(file_path)
        available_sheets = xls.sheet_names
        print(f"Available sheets in Excel file: {available_sheets}")
        
        # Try to find a matching sheet
        # Convert date format for more flexible matching
        day_sheet_clean = day_sheet.replace('/', '')
        matching_sheets = [s for s in available_sheets if day_sheet_clean in s.replace('/', '').replace('-', '')]
        selected_sheet = None
        
        if day_sheet in available_sheets:
            selected_sheet = day_sheet
            print(f"Found exact match for sheet: {day_sheet}")
        elif matching_sheets:
            selected_sheet = matching_sheets[0]
            print(f"Found partial match for sheet: {selected_sheet}")
        else:
            # Fall back to first sheet
            selected_sheet = available_sheets[0]
            print(f"No matching sheet found. Using first sheet: {selected_sheet}")
        
        # Load the selected sheet
        print(f"Loading data from sheet: {selected_sheet}")
        df = pd.read_excel(file_path, sheet_name=selected_sheet)
        
        # Print column names for debugging
        print(f"Columns in sheet: {df.columns.tolist()}")
        
        # Map column names based on what's available
        column_mapping = {
            'team_id': ['Team', 'team_id', 'team', 'team id', 'teamid', 'tid'],
            'name': ['Nexus Being', 'name', 'character', 'character name', 'char_name', 'character_name', 'charname'],
            'role': ['Position', 'PositionFull', 'role', 'position', 'char_role', 'character_role']
        }
        
        # Create new columns with required names based on available columns
        required_columns = ['team_id', 'name', 'role']
        
        for required_col, possible_cols in column_mapping.items():
            found = False
            for col in possible_cols:
                if col in df.columns:
                    print(f"Mapping '{col}' to '{required_col}'")
                    df[required_col] = df[col]
                    found = True
                    break
            
            if not found:
                print(f"Error: Could not find any column to map to '{required_col}'")
                raise ValueError(f"Could not find any column to map to '{required_col}'")
        
        # Convert 'Position' values to role codes
        if 'role' in df.columns:
            df['role'] = df['role'].apply(map_position_to_role)
        
        # Initialize trait system for assigning traits
        trait_system = TraitSystem()
        
        # Organize by teams
        teams = {}
        valid_rows = 0
        
        for _, row in df.iterrows():
            # Skip completely empty rows
            if pd.isna(row.get('team_id', None)) and pd.isna(row.get('name', None)):
                continue
                
            team_id = str(row.get('team_id', '')).strip()
            
            # Skip rows with empty team_id
            if not team_id or pd.isna(team_id):
                continue
                
            # Clean team_id format if needed (some Excel exports add '.0')
            if team_id.endswith('.0'):
                team_id = team_id[:-2]
            
            # Ensure team_id starts with 't' 
            if not team_id.startswith('t'):
                team_id = 't' + team_id
            
            if team_id not in teams:
                teams[team_id] = []
            
            # Get character name
            char_name = str(row.get('name', f"Character {len(teams[team_id])}")).strip()
            if not char_name or pd.isna(char_name):
                char_name = f"Character {len(teams[team_id])}"
            
            # Get role
            role = str(row.get('role', 'FL')).strip()
            if not role or pd.isna(role):
                role = 'FL'
            
            # Get team name (from Team column or construct from team_id)
            team_name = None
            if 'Team' in df.columns and not pd.isna(row.get('Team')):
                team_name = f"Team {row.get('Team')}"
            else:
                team_name = f"Team {team_id[1:]}"  # Remove 't' prefix for name
            
            # Create character dictionary for initialization
            character_data = {
                'id': f"{team_id}_{len(teams[team_id])}",
                'name': char_name,
                'team_id': team_id,
                'team_name': team_name,
                'role': role,
                'division': get_division_from_role(role),
                'HP': 100,
                'stamina': 100,
                'life': 100,
                'morale': 50,
                'traits': [],
                'rStats': {},
                'xp_total': 0,
                'games_with_team': 0
            }
            
            # Add attributes - use default values since these usually aren't in the Excel
            for stat in ['STR', 'SPD', 'FS', 'LDR', 'DUR', 'RES', 'WIL', 'OP', 'AM', 'SBY', 'INT', 'LCK', 'ESP', 'EP']:
                attr_key = f'a{stat}'
                character_data[attr_key] = 5
            
            # Try to get Rank as a value for attributes
            if 'Rank' in df.columns and not pd.isna(row.get('Rank')):
                try:
                    rank = int(row.get('Rank'))
                    # Scale rank to attributes (assuming rank is 1-10)
                    stat_value = min(10, max(1, rank))
                    # Apply to key attributes
                    character_data["aSTR"] = stat_value
                    character_data["aSPD"] = stat_value
                    character_data["aOP"] = stat_value
                except:
                    pass
            
            # Check for custom traits assigned in the spreadsheet
            if 'Traits' in df.columns and not pd.isna(row.get('Traits')):
                traits_str = str(row.get('Traits')).strip()
                custom_traits = [t.strip() for t in traits_str.split(',') if t.strip()]
                character_data['custom_traits'] = custom_traits
            
            # Try to get Type for traits
            if 'Primary Type' in df.columns and not pd.isna(row.get('Primary Type')):
                primary_type = str(row.get('Primary Type')).lower()
                
                # Map primary types to traits
                type_to_trait = {
                    'tech': ['genius', 'armor'],
                    'energy': ['genius', 'tactical'],
                    'cosmic': ['shield', 'healing'],
                    'mutant': ['agile', 'stretchy'],
                    'bio': ['agile', 'spider-sense'],
                    'mystic': ['tactical', 'healing'],
                    'skill': ['tactical', 'spider-sense']
                }
                
                # Assign traits based on primary type
                for type_key, traits in type_to_trait.items():
                    if type_key in primary_type:
                        character_data['traits'] = traits
                        break
                
                # Default traits if no match
                if not character_data['traits']:
                    character_data['traits'] = ['genius', 'tactical']
            
            # Create Character object
            character = Character(character_data)
            
            # Assign traits based on attributes if they haven't been set from Type
            if not character.traits and hasattr(trait_system, 'assign_traits_from_attributes'):
                character.traits = trait_system.assign_traits_from_attributes(character)
            
            teams[team_id].append(character)
            valid_rows += 1
        
        print(f"Successfully loaded {valid_rows} characters across {len(teams)} teams")
        
        # If no valid teams loaded, return error
        if not teams:
            raise ValueError("No valid teams found in the Excel file")
        
        return teams
    except Exception as e:
        print(f"Error loading lineups from Excel: {e}")
        import traceback
        traceback.print_exc()
        raise e

def create_sample_teams() -> Dict[str, List[Character]]:
    """Create sample teams with balanced divisions"""
    # Sample data for creating characters
    sample_chars = [
        {
            "id": "t001_1",
            "name": "Iron Man",
            "team_id": "t001",
            "team_name": "Avengers",
            "role": "FL",
            "division": "o",
            "HP": 100,
            "stamina": 100,
            "life": 100,
            "morale": 50,
            "traits": ["genius", "armor"],
            "aSTR": 8, "aSPD": 7, "aFS": 9, "aLDR": 8, "aDUR": 7, "aRES": 6, "aWIL": 8,
            "aOP": 9, "aAM": 7, "aSBY": 8,
            "rStats": {},
            "xp_total": 0
        },
        {
            "id": "t001_2",
            "name": "Captain America",
            "team_id": "t001",
            "team_name": "Avengers",
            "role": "VG",
            "division": "o",
            "HP": 100,
            "stamina": 100,
            "life": 100,
            "morale": 50,
            "traits": ["tactical", "shield"],
            "aSTR": 7, "aSPD": 7, "aFS": 8, "aLDR": 9, "aDUR": 8, "aRES": 7, "aWIL": 9,
            "aOP": 7, "aAM": 8, "aSBY": 9,
            "rStats": {},
            "xp_total": 0
        },
        {
            "id": "t002_1",
            "name": "Spider-Man",
            "team_id": "t002",
            "team_name": "Champions",
            "role": "VG",
            "division": "o",
            "HP": 100,
            "stamina": 100,
            "life": 100,
            "morale": 50,
            "traits": ["agile", "spider-sense"],
            "aSTR": 8, "aSPD": 9, "aFS": 7, "aLDR": 6, "aDUR": 6, "aRES": 7, "aWIL": 7,
            "aOP": 8, "aAM": 7, "aSBY": 7,
            "rStats": {},
            "xp_total": 0
        },
        {
            "id": "t002_2",
            "name": "Ms. Marvel",
            "team_id": "t002",
            "team_name": "Champions",
            "role": "FL",
            "division": "o",
            "HP": 100,
            "stamina": 100,
            "life": 100,
            "morale": 50,
            "traits": ["stretchy", "healing"],
            "aSTR": 7, "aSPD": 6, "aFS": 8, "aLDR": 7, "aDUR": 6, "aRES": 8, "aWIL": 8,
            "aOP": 7, "aAM": 8, "aSBY": 7,
            "rStats": {},
            "xp_total": 0
        },
        {
            "id": "t003_1",
            "name": "Professor X",
            "team_id": "t003",
            "team_name": "X-Men",
            "role": "FL",
            "division": "i",
            "HP": 100,
            "stamina": 100,
            "life": 100,
            "morale": 50,
            "traits": ["telepathic", "genius"],
            "aSTR": 3, "aSPD": 5, "aFS": 9, "aLDR": 10, "aDUR": 5, "aRES": 9, "aWIL": 10,
            "aOP": 10, "aAM": 8, "aSBY": 9,
            "rStats": {},
            "xp_total": 0
        },
        {
            "id": "t003_2",
            "name": "Wolverine",
            "team_id": "t003",
            "team_name": "X-Men",
            "role": "VG",
            "division": "i",
            "HP": 100,
            "stamina": 100,
            "life": 100,
            "morale": 50,
            "traits": ["healing", "agile"],
            "aSTR": 9, "aSPD": 8, "aFS": 7, "aLDR": 6, "aDUR": 10, "aRES": 8, "aWIL": 8,
            "aOP": 7, "aAM": 7, "aSBY": 6,
            "rStats": {},
            "xp_total": 0
        },
        {
            "id": "t004_1",
            "name": "Dr. Strange",
            "team_id": "t004",
            "team_name": "Illuminati",
            "role": "FL",
            "division": "i",
            "HP": 100,
            "stamina": 100,
            "life": 100,
            "morale": 50,
            "traits": ["tactical", "genius"],
            "aSTR": 5, "aSPD": 6, "aFS": 10, "aLDR": 8, "aDUR": 7, "aRES": 10, "aWIL": 9,
            "aOP": 9, "aAM": 9, "aSBY": 8,
            "rStats": {},
            "xp_total": 0
        },
        {
            "id": "t004_2",
            "name": "Black Bolt",
            "team_id": "t004",
            "team_name": "Illuminati",
            "role": "SV",
            "division": "i",
            "HP": 100,
            "stamina": 100,
            "life": 100,
            "morale": 50,
            "traits": ["tactical", "shield"],
            "aSTR": 9, "aSPD": 8, "aFS": 7, "aLDR": 8, "aDUR": 9, "aRES": 7, "aWIL": 8,
            "aOP": 10, "aAM": 7, "aSBY": 8,
            "rStats": {},
            "xp_total": 0
        }
    ]
    
    # Create characters and group by team
    teams = {}
    for char_data in sample_chars:
        team_id = char_data["team_id"]
        if team_id not in teams:
            teams[team_id] = []
        
        character = Character(char_data)
        teams[team_id].append(character)
    
    return teams