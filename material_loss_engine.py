# material_loss_engine.py
# Calculates material loss for a given board state or completed PGN

import chess.pgn
from io import StringIO

# Piece values for evaluation (relative impact)
PIECE_VALUES = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9
}


def calculate_material_loss(pgn_text: str) -> dict:
    """
    Parses a PGN string and calculates material loss for both sides.
    Returns a dict with total loss by side.
    """
    game = chess.pgn.read_game(StringIO(pgn_text))
    board = game.board()

    white_lost = 0
    black_lost = 0

    for move in game.mainline_moves():
        captured_piece = board.piece_at(move.to_square)
        if captured_piece and captured_piece.piece_type != chess.KING:
            value = PIECE_VALUES.get(captured_piece.piece_type, 0)
            if board.turn == chess.WHITE:
                black_lost += value
            else:
                white_lost += value
        board.push(move)

    return {"white_loss": white_lost, "black_loss": black_lost}


# Example
if __name__ == "__main__":
    sample_pgn = """
    [Event "Test"]
    [Site "Local"]
    [Date "2025.04.25"]
    [Round "1"]
    [White "Unit A"]
    [Black "AI"]
    [Result "1-0"]

    1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Bxc6 dxc6 5. Nxe5 Qd4 6. Nf3 Qxe4+ 7. Qe2 Qxe2+ 8. Kxe2
    """
    print(calculate_material_loss(sample_pgn))