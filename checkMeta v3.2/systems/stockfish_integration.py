"""
META Fantasy League - Stockfish Integration
Handles chess move selection using the Stockfish engine
"""

import os
import random
import chess
import chess.engine
from typing import Dict, Any, Optional

class StockfishIntegration:
    """System for integrating Stockfish chess engine for move selection"""
    
    def __init__(self, stockfish_path=None):
        """Initialize Stockfish integration
        
        Args:
            stockfish_path: Path to Stockfish executable
        """
        self.stockfish_path = stockfish_path
        self.stockfish_available = False
        self.activate()
    
    def activate(self):
        """Activate Stockfish integration
        
        Returns:
            bool: Activation success status
        """
        try:
            # Check if path is set
            if not self.stockfish_path:
                # Try to find Stockfish in common locations
                common_paths = [
                    "/usr/local/bin/stockfish",
                    "/usr/bin/stockfish",
                    "C:/Program Files/Stockfish/stockfish.exe",
                    "stockfish"  # Relies on PATH environment variable
                ]
                
                for path in common_paths:
                    if os.path.exists(path):
                        self.stockfish_path = path
                        break
            
            # Check if we found Stockfish
            if not self.stockfish_path:
                print("Warning: Stockfish not found. Using fallback move selection.")
                self.stockfish_available = False
                return False
            
            # Try to initialize Stockfish
            try:
                engine = chess.engine.SimpleEngine.popen_uci(self.stockfish_path)
                engine.quit()  # Just testing, close it right away
                self.stockfish_available = True
                print(f"Stockfish integration activated at {self.stockfish_path}")
                return True
            except Exception as e:
                print(f"Error initializing Stockfish: {e}")
                self.stockfish_available = False
                return False
                
        except Exception as e:
            print(f"Error activating Stockfish integration: {e}")
            self.stockfish_available = False
            return False
    
    def select_move(self, board, character):
        """Select a move using Stockfish with character traits influencing choice
        
        Args:
            board: Chess board to select move for
            character: Character making the move
            
        Returns:
            Move: Selected chess move
        """
        if not self.stockfish_available:
            # Fall back to random move selection
            return self._select_move_random(board)
        
        try:
            # Determine analysis depth based on character attributes
            base_depth = min(max(2, character.get("aFS", 5) // 2), 10)
            
            # Adjust depth based on stamina (lower stamina = lower depth)
            stamina_factor = max(0.5, character.get("stamina", 100) / 100)
            adjusted_depth = max(1, int(base_depth * stamina_factor))
            
            # Initialize Stockfish engine
            with chess.engine.SimpleEngine.popen_uci(self.stockfish_path) as engine:
                # Set thinking time based on character's Focus/Speed
                thinking_ms = character.get("aFS", 5) * 50
                
                # Set limit object
                limit = chess.engine.Limit(depth=adjusted_depth, time=thinking_ms/1000.0)
                
                # Get trait-influenced decision quality
                decision_quality = self._calculate_decision_quality(character)
                
                # Select move based on decision quality
                if decision_quality > 0.9:  # Excellent move
                    # Get best move directly
                    result = engine.play(board, limit)
                    return result.move
                elif decision_quality > 0.7:  # Good move
                    # Get top 3 moves and pick randomly
                    analysis = engine.analyse(board, limit, multipv=3)
                    if analysis:
                        moves = [entry["pv"][0] for entry in analysis if "pv" in entry and entry["pv"]]
                        return random.choice(moves) if moves else None
                elif decision_quality > 0.4:  # Average move
                    # Get top 5 moves and pick randomly
                    analysis = engine.analyse(board, limit, multipv=5)
                    if analysis:
                        moves = [entry["pv"][0] for entry in analysis if "pv" in entry and entry["pv"]]
                        return random.choice(moves) if moves else None
                else:  # Below average move
                    # Pick a random legal move with some bias towards non-terrible moves
                    legal_moves = list(board.legal_moves)
                    if legal_moves:
                        # Try to avoid obvious blunders
                        if random.random() > 0.3:  # 70% chance to avoid obvious blunders
                            info = engine.analyse(board, chess.engine.Limit(depth=1))
                            if "pv" in info and info["pv"]:
                                safe_move = info["pv"][0]
                                return safe_move
                        
                        return random.choice(legal_moves)
        except Exception as e:
            print(f"Error selecting move with Stockfish: {e}")
            # Fall back to random move selection
            return self._select_move_random(board)
        
        # Final fallback
        return self._select_move_random(board)
    
    def _select_move_random(self, board):
        """Select a random legal move as fallback
        
        Args:
            board: Chess board
            
        Returns:
            Move: Selected chess move
        """
        legal_moves = list(board.legal_moves)
        return random.choice(legal_moves) if legal_moves else None
    
    def _calculate_decision_quality(self, character):
        """Calculate decision quality based on character attributes and state
        
        Args:
            character: Character making the decision
            
        Returns:
            float: Decision quality (0-1)
        """
        # Base quality on Focus/Speed and Willpower
        base_quality = (character.get("aFS", 5) + character.get("aWIL", 5)) / 20.0
        
        # Apply stamina factor
        stamina = character.get("stamina", 100)
        stamina_factor = max(0.6, stamina / 100)  # 60% minimum
        
        # Apply additional factors...
        
        # Clamp to valid range
        return max(0.1, min(base_quality * stamina_factor, 0.99))