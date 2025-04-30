def _process_convergences(self, team_a: List[Dict[str, Any]], team_a_boards: List[chess.Board],
                        team_b: List[Dict[str, Any]], team_b_boards: List[chess.Board],
                        match_context: Dict[str, Any]) -> None:
    """Process convergences between boards"""
    convergence_system = self.registry.get("convergence_system")
    
    if not convergence_system:
        raise ValueError("Convergence system not available")
    
    max_per_char = self.config.get("simulation.max_convergences_per_char", 3)
    
    # Process convergences
    convergences = convergence_system.process_convergences(
        team_a, team_a_boards,
        team_b, team_b_boards,
        match_context,
        max_per_char
    )
    
    # Log convergence count
    self.logger.info(f"Processed {len(convergences)} convergences")