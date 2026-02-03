"""
Flow analysis utilities for Lyrical Lab.

Extracted from the original monolithic file to keep UI code lighter.
"""
from __future__ import annotations

import logging
from typing import List, Optional
import pronouncing

logger = logging.getLogger(__name__)


def get_stress_pattern(line: str) -> str:
    """Return a string of u (unstressed) and S (stressed) syllables for a line."""
    words = line.lower().split()
    pattern: List[str] = []

    for word in words:
        phones = pronouncing.phones_for_word(word)
        if phones:
            stress = pronouncing.stresses(phones[0])  # e.g. "010"
            for c in stress:
                pattern.append('S' if c in "12" else 'u')
        else:
            pattern.append('?')

    return ''.join(pattern)


def alignment_score(patterns: List[str]) -> Optional[float]:
    """Calculate how aligned the stressed syllables are across multiple lines."""
    if len(patterns) < 2:
        return None

    max_len = max(len(p) for p in patterns)
    padded = [p.ljust(max_len) for p in patterns]

    aligned = 0
    total = 0
    for i in range(max_len):
        column = [p[i] for p in padded if p[i] != ' ']
        if not column:
            continue
        total += 1
        if all(c == column[0] for c in column):
            aligned += 1

    return aligned / total if total else 0.0


def highlight_flow(patterns: List[str], lines: List[str]) -> str:
    """Return HTML showing flow patterns with color coding."""
    max_len = max(len(p) for p in patterns) if patterns else 0
    padded = [p.ljust(max_len) for p in patterns]

    # Determine alignment per column
    column_alignment: List[Optional[bool]] = []
    for i in range(max_len):
        column = [p[i] for p in padded if p[i] != ' ']
        if not column:
            column_alignment.append(None)
        elif all(c == column[0] for c in column):
            column_alignment.append(True)
        else:
            column_alignment.append(False)

    html_lines: List[str] = []
    for line, pattern in zip(lines, padded):
        colored_pattern = ""
        for char, aligned in zip(pattern, column_alignment):
            if char == 'S':
                color = "green" if aligned else "red"
                colored_pattern += f"<span style='color:{color};font-weight:bold'>{char}</span>"
            elif char == 'u':
                colored_pattern += "<span style='color:gray'>u</span>"
            else:
                colored_pattern += " "
        html_lines.append(f"<b>{line}</b><br>{colored_pattern}<br><br>")

    return "".join(html_lines)
