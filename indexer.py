from parser import convert_response_to_words, compute_word_frequencies
from nltk.stem import PorterStemmer
import nltk

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


def indexer:
    pass


def run:
    pass