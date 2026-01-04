"""
Profile persistence module for the debate simulator.

Stores player profiles in JSON files for simplicity and inspectability.
"""

import json
from pathlib import Path
from datetime import datetime
from src.serving.models import (
    PlayerProfile,
    PlayerStats,
    Achievement,
    MatchHistory,
)

# Default profile storage location
PROFILES_DIR = Path(__file__).parent.parent.parent / "data" / "profiles"

# Default achievements
DEFAULT_ACHIEVEMENTS = [
    Achievement(
        id="first-debate",
        title="First Steps",
        description="Complete your first debate",
        unlocked=False,
    ),
    Achievement(
        id="first-win",
        title="Victory!",
        description="Win your first debate",
        unlocked=False,
    ),
    Achievement(
        id="combo-starter",
        title="Combo Starter",
        description="Achieve a 3-turn combo streak",
        unlocked=False,
    ),
    Achievement(
        id="combo-king",
        title="Combo King",
        description="Achieve a 5-turn combo streak",
        unlocked=False,
    ),
    Achievement(
        id="evidence-master",
        title="Evidence Master",
        description="Score 90+ on evidence use",
        unlocked=False,
    ),
    Achievement(
        id="civil-debater",
        title="Civil Debater",
        description="Maintain 95+ civility across a debate",
        unlocked=False,
    ),
    Achievement(
        id="topic-explorer",
        title="Topic Explorer",
        description="Debate 5 different topics",
        unlocked=False,
    ),
    Achievement(
        id="winning-streak",
        title="Winning Streak",
        description="Win 3 debates in a row",
        unlocked=False,
    ),
    Achievement(
        id="level-5",
        title="Rising Star",
        description="Reach level 5",
        unlocked=False,
    ),
    Achievement(
        id="level-10",
        title="Debate Champion",
        description="Reach level 10",
        unlocked=False,
    ),
]

# Rank titles by level
RANK_TITLES = {
    1: "Novice",
    2: "Apprentice",
    3: "Debater",
    5: "Skilled Debater",
    7: "Expert",
    10: "Master",
    15: "Grandmaster",
    20: "Legend",
}


def _get_profile_path(username: str = "default") -> Path:
    """Get path to profile JSON file."""
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    # Sanitize username for filesystem
    safe_name = "".join(c for c in username if c.isalnum() or c in "-_").lower()
    if not safe_name:
        safe_name = "default"
    return PROFILES_DIR / f"{safe_name}.json"


def _calculate_xp_for_level(level: int) -> int:
    """Calculate XP needed to reach next level."""
    return 100 * level * level


def _get_rank_title(level: int) -> str:
    """Get rank title for a level."""
    title = "Novice"
    for lvl, rank in sorted(RANK_TITLES.items()):
        if level >= lvl:
            title = rank
    return title


def get_default_profile() -> PlayerProfile:
    """Create a default new player profile."""
    return PlayerProfile(
        username="Debater",
        avatar="default",
        level=1,
        xp=0,
        xpNext=100,
        rankTitle="Novice",
        stats=PlayerStats(),
        achievements=DEFAULT_ACHIEVEMENTS.copy(),
        history=[],
    )


def load_profile(username: str = "default") -> PlayerProfile:
    """
    Load player profile from disk.

    Args:
        username: Player username

    Returns:
        PlayerProfile (creates default if not exists)
    """
    path = _get_profile_path(username)

    if not path.exists():
        profile = get_default_profile()
        profile.username = username if username != "default" else "Debater"
        save_profile(profile)
        return profile

    try:
        with open(path) as f:
            data = json.load(f)
        return PlayerProfile(**data)
    except (json.JSONDecodeError, ValueError):
        # Corrupted file, create new
        profile = get_default_profile()
        save_profile(profile)
        return profile


def save_profile(profile: PlayerProfile) -> None:
    """
    Save player profile to disk.

    Args:
        profile: PlayerProfile to save
    """
    path = _get_profile_path(profile.username)
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)

    with open(path, "w") as f:
        json.dump(profile.model_dump(by_alias=True), f, indent=2)


def update_profile(
    username: str,
    updates: dict,
) -> PlayerProfile:
    """
    Update player profile with partial data.

    Args:
        username: Player username
        updates: Dict of fields to update

    Returns:
        Updated PlayerProfile
    """
    profile = load_profile(username)

    # Apply simple field updates
    for field in ["username", "avatar"]:
        if field in updates:
            setattr(profile, field, updates[field])

    save_profile(profile)
    return profile


def add_match_result(
    username: str,
    topic: str,
    mode: str,
    score: int,
    won: bool,
    achievements_unlocked: list[str] | None = None,
) -> PlayerProfile:
    """
    Add a match result and update stats.

    Args:
        username: Player username
        topic: Debate topic
        mode: Game mode
        score: Final score
        won: Whether player won
        achievements_unlocked: List of achievement IDs unlocked

    Returns:
        Updated PlayerProfile
    """
    profile = load_profile(username)

    # Add to history
    match = MatchHistory(
        id=f"match-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        topic=topic,
        mode=mode,
        date=datetime.now().isoformat(),
        score=score,
        result="Win" if won else "Loss",
    )
    profile.history.insert(0, match)
    profile.history = profile.history[:50]  # Keep last 50 matches

    # Update stats
    stats = profile.stats
    if won:
        stats.wins += 1
    else:
        stats.losses += 1

    total = stats.wins + stats.losses
    stats.winRate = stats.wins / total if total > 0 else 0
    stats.averageScore = (
        (stats.averageScore * (total - 1) + score) / total
        if total > 0 else score
    )
    stats.topicsPlayed = len(set(m.topic for m in profile.history))

    # Update XP and level
    xp_gain = score  # Simple: score = XP
    if won:
        xp_gain += 50  # Bonus for winning

    profile.xp += xp_gain

    # Level up check
    while profile.xp >= profile.xpNext:
        profile.xp -= profile.xpNext
        profile.level += 1
        profile.xpNext = _calculate_xp_for_level(profile.level)
        profile.rankTitle = _get_rank_title(profile.level)

    # Unlock achievements
    if achievements_unlocked:
        for ach in profile.achievements:
            if ach.id in achievements_unlocked and not ach.unlocked:
                ach.unlocked = True

    # Check level achievements
    if profile.level >= 5:
        for ach in profile.achievements:
            if ach.id == "level-5":
                ach.unlocked = True
    if profile.level >= 10:
        for ach in profile.achievements:
            if ach.id == "level-10":
                ach.unlocked = True

    # Check first debate
    if len(profile.history) == 1:
        for ach in profile.achievements:
            if ach.id == "first-debate":
                ach.unlocked = True

    # Check first win
    if won and stats.wins == 1:
        for ach in profile.achievements:
            if ach.id == "first-win":
                ach.unlocked = True

    # Check topic explorer
    if stats.topicsPlayed >= 5:
        for ach in profile.achievements:
            if ach.id == "topic-explorer":
                ach.unlocked = True

    save_profile(profile)
    return profile
