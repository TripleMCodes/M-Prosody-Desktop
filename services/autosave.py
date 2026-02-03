"""
Simple autosave utility.
"""
from __future__ import annotations
from pathlib import Path


class Autosaver:
    def __init__(self, temp_file: Path):
        self.temp_file = temp_file
        self.last_saved_text = ""

    def maybe_save(self, text: str) -> None:
        if text != self.last_saved_text:
            self.temp_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.temp_file, "w", encoding="utf-8") as f:
                f.write(text)
            self.last_saved_text = text

    def load(self) -> str:
        try:
            with open(self.temp_file, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return ""
