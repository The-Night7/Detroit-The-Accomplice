#!/usr/bin/env python3
"""
Utility script to convert the provided AO3 interactive story HTML into a simple
game data format suitable for consumption by a C/SDL2 choose‑your‑own
adventure engine.

The script reads the `Detroit_The_Accomplice.html` file (bundled with this
project) and extracts each chapter.  Each chapter consists of a title,
plain‑text paragraphs (HTML tags stripped) and a set of choices.  A
choice includes the text the player will see along with a target
identifier.  We derive the target by matching the anchor text (the
visible text inside the hyperlink) to the title of another chapter.

The output is written to `game_data.txt` in the working directory.  It
uses a simple, line‑oriented format:

    ---PAGE---
    TITLE: <chapter title>
    TEXT:
    <paragraph 1>

    <paragraph 2>
    ...
    ENDTEXT
    CHOICES:
    <choice text>::<target title>
    <choice text>::<target title>
    ENDCHOICES

If a choice references a chapter that isn’t found by title (for
example because the HTML contains multiple chapters with the same
name), the target title is repeated verbatim as a signal that the
engine should not transition anywhere (the game will simply stay on
the current page).

This format is deliberately minimal: it can be parsed easily in C
without requiring external libraries.  The C engine is responsible for
mapping the target titles to internal indices.

Usage:
    python3 parse_story.py

The script writes `game_data.txt` into the same directory.
"""

import html
import os
import re
import sys
from collections import defaultdict

try:
    # BeautifulSoup is used for robust HTML parsing.  It should be
    # available in the environment.  If not, the user must install it.
    from bs4 import BeautifulSoup
except ImportError as exc:
    raise SystemExit(
        "BeautifulSoup4 is required to parse the story. Please install it "
        "(e.g. pip install beautifulsoup4) and run again."
    )


def parse_html(file_path: str):
    """Parse the HTML file and return a list of chapter dictionaries."""
    with open(file_path, "r", encoding="utf-8") as f:
        doc = f.read()
    soup = BeautifulSoup(doc, "html.parser")

    chapters = []
    # Build a list of chapter titles to enable mapping later.
    titles_seen = []
    # Each chapter is contained within a <div class="meta group"> element
    # followed by a <div class="userstuff"> element that holds the
    # narrative and choices.  The heading contains "Chapter n: TITLE".
    for meta in soup.find_all('div', class_='meta group'):
        h2 = meta.find('h2', class_='heading')
        if not h2:
            continue
        heading_text = h2.get_text(strip=True)
        # Remove the chapter number prefix ("Chapter n: ") if present.
        m = re.match(r'Chapter\s*\d+\s*:\s*(.*)', heading_text)
        title = m.group(1).strip() if m else heading_text
        # Find the corresponding content block
        content_div = meta.find_next('div', class_='userstuff')
        if not content_div:
            continue
        # Extract plain paragraphs
        paragraphs = []
        # The content is mostly contained in <p> tags; newlines within
        # paragraphs are represented by <br/> tags which BeautifulSoup
        # converts to \n automatically via get_text().
        for p in content_div.find_all('p'):
            # Skip paragraphs that contain anchor tags since those lines are
            # typically the choice options and will be handled separately.
            if p.find('a'):
                continue
            txt = p.get_text(separator="\n", strip=True)
            if txt:
                paragraphs.append(txt)
        # Extract choices: anchor text and href
        choices = []
        for a in content_div.find_all('a'):
            text = a.get_text(strip=True)
            href = a.get('href', '')
            # Skip the extension install link; it isn’t part of the game
            if 'chrome.google.com/webstore' in href:
                continue
            choices.append((text, href))
        chapters.append({
            'title': title,
            'paragraphs': paragraphs,
            'choices': choices,
        })
        titles_seen.append(title)
    return chapters


def build_remote_id_map(chapters):
    """
    Build a mapping from remote chapter IDs (the numeric part of the
    href attribute) to chapter titles.  If the same remote ID maps to
    multiple titles, the first occurrence wins.
    """
    remote_map = {}
    for ch in chapters:
        title = ch['title']
        for text, href in ch['choices']:
            # Extract numeric ID from the URL.  AO3 chapter links look like:
            # https://archiveofourown.org/works/15046616/chapters/34882277
            m = re.search(r'/chapters/(\d+)', href)
            if m:
                remote_id = m.group(1)
                if remote_id not in remote_map:
                    remote_map[remote_id] = text.strip()
    return remote_map


def assign_choice_targets(chapters, remote_map):
    """
    For each chapter, replace its choices with a tuple of (display text,
    target title).  The target title is determined by looking up the
    numeric remote ID in the remote_map and then locating the chapter
    whose title matches that text.  If a match cannot be found, the
    original anchor text is used as the target title.
    """
    # Build a lookup from title to index; if multiple chapters have the
    # same title, prefer the first occurrence.  This helps disambiguate
    # ambiguous targets.
    title_to_index = {}
    for idx, ch in enumerate(chapters):
        if ch['title'] not in title_to_index:
            title_to_index[ch['title']] = idx

    for ch in chapters:
        new_choices = []
        for anchor_text, href in ch['choices']:
            # Default target is the anchor text itself
            target_title = anchor_text.strip()
            m = re.search(r'/chapters/(\d+)', href)
            if m:
                remote_id = m.group(1)
                # Attempt to find target title via remote_map
                mapped_text = remote_map.get(remote_id)
                if mapped_text:
                    # If there is a chapter with this title, use it
                    if mapped_text in title_to_index:
                        target_title = mapped_text
                    else:
                        # Fallback: use the mapped text directly
                        target_title = mapped_text
            new_choices.append((anchor_text.strip(), target_title))
        ch['choices'] = new_choices


def write_game_data(chapters, out_path: str) -> None:
    """Write the chapters to a flat file using the custom game data format."""
    with open(out_path, 'w', encoding='utf-8') as f:
        for idx, ch in enumerate(chapters):
            f.write('---PAGE---\n')
            f.write(f'TITLE: {ch["title"]}\n')
            f.write('TEXT:\n')
            # Write paragraphs with blank line separation
            for p in ch['paragraphs']:
                # Escape any newline sequences to maintain readability
                f.write(p + '\n\n')
            f.write('ENDTEXT\n')
            f.write('CHOICES:\n')
            for opt_text, target in ch['choices']:
                # Use a double colon to separate the option text from the
                # target title.  Option text may contain colons itself.
                f.write(f'{opt_text}::{target}\n')
            f.write('ENDCHOICES\n')


def main():
    here = os.path.abspath(os.path.dirname(__file__))
    html_path = os.path.join(here, 'Detroit_The_Accomplice.html')
    if not os.path.exists(html_path):
        print(f'Error: {html_path} not found.', file=sys.stderr)
        sys.exit(1)
    chapters = parse_html(html_path)
    remote_map = build_remote_id_map(chapters)
    assign_choice_targets(chapters, remote_map)
    out_path = os.path.join(here, 'game_data.txt')
    write_game_data(chapters, out_path)
    print(f'Parsed {len(chapters)} chapters and wrote {out_path}')


if __name__ == '__main__':
    main()