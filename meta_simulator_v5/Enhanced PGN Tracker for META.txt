"""
Enhanced PGN Tracker for META League Simulator v4.2.1
Implements detailed PGN recording with backward compatibility
"""

import os
import json
import datetime
import chess
import chess.pgn
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from system_base import SystemBase

class EnhancedPGNTracker(SystemBase):
    """Enhanced system for recording chess games in PGN format with detailed metadata"""
    
    def __init__(self, config):
        """Initialize the enhanced PGN tracker"""
        super().__init__("pgn_tracker", None)
        self.config = config
        self.output_dir = config.get("paths.pgn_dir")
        self.metadata_dir = os.path.join(self.output_dir, "metadata")
        
        # Create necessary directories
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.metadata_dir, exist_ok=True)
        
        # Game tracking state
        self.game_count = 0
        self.current_match = None
        self.metadata_records = []
        
        # Read configuration options for PGN generation
        self.per_board_pgn = config.get("features.per_board_pgn", True)
        self.aggregate_match_pgn = config.get("features.aggregate_match_pgn", True)
        
        # Validate at least one mode is enabled
        if not self.per_board_pgn and not self.aggregate_match_pgn:
            self.logger.warning("Both per_board_pgn and aggregate_match_pgn are disabled! Enabling per_board_pgn for backward compatibility.")
            self.per_board_pgn = True
        
        # Log configuration
        if self.per_board_pgn:
            self.logger.info("Using individual board PGN generation (backward compatible mode)")
        else:
            self.logger.warning("Individual board PGN generation is disabled - this may break compatibility with analysis tools")
            
        if self.aggregate_match_pgn:
            self.logger.info("Aggregated match PGN generation is enabled")
    
    def _activate_implementation(self) -> bool:
        """Implementation-specific activation logic"""
        self.logger.info(f"Activating Enhanced PGN Tracker with per_board_pgn={self.per_board_pgn}, aggregate_match_pgn={self.aggregate_match_pgn}")
        return True
    
    def record_match_games(self, team_a: List[Dict[str, Any]], team_a_boards: List[chess.Board], 
                          team_b: List[Dict[str, Any]], team_b_boards: List[chess.Board], 
                          match_context: Dict[str, Any]) -> Tuple[str, str]:
        """Record PGN files for all characters in a match with enhanced metadata"""
        self.logger.info(f"Recording PGNs for match: {match_context['match_id']}")
        
        # Start tracking the match
        match_id = match_context["match_id"]
        team_a_name = match_context["team_a_name"]
        team_b_name = match_context["team_b_name"]
        team_a_id = match_context["team_a_id"]
        team_b_id = match_context["team_b_id"]
        day = match_context.get("day", 1)
        match_number = match_context.get("match_number", 1)
        
        # Setup match metadata
        self.current_match = {
            "match_id": match_id,
            "day": day,
            "match_number": match_number,
            "team_a_id": team_a_id,
            "team_b_id": team_b_id,
            "team_a_name": team_a_name,
            "team_b_name": team_b_name,
            "date": datetime.datetime.now().isoformat(),
            "games": [],
            "convergences": match_context.get("convergence_logs", []),
            "trait_logs": match_context.get("trait_logs", []),
            "stamina_logs": match_context.get("stamina_logs", [])
        }
        
        self.game_count = 0
        self.metadata_records = []
        
        # Store all games for possible aggregation
        all_game_pgns = []
        
        # Process each character's game
        for i, (char_a, board_a) in enumerate(zip(team_a, team_a_boards)):
            # Skip inactive characters
            if not char_a.get("is_active", True):
                continue
                
            # Create game index (1-based)
            game_idx = i + 1
            
            # Create game ID
            game_id = f"{match_id}_game{game_idx}"
            
            try:
                # Determine opponent (from team B)
                char_b = team_b[i] if i < len(team_b) else None
                char_b_name = char_b.get("name", "AI Opponent") if char_b else "AI Opponent"
                
                # Determine result
                result = "unknown"
                if "is_ko" in char_a and char_a["is_ko"]:
                    result = "loss"
                elif "result" in char_a:
                    result = char_a["result"]
                
                # Collect board metrics for metadata
                board_metrics = self._collect_board_metrics(board_a)
                
                # Generate PGN for this game
                pgn_text, game_metadata = self._generate_game_pgn(
                    game_id, 
                    board_a, 
                    char_a, 
                    char_b_name, 
                    result, 
                    match_context, 
                    game_idx,
                    board_metrics
                )
                
                # Add to match metadata
                self.current_match["games"].append(game_metadata)
                
                # Save individual PGN if enabled
                if self.per_board_pgn:
                    self._save_individual_pgn(game_id, pgn_text, game_metadata)
                    self.logger.debug(f"Saved individual PGN for game {game_idx} (Team A)")
                
                # Store for possible aggregation
                all_game_pgns.append((game_id, pgn_text, game_metadata))
                
            except Exception as e:
                self.logger.error(f"Error generating PGN for Team A game {game_idx}: {e}")
        
        # Process team B games
        for i, (char_b, board_b) in enumerate(zip(team_b, team_b_boards)):
            # Skip inactive characters
            if not char_b.get("is_active", True):
                continue
                
            # Create game index (using team size offset)
            game_idx = len(team_a) + i + 1
            
            # Create game ID
            game_id = f"{match_id}_game{game_idx}"
            
            try:
                # Determine opponent (from team A)
                char_a = team_a[i] if i < len(team_a) else None
                char_a_name = char_a.get("name", "AI Opponent") if char_a else "AI Opponent"
                
                # Determine result
                result = "unknown"
                if "is_ko" in char_b and char_b["is_ko"]:
                    result = "loss"
                elif "result" in char_b:
                    result = char_b["result"]
                
                # Collect board metrics for metadata
                board_metrics = self._collect_board_metrics(board_b)
                
                # Generate PGN for this game
                pgn_text, game_metadata = self._generate_game_pgn(
                    game_id, 
                    board_b, 
                    char_b, 
                    char_a_name, 
                    result, 
                    match_context, 
                    game_idx,
                    board_metrics
                )
                
                # Add to match metadata
                self.current_match["games"].append(game_metadata)
                
                # Save individual PGN if enabled
                if self.per_board_pgn:
                    self._save_individual_pgn(game_id, pgn_text, game_metadata)
                    self.logger.debug(f"Saved individual PGN for game {game_idx} (Team B)")
                
                # Store for possible aggregation
                all_game_pgns.append((game_id, pgn_text, game_metadata))
                
            except Exception as e:
                self.logger.error(f"Error generating PGN for Team B game {game_idx}: {e}")
        
        # Save aggregated match PGN if enabled
        aggregated_pgn_path = ""
        aggregated_metadata_path = ""
        
        if self.aggregate_match_pgn and all_game_pgns:
            aggregated_pgn_path, aggregated_metadata_path = self._save_aggregated_pgn(
                match_id, all_game_pgns, self.current_match
            )
            self.logger.info(f"Saved aggregated match PGN: {aggregated_pgn_path}")
        
        # Determine which paths to return based on configuration
        if self.aggregate_match_pgn:
            return aggregated_pgn_path, aggregated_metadata_path
        else:
            # For backward compatibility, return the first individual PGN
            if all_game_pgns:
                game_id, _, _ = all_game_pgns[0]
                return os.path.join(self.output_dir, f"{game_id}.pgn"), os.path.join(self.metadata_dir, f"{game_id}_metadata.json")
            else:
                return "", ""
    
    def _generate_game_pgn(self, 
                          game_id: str, 
                          board: chess.Board,
                          character: Dict[str, Any], 
                          opponent_name: str,
                          result: str, 
                          match_context: Dict[str, Any],
                          game_idx: int,
                          board_metrics: Dict[str, Any] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Generate PGN for a single game.
        
        Args:
            game_id: Game identifier
            board: Chess board with moves
            character: Character dictionary
            opponent_name: Name of opponent
            result: Game result
            match_context: Match context dictionary
            game_idx: Game index (1-based)
            board_metrics: Optional metrics about the board
            
        Returns:
            Tuple[str, Dict[str, Any]]: PGN text and game metadata
        """
        # Create a new game from the board's move stack
        game = chess.pgn.Game()
        
        # Add headers
        game.headers["Event"] = f"META League Day {match_context['day']} Match {match_context['match_number']}"
        game.headers["Site"] = "META Fantasy League"
        game.headers["Date"] = datetime.datetime.now().strftime("%Y.%m.%d")
        game.headers["Round"] = str(match_context.get("round", 1))
        game.headers["White"] = character.get("name", f"Player {character.get('id', 'Unknown')}")
        game.headers["Black"] = opponent_name
        
        # Add game result
        pgn_result = "*"  # Default (game in progress)
        
        if result == "win":
            pgn_result = "1-0"
        elif result == "loss":
            pgn_result = "0-1"
        elif result == "draw":
            pgn_result = "1/2-1/2"
            
        game.headers["Result"] = pgn_result
        
        # Add custom META headers
        game.headers["WhiteTeam"] = character.get("team_name", "Unknown Team")
        game.headers["WhiteRole"] = character.get("role", "Unknown")
        game.headers["WhiteDivision"] = character.get("division", "Unknown")
        game.headers["MatchID"] = match_context["match_id"]
        game.headers["GameID"] = game_id
        
        # Add character metadata
        game.headers["CharacterID"] = character.get("id", "Unknown")
        game.headers["TeamID"] = character.get("team_id", "Unknown")
        
        # Add initial and final character stats
        game.headers["InitialHP"] = str(character.get("initial_HP", 100))
        game.headers["InitialStamina"] = str(character.get("initial_stamina", 100))
        game.headers["FinalHP"] = str(character.get("HP", 0))
        game.headers["FinalStamina"] = str(character.get("stamina", 0))
        
        # Add character attributes if available
        for stat in ["STR", "SPD", "FS", "LDR", "DUR", "RES", "WIL"]:
            attr_key = f"a{stat}"
            if attr_key in character:
                game.headers[f"Attr{stat}"] = str(character[attr_key])
        
        # Add trait information if available
        if "traits" in character and character["traits"]:
            if isinstance(character["traits"], list):
                traits_str = ",".join(str(t) for t in character["traits"])
                game.headers["Traits"] = traits_str
        
        # Add board metrics if provided
        if board_metrics:
            for key, value in board_metrics.items():
                # Convert complex values to string
                if isinstance(value, (dict, list)):
                    value_str = json.dumps(value)
                else:
                    value_str = str(value)
                
                if len(value_str) <= 200:  # Limit header size
                    game.headers[key] = value_str
        
        # Create comment with character information
        char_info = f"Character: {character.get('name', 'Unknown')}, "
        char_info += f"Role: {character.get('role', 'Unknown')}, "
        char_info += f"Team: {character.get('team_name', 'Unknown')}, "
        char_info += f"HP: {character.get('HP', 0)}, "
        char_info += f"Stamina: {character.get('stamina', 0)}"
        
        # Add rStats summary if available
        if "rStats" in character and character["rStats"]:
            rstats = []
            for key, value in character["rStats"].items():
                if key.startswith('r'):  # Valid rStat
                    rstats.append(f"{key}: {value}")
            
            if rstats:
                char_info += " | rStats: " + ", ".join(rstats)
        
        game.comment = char_info
        
        # Set up the moves from the board's move stack
        node = game
        
        # Track material changes for annotations
        prev_material = 0
        
        for move_idx, move in enumerate(board.move_stack):
            # Add the move to the game tree
            node = node.add_variation(move)
            
            # Create a new board to evaluate this position
            pos_board = chess.Board()
            for m in board.move_stack[:move_idx + 1]:
                pos_board.push(m)
            
            # Calculate material difference
            material = self._calculate_material_difference(pos_board)
            material_change = material - prev_material
            prev_material = material
            
            # Add annotations for significant material changes
            if abs(material_change) >= 3:
                if material_change > 0:
                    node.comment = f"Significant material gain: +{material_change}"
                else:
                    node.comment = f"Significant material loss: {material_change}"
        
        # Convert to PGN text
        exporter = chess.pgn.StringExporter(headers=True, variations=True, comments=True)
        pgn_text = game.accept(exporter)
        
        # Create metadata record for this game
        metadata_record = {
            "game_id": game_id,
            "match_id": match_context["match_id"],
            "character_id": character.get("id", "Unknown"),
            "character_name": character.get("name", "Unknown"),
            "team_id": character.get("team_id", "Unknown"),
            "role": character.get("role", "Unknown"),
            "division": character.get("division", "Unknown"),
            "result": result,
            "timestamp": datetime.datetime.now().isoformat(),
            "initial_hp": character.get("initial_HP", 100),
            "final_hp": character.get("HP", 0),
            "initial_stamina": character.get("initial_stamina", 100),
            "final_stamina": character.get("stamina", 0),
            "moves_count": len(board.move_stack),
            "material_final": self._calculate_material_difference(board)
        }
        
        # Add board metrics if provided
        if board_metrics:
            metadata_record["board_metrics"] = board_metrics
        
        # Add rStats if available
        if "rStats" in character:
            metadata_record["rstats"] = character["rStats"]
        
        # Add to metadata records
        self.metadata_records.append(metadata_record)
        
        return pgn_text, metadata_record
    
    def _save_individual_pgn(self, game_id: str, pgn_text: str, metadata: Dict[str, Any]) -> Tuple[str, str]:
        """Save an individual board's PGN to its own file (backward compatible behavior)"""
        # Generate filenames
        pgn_filename = f"{game_id}.pgn"
        metadata_filename = f"{game_id}_metadata.json"
        
        pgn_path = os.path.join(self.output_dir, pgn_filename)
        metadata_path = os.path.join(self.metadata_dir, metadata_filename)
        
        try:
            # Write PGN to file
            with open(pgn_path, 'w') as pgn_file:
                pgn_file.write(pgn_text)
            
            # Write metadata to file
            with open(metadata_path, 'w') as metadata_file:
                json.dump(metadata, metadata_file, indent=2)
            
            self.logger.debug(f"Saved individual PGN: {pgn_path}")
            return pgn_path, metadata_path
        except Exception as e:
            self.logger.error(f"Error saving individual PGN {game_id}: {e}")
            raise
    
    def _save_aggregated_pgn(self, 
                            match_id: str, 
                            all_game_pgns: List[Tuple[str, str, Dict[str, Any]]], 
                            match_metadata: Dict[str, Any]) -> Tuple[str, str]:
        """Save an aggregated match PGN and metadata"""
        # Generate filenames
        aggregated_pgn_file = os.path.join(self.output_dir, f"{match_id}_combined.pgn")
        aggregated_metadata_file = os.path.join(self.metadata_dir, f"{match_id}_combined_metadata.json")
        
        try:
            # Create aggregated PGN content
            aggregated_pgn_content = ""
            
            for game_id, pgn_text, game_metadata in all_game_pgns:
                # Add a separator comment before each game
                aggregated_pgn_content += f"\n\n[{game_metadata['character_name']} vs {game_metadata.get('opponent_name', 'Opponent')}]\n\n"
                aggregated_pgn_content += pgn_text
                aggregated_pgn_content += "\n\n"
            
            # Save aggregated PGN file
            with open(aggregated_pgn_file, 'w') as f:
                f.write(aggregated_pgn_content)
            
            # Update match metadata with path information
            match_metadata["aggregated_pgn_file"] = f"{match_id}_combined.pgn"
            match_metadata["aggregated_metadata_file"] = f"{match_id}_combined_metadata.json"
            
            # Save aggregated metadata file
            with open(aggregated_metadata_file, 'w') as f:
                json.dump(match_metadata, f, indent=2)
            
            return aggregated_pgn_file, aggregated_metadata_file
        except Exception as e:
            self.logger.error(f"Error saving aggregated PGN for {match_id}: {e}")
            return "", ""
    
    def _calculate_material_difference(self, board: chess.Board) -> int:
        """Calculate material difference from White's perspective"""
        piece_values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9,
            chess.KING: 0  # King isn't counted in material difference
        }
        
        white_material = 0
        black_material = 0
        
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                value = piece_values.get(piece.piece_type, 0)
                if piece.color == chess.WHITE:
                    white_material += value
                else:
                    bl