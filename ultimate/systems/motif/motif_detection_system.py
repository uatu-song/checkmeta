"""
Motif Detection System for META Fantasy League Simulator
Identifies patterns and themes in chess games and emits motif events

Version: 5.1.0 - Guardian Compliant
"""

import time
import json
import datetime
import logging
import chess
import chess.pgn
import re
from io import StringIO
from typing import Dict, List, Any, Optional, Tuple, Union, Set
from collections import defaultdict

from system_base import SystemBase

class MotifDetectionSystem(SystemBase):
    """
    Motif Detection System for META Fantasy League
    
    Analyzes chess games and PGNs to detect tactical patterns and thematic elements
    that can be used for narrative generation and rStats tracking.
    
    Compliant with Guardian standards:
    - Event emissions via EventEmitter
    - External configuration
    - Structured logging
    - Error handling
    - System registration
    """
    
    def __init__(self, config, registry=None):
        """Initialize the motif detection system"""
        super().__init__(config)
        self.name = "motif_detection_system"
        self.logger = logging.getLogger("META_SIMULATOR.MotifDetectionSystem")
        
        # Store registry if provided
        self._registry = registry
        
        # Cache for commonly used systems and configurations
        self._event_system = None
        self._pgn_tracker = None
        
        # Load motif configuration
        self._load_motif_configuration()
        
        # Initialize state
        self.active = False
        self.detected_motifs = defaultdict(int)
        
        self.logger.info("Motif detection system initialized with {} motif patterns".format(
            len(self._motif_patterns)))
    
    def _load_motif_configuration(self):
        """Load motif configuration from config"""
        try:
            # Load motif patterns
            motif_config = self.config.get("motif_detection", {})
            self._motif_patterns = motif_config.get("patterns", {})
            
            # If no patterns in config, use default patterns
            if not self._motif_patterns:
                self._motif_patterns = {
                    # Attack patterns
                    "fork": {
                        "description": "A single piece threatens two or more opponent pieces",
                        "score": 5,
                        "detection_method": "position_analysis",
                        "category": "tactical"
                    },
                    "pin": {
                        "description": "A piece is prevented from moving because it would expose a more valuable piece behind it",
                        "score": 5,
                        "detection_method": "position_analysis",
                        "category": "tactical"
                    },
                    "skewer": {
                        "description": "A piece is attacked, and when it moves, a less valuable piece behind it is exposed",
                        "score": 5,
                        "detection_method": "position_analysis",
                        "category": "tactical"
                    },
                    
                    # Material patterns
                    "sacrifice": {
                        "description": "Deliberately giving up material for positional advantage",
                        "score": 7,
                        "detection_method": "move_sequence",
                        "category": "strategic"
                    },
                    "exchange": {
                        "description": "Trading pieces of equal value",
                        "score": 3,
                        "detection_method": "move_sequence",
                        "category": "strategic"
                    },
                    
                    # Defensive patterns
                    "fianchetto": {
                        "description": "Development of a bishop on the long diagonal after moving a knight pawn",
                        "score": 3,
                        "detection_method": "move_sequence",
                        "category": "strategic",
                        "pgn_pattern": r"[Nn][bfg]\d [Bb]g\d"
                    },
                    "castling": {
                        "description": "King safety move",
                        "score": 4,
                        "detection_method": "pgn_analysis",
                        "category": "strategic",
                        "pgn_pattern": r"O-O|O-O-O"
                    },
                    
                    # Checkmate patterns
                    "scholars_mate": {
                        "description": "Quick checkmate targeting f7/f2",
                        "score": 10,
                        "detection_method": "pgn_analysis",
                        "category": "tactical",
                        "pgn_pattern": r"[Qq]h5.*[Qq]xf7#|[Qq]h4.*[Qq]xf2#"
                    },
                    "back_rank_mate": {
                        "description": "Checkmate on the back rank",
                        "score": 8,
                        "detection_method": "position_analysis",
                        "category": "tactical"
                    },
                    
                    # Opening patterns
                    "queens_gambit": {
                        "description": "Queens Gambit Opening",
                        "score": 3,
                        "detection_method": "pgn_analysis",
                        "category": "opening",
                        "pgn_pattern": r"^1\. d4 d5 2\. c4"
                    },
                    "sicilian_defense": {
                        "description": "Sicilian Defense",
                        "score": 3,
                        "detection_method": "pgn_analysis", 
                        "category": "opening",
                        "pgn_pattern": r"^1\. e4 c5"
                    },
                    
                    # Endgame patterns
                    "promotion": {
                        "description": "Pawn promotion",
                        "score": 6,
                        "detection_method": "pgn_analysis",
                        "category": "endgame",
                        "pgn_pattern": r"=[QRBN]"
                    },
                    "zugzwang": {
                        "description": "Position where any move worsens the situation",
                        "score": 7, 
                        "detection_method": "position_analysis",
                        "category": "endgame"
                    }
                }
            
            # Load detection thresholds
            self._position_analysis_enabled = motif_config.get("enable_position_analysis", True)
            self._min_motif_score = motif_config.get("min_motif_score", 3)
            self._max_motifs_per_game = motif_config.get("max_motifs_per_game", 5)
            
            # Configure PGN analysis settings
            self._pgn_analysis_enabled = motif_config.get("enable_pgn_analysis", True)
            self._move_sequence_enabled = motif_config.get("enable_move_sequence", True)
            
            # Emit configuration loaded event
            self._emit_event("motif_configuration_loaded", {
                "pattern_count": len(self._motif_patterns),
                "position_analysis_enabled": self._position_analysis_enabled,
                "pgn_analysis_enabled": self._pgn_analysis_enabled,
                "move_sequence_enabled": self._move_sequence_enabled,
                "min_motif_score": self._min_motif_score
            })
            
        except Exception as e:
            self.logger.error("Error loading motif configuration: {}".format(e))
            self._emit_error_event("load_motif_configuration", str(e))
            
            # Set default values
            self._motif_patterns = {}
            self._position_analysis_enabled = True
            self._pgn_analysis_enabled = True
            self._move_sequence_enabled = True
            self._min_motif_score = 3
            self._max_motifs_per_game = 5
    
    def activate(self):
        """Activate the motif detection system"""
        self.active = True
        self.logger.info("Motif detection system activated")
        return True
    
    def deactivate(self):
        """Deactivate the motif detection system"""
        self.active = False
        self.logger.info("Motif detection system deactivated")
        return True
    
    def is_active(self):
        """Check if the motif detection system is active"""
        return self.active
    
    def _get_registry(self):
        """Get system registry (lazy loading)"""
        if not self._registry:
            from system_registry import SystemRegistry
            self._registry = SystemRegistry()
        return self._registry
    
    def _get_event_system(self):
        """Get event system from registry (lazy loading)"""
        if not self._event_system:
            registry = self._get_registry()
            self._event_system = registry.get("event_system")
            if not self._event_system:
                self.logger.warning("Event system not available, events will not be emitted")
        return self._event_system
    
    def _get_pgn_tracker(self):
        """Get PGN tracker from registry (lazy loading)"""
        if not self._pgn_tracker:
            registry = self._get_registry()
            self._pgn_tracker = registry.get("pgn_tracker")
            if not self._pgn_tracker:
                self.logger.warning("PGN tracker not available, PGN analysis will be limited")
        return self._pgn_tracker
    
    def detect_motifs_in_game(self, character: Dict[str, Any], board: chess.Board, 
                            pgn_text: str, match_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect motifs in a game
        
        Args:
            character: Character dictionary
            board: Chess board
            pgn_text: PGN text of the game
            match_context: Match context dictionary
            
        Returns:
            List of detected motifs
        """
        if not self.active:
            self.logger.warning("Motif detection system not active, motifs will not be detected")
            return []
            
        try:
            character_id = character.get("id", "unknown")
            character_name = character.get("name", "Unknown")
            board_id = match_context.get("board_id", "unknown")
            
            self.logger.info("Detecting motifs for character {} on board {}".format(
                character_name, board_id))
            
            detected_motifs = []
            
            # Run PGN analysis if enabled
            if self._pgn_analysis_enabled and pgn_text:
                pgn_motifs = self._analyze_pgn(pgn_text, character, match_context)
                detected_motifs.extend(pgn_motifs)
                
                self.logger.debug("PGN analysis detected {} motifs for character {}".format(
                    len(pgn_motifs), character_name))
            
            # Run position analysis if enabled
            if self._position_analysis_enabled and board:
                position_motifs = self._analyze_position(board, character, match_context)
                detected_motifs.extend(position_motifs)
                
                self.logger.debug("Position analysis detected {} motifs for character {}".format(
                    len(position_motifs), character_name))
            
            # Run move sequence analysis if enabled
            if self._move_sequence_enabled and pgn_text and board:
                sequence_motifs = self._analyze_move_sequence(pgn_text, board, character, match_context)
                detected_motifs.extend(sequence_motifs)
                
                self.logger.debug("Move sequence analysis detected {} motifs for character {}".format(
                    len(sequence_motifs), character_name))
            
            # Sort by score and limit to max_motifs_per_game
            detected_motifs.sort(key=lambda m: m.get("score", 0), reverse=True)
            detected_motifs = detected_motifs[:self._max_motifs_per_game]
            
            # Emit motifs_detected event
            if detected_motifs:
                self._emit_event("motifs_detected", {
                    "character": character,
                    "board_id": board_id,
                    "motif_count": len(detected_motifs),
                    "motifs": detected_motifs,
                    "match_context": match_context
                })
                
                # Emit individual motif_detected events
                for motif in detected_motifs:
                    self._emit_event("motif_detected", {
                        "character": character,
                        "board_id": board_id,
                        "motif_id": motif.get("id"),
                        "motif_name": motif.get("name"),
                        "motif_score": motif.get("score", 0),
                        "motif_category": motif.get("category"),
                        "match_context": match_context
                    })
                    
                    # Update detected motifs counter
                    self.detected_motifs[motif.get("id")] += 1
                
                # Update character rStats if available
                if "rStats" in character:
                    if "MOTIFS_DETECTED" not in character["rStats"]:
                        character["rStats"]["MOTIFS_DETECTED"] = 0
                    character["rStats"]["MOTIFS_DETECTED"] += len(detected_motifs)
                    
                    # Update category-specific rStats
                    for motif in detected_motifs:
                        category = motif.get("category", "general").upper()
                        stat_name = f"{category}_MOTIFS"
                        if stat_name not in character["rStats"]:
                            character["rStats"][stat_name] = 0
                        character["rStats"][stat_name] += 1
            
            self.logger.info("Detected {} motifs for character {} on board {}".format(
                len(detected_motifs), character_name, board_id))
            
            return detected_motifs
            
        except Exception as e:
            self.logger.error("Error detecting motifs in game: {}".format(e))
            self._emit_error_event("detect_motifs_in_game", str(e), {
                "character_id": character.get("id", "unknown"),
                "board_id": match_context.get("board_id", "unknown")
            })
            return []
    
    def _analyze_pgn(self, pgn_text: str, character: Dict[str, Any], 
                   match_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Analyze PGN text for motifs
        
        Args:
            pgn_text: PGN text of the game
            character: Character dictionary
            match_context: Match context dictionary
            
        Returns:
            List of detected motifs
        """
        try:
            detected_motifs = []
            
            # Get all patterns that use pgn_analysis
            pgn_patterns = {
                motif_id: pattern for motif_id, pattern in self._motif_patterns.items()
                if pattern.get("detection_method") == "pgn_analysis" and "pgn_pattern" in pattern
            }
            
            # Skip if no patterns to check
            if not pgn_patterns:
                return []
            
            # Check each pattern against the PGN
            for motif_id, pattern in pgn_patterns.items():
                regex_pattern = pattern.get("pgn_pattern")
                if not regex_pattern:
                    continue
                    
                try:
                    # Check if pattern matches
                    if re.search(regex_pattern, pgn_text):
                        # Create motif object
                        motif = {
                            "id": motif_id,
                            "name": motif_id.replace("_", " ").title(),
                            "description": pattern.get("description", ""),
                            "score": pattern.get("score", self._min_motif_score),
                            "category": pattern.get("category", "general"),
                            "detection_method": "pgn_analysis",
                            "detected_at": datetime.datetime.now().isoformat()
                        }
                        
                        # Add to detected motifs if score meets threshold
                        if motif["score"] >= self._min_motif_score:
                            detected_motifs.append(motif)
                            
                            self.logger.debug("Detected motif {} in PGN analysis".format(motif_id))
                except re.error as e:
                    self.logger.warning("Invalid regex pattern for motif {}: {}".format(motif_id, e))
            
            return detected_motifs
            
        except Exception as e:
            self.logger.error("Error in PGN analysis: {}".format(e))
            self._emit_error_event("analyze_pgn", str(e), {
                "character_id": character.get("id", "unknown")
            })
            return []
    
    def _analyze_position(self, board: chess.Board, character: Dict[str, Any], 
                         match_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Analyze current board position for motifs
        
        Args:
            board: Chess board
            character: Character dictionary
            match_context: Match context dictionary
            
        Returns:
            List of detected motifs
        """
        try:
            detected_motifs = []
            
            # Get all patterns that use position_analysis
            position_patterns = {
                motif_id: pattern for motif_id, pattern in self._motif_patterns.items()
                if pattern.get("detection_method") == "position_analysis"
            }
            
            # Skip if no patterns to check
            if not position_patterns:
                return []
            
            # Check specific position-based motifs
            
            # Check for back rank mate
            if "back_rank_mate" in position_patterns and board.is_checkmate():
                # Determine if it's a back rank mate
                king_square = None
                back_rank_white = [chess.A1, chess.B1, chess.C1, chess.D1, chess.E1, chess.F1, chess.G1, chess.H1]
                back_rank_black = [chess.A8, chess.B8, chess.C8, chess.D8, chess.E8, chess.F8, chess.G8, chess.H8]
                
                # Find king square
                for square in chess.SQUARES:
                    piece = board.piece_at(square)
                    if piece and piece.piece_type == chess.KING:
                        if piece.color == chess.WHITE and board.turn == chess.BLACK:
                            king_square = square
                            break
                        elif piece.color == chess.BLACK and board.turn == chess.WHITE:
                            king_square = square
                            break
                
                # Check if king is on back rank
                is_back_rank_mate = False
                if king_square is not None:
                    if (king_square in back_rank_white and board.turn == chess.BLACK) or \
                       (king_square in back_rank_black and board.turn == chess.WHITE):
                        is_back_rank_mate = True
                
                if is_back_rank_mate:
                    pattern = position_patterns["back_rank_mate"]
                    motif = {
                        "id": "back_rank_mate",
                        "name": "Back Rank Mate",
                        "description": pattern.get("description", ""),
                        "score": pattern.get("score", self._min_motif_score),
                        "category": pattern.get("category", "tactical"),
                        "detection_method": "position_analysis",
                        "detected_at": datetime.datetime.now().isoformat()
                    }
                    detected_motifs.append(motif)
            
            # Check for fork
            if "fork" in position_patterns:
                # Basic fork detection (very simplified)
                # A complete implementation would check each piece and its attacks
                has_fork = False
                
                # Get player's color
                player_color = chess.WHITE  # Default to white
                character_role = character.get("role", "unknown")
                if "color" in match_context:
                    color_str = match_context.get("color", "white")
                    player_color = chess.WHITE if color_str.lower() == "white" else chess.BLACK
                
                # Check for knight forks as a simple example
                for square in chess.SQUARES:
                    piece = board.piece_at(square)
                    if piece and piece.piece_type == chess.KNIGHT and piece.color == player_color:
                        # Get all attacks from this knight
                        attacked_squares = []
                        for target in chess.SQUARES:
                            if chess.square_distance(square, target) == 2:  # Knight's move
                                # Check if square is valid attack
                                if (target > square - 17 and 
                                    abs(chess.square_file(square) - chess.square_file(target)) <= 2):
                                    attacked_pieces = 0
                                    target_piece = board.piece_at(target)
                                    if target_piece and target_piece.color != player_color:
                                        attacked_pieces += 1
                                    
                                    if attacked_pieces >= 2:
                                        has_fork = True
                                        break
                
                if has_fork:
                    pattern = position_patterns["fork"]
                    motif = {
                        "id": "fork",
                        "name": "Fork",
                        "description": pattern.get("description", ""),
                        "score": pattern.get("score", self._min_motif_score),
                        "category": pattern.get("category", "tactical"),
                        "detection_method": "position_analysis",
                        "detected_at": datetime.datetime.now().isoformat()
                    }
                    detected_motifs.append(motif)
            
            # This is a simplified implementation
            # A complete system would implement many more position analysis checks
            
            return detected_motifs
            
        except Exception as e:
            self.logger.error("Error in position analysis: {}".format(e))
            self._emit_error_event("analyze_position", str(e), {
                "character_id": character.get("id", "unknown")
            })
            return []
    
    def _analyze_move_sequence(self, pgn_text: str, board: chess.Board, 
                              character: Dict[str, Any], match_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Analyze move sequence for motifs
        
        Args:
            pgn_text: PGN text of the game
            board: Chess board
            character: Character dictionary
            match_context: Match context dictionary
            
        Returns:
            List of detected motifs
        """
        try:
            detected_motifs = []
            
            # Get all patterns that use move_sequence
            sequence_patterns = {
                motif_id: pattern for motif_id, pattern in self._motif_patterns.items()
                if pattern.get("detection_method") == "move_sequence"
            }
            
            # Skip if no patterns to check
            if not sequence_patterns:
                return []
            
            # Try to load the game from PGN
            pgn = chess.pgn.read_game(StringIO(pgn_text))
            if not pgn:
                return []
            
            # Check for sacrifice
            if "sacrifice" in sequence_patterns:
                # Simple sacrifice detection
                has_sacrifice = False
                
                # Create a new board to replay the game
                analysis_board = chess.Board()
                
                # Track piece values
                piece_values = {
                    chess.PAWN: 1,
                    chess.KNIGHT: 3,
                    chess.BISHOP: 3,
                    chess.ROOK: 5,
                    chess.QUEEN: 9,
                    chess.KING: 0  # King cannot be captured
                }
                
                # Replay the moves and check for sacrifices
                material_balance = 0
                prev_material_balance = 0
                
                for move in pgn.mainline_moves():
                    # Get the piece being moved
                    from_square = move.from_square
                    to_square = move.to_square
                    moving_piece = analysis_board.piece_at(from_square)
                    
                    # Check if it's a capture
                    captured_piece = analysis_board.piece_at(to_square)
                    
                    # Process the move
                    analysis_board.push(move)
                    
                    # Calculate material balance
                    white_material = 0
                    black_material = 0
                    
                    for square in chess.SQUARES:
                        piece = analysis_board.piece_at(square)
                        if piece:
                            value = piece_values.get(piece.piece_type, 0)
                            if piece.color == chess.WHITE:
                                white_material += value
                            else:
                                black_material += value
                    
                    # Calculate material balance from white's perspective
                    material_balance = white_material - black_material
                    
                    # Check for sacrifice - material loss followed by material gain
                    if moving_piece and captured_piece:
                        moving_value = piece_values.get(moving_piece.piece_type, 0)
                        captured_value = piece_values.get(captured_piece.piece_type, 0)
                        
                        # If voluntarily trading a higher piece for a lower piece
                        if moving_value > captured_value:
                            has_sacrifice = True
                            break
                    
                    prev_material_balance = material_balance
                
                if has_sacrifice:
                    pattern = sequence_patterns["sacrifice"]
                    motif = {
                        "id": "sacrifice",
                        "name": "Sacrifice",
                        "description": pattern.get("description", ""),
                        "score": pattern.get("score", self._min_motif_score),
                        "category": pattern.get("category", "strategic"),
                        "detection_method": "move_sequence",
                        "detected_at": datetime.datetime.now().isoformat()
                    }
                    detected_motifs.append(motif)
            
            # Check for exchange
            if "exchange" in sequence_patterns:
                # Simple exchange detection
                has_exchange = False
                
                # Create a new board to replay the game
                analysis_board = chess.Board()
                
                # Track piece values
                piece_values = {
                    chess.PAWN: 1,
                    chess.KNIGHT: 3,
                    chess.BISHOP: 3,
                    chess.ROOK: 5,
                    chess.QUEEN: 9,
                    chess.KING: 0  # King cannot be captured
                }
                
                # Replay the moves and check for exchanges
                for move in pgn.mainline_moves():
                    # Get the piece being moved
                    from_square = move.from_square
                    to_square = move.to_square
                    moving_piece = analysis_board.piece_at(from_square)
                    
                    # Check if it's a capture
                    captured_piece = analysis_board.piece_at(to_square)
                    
                    # Process the move
                    analysis_board.push(move)
                    
                    # Check for exchange - equal value piece trade
                    if moving_piece and captured_piece:
                        moving_value = piece_values.get(moving_piece.piece_type, 0)
                        captured_value = piece_values.get(captured_piece.piece_type, 0)
                        
                        # If trading pieces of equal value
                        if moving_value == captured_value and moving_value >= 3:  # Ignore pawn exchanges
                            has_exchange = True
                            break
                
                if has_exchange:
                    pattern = sequence_patterns["exchange"]
                    motif = {
                        "id": "exchange",
                        "name": "Exchange",
                        "description": pattern.get("description", ""),
                        "score": pattern.get("score", self._min_motif_score),
                        "category": pattern.get("category", "strategic"),
                        "detection_method": "move_sequence",
                        "detected_at": datetime.datetime.now().isoformat()
                    }
                    detected_motifs.append(motif)
            
            # This is a simplified implementation
            # A complete system would implement many more move sequence checks
            
            return detected_motifs
            
        except Exception as e:
            self.logger.error("Error in move sequence analysis: {}".format(e))
            self._emit_error_event("analyze_move_sequence", str(e), {
                "character_id": character.get("id", "unknown")
            })
            return []
    
    def process_match_pgns(self, match_id: str, pgn_files: List[str], 
                         characters: List[Dict[str, Any]], match_context: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Process all PGNs for a match and detect motifs
        
        Args:
            match_id: Match ID
            pgn_files: List of PGN file paths
            characters: List of characters
            match_context: Match context dictionary
            
        Returns:
            Dictionary mapping character IDs to lists of detected motifs
        """
        if not self.active:
            self.logger.warning("Motif detection system not active, motifs will not be detected")
            return {}
            
        try:
            character_motifs = {}
            
            self.logger.info("Processing {} PGN files for match {}".format(len(pgn_files), match_id))
            
            # Emit match_motif_detection_start event
            self._emit_event("match_motif_detection_start", {
                "match_id": match_id,
                "pgn_count": len(pgn_files),
                "character_count": len(characters)
            })
            
            # Create character lookup by ID
            character_lookup = {char.get("id", "unknown"): char for char in characters}
            
            # Process each PGN file
            for i, pgn_file in enumerate(pgn_files):
                try:
                    # Extract character ID and board ID from filename
                    filename = os.path.basename(pgn_file)
                    parts = filename.split("_")
                    
                    # Try to extract character and board IDs
                    character_id = None
                    board_id = None
                    
                    for part in parts:
                        if part.startswith("char") or part.startswith("c"):
                            character_id = part
                        elif part.startswith("board") or part.startswith("b") or part.startswith("game"):
                            board_id = part
                    
                    # If we couldn't extract IDs, use index
                    if not character_id:
                        character_id = f"character_{i+1}"
                    
                    if not board_id:
                        board_id = f"board_{i+1}"
                    
                    # Get character from lookup
                    character = character_lookup.get(character_id)
                    
                    # Skip if character not found
                    if not character:
                        self.logger.warning("Character {} not found for PGN {}".format(character_id, pgn_file))
                        continue
                    
                    # Read PGN file
                    with open(pgn_file, 'r') as f:
                        pgn_text = f.read()
                    
                    # Create board from PGN
                    pgn = chess.pgn.read_game(StringIO(pgn_text))
                    board = chess.Board()
                    
                    # Replay the game to the end
                    if pgn:
                        for move in pgn.mainline_moves():
                            board.push(move)
                    
                    # Update match context with board ID
                    context = match_context.copy()
                    context["board_id"] = board_id
                    
                    # Detect motifs
                    motifs = self.detect_motifs_in_game(character, board, pgn_text, context)
                    
                    # Store detected motifs
                    character_motifs[character_id] = motifs
                    
                    self.logger.info("Detected {} motifs for character {} in PGN {}".format(
                        len(motifs), character.get("name", character_id), pgn_file))
                    
                except Exception as e:
                    self.logger.error("Error processing PGN file {}: {}".format(pgn_file, e))
                    self._emit_error_event("process_pgn_file", str(e), {
                        "pgn_file": pgn_file,
                        "match_id": match_id
                    })
            
            # Emit match_motif_detection_complete event
            motif_count = sum(len(motifs) for motifs in character_motifs.values())
            self._emit_event("match_motif_detection_complete", {
                "match_id": match_id,
                "pgn_count": len(pgn_files),
                "character_count": len(characters),
                "motif_count": motif_count
            })
            
            self.logger.info("Processed {} PGN files for match {}, detected {} motifs".format(
                len(pgn_files), match_id, motif_count))
            
            return character_motifs
            
        except Exception as e:
            self.logger.error("Error processing match PGNs: {}".format(e))
            self._emit_error_event("process_match_pgns", str(e), {
                "match_id": match_id
            })
            return {}
    
    def get_motif_statistics(self) -> Dict[str, Any]:
        """Get motif detection statistics"""
        total_motifs = sum(self.detected_motifs.values())
        stats = {
            "total_motifs_detected": total_motifs,
            "motif_counts": dict(self.detected_motifs)
        }
        
        # Add percentage breakdown
        if total_motifs > 0:
            stats["motif_percentages"] = {
                motif_id: (count / total_motifs) * 100
                for motif_id, count in self.detected_motifs.items()
            }
        
        return stats
    
    def _emit_event(self, event_name: str, data: Dict[str, Any]) -> None:
        """Emit an event with the given name and data"""
        event_system = self._get_event_system()
        if event_system:
            try:
                event_system.emit(event_name, data)
            except Exception as e:
                self.logger.error("Error emitting event {}: {}".format(event_name, e))
    
    def _emit_error_event(self, function_name: str, error_message: str, 
                         context: Optional[Dict[str, Any]] = None) -> None:
        """Emit a system error event"""
        event_system = self._get_event_system()
        if event_system:
            try:
                error_data = {
                    "system": self.name,
                    "function": function_name,
                    "error": error_message,
                    "timestamp": datetime.datetime.now().isoformat()
                }
                
                if context:
                    error_data["context"] = context
                    
                event_system.emit("system_error", error_data)
            except Exception as e:
                self.logger.error("Error emitting error event: {}".format(e))
    
    def save_persistent_data(self) -> None:
        """Save persistent data for motif detection system"""
        try:
            # Save motif statistics
            data_dir = self.config.get("paths.data_dir", "data")
            stats_dir = os.path.join(data_dir, "statistics")
            os.makedirs(stats_dir, exist_ok=True)
            
            stats_file = os.path.join(stats_dir, "motif_statistics.json")
            with open(stats_file, 'w') as f:
                json.dump({
                    "motif_statistics": self.get_motif_statistics(),
                    "timestamp": datetime.datetime.now().isoformat()
                }, f, indent=2)
                
            self.logger.info("Motif statistics saved")
        except Exception as e:
            self.logger.error("Error saving persistent data: {}".format(e))
            self._emit_error_event("save_persistent_data", str(e))
    
    def export_state(self) -> Dict[str, Any]:
        """Export state for backup"""
        return {
            "detected_motifs": dict(self.detected_motifs),
            "active": self.active
        }
