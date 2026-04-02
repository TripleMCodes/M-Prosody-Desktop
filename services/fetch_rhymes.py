from Rhyme_engine.rhyme_engine import find_rhymes_api

def find_rhymes(word:str):

    results = find_rhymes_api(word)
    print(results)

find_rhymes()
