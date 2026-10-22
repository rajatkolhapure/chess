"""Abstract base class for all chess bots in our evolutionary journey."""
from abc import ABC, abstractmethod
import chess


class BaseEngine(ABC):
    """Base interface for all chess engines."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.nodes_evaluated = 0

    @abstractmethod
    def evaluate(self, board: chess.Board) -> int:
        """Evaluate the current static board position.
        
        Returns:
            int: Centipawn score from the perspective of White.
                 (+100 means White is up ~1 pawn, -100 means Black is up ~1 pawn).
        """
        pass

    @abstractmethod
    def select_move(self, board: chess.Board) -> chess.Move:
        """Select and return the best legal move for the current side to play."""
        pass
