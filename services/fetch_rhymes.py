from __future__ import annotations

from Rhyme_engine.rhyme_engine import find_rhymes_api
import logging
logging.basicConfig(level=logging.DEBUG)


def find_rhymes(word: str):
    """
    Returns rhyme results for a given word.
    This function is safe to import into APIs, desktop apps, or other modules.
    """
    logging.debug("finding rhymes...")
    return find_rhymes_api(word)



if __name__ == "__main__":
    word = input("Enter word: ").strip()
    results = find_rhymes(word)

    for rhyme, score in results:
        print(f"{rhyme} -> {score:.2f}")