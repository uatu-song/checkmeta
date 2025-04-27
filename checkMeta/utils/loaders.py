"""
META Fantasy League - Data Loading Utilities
Handles loading lineups from Excel files and other data sources
"""

import os
import pandas as pd
import random
from typing import Dict, List, Any

def load_lineups_from_excel(file_path, day_sheet="4/7/25"):
    """Load character lineups from an Excel file
    
    Args:
        file_path: Path to Excel file
        day_sheet: Sheet name for day-specific lineups
        
    Returns:
        dict: Dictionary of teams by team_id
    """
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
            'name': ['Nexus Being', 'name', 'character', 'character name', 'char_name', 'character_name'],
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
            if not team_id.lower().startswith('t'):
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
            
            # Create character
            role = map_position_to_role(role)
            division = get_division_from_role(role)
            
            character = {
                'id': f"{team_id}_{len(teams[team_id])}",
                'name': char_name,
                'team_id': team_id,
                'team_name': team_name,
                'role': role,
                'division': division,
                'HP': 100,
                'stamina': 100,
                'life': 100,
                'morale': 50,
                'traits': [],
                'rStats': {},
                'xp_total': 0
            }
            
            # Add stats - use default values since these usually aren't in the Excel
            for stat in ['STR', 'SPD', 'FS', 'LDR', 'DUR', 'RES', 'WIL', 'OP', 'AM', 'SBY']:
                character[f"a{stat}"] = 5
            
            # Try to get Rank as a value for stats
            if 'Rank' in df.columns and not pd.isna(row.get('Rank')):
                try:
                    rank = int(row.get('Rank'))
                    # Scale rank to stats (assuming rank is 1-10)
                    stat_value = min(10, max(1, rank))
                    # Apply to key stats
                    character["aSTR"] = stat_value
                    character["aSPD"] = stat_value
                    character["aOP"] = stat_value
                except:
                    pass
            
            # Add traits based on Primary Type
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
                        character['traits'] = traits
                        break
                
                # Default traits if no match
                if not character['traits']:
                    character['traits'] = ['genius', 'tactical']
            else:
                # Default traits if no primary type
                character['traits'] = ['genius', 'tactical']
            
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
        raise e  # Re-raise to ensure the error is propagated

def load_team_name_map(csv_path='data/teams/SimEngine v3 teamIDs 1.csv'):
    """Load team name mapping from CSV file
    
    Args:
        csv_path: Path to team IDs CSV file
        
    Returns:
        dict: Dictionary mapping team_ids to team names
    """
    try:
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            return dict(zip(df['team_ids'], df['teamName']))
    except Exception as e:
        print(f"Error loading team names: {e}")
    
    # Fallback mapping if CSV cannot be loaded
    return {
        'tT001': "Xavier's School", 
        'tT002': 'Brotherhood', 
        'tT003': 'Avengers', 
        'tT004': 'Fantastic Four', 
        'tT005': 'Hellfire Club', 
        'tT006': 'Asgardians', 
        'tT007': 'Shield Ops', 
        'tT008': 'Mutant Underground', 
        'tT009': 'X-Force', 
        'tT010': 'The Illuminati'
    }

def load_trait_catalog(csv_path='data/traits/SimEngine v2  full_trait_catalog_export.csv'):
    """Load trait catalog from CSV file
    
    Args:
        csv_path: Path to trait catalog CSV
        
    Returns:
        dict: Dictionary of trait definitions
    """
    traits = {}
    
    try:
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            
            for _, row in df.iterrows():
                team_id = str(row.get('team_id', '')).strip()
                division = str(row.get('division', '')).strip()
                
                if team_id and division:
                    # Normalize team ID
                    if not team_id.lower().startswith('t'):
                        team_id = 't' + team_id
                        
                    team_divisions[team_id] = division
            
            print(f"Loaded {len(team_divisions)} team divisions from {csv_path}")
            return team_divisions
    except Exception as e:
        print(f"Error loading division data: {e}")
    
    # Return empty if loading fails
    return team_divisions

