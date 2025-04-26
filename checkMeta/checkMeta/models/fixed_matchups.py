"""
Fixed matchups for META Fantasy League Simulator
Provides standard day-by-day matchups for a 10-team league
"""

def get_day_matchups(day_number):
    """
    Return fixed matchups for a specific day
    
    For a 10-team league with 5 matches per day
    Each team plays exactly once per day
    """
    # Standard matchups for a 10-team league
    all_matchups = {
        # Day 1: Standard pairing
        1: [
            ("tT002", "tT001"),
            ("tT003", "tT004"),
            ("tT006", "tT005"),
            ("tT007", "tT008"),
            ("tT010", "tT009")
        ],
        # Day 2: Rotate for different matchups
        2: [
            ("tT002", "tT004"),
            ("tT003", "tT005"),
            ("tT006", "tT008"),
            ("tT007", "tT009"),
            ("tT010", "tT001")
        ],
        # Day 3: Another rotation
        3: [
            ("tT002", "tT005"),
            ("tT003", "tT008"),
            ("tT006", "tT009"),
            ("tT007", "tT001"),
            ("tT010", "tT004")
        ],
        # Day 4
        4: [
            ("tT002", "tT008"),
            ("tT003", "tT009"),
            ("tT006", "tT001"),
            ("tT007", "tT004"),
            ("tT010", "tT005")
        ],
        # Day 5
        5: [
            ("tT002", "tT009"),
            ("tT003", "tT001"),
            ("tT006", "tT004"),
            ("tT007", "tT005"),
            ("tT010", "tT008")
        ]
        # Add more days if needed
    }
    
    # Default to day 1 if the requested day isn't defined
    if day_number not in all_matchups:
        print(f"Warning: No predefined matchups for day {day_number}, using day 1 matchups")
        return all_matchups[1]
    
    return all_matchups[day_number]