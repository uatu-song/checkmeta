"""
Chess engine integration for META League Simulator
"""

import chess
import chess.engine
import os
import random
from typing import Dict, Any, Optional, List, Tuple
from ..models.character import Character

class ChessEngine:
    """System for integrating chess mechanics into the simulation"""
    
    def __init__(self, stockfish_path: str = "/usr/local/bin/stockfish"):
        """Initialize chess engine"""
        self.stockfish_path = stockfish_path
        
        # Check if Stockfish is available
        if not os.path.exists(stockfish_path):
            print(f"Warning: Stockfish not found at {stockfish_path}")
            self.stockfish_available = False
        else:
            self.stockfish_available = True
            print(f"Stockfish found at {stockfish_path}")
    
    def create_board(self) -> chess.Board:
        """Create a new chess board"""
        return chess.Board()
    
    def apply_opening(self, board: chess.Board, role: str, opening_config: Dict[str, List[str]]) -> chess.Board:
        """Apply role-based opening moves to a chess board"""
        if role in opening_config:
            # Choose a random opening for this role
            opening_sequence = random.choice(opening_config[role])
            moves = opening_sequence.split()
            
            # Apply opening moves
            for move_str in moves:
                try:
                    if len(move_str) == 4 and move_str[0] in 'abcdefgh' and move_str[2] in 'abcdefgh':
                        # This is a UCI move
                        move = chess.Move.from_uci(move_str)
                    else:
                        # This is SAN notation
                        move = board.parse_san(move_str)
                    
                    if move in board.legal_moves:
                        board.push(move)
                except Exception as e:
                    continue  # Skip invalid moves
        
        return board
    
    def select_move(self, board: chess.Board, character: Character) -> Optional[chess.Move]:
        """Select a move for a character based on their stats and traits"""
        if not self.stockfish_available:
            # Fallback to random move selection
            legal_moves = list(board.legal_moves)
            return random.choice(legal_moves) if legal_moves else None
        
        try:
            # Determine search depth based on character stats
            base_depth = min(max(2, character.get_attribute('SPD') // 2), 10)
            
            # Adjust depth based on stamina (lower stamina = lower depth)
            stamina_factor = max(0.5, character.stamina / 100)
            adjusted_depth = max(1, int(base_depth * stamina_factor))
            
            # Open Stockfish engine
            with chess.engine.SimpleEngine.popen_uci(self.stockfish_path) as engine:
                # Add thinking time based on character's Focus/Speed
                thinking_ms = character.get_attribute('FS') * 50
                
                # Get analysis from Stockfish
                limit = chess.engine.Limit(depth=adjusted_depth, time=thinking_ms/1000.0)
                
                # Determine move quality based on character stats and traits
                quality_roll = random.random()
                quality_boost = (character.get_attribute('STR') + character.get_attribute('FS')) / 20.0
                
                # Apply modifiers from character
                # Morale modifier
                if hasattr(character, 'morale_modifiers') and character.morale_modifiers:
                    morale_combat = character.morale_modifiers.get("combat_bonus", 0)
                    quality_boost += morale_combat / 100.0
                
                # Team synergy modifier
                if hasattr(character, 'team_synergy') and character.team_synergy:
                    synergy_combat = character.team_synergy.get("combat_bonus", 0)
                    quality_boost += synergy_combat / 100.0
                
                quality_roll += quality_boost
                
                # Select move based on quality roll
                if quality_roll > 0.9:  # Brilliant move
                    result = engine.play(board, limit)
                    return result.move
                elif quality_roll > 0.7:  # Good move
                    # Get top 3 moves and pick randomly from them
                    analysis = engine.analyse(board, limit, multipv=3)
                    if analysis:
                        moves = [entry["pv"][0] for entry in analysis if "pv" in entry and entry["pv"]]
                        return random.choice(moves) if moves else None
                elif quality_roll > 0.4:  # Decent move
                    # Get top 5 moves and pick randomly from them
                    analysis = engine.analyse(board, limit, multipv=5)
                    if analysis:
                        moves = [entry["pv"][0] for entry in analysis if "pv" in entry and entry["pv"]]
                        return random.choice(moves) if moves else None
                else:  # Suboptimal move
                    # Pick a random legal move with some bias for non-terrible moves
                    legal_moves = list(board.legal_moves)
                    if legal_moves:
                        # Try to avoid obvious blunders
                        if random.random() > 0.3:  # 70% chance of avoiding obvious blunders
                            info = engine.analyse(board, chess.engine.Limit(depth=1))
                            if "pv" in info and info["pv"]:
                                safe_move = info["pv"][0]
                                return safe_move
                        return random.choice(legal_moves)
        
        except Exception as e:
            print(f"Stockfish error: {e}")
            # Fallback to random move selection
            legal_moves = list(board.legal_moves)
            return random.choice(legal_moves) if legal_moves else None
        
        # Final fallback
        legal_moves = list(board.legal_moves)
        return random.choice(legal_moves) if legal_moves else None
    
    def calculate_material(self, board: chess.Board) -> int:
        """Calculate total material value on the chess board"""
        material = 0
        
        # Piece values (standard chess values)
        values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9
        }
        
        # Sum up material for white pieces
        for piece_type in values:
            material += len(board.pieces(piece_type, chess.WHITE)) * values[piece_type]
        
        return material
    
    def determine_game_result(self, board: chess.Board, character: Character) -> str:
        """Determine the result of a chess game"""
        # If character is KO'd or dead, they lose
        if character.is_ko or character.is_dead:
            return "loss"
            
        # Check chess rules for game over
        if board.is_checkmate():
            return "win" if board.turn == chess.BLACK else "loss"
        elif board.is_stalemate() or board.is_insufficient_material():
            return "draw"
        
        # Otherwise, use material advantage to estimate result
        material = self.calculate_material(board)
        starting_material = 39  # Standard starting material
        
        if material > starting_material * 0.7:
            return "win"
        elif material < starting_material * 0.3:
            return "loss"
        else:
            return "draw"

###############################