def generate_random_character(team_id, index, role=None):
    """Generate a random character for testing
    
    Args:
        team_id: Team ID for the character
        index: Index within team (for unique ID)
        role: Optional specific role
        
    Returns:
        dict: Randomly generated character
    """
    # Define possible roles
    roles = ["FL", "VG", "EN", "RG", "GO", "PO", "SV"]
    
    # Define name components
    first_names = ["Alex", "Jordan", "Morgan", "Taylor", "Casey", "Riley", "Quinn", 
                   "Avery", "Dakota", "Skyler", "Reese", "Phoenix", "Blake"]
    
    last_names = ["Smith", "Jones", "Lee", "Chen", "Garcia", "Patel", "Nguyen", 
                  "Kim", "Jackson", "Singh", "Lopez", "Williams", "Johnson"]
    
    # Define traits
    possible_traits = [
        "genius", "armor", "tactical", "shield", "agile", 
        "spider-sense", "stretchy", "healing"
    ]
    
    # Generate random character
    if role is None:
        role = random.choice(roles)
    
    division = get_division_from_role(role)
    
    # Generate random name
    first_name = random.choice(first_names)
    last_name = random.choice(last_names)
    char_name = f"{first_name} {last_name}"
    
    # Generate random attributes (5-9 range)
    attributes = {}
    for stat in ['STR', 'SPD', 'FS', 'LDR', 'DUR', 'RES', 'WIL', 'OP', 'AM', 'SBY']:
        attributes[f"a{stat}"] = random.randint(4, 9)
    
    # Enhance primary attributes based on role
    if role == "FL":
        attributes["aLDR"] += 1
    elif role == "VG":
        attributes["aSPD"] += 1
    elif role == "EN":
        attributes["aSTR"] += 1
    elif role == "RG":
        attributes["aFS"] += 1
    elif role == "GO":
        attributes["aSPD"] += 1
    elif role == "PO":
        attributes["aWIL"] += 1
    elif role == "SV":
        attributes["aOP"] += 1
    
    # Generate random traits (2-3)
    num_traits = random.randint(2, 3)
    traits = random.sample(possible_traits, num_traits)
    
    # Create character
    character = {
        'id': f"{team_id}_{index}",
        'name': char_name,
        'team_id': team_id,
        'team_name': f"Team {team_id[1:]}",
        'role': role,
        'division': division,
        'HP': 100,
        'stamina': 100,
        'life': 100,
        'morale': 50,
        'traits': traits,
        'rStats': {},
        'xp_total': 0
    }
    
    # Add attributes
    for stat, value in attributes.items():
        character[stat] = value
    
    return character

def generate_random_team(team_id, size=5):
    """Generate a random team for testing
    
    Args:
        team_id: Team ID
        size: Number of characters in team
        
    Returns:
        list: List of randomly generated characters
    """
    team = []
    
    # Ensure normalized team ID
    if not team_id.lower().startswith('t'):
        team_id = 't' + team_id
    
    # Always include a Field Leader
    fl = generate_random_character(team_id, 0, "FL")
    team.append(fl)
    
    # Add additional characters with random roles
    for i in range(1, size):
        char = generate_random_character(team_id, i)
        team.append(char)
    
    return team

def map_position_to_role(position):
    """Map position to standardized role code
    
    Args:
        position: Position name or code
        
    Returns:
        str: Standardized role code
    """
    position = str(position).upper().strip()
    
    # Standard position mappings
    position_map = {
        "FIELD LEADER": "FL",
        "VANGUARD": "VG",
        "ENFORCER": "EN",
        "RANGER": "RG",
        "GHOST OPERATIVE": "GO",
        "PSI OPERATIVE": "PO",
        "SOVEREIGN": "SV"
    }
    
    # Check for exact matches
    if position in position_map:
        return position_map[position]
    
    # Check for partial matches
    for key, value in position_map.items():
        if key in position:
            return value
    
    # Check if already a valid role code
    valid_roles = ["FL", "VG", "EN", "RG", "GO", "PO", "SV"]
    if position in valid_roles:
        return position
    
    # Default
    return "FL"

def get_division_from_role(role):
    """Map role to division
    
    Args:
        role: Role code
        
    Returns:
        str: Division code ('o' or 'i')
    """
    operations_roles = ["FL", "VG", "EN"]
    intelligence_roles = ["RG", "GO", "PO", "SV"]
    
    if role in operations_roles:
        return "o"
    elif role in intelligence_roles:
        return "i"
    else:
        return "o"  # Default to operations
                # Extract key info
                trait_id = row.get('trait_id', '').strip()
                if not trait_id:
                    continue
                    
                # Parse triggers
                triggers_raw = row.get('triggers', '').strip()
                triggers = [t.strip() for t in triggers_raw.split(',') if t.strip()]
                
                # Create trait definition
                traits[trait_id] = {
                    'name': row.get('name', trait_id),
                    'type': row.get('type', '').lower(),
                    'triggers': triggers,
                    'formula_key': row.get('formula_key', ''),
                    'formula_expr': row.get('formula_expr', ''),
                    'value': int(row.get('value', 0)) if row.get('value', '').isdigit() else 10,
                    'stamina_cost': int(row.get('stamina_cost', 0)) if row.get('stamina_cost', '').isdigit() else 0,
                    'cooldown': int(row.get('cooldown', 0)) if row.get('cooldown', '').isdigit() else 0,
                    'description': row.get('description', '')
                }
            
            print(f"Loaded {len(traits)} traits from {csv_path}")
            return traits
    except Exception as e:
        print(f"Error loading trait catalog: {e}")
    
    # Return empty if loading fails
    return traits

def load_divisions_data(csv_path='data/teams/SimEngine v3  Divisions.csv'):
    """Load division assignments data
    
    Args:
        csv_path: Path to divisions CSV
        
    Returns:
        dict: Dictionary mapping team IDs to divisions
    """
    team_divisions = {}
    
    try:
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            
            for _, row in df.iterrows():