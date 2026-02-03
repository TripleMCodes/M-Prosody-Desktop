"""
Rhymes & lexicon wrapper around WordFinder.
"""
from __future__ import annotations
from wordfinder import WordFinder


class LexiconService:
    def __init__(self, limit: int = 15, tags: str = "music,poetry"):
        self.engine = WordFinder(limit, tags)

    def rhymes(self, word: str):
        return self.engine.rhymes_with(word)

    def slant_rhymes(self, word: str):
        return self.engine.slant_rhymes(word)

    def synonyms(self, word: str):
        return self.engine.synonyms_for(word)

    def antonyms(self, word: str):
        return self.engine.antonyms_for(word)

    def homophones(self, word: str):
        return self.engine.homophones_for(word)

    def related(self, word: str):
        return self.engine.triggers(word)

    def adjectives(self, word: str):
        return self.engine.adjectives_for(word)

    def nouns_described_by(self, word: str):
        return self.engine.nouns_described_by(word)

    def spelled_like(self, word: str):
        return self.engine.spelled_like(word)

    def hyponyms(self, word: str):
        return self.engine.more_specific_than(word)

    def hypernyms(self, word: str):
        return self.engine.more_general_than(word)

    def sounds_like(self, word: str):
        return self.engine.sounds_like(word)
