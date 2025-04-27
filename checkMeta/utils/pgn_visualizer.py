"""
META Fantasy League Simulator - PGN Visualization Utilities
Generate text-based visualizations of chess games from PGN files
"""

import os
import chess
import chess.pgn
import datetime
from typing import Dict, List, Any, Optional

def generate_ascii_board(board):
    """
    Generate ASCII representation of a chess board
    
    Args:
        board: Chess board position
        
    Returns:
        str: ASCII board representation
    """
    # Get board as Unicode string and convert to ASCII
    unicode_str = str(board)
    
    # Replace Unicode characters with ASCII
    replacements = {
        '♔': 'K', '♕': 'Q', '♖': 'R', '♗': 'B', '♘': 'N', '♙': 'P',
        '♚': 'k', '♛': 'q', '♜': 'r', '♝': 'b', '♞': 'n', '♟': 'p',
        '·': '.'
    }
    
    for unicode_char, ascii_char in replacements.items():
        unicode_str = unicode_str.replace(unicode_char, ascii_char)
    
    # Return the converted string
    return unicode_str

def generate_game_report(pgn_file, game_index=0):
    """
    Generate a text report of a specific game from a PGN file
    
    Args:
        pgn_file: Path to PGN file
        game_index: Index of game to report (0 = first game)
        
    Returns:
        str: Text report of the game
    """
    # Open the PGN file
    with open(pgn_file) as f:
        # Skip to the requested game
        for _ in range(game_index):
            if not chess.pgn.read_game(f):
                return "Game not found"
        
        # Read the requested game
        game = chess.pgn.read_game(f)
        
        if not game:
            return "Game not found"
        
        # Extract headers
        white = game.headers.get("White", "Unknown")
        black = game.headers.get("Black", "Unknown")
        result = game.headers.get("Result", "*")
        
        # Extract custom headers
        team = game.headers.get("WhiteTeam", "Unknown")
        role = game.headers.get("WhiteRole", "Unknown")
        division = game.headers.get("WhiteDivision", "Unknown")
        
        initial_hp = game.headers.get("InitialHP", "100")
        final_hp = game.headers.get("FinalHP", "0")
        initial_stamina = game.headers.get("InitialStamina", "100")
        final_stamina = game.headers.get("FinalStamina", "0")
        
        # Format result
        result_text = "???"
        if result == "1-0":
            result_text = "White wins"
        elif result == "0-1":
            result_text = "Black wins"
        elif result == "1/2-1/2":
            result_text = "Draw"
        
        # Generate report header
        report = f"""
=== Game Report: {white} vs {black} ===
Role: {role}
Team: {team}
Division: {division}
Result: {result_text}

Health: {initial_hp} → {final_hp}
Stamina: {initial_stamina} → {final_stamina}

MOVES:
"""
        
        # Generate move list
        board = chess.Board()
        move_number = 1
        
        for node in game.mainline():
            if board.turn == chess.WHITE:
                report += f"{move_number}. "
                move_number += 1
            
            move = node.move
            
            # Check for special moves
            move_annotation = ""
            if board.is_capture(move):
                captured_piece = board.piece_at(move.to_square)
                piece_symbol = captured_piece.symbol() if captured_piece else "?"
                move_annotation = f"x{piece_symbol}"
            elif board.is_check(move):
                move_annotation = "+"
            
            # Add the move
            move_san = board.san(move)
            report += f"{move_san}{move_annotation} "
            
            # New line every 5 full moves
            if move_number % 5 == 0 and board.turn == chess.BLACK:
                report += "\n"
            
            # Apply the move
            board.push(move)
        
        # Add final board position
        report += "\n\nFinal Position:\n"
        report += generate_ascii_board(board)
        
        return report

