import requests
import logging
logging.basicConfig(level=logging.DEBUG)

class WordFinder:
    BASE_URL = "https://api.datamuse.com/words"

    def __init__(self, max_results=20, topics=None):
        self.max_results = max_results
        self.topics = topics  # Can be a string like "music,poetry"

    def _get_words(self, param, word):
        params = {
            param: word,
            "max": self.max_results
        }
        if self.topics:
            params["topics"] = self.topics

        response = requests.get(self.BASE_URL, params=params)
        if response.status_code == 200:
            return [item["word"] for item in response.json()]
        else:
            print(f"Error {response.status_code}: {response.text}")
            return []

    def rhymes_with(self, word):
        """Returns perfect rhymes"""
        return self._get_words("rel_rhy", word)

    def synonyms_for(self, word):
        """Returns synonyms"""
        return self._get_words("rel_syn", word)

    def antonyms_for(self, word):
        """Returns antonyms"""
        return self._get_words("rel_ant", word)

    def sounds_like(self, word):
        """Retruns phonetically similar words"""
        return self._get_words("sl", word)

    def triggers(self, word):
        """Returns the commonly appear near or are associated with the word"""
        return self._get_words("rel_trg", word)

    def adjectives_for(self, noun):
        """Returns adjective that describe a noun"""
        return self._get_words("rel_jjb", noun)

    def nouns_described_by(self, adjective):
        """Returns nouns described by a given adjective"""
        return self._get_words("rel_jja", adjective)

    def spelled_like(self, pattern):  # Use wildcards like ho??
        """Returns words that match a spelling pattern. You can use wildcars like * or ?"""
        return self._get_words("sp", pattern)
    

    def homophones_for(self, word):
        """Returns homophones"""
        return self._get_words("rel_hom", word)

    def more_specific_than(self, word):
        """Returns hyponyms - more specific terms"""
        return self._get_words("rel_spc", word)

    def slant_rhymes(self, word):
        """
            * Gets perfect rhymes.
            * Gets "sounds like" words.
            * Subtracts perfect rhymes from the sounds-like list → leaving you with **slant rhymes**.
        """
        rhymes = set(self.rhymes_with(word))
        sounds_like = set(self.sounds_like(word))
        near_rhymes = sounds_like - rhymes  # Remove perfect rhymes
        return list(near_rhymes)

    def more_general_than(self, word):
        """"""
        return self._get_words("rel_gen", word)

# if __name__ == "__main__":
#     wf = WordFinder(max_results=10, topics="music,poetry")

#     logging.debug("🎤 Rhymes with 'dream':", wf.rhymes_with("dream"))
    # logging.debug("🧠 Synonyms for 'bright':", wf.synonyms_for("bright"))
    # logging.debug("🌑 Antonyms of 'dark':", wf.antonyms_for("dark"))
    # logging.debug("🧩 Sounds like 'nite':", wf.sounds_like("nite"))
    # logging.debug("🔗 Words triggered by 'ocean':", wf.triggers("ocean"))
    # logging.debug("🎨 Adjectives for 'voice':", wf.adjectives_for("voice"))
    # logging.debug("💡 Nouns described by 'lonely':", wf.nouns_described_by("lonely"))
    # logging.debug("🕵️ Spelled like 'glow*':", wf.spelled_like("glow*"))
    # logging.debug("👯 Homophones of 'knight':", wf.homophones_for("knight"))
    # logging.debug("🧬 More specific than 'emotion':", wf.more_specific_than("emotion"))
    # logging.debug("🧠 More general than 'violin':", wf.more_general_than("violin"))
