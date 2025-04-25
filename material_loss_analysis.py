material_loss_analysis.py# material_loss_analysis.py
# Calculates material loss based on final board state (placeholder PGN simulation)

import chess
import chess.pgn
from io import StringIO

PIECE_VALUES = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9
}


def calculate_material_loss(pgn_string: str) -> dict:
    """
    Evaluates material loss from PGN string.
    Returns material loss totals for White and Black.
    """
    game = chess.pgn.read_game(StringIO(pgn_string))
    board = game.end().board()

    white_material = 0
    black_material = 0

    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece and piece.piece_type in PIECE_VALUES:
            value = PIECE_VALUES[piece.piece_type]
            if piece.color == chess.WHITE:
                white_material += value
            else:
                black_material += value

    max_material = 39  # 8P + 2N + 2B + 2R + Q (excluding king)
    return {
        "white_loss": max_material - white_material,
        "black_loss": max_material - black_material
    }


# Example PGN (white sacrifices queen early)
pgn = """
[Event "Example"]
[Site "Metachess"]
[Date "2025.04.25"]
[Round "1"]
[White "UnitA"]
[Black "AI"]
[Result "1-0"]

1. e4 e5 2. Qh5 Nc6 3. Qxf7#
"""

if __name__ == "__main__":
    loss = calculate_material_loss(pgn)
    print("Material Loss:", loss)