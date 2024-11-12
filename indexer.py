from parser import convert_response_to_words, compute_word_frequencies
from nltk.stem import PorterStemmer
from bs4 import BeautifulSoup
import lxml
import nltk
import json

stemmer = PorterStemmer()
def convert_freq_stemming(response_content):
    try:
        text = convert_response_to_words(response_content)
        #stopwords
        stem_word = [stemmer.stem(word) for word in text]
        frequency = compute_word_frequencies(stem_word)
    except Exception as e:
        print(f"Error processing stemmed token frequency: {e}")
        return {}
    return frequency
    pass

def json_parse(filepath):
    try:
        with open(filepath, "r") as file:
            file_data = json.load(file)
    except json.JSONDecodeError:
        return ""
    
    content = BeautifulSoup(file_data["content"], "lxml")
    for element in content(["script", "style"]):
        element.decompose()

    text = content.get_text(separator=" ")

    important_text = content.find_all(["h1", "h2", "h3", "b", "a"], string = True)
    important_content = ' '.join(tags.string for tags in important_text)

    return f"{text} {important_content}" #string > list to stem > token > freq.


def indexer:
    pass


def run:
    pass