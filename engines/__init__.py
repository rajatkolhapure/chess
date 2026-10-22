"""Chess Engines Module - Evolutionary Ladder from Level 1 to Superhuman."""
from .base import BaseEngine
from .level1_greedy import GreedyBot

__all__ = ["BaseEngine", "GreedyBot"]
