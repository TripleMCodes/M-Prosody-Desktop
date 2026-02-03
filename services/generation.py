"""
Text generation (lyrics + figures of speech) wrapper.
"""
from __future__ import annotations

from typing import Optional
from lyrics_n_summarization import OpenRouterClient


class GenerationService:
    def __init__(self):
        self.client = OpenRouterClient()

    def generate_lyrics(self, prompt: str, genre: str) -> Optional[str]:
        return self.client.generate_lyrics(prompt, genre)

    def generate_fos(self, prompt: str, figure_of_speech: str) -> Optional[str]:
        return self.client.cliches_phrase_quotes(prompt, figure_of_speech)
