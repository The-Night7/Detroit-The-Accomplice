
import os
import json

SAVES_DIR = "saves"

def _ensure_dir():
    os.makedirs(SAVES_DIR, exist_ok=True)

def list_saves():
    _ensure_dir()
    saves = [f for f in os.listdir(SAVES_DIR) if f.endswith(".txt")]
    return sorted(saves)

def load_save(slot="save_01"):
    _ensure_dir()
    path = os.path.join(SAVES_DIR, f"{slot}.txt")
    if not os.path.exists(path):
        return None
    data = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                key, _, val = line.partition("=")
                key = key.strip()
                val = val.strip()
                # Parse JSON-like lists stored as  KEY=["a","b"]
                if val.startswith("[") or val.startswith("{"):
                    try:
                        val = json.loads(val)
                    except Exception:
                        pass
                elif val.lstrip("-").isdigit():
                    val = int(val)
                data[key] = val
    return data

def save_game(slot, chapter, choice_key, player_stats, history):
    """
    slot         – save filename without extension
    chapter      – current chapter filename (no path)
    choice_key   – key of the choice just made
    player_stats – dict of player stats
    history      – list of "chapter:key" strings
    """
    _ensure_dir()
    path = os.path.join(SAVES_DIR, f"{slot}.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"CHAPTER={chapter}\n")
        f.write(f"LAST_CHOICE={choice_key}\n")
        f.write(f"CHOICES_HISTORY={json.dumps(history)}\n")
        for key, val in player_stats.items():
            f.write(f"{key}={val}\n")

def new_game_state():
    return {
        "chapter": "chapter_01.txt",
        "history": [],
        "player_stats": {
            "SOFTWARE_INSTABILITY": 0,
            "HEALTH": 100,
            "MORALITY": 50,
        }
    }

def state_from_save(data):
    """Convert raw save dict into a usable game state."""
    player_stats = {
        "SOFTWARE_INSTABILITY": data.get("SOFTWARE_INSTABILITY", 0),
        "HEALTH":               data.get("HEALTH", 100),
        "MORALITY":             data.get("MORALITY", 50),
    }
    return {
        "chapter":      data.get("CHAPTER", "chapter_01.txt"),
        "history":      data.get("CHOICES_HISTORY", []),
        "player_stats": player_stats,
    }
