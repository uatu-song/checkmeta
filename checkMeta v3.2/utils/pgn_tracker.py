"""
META Fantasy League Simulator - PGN Tracking System
Records and manages chess games in PGN (Portable Game Notation) format
"""

import os
import chess
import chess.pgn
import datetime
import io
from typing import Dict, List, Any, Optional, Union

class PGNTracker:
    """System for recording chess games in PGN format with character metadata"""
    
    def __init__(self, output_dir="results/pgn"):
        """Initialize the PGN tracker
        
        Args:
            output_dir: Directory to store PGN files
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.game_count = 0
        self.current_match = None
    
    def start_match(self, team_a_name, team_b_name, team_a_id, team_b_id, day=1):
        """Start tracking a new match
        
        Args:
            team_a_name: Name of team A
            team_b_name: Name of team B
            team_a_id: ID of team A
            team_b_id: ID of team B
            day: Match day number
        """
        self.current_match = {
            "team_a_name": team_a_name,
            "team_b_name": team_b_name,
            "team_a_id": team_a_id,
            "team_b_id": team_b_id,
            "day": day,
            "date": datetime.datetime.now(),
            "games": []
        }
        self.game_count = 0
    
    def record_game(self, board, character_data, opponent_name="AI Opponent", result="unknown"):
        """Record a chess game in PGN format
        
        Args:
            board: Chess board with move history
            character_data: Character data dictionary
            opponent_name: Name of opponent (default: "AI Opponent")
            result: Game result ("win", "loss", "draw", or "unknown")
            
        Returns:
            str: PGN text of the recorded game
        """
        if not self.current_match:
            raise ValueError("No active match. Call start_match() first.")
        
        # Create a new game
        game = chess.pgn.Game()
        
        # Set headers
        game.headers["Event"] = f"META Fantasy League - Day {self.current_match['day']}"
        game.headers["Site"] = "META League Arena"
        game.headers["Date"] = self.current_match["date"].strftime("%Y.%m.%d")
        game.headers["Round"] = str(self.game_count + 1)
        game.headers["White"] = character_data.get("name", "Unknown")
        game.headers["Black"] = opponent_name
        
        # Set result based on game outcome
        if result == "win":
            game.headers["Result"] = "1-0"
        elif result == "loss":
            game.headers["Result"] = "0-1"
        elif result == "draw":
            game.headers["Result"] = "1/2-1/2"
        else:
            game.headers["Result"] = "*"  # Ongoing or unknown
        
        # Add META-specific headers
        game.headers["WhiteTeam"] = character_data.get("team_name", "Unknown Team")
        game.headers["WhiteRole"] = character_data.get("role", "Unknown")
        game.headers["WhiteDivision"] = character_data.get("division", "Unknown")
        
        # Add custom tags for easier analysis
        game.headers["CharacterID"] = character_data.get("id", "Unknown")
        game.headers["TeamID"] = character_data.get("team_id", "Unknown")
        
        # Add initial character stats
        game.headers["InitialHP"] = str(100)
        game.headers["InitialStamina"] = str(100)
        game.headers["FinalHP"] = str(character_data.get("HP", 0))
        game.headers["FinalStamina"] = str(character_data.get("stamina", 0))
        
        # Create comment with character information
        char_info = f"Character: {character_data.get('name', 'Unknown')}, "
        char_info += f"Role: {character_data.get('role', 'Unknown')}, "
        char_info += f"Team: {character_data.get('team_name', 'Unknown')}"
        
        game.comment = char_info
        
        # Add moves from board history
        node = game
        for move in board.move_stack:
            node = node.add_variation(move)
        
        # Convert to PGN text
        pgn_string = io.StringIO()
        exporter = chess.pgn.FileExporter(pgn_string)
        game.accept(exporter)
        pgn_text = pgn_string.getvalue()
        
        # Store game in current match
        self.current_match["games"].append({
            "character_id": character_data.get("id", "Unknown"),
            "character_name": character_data.get("name", "Unknown"),
            "pgn": pgn_text,
            "result": result
        })
        
        self.game_count += 1
        
        return pgn_text
    
    def save_match_pgn(self, filename=None):
        """Save all games from the current match to a PGN file
        
        Args:
            filename: Optional filename override
            
        Returns:
            str: Path to saved PGN file
        """
        if not self.current_match:
            raise ValueError("No active match to save")
        
        # Generate default filename if not specified
        if not filename:
            team_a_id = self.current_match["team_a_id"]
            team_b_id = self.current_match["team_b_id"]
            date_str = self.current_match["date"].strftime("%Y%m%d")
            filename = f"day{self.current_match['day']}_{team_a_id}_vs_{team_b_id}_{date_str}.pgn"
        
        # Ensure the filename has .pgn extension
        if not filename.endswith(".pgn"):
            filename += ".pgn"
        
        # Create full path
        file_path = os.path.join(self.output_dir, filename)
        
        # Write all games to file
        with open(file_path, "w") as pgn_file:
            for game in self.current_match["games"]:
                pgn_file.write(game["pgn"])
                pgn_file.write("\n\n")  # Add spacing between games
        
        print(f"Saved {self.game_count} games to {file_path}")
        
        return file_path
    
    def record_match_games(self, team_a, team_a_boards, team_b, team_b_boards, match_context):
        """Record PGN files for all characters in a match
        
        Args:
            team_a: List of team A characters
            team_a_boards: List of team A chess boards
            team_b: List of team B characters
            team_b_boards: List of team B chess boards
            match_context: Match context information
            
        Returns:
            str: Path to saved PGN file
        """
        # Start tracking the match
        self.start_match(
            team_a_name=match_context["team_a_name"],
            team_b_name=match_context["team_b_name"],
            team_a_id=match_context["team_a_id"],
            team_b_id=match_context["team_b_id"],
            day=match_context.get("day", 1)
        )
        
        # Record all active boards for team A
        for char, board in zip(team_a, team_a_boards):
            if char.get("is_active", True):
                # Determine result
                result = "unknown"
                if "is_ko" in char and char["is_ko"]:
                    result = "loss"
                elif "result" in char:
                    result = char["result"]
                
                self.record_game(board, char, opponent_name=f"{match_context['team_b_name']} AI", result=result)
        
        # Record all active boards for team B
        for char, board in zip(team_b, team_b_boards):
            if char.get("is_active", True):
                # Determine result
                result = "unknown"
                if "is_ko" in char and char["is_ko"]:
                    result = "loss"
                elif "result" in char:
                    result = char["result"]
                
                self.record_game(board, char, opponent_name=f"{match_context['team_a_name']} AI", result=result)
        
        # Save to file
        return self.save_match_pgn()
    
    def export_pgn_statistics(self, match_pgn_path=None):
        """Export statistics about the recorded games
        
        Args:
            match_pgn_path: Optional path to a specific PGN file to analyze
            
        Returns:
            dict: Statistics about the games
        """
        stats = {
            "total_games": self.game_count,
            "games_by_result": {"win": 0, "loss": 0, "draw": 0, "unknown": 0},
            "average_moves": 0,
            "openings": {},
            "move_frequency": {}
        }
        
        # If a specific file is provided, analyze it
        if match_pgn_path and os.path.exists(match_pgn_path):
            with open(match_pgn_path) as pgn_file:
                games = []
                game = chess.pgn.read_game(pgn_file)
                while game:
                    games.append(game)
                    game = chess.pgn.read_game(pgn_file)
                
                stats["total_games"] = len(games)
                
                # Analyze each game
                total_moves = 0
                for game in games:
                    # Count result
                    result = game.headers.get("Result", "*")
                    if result == "1-0":
                        stats["games_by_result"]["win"] += 1
                    elif result == "0-1":
                        stats["games_by_result"]["loss"] += 1
                    elif result == "1/2-1/2":
                        stats["games_by_result"]["draw"] += 1
                    else:
                        stats["games_by_result"]["unknown"] += 1
                    
                    # Count moves
                    moves = list(game.mainline_moves())
                    total_moves += len(moves)
                    
                    # Analyze opening (first 4 moves)
                    opening = []
                    for i, move in enumerate(moves[:4]):
                        board = chess.Board()
                        for prev_move in moves[:i]:
                            board.push(prev_move)
                        
                        san = board.san(move)
                        opening.append(san)
                    
                    opening_str = " ".join(opening)
                    stats["openings"][opening_str] = stats["openings"].get(opening_str, 0) + 1
                    
                    # Analyze move frequency
                    board = chess.Board()
                    for move in moves:
                        san = board.san(move)
                        stats["move_frequency"][san] = stats["move_frequency"].get(san, 0) + 1
                        board.push(move)
                
                # Calculate average moves
                if stats["total_games"] > 0:
                    stats["average_moves"] = total_moves / stats["total_games"]
        
        # If no file specified, use current match data
        elif self.current_match:
            stats["total_games"] = self.game_count
            
            for game_data in self.current_match["games"]:
                result = game_data["result"]
                stats["games_by_result"][result] += 1
        
        return stats
    
    def analyze_character_games(self, character_id, pgn_files=None):
        """Analyze games for a specific character
        
        Args:
            character_id: ID of character to analyze
            pgn_files: Optional list of PGN file paths to analyze (if None, uses all files in output_dir)
            
        Returns:
            dict: Statistics about the character's games
        """
        stats = {
            "character_id": character_id,
            "total_games": 0,
            "wins": 0,
            "losses": 0,
            "draws": 0,
            "avg_moves": 0,
            "avg_hp_loss": 0,
            "favorite_opening": None,
            "most_common_moves": [],
            "most_captured_piece": None
        }
        
        # Determine files to analyze
        if pgn_files is None:
            pgn_files = [os.path.join(self.output_dir, f) for f in os.listdir(self.output_dir) if f.endswith(".pgn")]
        
        total_moves = 0
        total_hp_loss = 0
        openings = {}
        move_counts = {}
        capture_counts = {"P": 0, "N": 0, "B": 0, "R": 0, "Q": 0}
        
        # Analyze each file
        for pgn_file_path in pgn_files:
            with open(pgn_file_path) as pgn_file:
                game = chess.pgn.read_game(pgn_file)
                
                while game:
                    # Check if this game belongs to the character
                    if game.headers.get("CharacterID") == character_id:
                        stats["total_games"] += 1
                        
                        # Track result
                        result = game.headers.get("Result")
                        if result == "1-0":
                            stats["wins"] += 1
                        elif result == "0-1":
                            stats["losses"] += 1
                        elif result == "1/2-1/2":
                            stats["draws"] += 1
                        
                        # Track HP loss
                        try:
                            initial_hp = float(game.headers.get("InitialHP", 100))
                            final_hp = float(game.headers.get("FinalHP", 0))
                            hp_loss = initial_hp - final_hp
                            total_hp_loss += hp_loss
                        except:
                            pass
                        
                        # Track moves
                        board = chess.Board()
                        moves = list(game.mainline_moves())
                        total_moves += len(moves)
                        
                        # Analyze opening
                        opening_moves = " ".join([board.san(move) for move in moves[:4]])
                        openings[opening_moves] = openings.get(opening_moves, 0) + 1
                        
                        # Track move frequency and captures
                        for move in moves:
                            san = board.san(move)
                            
                            # Count move
                            move_counts[san] = move_counts.get(san, 0) + 1
                            
                            # Check if capture
                            if board.is_capture(move):
                                # Determine captured piece
                                to_square = move.to_square
                                piece = board.piece_at(to_square)
                                
                                if piece:
                                    piece_symbol = piece.symbol().upper()
                                    if piece_symbol in capture_counts:
                                        capture_counts[piece_symbol] += 1
                            
                            # Apply move
                            board.push(move)
                    
                    # Read next game
                    game = chess.pgn.read_game(pgn_file)
        
        # Calculate averages
        if stats["total_games"] > 0:
            stats["avg_moves"] = total_moves / stats["total_games"]
            stats["avg_hp_loss"] = total_hp_loss / stats["total_games"]
        
        # Find favorite opening
        if openings:
            stats["favorite_opening"] = max(openings.items(), key=lambda x: x[1])[0]
        
        # Find most common moves
        if move_counts:
            sorted_moves = sorted(move_counts.items(), key=lambda x: x[1], reverse=True)
            stats["most_common_moves"] = [move for move, count in sorted_moves[:5]]
        
        # Find most captured piece
        if any(capture_counts.values()):
            stats["most_captured_piece"] = max(capture_counts.items(), key=lambda x: x[1])[0]
        
        return stats