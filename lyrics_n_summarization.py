import logging
import requests
from pathlib import Path
import sys
import pyphen
import pronouncing
logging.basicConfig(level=logging.DEBUG)


# API_KEY = Path(__file__).parent / "secrets" / ".env"
API_KEY = 'thisismyapikeynowfornow'
# if not API_KEY.exists():
#     logging.debug("API key not found")
#     sys.exit()

class OpenRouterClient:
    def __init__(self, model="meta-llama/llama-3-70b-instruct", app_title="Autodidex", referer="https://Autodidex.com"):
        self.api_key = API_KEY
        self.model = model
        self.url = "https://openrouter.ai/api/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "X-Referer": referer,
            "X-Title": app_title
        }

    def _send_request(self, prompt):
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}]
        }

        try:
            response = requests.post(self.url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except requests.exceptions.RequestException as e:
            logging.debug(f"API request failed {e}")
            return None
    
    def generate_lyrics(self, theme, genre):
        prompt = f"""Give me 3 poetic and creative song lyric ideas about '{theme}' , styled like a modern emotional {genre} song"""

        return self._send_request(prompt)
    
    def summarize_text(self, text):
        prompt = f"""Summarize the following text in bullet points: {text}"""
        return self._send_request(prompt)
    
    def cliches_phrase_quotes(self, theme, figure_of_speech):
        prompt = f"Give me a {figure_of_speech} related to {theme}"
        return self._send_request(prompt)

    def critique_lyrics(self, lyrics):
        prompt = """
                I’m going to share some lyrics. I want you to critique them the way a seasoned songwriter, poet, and music critic would. Analyze them for:

                Theme and Emotion: What feelings or story come through? Is it cohesive or scattered?

                Imagery and Metaphor: Are the images powerful, fresh, and evocative?

                Flow and Structure: Comment on rhythm, pacing, rhyme scheme, and overall musicality.

                Word Choice and Diction: Are the words vivid, too plain, or too complex for the tone?

                Authenticity: Does it feel honest, or forced? What kind of persona or voice emerges?

                Suggestions: Offer specific ideas for improvement (e.g., tightening a verse, reworking metaphors, or changing rhyme patterns).

                Keep the tone constructive but real — like a producer giving notes to an artist they believe in. Be analytical, but also interpretive and artistic. Feel free to reference literary or musical comparisons if it helps clarify your points.

                Here are the lyrics:
                """

        prompt += lyrics
        return self._send_request(prompt)




def get_stress_pattern(line):
    """Return a string of U (unstressed) and S (stressed) syllables for a line"""

    words = line.lower().split()
    pattern = []


    for word in words:
        phones = pronouncing.phones_for_word(word)

        if phones:
            logging.debug(phones[0])
            stress = pronouncing.stresses(phones[0])
            
            for c in stress:
                if c in '12': # If this syllable is primary stress or secondary stress
                    pattern.append("S") # add stressed syllable
                else:
                    pattern.append('u') # c == 0, unstressed
        else:
            pattern.append("?") #unknown word
    
    return "".join(pattern)

def alignment_score(patterns):
    """Calculate how aligned the stressed syllables are across multiple lines"""

    if len(patterns) < 2:
        return None

    # Pad patterns to same length
    # max_len = max(len(p) for p in patterns)
    min_len = min(len(p) for p in patterns)
    padded = [p.ljust(min_len) for p in patterns]
    # padded = [p.ljust(max_len) for p in patterns]

    # Compare syllable column by column
    aligned = 0
    total = 0
    # for i in range(max_len):
    for i in range(min_len):
        # Check if all non-space syllbles in this column are the same
        column = [p[i] for p in padded if p[i] != " "]
        if column:
            total += 1
            if all(c == column[0] for c in column):
                aligned += 1

    return aligned / total if total else 0


def highlight_flow(patterns, lines):
    """Return HTML showing flow pattern with color coding"""

    max_len = max(len(p) for p in patterns)
    padded = [p.ljust(max_len) for p in patterns]

    #determine alignment per column
    column_alignment = []
    for i  in range(max_len):
        #loops over every line's stress pattern 
        #looks at the i-th syllable or space
        #skips if it's just a padding space
        #collect only the real syllables into column list
        column = [p[i] for p in padded if p[i] != " "]
        if not column:
            column_alignment.append(None)
        elif all( c == column[0] for c in column ):
            column_alignment.append(True) #aligned
        else:
            column_alignment.append(False) #misaligned
        
    # Build HTML with colors
    html_lines = []
    for line, pattern in zip(lines, padded):
        # Green if it aligns with the other lines
        # Red if it’s off-beat
        # Add it as bold colored HTML
        colored_pattern = ""
        for char, aligned in zip(pattern, column_alignment):
            if char == 'S':
                color = "green" if aligned else "red"
                colored_pattern += f"<span style='color:{color};font-weight:bold'>{char}</span>"
            elif char == 'u':
                colored_pattern += f"<span style='color:gray'>{char}</span>"
            else:
                colored_pattern += " "
        html_lines.append(f"<b>{line}</b><br>{colored_pattern}<br><br>")
    
    logging.debug("".join(html_lines))    
    return "".join(html_lines)
    

class StressedSyllableAnotator():

    def __init__(self, lines):
        self.lines = lines # list

    def analyze_flow_on_stressed_syllables(self):
        """Analyze flow of selected text in editor"""

        patterns = [get_stress_pattern(line) for line in self.lines]
        logging.debug(patterns)

        # Generate color-coded HTML flow map
        html = highlight_flow(patterns, self.lines)

        # Compute alignment score
        score = alignment_score(patterns)

        if score is not None:
            html += f"<b>flow Aligment Score: {score:.2f}</b>"
        
        return html
     
if __name__ == "__main__":
    
    lst = [
        'I am here',
        'Have no fear',
        'All is clear'
        
    ]

    stress_syllables = StressedSyllableAnotator(lst)
    print(stress_syllables.analyze_flow_on_stressed_syllables())
