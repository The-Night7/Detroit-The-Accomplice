import os
import time
import sys

CHAPTERS_DIR = "chapters"
CHOICE_SYMBOLS = ["[X]", "[∆]", "[O]", "[□]"]
CHOICE_KEYS    = ["x", "t", "o", "s"]   # t = triangle, s = square
CHOICE_LABELS  = ["X", "△", "O", "□"]

CYAN    = "\033[96m"
YELLOW  = "\033[93m"
GREEN   = "\033[92m"
RED     = "\033[91m"
MAGENTA = "\033[95m"
BOLD    = "\033[1m"
DIM     = "\033[2m"
RESET   = "\033[0m"
WHITE   = "\033[97m"

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def typewrite(text, delay=0.018, color=""):
    """Print text character by character like a terminal effect."""
    for ch in text:
        sys.stdout.write(color + ch + RESET)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def print_header(chapter_name):
    print(f"\n{CYAN}{'─'*60}{RESET}")
    print(f"{BOLD}{CYAN}  ◈  DETROIT : THE ACCOMPLICE  ◈{RESET}")
    print(f"{DIM}{CYAN}  {chapter_name}{RESET}")
    print(f"{CYAN}{'─'*60}{RESET}\n")

def print_status_bar(player_stats, relations):
    print(f"\n{DIM}{'─'*60}{RESET}")
    instability = player_stats.get("SOFTWARE_INSTABILITY", 0)
    bar_len = 20
    filled = int((instability / 100) * bar_len)
    bar = "█" * filled + "░" * (bar_len - filled)
    color = GREEN if instability < 40 else YELLOW if instability < 70 else RED
    print(f"  {BOLD}Software Instability:{RESET} {color}[{bar}] {instability}%{RESET}")

    rel_str = "  "
    for name, status in relations.items():
        emoji = {"Trusted": "💙", "Friend": "🟢", "Neutral": "⚪", "Tense": "🟡", "Hostile": "🔴"}.get(status, "⚪")
        rel_str += f"{emoji} {name}: {DIM}{status}{RESET}  "
    print(rel_str)
    print(f"{DIM}{'─'*60}{RESET}\n")

def parse_chapter(filepath):
    """
    Returns:
        narrative (str)  – the story text
        choices   (list) – list of (symbol, label, text)
        metadata  (dict) – NEXT_CHAPTER, EFFECT lines etc.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    narrative_lines = []
    choices = []
    metadata = {}

    for line in lines:
        stripped = line.rstrip("\n")

        # Metadata lines  →  KEY=VALUE
        if stripped.startswith("##") and "=" in stripped:
            key, _, val = stripped[2:].partition("=")
            metadata[key.strip()] = val.strip()
            continue

        # Choice lines
        found_choice = False
        for sym, key, label in zip(CHOICE_SYMBOLS, CHOICE_KEYS, CHOICE_LABELS):
            if stripped.startswith(sym):
                choice_text = stripped[len(sym):].strip()
                choices.append({"symbol": sym, "key": key, "label": label, "text": choice_text})
                found_choice = True
                break

        if not found_choice:
            narrative_lines.append(stripped)

    narrative = "\n".join(narrative_lines).strip()
    return narrative, choices, metadata

def display_narrative(narrative, chapter_name, player_stats, relations):
    from character_manager import get_player_name
    player_name = get_player_name()
    # Replace {PLAYER_NAME} in all text
    narrative = narrative.replace("{PLAYER_NAME}", player_name)
    
    clear()
    print_header(chapter_name)
    print_status_bar(player_stats, relations)
    for paragraph in narrative.split("\n\n"):
        typewrite(paragraph.strip(), delay=0.015, color=WHITE)
        print()
    print()

def display_choices(choices):
    print(f"{BOLD}{YELLOW}  ── CHOICES ──{RESET}\n")
    key_map = {"x": "X", "t": "△", "o": "O", "s": "□"}
    for c in choices:
        print(f"  {BOLD}{MAGENTA}[{key_map[c['key']]}]{RESET}  {c['text']}")
    print()

def ask_choice(choices):
    key_map = {"x": "X", "t": "△", "o": "O", "s": "□"}
    valid_keys = [c["key"] for c in choices]
    while True:
        raw = input(f"{CYAN}  Your choice {DIM}({'/'.join([key_map[k] for k in valid_keys])}){RESET}{CYAN} → {RESET}").strip().lower()
        if raw in valid_keys:
            chosen = next(c for c in choices if c["key"] == raw)
            return chosen
        print(f"  {RED}Invalid input. Please press one of: {', '.join([key_map[k] for k in valid_keys])}{RESET}")
