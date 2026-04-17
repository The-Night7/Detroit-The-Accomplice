import os

CHARACTERS_DIR = "characters"
PLAYER_FILE    = os.path.join(CHARACTERS_DIR, "yn600.txt")

# ── I/O helpers ──────────────────────────────────────────────────────────────

def _load_char(filepath):
    """Parse a character .txt file into a dict."""
    data = {}
    if not os.path.exists(filepath):
        return data
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, val = line.partition("=")
                data[key.strip()] = val.strip()
    return data


def _save_char(filepath, data):
    """Write a dict back to a character .txt file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        for key, val in data.items():
            f.write(f"{key}={val}\n")


def _char_path(name):
    """Return the filepath for a character by filename (without extension)."""
    return os.path.join(CHARACTERS_DIR, f"{name}.txt")


# ── Player ────────────────────────────────────────────────────────────────────

def get_player_name():
    """Return the player's display name (defaults to YN600)."""
    data = _load_char(PLAYER_FILE)
    return data.get("DISPLAY_NAME", "YN600")


def update_player_name(new_name):
    """Update DISPLAY_NAME in yn600.txt."""
    data = _load_char(PLAYER_FILE)
    data["DISPLAY_NAME"] = new_name.strip()
    _save_char(PLAYER_FILE, data)


# ── Relations ─────────────────────────────────────────────────────────────────

def get_all_relations():
    """
    Return a dict { display_name: relation_string }
    for every character file found in the characters/ folder,
    excluding the player file itself.
    """
    relations = {}
    if not os.path.isdir(CHARACTERS_DIR):
        return relations
    for filename in sorted(os.listdir(CHARACTERS_DIR)):
        if not filename.endswith(".txt"):
            continue
        filepath = os.path.join(CHARACTERS_DIR, filename)
        if os.path.abspath(filepath) == os.path.abspath(PLAYER_FILE):
            continue
        data     = _load_char(filepath)
        name     = data.get("NAME", filename.replace(".txt", ""))
        relation = data.get("RELATION", "Unknown")
        relations[name] = relation
    return relations


def get_relation(char_filename):
    """Return the RELATION value for a given character file (no extension)."""
    data = _load_char(_char_path(char_filename))
    return data.get("RELATION", "Unknown")


def set_relation(char_filename, new_relation):
    """Set the RELATION value for a given character."""
    path = _char_path(char_filename)
    data = _load_char(path)
    data["RELATION"] = new_relation
    _save_char(path, data)


def update_stat(char_filename, stat, delta):
    """
    Add delta (int, can be negative) to a numeric stat of a character.
    Clamps the result between 0 and 100.
    """
    path    = _char_path(char_filename)
    data    = _load_char(path)
    current = int(data.get(stat, 0))
    new_val = max(0, min(100, current + delta))
    data[stat] = str(new_val)
    _save_char(path, data)


def get_stat(char_filename, stat, default=0):
    """Return a numeric stat for a character."""
    data = _load_char(_char_path(char_filename))
    return int(data.get(stat, default))
