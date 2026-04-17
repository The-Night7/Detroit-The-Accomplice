import os
import sys
from engine import (
    clear, typewrite, display_narrative, display_choices,
    ask_choice, print_header, CYAN, YELLOW, GREEN, RED,
    BOLD, DIM, RESET, MAGENTA, WHITE
)
from save_manager import (
    list_saves, load_save, save_game,
    new_game_state, state_from_save
)
from character_manager import get_all_relations

CHAPTERS_DIR = "chapters"


# ── Helpers ──────────────────────────────────────────────

def apply_effects(metadata, player_stats):
    """
    Read EFFECT lines from chapter metadata and apply them.
    Format in chapter file:  ##EFFECT=SOFTWARE_INSTABILITY+10
    """
    for key, val in metadata.items():
        if key.startswith("EFFECT"):
            # e.g.  SOFTWARE_INSTABILITY+10  or  HEALTH-5
            for op in ["+", "-"]:
                if op in val:
                    stat, _, amount = val.partition(op)
                    stat = stat.strip()
                    amount = int(amount.strip())
                    if stat in player_stats:
                        if op == "+":
                            player_stats[stat] = min(100, player_stats[stat] + amount)
                        else:
                            player_stats[stat] = max(0, player_stats[stat] - amount)
                    break


def resolve_next_chapter(metadata, choice):
    """
    Determine the next chapter filename.
    Priority:
      1. Choice-specific override  →  ##NEXT_X=chapter_02b.txt
      2. Generic next              →  ##NEXT=chapter_02.txt
      3. None (end of game)
    """
    key_upper = choice["key"].upper()
    specific = metadata.get(f"NEXT_{key_upper}")
    if specific:
        return specific
    return metadata.get("NEXT")


# ── Menus ────────────────────────────────────────────────

def menu_main():
    clear()
    print(f"""
{CYAN}{'═'*60}{RESET}
{BOLD}{CYAN}
      ██████╗ ███████╗████████╗██████╗  ██████╗ ██╗████████╗
      ██╔══██╗██╔════╝╚══██╔══╝██╔══██╗██╔═══██╗██║╚══██╔══╝
      ██║  ██║█████╗     ██║   ██████╔╝██║   ██║██║   ██║
      ██║  ██║██╔══╝     ██║   ██╔══██╗██║   ██║██║   ██║
      ██████╔╝███████╗   ██║   ██║  ██║╚██████╔╝██║   ██║
      ╚═════╝ ╚══════╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚═╝   ╚═╝
{RESET}
{CYAN}              T H E   A C C O M P L I C E{RESET}
{CYAN}{'═'*60}{RESET}

  {BOLD}[1]{RESET}  New Game
  {BOLD}[2]{RESET}  Load Game
  {BOLD}[3]{RESET}  Quit
""")
    while True:
        choice = input(f"{CYAN}  → {RESET}").strip()
        if choice in ("1", "2", "3"):
            return choice
        print(f"  {RED}Invalid input.{RESET}")


def menu_load():
    saves = list_saves()
    if not saves:
        print(f"\n  {RED}No save files found.{RESET}")
        input(f"\n  {DIM}Press Enter to go back...{RESET}")
        return None
    clear()
    print(f"\n{CYAN}{'─'*60}{RESET}")
    print(f"{BOLD}{CYAN}  LOAD GAME{RESET}")
    print(f"{CYAN}{'─'*60}{RESET}\n")
    for i, s in enumerate(saves, 1):
        data = load_save(s[:-4])
        chapter = data.get("CHAPTER", "?") if data else "?"
        print(f"  {BOLD}[{i}]{RESET}  {s}  {DIM}→ {chapter}{RESET}")
    print(f"\n  {BOLD}[0]{RESET}  Back")
    while True:
        raw = input(f"\n{CYAN}  → {RESET}").strip()
        if raw == "0":
            return None
        if raw.isdigit() and 1 <= int(raw) <= len(saves):
            slot = saves[int(raw) - 1][:-4]
            data = load_save(slot)
            return state_from_save(data) if data else None
        print(f"  {RED}Invalid choice.{RESET}")


def menu_save_slot():
    print(f"\n{YELLOW}  Save to slot (e.g. save_01) or press Enter to skip:{RESET}")
    raw = input(f"{CYAN}  → {RESET}").strip()
    return raw if raw else None


# ── Core game loop ───────────────────────────────────────

def game_loop(state):
    from engine import parse_chapter

    chapter_file = state["chapter"]
    history      = state["history"]
    player_stats = state["player_stats"]

    while True:
        path = os.path.join(CHAPTERS_DIR, chapter_file)

        # ── End of game ──
        if not os.path.exists(path):
            clear()
            print_header("— END —")
            typewrite("\n  Thank you for playing Detroit: The Accomplice.\n",
                      color=CYAN)
            input(f"\n  {DIM}Press Enter to return to menu...{RESET}")
            return

        # ── Parse & display ──
        narrative, choices, metadata = parse_chapter(path)
        chapter_name = metadata.get("TITLE", chapter_file.replace(".txt", "").replace("_", " ").title())
        relations    = get_all_relations()

        display_narrative(narrative, chapter_name, player_stats, relations)

        # ── No choices = cutscene, press Enter to continue ──
        if not choices:
            next_ch = metadata.get("NEXT")
            if next_ch:
                input(f"  {DIM}Press Enter to continue...{RESET}")
                chapter_file = next_ch
                continue
            else:
                input(f"  {DIM}Press Enter to return to menu...{RESET}")
                return

        display_choices(choices)

        # ── Player chooses ──
        chosen = ask_choice(choices)

        if metadata.get("ACTION") == "RENAME":
            if chosen["key"] == "x":
                # Saisie manuelle
                new_name = ask_player_name()
                update_player_name(new_name)

            elif chosen["key"] == "t":  # ∆
                # Andre choisit → nom fixe défini dans les métadonnées
                new_name = metadata.get("RENAME_T", "YN600")
                update_player_name(new_name)

            elif chosen["key"] == "o":
                pass  # Reste YN600

            elif chosen["key"] == "s":  # □
                pass  # Reste YN600, mais effet narratif différent

        # ── Apply stat effects from metadata ──
        apply_effects(metadata, player_stats)

        # ── Apply choice-specific effects ──
        choice_effect_key = f"EFFECT_{chosen['key'].upper()}"
        if choice_effect_key in metadata:
            fake_meta = {"EFFECT": metadata[choice_effect_key]}
            apply_effects(fake_meta, player_stats)

        # ── Record history ──
        history.append(f"{chapter_file}:{chosen['key']}")

        # ── Save prompt ──
        slot = menu_save_slot()
        if slot:
            save_game(slot, chapter_file, chosen["key"], player_stats, history)
            print(f"  {GREEN}✔ Game saved to {slot}.{RESET}")
            import time; time.sleep(1)

        # ── Advance chapter ──
        next_ch = resolve_next_chapter(metadata, chosen)
        if not next_ch:
            clear()
            print_header("— END OF CHAPTER —")
            typewrite("\n  No further chapter linked. Returning to menu...\n", color=DIM)
            import time; time.sleep(2)
            return

        chapter_file = next_ch
        state["chapter"] = chapter_file


# ── Entry point ─────────────────────────────────────────

def main():
    while True:
        choice = menu_main()
        if choice == "1":
            game_loop(new_game_state())
        elif choice == "2":
            state = menu_load()
            if state:
                game_loop(state)
        elif choice == "3":
            clear()
            print(f"\n  {CYAN}Goodbye.{RESET}\n")
            sys.exit(0)


if __name__ == "__main__":
    main()