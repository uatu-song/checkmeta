"""
META Fantasy League Simulator - Enhanced Trait Loader
Ensures reliable loading of all traits from the trait catalog CSV
"""

import os
import csv
import logging
import pandas as pd
from typing import Dict, List, Any, Optional, Set

logger = logging.getLogger("TraitLoader")

class TraitLoader:
    """Enhanced system for loading and validating trait data from CSV"""
    
    def __init__(self, config=None):
        """Initialize the trait loader
        
        Args:
            config: Optional configuration object
        """
        self.config = config
        self.trait_file = self._get_trait_file_path()
        self.traits = {}
        self.loaded_trait_count = 0
        self.expected_trait_count = 41  # Expected number of traits in catalog
        
    def _get_trait_file_path(self) -> str:
        """Get the path to the trait catalog file
        
        Returns:
            str: Path to trait catalog file
        """
        # Try to get from config
        if self.config and hasattr(self.config, "paths"):
            trait_file = self.config.paths.get("trait_catalog")
            if trait_file:
                return trait_file
        
        # Default paths to try
        default_paths = [
            "data/traits/SimEngine v2  full_trait_catalog_export.csv",
            "SimEngine v2  full_trait_catalog_export.csv",
            "full_trait_catalog_export.csv"
        ]
        
        for path in default_paths:
            if os.path.exists(path):
                logger.info(f"Found trait catalog at: {path}")
                return path
        
        logger.warning("Could not find trait catalog file. Using first default path.")
        return default_paths[0]
    
    def load_traits(self) -> Dict[str, Dict[str, Any]]:
        """Load all traits from the trait catalog
        
        Returns:
            dict: Dictionary of loaded traits
        """
        # Try both loading methods
        try:
            # Try pandas method first (more robust)
            traits = self._load_traits_pandas()
            
            # If pandas failed or returned empty, try CSV method
            if not traits:
                traits = self._load_traits_csv()
            
            # If still empty, use defaults
            if not traits:
                traits = self._get_default_traits()
            
            # Store and return traits
            self.traits = traits
            self.loaded_trait_count = len(traits)
            
            # Log results
            if self.loaded_trait_count > 0:
                logger.info(f"Successfully loaded {self.loaded_trait_count} traits")
                if self.loaded_trait_count < self.expected_trait_count:
                    logger.warning(f"Expected {self.expected_trait_count} traits, but only loaded {self.loaded_trait_count}")
            else:
                logger.error(f"Failed to load any traits from {self.trait_file}")
            
            return traits
            
        except Exception as e:
            logger.error(f"Error loading traits: {e}")
            
            # Fall back to defaults
            default_traits = self._get_default_traits()
            self.traits = default_traits
            self.loaded_trait_count = len(default_traits)
            
            logger.warning(f"Using {self.loaded_trait_count} default traits due to loading error")
            return default_traits
    
    def _load_traits_pandas(self) -> Dict[str, Dict[str, Any]]:
        """Load traits using pandas (more robust method)
        
        Returns:
            dict: Dictionary of loaded traits
        """
        traits = {}
        
        try:
            if not os.path.exists(self.trait_file):
                logger.error(f"Trait file not found: {self.trait_file}")
                return {}
            
            # Read CSV with pandas
            df = pd.read_csv(self.trait_file)
            
            # Log column names for debugging
            logger.debug(f"CSV columns: {df.columns.tolist()}")
            
            # Normalize column names (case-insensitive)
            column_map = {}
            for col in df.columns:
                col_lower = col.lower()
                if 'trait_id' in col_lower or 'traitid' in col_lower:
                    column_map[col] = 'trait_id'
                elif 'name' in col_lower:
                    column_map[col] = 'name'
                elif 'type' in col_lower:
                    column_map[col] = 'type'
                elif 'triggers' in col_lower:
                    column_map[col] = 'triggers'
                elif 'formula_key' in col_lower or 'formulakey' in col_lower:
                    column_map[col] = 'formula_key'
                elif 'formula_expr' in col_lower or 'formulaexpr' in col_lower:
                    column_map[col] = 'formula_expr'
                elif 'value' in col_lower:
                    column_map[col] = 'value'
                elif 'stamina_cost' in col_lower or 'staminacost' in col_lower:
                    column_map[col] = 'stamina_cost'
                elif 'cooldown' in col_lower:
                    column_map[col] = 'cooldown'
                elif 'description' in col_lower:
                    column_map[col] = 'description'
            
            # Rename columns
            df = df.rename(columns=column_map)
            
            # Check required columns
            required_cols = ['trait_id']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                logger.error(f"Missing required columns in trait file: {missing_cols}")
                return {}
            
            # Process each row
            for _, row in df.iterrows():
                trait_id = str(row.get('trait_id', '')).strip()
                
                # Skip empty trait_id
                if not trait_id:
                    continue
                
                # Parse triggers
                triggers_raw = str(row.get('triggers', '')).strip()
                triggers = [t.strip() for t in triggers_raw.split(',') if t.strip()]
                
                # Create trait definition
                traits[trait_id] = {
                    'name': str(row.get('name', trait_id)).strip(),
                    'type': str(row.get('type', '')).lower().strip(),
                    'triggers': triggers,
                    'formula_key': str(row.get('formula_key', '')).strip(),
                    'formula_expr': str(row.get('formula_expr', '')).strip(),
                    'value': int(row.get('value', 0)) if pd.notna(row.get('value')) and str(row.get('value', '')).strip().isdigit() else 10,
                    'stamina_cost': int(row.get('stamina_cost', 0)) if pd.notna(row.get('stamina_cost')) and str(row.get('stamina_cost', '')).strip().isdigit() else 0,
                    'cooldown': int(row.get('cooldown', 0)) if pd.notna(row.get('cooldown')) and str(row.get('cooldown', '')).strip().isdigit() else 0,
                    'description': str(row.get('description', '')).strip()
                }
            
            # Log loaded traits
            logger.info(f"Loaded {len(traits)} traits using pandas from {self.trait_file}")
            return traits
            
        except Exception as e:
            logger.error(f"Error loading traits with pandas: {e}")
            return {}
    
    def _load_traits_csv(self) -> Dict[str, Dict[str, Any]]:
        """Load traits using standard CSV reader (fallback method)
        
        Returns:
            dict: Dictionary of loaded traits
        """
        traits = {}
        
        try:
            if not os.path.exists(self.trait_file):
                logger.error(f"Trait file not found: {self.trait_file}")
                return {}
            
            with open(self.trait_file, 'r', encoding='utf-8') as f:
                # Read the first line to determine if we need to skip it
                first_line = f.readline().strip()
                f.seek(0)  # Reset file pointer
                
                # Check if first line is a header
                has_header = 'trait_id' in first_line.lower() or 'name' in first_line.lower()
                
                # Create CSV reader
                if has_header:
                    reader = csv.DictReader(f)
                else:
                    # If no header, use default column names
                    reader = csv.DictReader(f, fieldnames=[
                        'trait_id', 'name', 'type', 'triggers', 'formula_key', 
                        'formula_expr', 'value', 'stamina_cost', 'cooldown', 'description'
                    ])
                
                # Normalize field names (case-insensitive)
                normalized_fieldnames = {}
                for field in reader.fieldnames:
                    field_lower = field.lower()
                    if 'trait_id' in field_lower or 'traitid' in field_lower:
                        normalized_fieldnames[field] = 'trait_id'
                    elif 'name' in field_lower:
                        normalized_fieldnames[field] = 'name'
                    elif 'type' in field_lower:
                        normalized_fieldnames[field] = 'type'
                    elif 'triggers' in field_lower:
                        normalized_fieldnames[field] = 'triggers'
                    elif 'formula_key' in field_lower or 'formulakey' in field_lower:
                        normalized_fieldnames[field] = 'formula_key'
                    elif 'formula_expr' in field_lower or 'formulaexpr' in field_lower:
                        normalized_fieldnames[field] = 'formula_expr'
                    elif 'value' in field_lower:
                        normalized_fieldnames[field] = 'value'
                    elif 'stamina_cost' in field_lower or 'staminacost' in field_lower:
                        normalized_fieldnames[field] = 'stamina_cost'
                    elif 'cooldown' in field_lower:
                        normalized_fieldnames[field] = 'cooldown'
                    elif 'description' in field_lower:
                        normalized_fieldnames[field] = 'description'
                
                # Process each row
                for row in reader:
                    # Normalize field names
                    normalized_row = {}
                    for field, value in row.items():
                        if field in normalized_fieldnames:
                            normalized_row[normalized_fieldnames[field]] = value
                        else:
                            normalized_row[field] = value
                    
                    # Get trait ID
                    trait_id = normalized_row.get('trait_id', '').strip()
                    
                    # Skip empty trait_id
                    if not trait_id:
                        continue
                    
                    # Parse triggers
                    triggers_raw = normalized_row.get('triggers', '').strip()
                    triggers = [t.strip() for t in triggers_raw.split(',') if t.strip()]
                    
                    # Create trait definition
                    traits[trait_id] = {
                        'name': normalized_row.get('name', trait_id),
                        'type': normalized_row.get('type', '').lower(),
                        'triggers': triggers,
                        'formula_key': normalized_row.get('formula_key', ''),
                        'formula_expr': normalized_row.get('formula_expr', ''),
                        'value': int(normalized_row.get('value', 0)) if normalized_row.get('value', '').isdigit() else 10,
                        'stamina_cost': int(normalized_row.get('stamina_cost', 0)) if normalized_row.get('stamina_cost', '').isdigit() else 0,
                        'cooldown': int(normalized_row.get('cooldown', 0)) if normalized_row.get('cooldown', '').isdigit() else 0,
                        'description': normalized_row.get('description', '')
                    }
            
            # Log loaded traits
            logger.info(f"Loaded {len(traits)} traits using CSV reader from {self.trait_file}")
            return traits
            
        except Exception as e:
            logger.error(f"Error loading traits with CSV reader: {e}")
            return {}
    
    def _get_default_traits(self) -> Dict[str, Dict[str, Any]]:
        """Get default trait definitions if loading fails
        
        Returns:
            dict: Default trait definitions
        """
        logger.warning("Using default traits as fallback")
        return {
            "genius": {
                "name": "Genius Intellect",
                "type": "combat",
                "triggers": ["convergence", "critical_hit"],
                "formula_key": "bonus_roll",
                "value": 15,
                "stamina_cost": 5,
                "cooldown": 1,
                "description": "Enhanced cognitive abilities provide combat advantages"
            },
            "armor": {
                "name": "Power Armor",
                "type": "defense",
                "triggers": ["damage_taken"],
                "formula_key": "damage_reduction",
                "value": 25,
                "stamina_cost": 0,
                "cooldown": 0,
                "description": "Advanced armor reduces incoming damage"
            },
            "tactical": {
                "name": "Tactical Mastery",
                "type": "leadership",
                "triggers": ["convergence", "team_boost"],
                "formula_key": "bonus_roll",
                "value": 20,
                "stamina_cost": 10,
                "cooldown": 2,
                "description": "Superior tactical thinking improves combat capabilities"
            },
            "shield": {
                "name": "Vibranium Shield",
                "type": "defense",
                "triggers": ["damage_taken", "convergence"],
                "formula_key": "damage_reduction",
                "value": 30,
                "stamina_cost": 5,
                "cooldown": 1,
                "description": "Near-indestructible shield provides exceptional protection"
            },
            "agile": {
                "name": "Enhanced Agility",
                "type": "mobility",
                "triggers": ["convergence", "evasion"],
                "formula_key": "bonus_roll",
                "value": 15,
                "stamina_cost": 3,
                "cooldown": 0,
                "description": "Superhuman agility improves combat capabilities"
            },
            "spider-sense": {
                "name": "Spider Sense",
                "type": "precognition",
                "triggers": ["combat", "danger"],
                "formula_key": "defense_bonus",
                "value": 20,
                "stamina_cost": 0,
                "cooldown": 0,
                "description": "Danger-sensing ability provides combat advantages"
            },
            "stretchy": {
                "name": "Polymorphic Body",
                "type": "mobility",
                "triggers": ["convergence", "positioning"],
                "formula_key": "bonus_roll",
                "value": 10,
                "stamina_cost": 5,
                "cooldown": 0,
                "description": "Malleable physiology allows for creative attacks"
            },
            "healing": {
                "name": "Rapid Healing",
                "type": "regeneration",
                "triggers": ["end_of_turn", "damage_taken"],
                "formula_key": "heal",
                "value": 5,
                "stamina_cost": 0,
                "cooldown": 0,
                "description": "Accelerated healing factor repairs injuries quickly"
            }
        }
    
    def validate_traits(self) -> Dict[str, Any]:
        """Validate loaded traits and provide a report
        
        Returns:
            dict: Validation report
        """
        # Initialize report
        report = {
            "loaded_count": len(self.traits),
            "expected_count": self.expected_trait_count,
            "success": len(self.traits) > 0,
            "missing_fields": [],
            "invalid_traits": []
        }
        
        # Check each trait for required fields
        required_fields = ['name', 'type', 'triggers', 'formula_key']
        
        for trait_id, trait in self.traits.items():
            # Check for missing fields
            missing = [field for field in required_fields if field not in trait or not trait[field]]
            
            if missing:
                report["missing_fields"].append({
                    "trait_id": trait_id,
                    "missing": missing
                })
            
            # Validate trigger field
            if 'triggers' in trait and not isinstance(trait['triggers'], list):
                report["invalid_traits"].append({
                    "trait_id": trait_id,
                    "issue": "triggers is not a list"
                })
        
        # Calculate success percentage
        report["success_percentage"] = (report["loaded_count"] / report["expected_count"]) * 100 if report["expected_count"] > 0 else 0
        
        # Log validation results
        if report["loaded_count"] == 0:
            logger.error("No traits loaded!")
        elif report["loaded_count"] < report["expected_count"]:
            logger.warning(f"Loaded {report['loaded_count']}/{report['expected_count']} traits ({report['success_percentage']:.1f}%)")
        else:
            logger.info(f"Successfully loaded all {report['loaded_count']} traits")
        
        if report["missing_fields"]:
            logger.warning(f"{len(report['missing_fields'])} traits have missing fields")
        
        if report["invalid_traits"]:
            logger.warning(f"{len(report['invalid_traits'])} traits have validation issues")
        
        return report
    
    def get_trait_types(self) -> Dict[str, List[str]]:
        """Get traits grouped by type
        
        Returns:
            dict: Dictionary of traits grouped by type
        """
        types = {}
        
        for trait_id, trait in self.traits.items():
            trait_type = trait.get('type', '').strip()
            
            if not trait_type:
                trait_type = 'unknown'
            
            if trait_type not in types:
                types[trait_type] = []
            
            types[trait_type].append(trait_id)
        
        return types
    
    def get_trait_triggers(self) -> Dict[str, List[str]]:
        """Get traits grouped by trigger
        
        Returns:
            dict: Dictionary of traits grouped by trigger
        """
        triggers = {}
        
        for trait_id, trait in self.traits.items():
            for trigger in trait.get('triggers', []):
                trigger = trigger.strip()
                
                if not trigger:
                    continue
                
                if trigger not in triggers:
                    triggers[trigger] = []
                
                triggers[trigger].append(trait_id)
        
        return triggers
    
    def print_trait_summary(self) -> None:
        """Print a summary of loaded traits"""
        # Get traits by type
        types = self.get_trait_types()
        
        # Get traits by trigger
        triggers = self.get_trait_triggers()
        
        # Print summary
        print(f"\n{'=' * 40}")
        print(f"TRAIT CATALOG SUMMARY")
        print(f"{'=' * 40}")
        print(f"Loaded {len(self.traits)} traits from {self.trait_file}")
        print(f"Expected: {self.expected_trait_count}")
        print(f"Success rate: {(len(self.traits) / self.expected_trait_count) * 100:.1f}%\n")
        
        # Print types
        print(f"TRAIT TYPES ({len(types)}):")
        for trait_type, traits in sorted(types.items()):
            print(f"  {trait_type}: {len(traits)} traits")
        
        print(f"\nTRIGGERS ({len(triggers)}):")
        for trigger, traits in sorted(triggers.items()):
            print(f"  {trigger}: {len(traits)} traits")
        
        print(f"\nFIRST 5 TRAITS:")
        for i, (trait_id, trait) in enumerate(list(self.traits.items())[:5]):
            print(f"  {i+1}. {trait.get('name', trait_id)} ({trait_id}): {trait.get('description', '')[:50]}...")
        
        print(f"{'=' * 40}\n")
        