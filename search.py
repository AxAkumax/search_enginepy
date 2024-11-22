import re
from time import time
from urllib.parse import urlparse, urlunparse
from indexer import *
from helpers.indexerHelper import *


# This path will change based on who it is. In your own local you have to change this
# NOTE you will also need to change this in indexer.py
shelveDirectory = "C:/Users/shake/Documents/GitHub/search_enginepy/shelve"

def web_search(user_input):
    global shelveDirectory
    # Preprocess user input into stemmed words
    stemmed_words = [stemmer.stem(word) for word in user_input.split()]

    # Retrieve compatible documents using the `query` function
    compatible_docs = query(stemmed_words, inverted_index)

    if not compatible_docs:
        return []  # Return empty list if no compatible documents found
    
    file_mapper = fileMapper()

    # Get the top 5 websites based on the `top5Websites` function
    top_websites = top5Websites(stemmed_words, inverted_index, compatible_docs, shelveDirectory, file_mapper)

    search_results = []
    visited_urls = set()

    # Format the top websites for output
    for website, score in top_websites:
        parsed_url = urlparse(website)
        # Normalize URL by removing file extensions, fragments, and queries
        path_without_extension = re.sub(r'\.\w+$', '', parsed_url.path)
        normalized_url = urlunparse(parsed_url._replace(path = path_without_extension, fragment = '', query = ''))
        
        # Check for duplicate and invalid URLs
        if not re.search(r'\.\w+$', normalized_url) and normalized_url not in visited_urls:
            search_results.append(normalized_url)
            visited_urls.add(normalized_url)

    return search_results