def visualize_game_flow(pgn_file, game_index=0):
    """
    Visualize the flow of a game with material balance
    
    Args:
        pgn_file: Path to PGN file
        game_index: Index of game to visualize
        
    Returns:
        str: Text visualization of game flow
    """
    # Open the PGN file
    with open(pgn_file) as f:
        # Skip to the requested game
        for _ in range(game_index):
            if not chess.pgn.read_game(f):
                return "Game not found"
        
        # Read the requested game
        game = chess.pgn.read_game(f)
        
        if not game:
            return "Game not found"
        
        # Extract headers
        white = game.headers.get("White", "Unknown")
        black = game.headers.get("Black", "Unknown")
        
        # Function to calculate material value
        def calculate_material(board):
            """Calculate material value for white"""
            values = {
                chess.PAWN: 1,
                chess.KNIGHT: 3,
                chess.BISHOP: 3,
                chess.ROOK: 5,
                chess.QUEEN: 9
            }
            
            white_material = 0
            black_material = 0
            
            for piece_type in values:
                white_pieces = len(board.pieces(piece_type, chess.WHITE))
                black_pieces = len(board.pieces(piece_type, chess.BLACK))
                white_material += values[piece_type] * white_pieces
                black_material += values[piece_type] * black_pieces
            
            return white_material, black_material
        
        # Track material balance through the game
        board = chess.Board()
        moves = []
        white_material = []
        black_material = []
        
        # Get initial material
        w_mat, b_mat = calculate_material(board)
        white_material.append(w_mat)
        black_material.append(b_mat)
        
        # Process moves
        for node in game.mainline():
            move = node.move
            move_san = board.san(move)
            moves.append(move_san)
            
            # Apply move
            board.push(move)
            
            # Calculate new material
            w_mat, b_mat = calculate_material(board)
            white_material.append(w_mat)
            black_material.append(b_mat)
        
        # Generate visualization
        viz = f"""
=== Game Flow: {white} vs {black} ===

Material Balance Over Time:
"""
        
        # Generate material balance chart
        max_material = max(max(white_material), max(black_material))
        scale = 40 / max_material if max_material > 0 else 1
        
        for i, (w_mat, b_mat) in enumerate(zip(white_material, black_material)):
            # Skip initial position
            if i == 0:
                continue
                
            # Create bar chart representing material balance
            w_bar = "W" * int(w_mat * scale)
            b_bar = "B" * int(b_mat * scale)
            
            # Calculate advantage
            advantage = w_mat - b_mat
            adv_text = ""
            if advantage > 0:
                adv_text = f"+{advantage} White"
            elif advantage < 0:
                adv_text = f"+{-advantage} Black"
            
            # Add move number and move
            move_num = (i // 2) + 1
            half_move = i % 2
            
            if half_move == 1:
                move_text = f"{move_num}. ... {moves[i-1]}"
            else:
                move_text = f"{move_num}. {moves[i-1]}"
            
            # Format chart line
            viz += f"{move_text:15} {w_bar}{b_bar} {adv_text}\n"
        
        return viz

def generate_position_report(fen, move_options=3):
    """
    Generate a text report analyzing a specific position
    
    Args:
        fen: FEN string representation of position
        move_options: Number of candidate moves to suggest
        
    Returns:
        str: Text analysis of the position
    """
    # Create board from FEN
    try:
        board = chess.Board(fen)
    except ValueError:
        return "Invalid FEN position"
    
    # Generate board representation
    board_text = generate_ascii_board(board)
    
    # Generate position report
    report = f"""
=== Position Analysis ===

FEN: {fen}

{board_text}

"""
    
    # Add turn information
    if board.turn == chess.WHITE:
        report += "White to move\n"
    else:
        report += "Black to move\n"
    
    # Add check information
    if board.is_check():
        report += "Position is in CHECK\n"
    
    # Add material count
    piece_symbols = ['P', 'N', 'B', 'R', 'Q', 'K', 'p', 'n', 'b', 'r', 'q', 'k']
    piece_counts = {s: 0 for s in piece_symbols}
    
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            piece_counts[piece.symbol()] += 1
    
    white_material = (
        piece_counts['P'] * 1 +
        piece_counts['N'] * 3 +
        piece_counts['B'] * 3 +
        piece_counts['R'] * 5 +
        piece_counts['Q'] * 9
    )
    
    black_material = (
        piece_counts['p'] * 1 +
        piece_counts['n'] * 3 +
        piece_counts['b'] * 3 +
        piece_counts['r'] * 5 +
        piece_counts['q'] * 9
    )
    
    report += f"\nMaterial: White {white_material} vs Black {black_material}\n"
    
    # List available moves
    report += f"\nLegal moves: {board.legal_moves.count()}\n"
    
    # Suggest candidate moves if Stockfish available
    # (This is normally replaced with actual engine suggestions)
    report += "\nCandidate moves:\n"
    
    # Placeholder for move suggestions
    legal_moves = list(board.legal_moves)
    if legal_moves:
        for i in range(min(move_options, len(legal_moves))):
            move = legal_moves[i]
            move_san = board.san(move)
            report += f"  {i+1}. {move_san}\n"
    else:
        report += "  No legal moves available\n"
    
    return report

def extract_openings_from_pgn(pgn_file, depth=4):
    """
    Extract and analyze openings from a PGN file
    
    Args:
        pgn_file: Path to PGN file
        depth: Number of moves to consider for openings
        
    Returns:
        dict: Dictionary of openings and their frequencies
    """
    # Open the PGN file
    openings = {}
    
    with open(pgn_file) as f:
        game = chess.pgn.read_game(f)
        
        while game:
            # Extract openings
            board = chess.Board()
            opening_moves = []
            
            # Get first 'depth' moves (or fewer if the game is shorter)
            for i, move in enumerate(game.mainline_moves()):
                if i >= depth * 2:  # Both sides count as moves
                    break
                
                move_san = board.san(move)
                opening_moves.append(move_san)
                board.push(move)
            
            # Combine into a string representation
            if opening_moves:
                opening_str = " ".join(opening_moves)
                openings[opening_str] = openings.get(opening_str, 0) + 1
            
            # Read next game
            game = chess.pgn.read_game(f)
    
    return openings

def summarize_pgn_file(pgn_file):
    """
    Generate a summary of a PGN file with multiple games
    
    Args:
        pgn_file: Path to PGN file
        
    Returns:
        str: Summary of the PGN file
    """
    # Check if file exists
    if not os.path.exists(pgn_file):
        return f"File not found: {pgn_file}"
    
    # Open the PGN file
    game_count = 0
    results = {"1-0": 0, "0-1": 0, "1/2-1/2": 0, "*": 0}
    white_players = {}
    roles = {}
    move_counts = []
    
    with open(pgn_file) as f:
        game = chess.pgn.read_game(f)
        
        while game:
            game_count += 1
            
            # Count result
            result = game.headers.get("Result", "*")
            results[result] = results.get(result, 0) + 1
            
            # Track white player
            white = game.headers.get("White", "Unknown")
            white_players[white] = white_players.get(white, 0) + 1
            
            # Track role
            role = game.headers.get("WhiteRole", "Unknown")
            roles[role] = roles.get(role, 0) + 1
            
            # Count moves
            move_count = len(list(game.mainline_moves()))
            move_counts.append(move_count)
            
            # Read next game
            game = chess.pgn.read_game(f)
    
    # Generate summary
    avg_moves = sum(move_counts) / len(move_counts) if move_counts else 0
    
    summary = f"""
=== PGN File Summary: {os.path.basename(pgn_file)} ===

Games: {game_count}

Results:
- White Wins: {results["1-0"]}
- Black Wins: {results["0-1"]}
- Draws: {results["1/2-1/2"]}
- Incomplete: {results["*"]}

Move Statistics:
- Average Moves: {avg_moves:.1f}
- Shortest Game: {min(move_counts) if move_counts else 0} moves
- Longest Game: {max(move_counts) if move_counts else 0} moves

Characters:
"""
    
    # Add character breakdown
    for char, count in sorted(white_players.items(), key=lambda x: x[1], reverse=True):
        summary += f"- {char}: {count} games\n"
    
    # Add role breakdown
    summary += "\nRoles:\n"
    for role, count in sorted(roles.items(), key=lambda x: x[1], reverse=True):
        summary += f"- {role}: {count} games\n"
    
    # Extract and add opening analysis
    summary += "\nCommon Openings:\n"
    openings = extract_openings_from_pgn(pgn_file)
    
    for opening, count in sorted(openings.items(), key=lambda x: x[1], reverse=True)[:5]:
        summary += f"- {opening}: {count} games\n"
    
    return summary