# pgn_recorder.py
# Records chess games from the simulation in PGN format

import chess.pgn
import io
import os
import datetime

def record_game_to_pgn(board, character_name, team_name, team_id, character_id, role, result="unknown"):
    """
    Converts a chess.Board to PGN format with character metadata.
    
    Args:
        board (chess.Board): The chess board with move history
        character_name (str): Name of the character
        team_name (str): Name of the team
        team_id (str): Team ID (e.g., "tT001")
        character_id (str): Character ID (e.g., "tT001_1")
        role (str): Character role (e.g., "FL", "VG", etc.)
        result (str): Result of the game ("win", "loss", "draw", "bench")
    
    Returns:
        str: Game in PGN format
    """
    game = chess.pgn.Game()
    
    # Set standard game headers
    game.headers["Event"] = "META Fantasy League Simulation"
    game.headers["Site"] = "Virtual Chess Arena"
    game.headers["Date"] = datetime.datetime.now().strftime("%Y.%m.%d")
    game.headers["Round"] = "1"
    
    # In chess, white is always the active character/player
    game.headers["White"] = character_name
    game.headers["Black"] = "AI Opponent"
    
    # Set game result
    if result == "win":
        game.headers["Result"] = "1-0"
    elif result == "loss":
        game.headers["Result"] = "0-1"
    elif result == "draw":
        game.headers["Result"] = "1/2-1/2"
    else:
        game.headers["Result"] = "*"  # Unknown or ongoing
    
    # Add META-specific headers
    game.headers["Team"] = team_name
    game.headers["TeamID"] = team_id
    game.headers["Character"] = character_name
    game.headers["CharacterID"] = character_id
    game.headers["Role"] = role
    
    # Add moves from board history
    node = game
    for move in board.move_stack:
        node = node.add_variation(move)
    
    # Convert to PGN text
    pgn_string = io.StringIO()
    exporter = chess.pgn.FileExporter(pgn_string)
    game.accept(exporter)
    
    return pgn_string.getvalue()

def save_pgn_to_file(pgn_text, filename):
    """
    Saves PGN text to a file.
    
    Args:
        pgn_text (str): The PGN text to save
        filename (str): The filename to save to
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # Write or append to the file
    with open(filename, "a") as f:
        f.write(pgn_text)
        f.write("\n\n")  # Add spacing between games

def record_match_pgns(team_a, team_a_boards, team_b, team_b_boards, match_context):
    """
    Records PGN files for all characters in a match.
    
    Args:
        team_a (list): List of team A characters
        team_a_boards (list): List of team A chess boards
        team_b (list): List of team B characters
        team_b_boards (list): List of team B chess boards
        match_context (dict): Match context information
    """
    match_date = datetime.datetime.now().strftime("%Y%m%d")
    match_dir = f"results/pgn/{match_date}_{match_context['team_a_id']}_vs_{match_context['team_b_id']}"
    os.makedirs(match_dir, exist_ok=True)
    
    # Record team A games
    for i, (character, board) in enumerate(zip(team_a, team_a_boards)):
        if not hasattr(character, "is_active") or character.get("is_active", True):
            pgn_text = record_game_to_pgn(
                board=board, 
                character_name=character["name"], 
                team_name=match_context["team_a_name"],
                team_id=character["team_id"],
                character_id=character["id"],
                role=character.get("role", ""),
                result=character.get("result", "unknown")
            )
            filename = f"{match_dir}/{character['id']}.pgn"
            save_pgn_to_file(pgn_text, filename)
    
    # Record team B games
    for i, (character, board) in enumerate(zip(team_b, team_b_boards)):
        if not hasattr(character, "is_active") or character.get("is_active", True):
            pgn_text = record_game_to_pgn(
                board=board, 
                character_name=character["name"], 
                team_name=match_context["team_b_name"],
                team_id=character["team_id"],
                character_id=character["id"],
                role=character.get("role", ""),
                result=character.get("result", "unknown")
            )
            filename = f"{match_dir}/{character['id']}.pgn"
            save_pgn_to_file(pgn_text, filename)

# Example usage (if run directly)
if __name__ == "__main__":
    board = chess.Board()
    
    # Make some example moves
    moves = ["e4", "e5", "Nf3", "Nc6", "Bb5", "a6"]
    for move_san in moves:
        board.push_san(move_san)
    
    # Record the game
    pgn_text = record_game_to_pgn(
        board=board, 
        character_name="Iron Man", 
        team_name="Avengers",
        team_id="tT003",
        character_id="tT003_0",
        role="FL",
        result="win"
    )
    print(pgn_text)
    
    # Save to file
    save_pgn_to_file(pgn_text, "results/pgn/example_game.pgn")
    print("PGN saved to results/pgn/example_game.pgn")