"""
Preferences + theme loading helpers.

Keeps file IO and caching out of the UI.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from autodidex_cache import DictionaryCache
from themes_db import Themes

themes = Themes()
cache = DictionaryCache()


@dataclass
class UserPrefs:
    theme: str = "dark"   # "light" | "dark" | "neutral"
    font_size: int = 14


class Preferences:
    def __init__(self, config_file: Path):
        self.config_file = config_file

    def load(self) -> Optional[UserPrefs]:
        # theme can be saved in cache/db
        theme = cache.get("theme") or themes.get_chosen_theme() or "dark"

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            font_size = int(data.get("font_size", 14))
            return UserPrefs(theme=theme, font_size=font_size)
        except (FileNotFoundError, json.JSONDecodeError, ValueError, TypeError):
            # keep app usable even if config is missing/corrupt
            return UserPrefs(theme=theme, font_size=14)


class ThemeManager:
    def __init__(self):
        self.light_mode: Optional[str] = None
        self.dark_mode: Optional[str] = None
        self.neutral_mode: Optional[str] = None

    def load_themes(self) -> None:
        self.light_mode = cache.get("light") or themes.get_theme_mode("light")
        cache.set("light", self.light_mode)

        self.dark_mode = cache.get("dark") or themes.get_theme_mode("dark")
        cache.set("dark", self.dark_mode)

        self.neutral_mode = cache.get("neutral") or themes.get_theme_mode("neutral")
        cache.set("neutral", self.neutral_mode)

    def next_theme(self, current: str) -> str:
        if current == "light":
            return "dark"
        if current == "dark":
            return "neutral"
        return "light"

    def stylesheet_for(self, theme: str) -> str:
        if theme == "light":
            return self.light_mode or ""
        if theme == "neutral":
            return self.neutral_mode or ""
        return self.dark_mode or ""
