"""Elo Rating System for Tracking Player Skill Progression."""
import json
import os
from typing import Dict, Any

PROFILE_PATH = os.path.join(os.path.dirname(__file__), "player_profile.json")

BOT_RATINGS = {
    "1": 800,   # Level 1: The Greedy Bot
    "2": 1200,  # Level 2: The Minimax Bot
    "3": 1500,  # Level 3: The Tactician (Quiescence)
    "4": 1900,  # Level 4: The Deep Searcher (Alpha-Beta)
    "5": 2200,  # Level 5: Positional Master
    "6": 2500,  # Level 6: Speed Demon (Zobrist & TT)
    "7": 3500,  # Level 7: NNUE Superhuman
}


def load_profile() -> Dict[str, Any]:
    """Load player rating profile from disk."""
    if os.path.exists(PROFILE_PATH):
        try:
            with open(PROFILE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "username": "Player",
        "rating": 1000,
        "games_played": 0,
        "wins": 0,
        "losses": 0,
        "draws": 0,
        "history": []
    }


def save_profile(profile: Dict[str, Any]) -> None:
    """Save player rating profile to disk."""
    with open(PROFILE_PATH, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2)


def update_player_rating(bot_level: str, result: float) -> Dict[str, Any]:
    """Update player's Elo rating after a match.
    
    Args:
        bot_level: Bot level played against ("1", "2", etc.)
        result: 1.0 for Win, 0.5 for Draw, 0.0 for Loss.
    
    Returns:
        Updated profile dictionary with old_rating and delta.
    """
    profile = load_profile()
    user_rating = profile.get("rating", 1000)
    bot_rating = BOT_RATINGS.get(str(bot_level), 1000)

    # Standard FIDE Elo calculation formula
    expected_score = 1.0 / (1.0 + 10.0 ** ((bot_rating - user_rating) / 400.0))
    k_factor = 32.0 if profile.get("games_played", 0) < 30 else 20.0
    delta = round(k_factor * (result - expected_score))

    new_rating = max(100, user_rating + delta)
    old_rating = user_rating

    profile["rating"] = new_rating
    profile["games_played"] = profile.get("games_played", 0) + 1

    if result == 1.0:
        profile["wins"] = profile.get("wins", 0) + 1
        outcome = "WIN"
    elif result == 0.0:
        profile["losses"] = profile.get("losses", 0) + 1
        outcome = "LOSS"
    else:
        profile["draws"] = profile.get("draws", 0) + 1
        outcome = "DRAW"

    profile["history"].append({
        "bot_level": bot_level,
        "bot_rating": bot_rating,
        "old_rating": old_rating,
        "new_rating": new_rating,
        "delta": delta,
        "outcome": outcome
    })

    save_profile(profile)
    profile["last_delta"] = delta
    profile["old_rating"] = old_rating
    return profile
