from urllib.parse import urlparse, urlunparse
from parser import convert_response_to_words, compute_word_frequencies
from nltk.stem import PorterStemmer
from bs4 import BeautifulSoup
import lxml
import nltk
import json
import os
from helpers.indexerHelper import *
from concurrent.futures import ThreadPoolExecutor, as_completed
import shelve
import dbm.dumb as dbm
from shelve_parser import parse_shelve_files
import time
import heapq

import pprint

stemmer = PorterStemmer()

shelve._dbm = dbm

print(nltk.__version__)

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
        with open(filepath, "r+", encoding='utf-8') as file:
            file_data = json.load(file)
    except json.JSONDecodeError:
        return ""
    
    content = BeautifulSoup(file_data["content"], "lxml")
    for element in content(["script", "style"]):
        element.decompose()

    for anchor in content.find_all('a', href=True):
        anchor.decompose()

    text = ' '.join(content.get_text(separator=' ').split())

    tagDict = {
        #high importance
    "h1": [tag.get_text(strip=True) for tag in content.find_all("h1")],
    "title": [tag.get_text(strip=True) for tag in content.find_all("title")],

        #middle importance
    "h2": [tag.get_text(strip=True) for tag in content.find_all("h2")],
    "h3": [tag.get_text(strip=True) for tag in content.find_all("h3")],
    "b": [tag.get_text(strip=True) for tag in content.find_all("b")],
    "strong": [tag.get_text(strip=True) for tag in content.find_all("strong")],
    "em": [tag.get_text(strip=True) for tag in content.find_all("em")],
    "i": [tag.get_text(strip=True) for tag in content.find_all("i")],

        #low importance
    "h4": [tag.get_text(strip=True) for tag in content.find_all("h4")],
    "h5": [tag.get_text(strip=True) for tag in content.find_all("h5")],
    "h6": [tag.get_text(strip=True) for tag in content.find_all("h6")],
    "a": [tag.get_text(strip=True) for tag in content.find_all("a")],
    "p": [tag.get_text(strip=True) for tag in content.find_all("p")],
    "span": [tag.get_text(strip=True) for tag in content.find_all("span")]
    }

    return {"text": text, "tagDict": tagDict} #string > list to stem > token > freq.

def index_document(file_path, inverted_index, file_mapper):
    thread_id = threading.get_ident()
    thread_name = threading.current_thread().name
    shelve_filename = f"shelve/thread_data_{thread_id}.db"

    print(f"[{thread_name}] Processing file: {file_path}")

    #Get the important information from the file. The text and the tagDict that will be used in later portions, like m2/3
    parsed_data = json_parse(file_path)

    if parsed_data == "":
        print(f"[{thread_name}] No content found in {file_path}")
        return None

    text = parsed_data["text"]
    tagDict = parsed_data["tagDict"]

    wordFreq = convert_freq_stemming(text)
    word_scores = calculateWordScores(wordFreq, tagDict)

    doc_id = file_mapper.addFile(file_path)

    try:
        with open_shelve(shelve_filename, flag='c', protocol=2, writeback=True) as shelve_db:
            shelve_db[str(doc_id)] = {
                "file_path": file_path,
                "word_scores": word_scores,
                "wordFreq": wordFreq
            }
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")

    inverted_index.addDocument(doc_id, wordFreq)

def open_shelve(filename, flag='c', protocol=None, writeback=False):
    return shelve.Shelf(dbm.open(filename, flag), protocol=protocol, writeback=writeback)

def run(indexer, file_mapper, document_paths, invertedIndexLocation, max_threads=10):
    with ThreadPoolExecutor(max_threads) as executor:
        fileTask = {executor.submit(index_document, file_path, indexer, file_mapper): file_path for file_path in document_paths}

        for future in as_completed(fileTask):
            file_path = fileTask[future]
            # Wait for the task to finish. This is to ensure the thread doesn't start processing another file until it has finished with the file it is already on.
            try:
                future.result()
            except Exception as e:
                print(f"Error processing file {file_path}: {e}")

    return indexer

def setup_shelve_dir(shelve_dir):
    if not os.path.exists(shelve_dir):
        os.makedirs(shelve_dir)

# use to search index through cmd for debugging
def cmd_search(inverted_index, shelveDirectory, file_mapper):
    while True:
        user_input = input("Enter your inputs (Q to quit): ")

        if user_input.lower() != "q":
            # Stem the user's input
            stemmed_words = [stemmer.stem(word) for word in user_input.split()]

            start_time = time.time()
            # Use the query function to get compatible websites
            compatible_websites = query(stemmed_words, inverted_index)

            if not compatible_websites:
                print("No results found!!!")
                continue

            # Use top5Websites to score and rank the websites
            top_results = top5Websites(
                listOfWords = stemmed_words,
                index = inverted_index,
                websites = compatible_websites,
                shelveDir = shelveDirectory,
                fileMapper = file_mapper
            )
            search_time = (time.time() - start_time) * 1000
            print(f"This search took {search_time:.2f} ms")

            if not top_results:
                print("No results found after ranking!!!")
                continue

            print(f"Top 5 search results for '{user_input}':")
            for rank, (website_path, score) in enumerate(top_results, start=1):
                # Extract the URL from the JSON file associated with the website
                try:
                    with open(website_path, 'r', encoding='utf-8') as json_file:
                        json_data = json.load(json_file)
                        url = json_data.get('url')  # Assuming the URL is stored under 'url' key
                        if url:
                            print(f"{rank}. {url} (Score: {score:.2f})")
                        else:
                            print(f"{rank}. URL not found (Score: {score:.2f})")
                except (FileNotFoundError, json.JSONDecodeError) as e:
                    print(f"Error reading JSON file {website_path}: {e}")
                    print(f"{rank}. {website_path} (Score: {score:.2f})")

        else:
            print("Exiting search...")
            break

def web_search(user_input, inverted_index, shelveDirectory, file_mapper):
    # Preprocess user input into stemmed words
    stemmed_words = [stemmer.stem(word) for word in user_input.split()]

    # Retrieve compatible documents using the `query` function
    compatible_docs = query(stemmed_words, inverted_index)

    if not compatible_docs:
        return []  # Return empty list if no compatible documents found
    
    # Get the top 5 websites based on the `top5Websites` function
    top_websites = top5Websites(stemmed_words, inverted_index, compatible_docs, shelveDirectory, file_mapper)

    search_results = []
    visited_urls = set()

    # Format the top websites for output
    for website, score in top_websites:
        try:
            with open(website, 'r', encoding='utf-8') as json_file:
                json_data = json.load(json_file)
                url = json_data.get('url')  # Assuming the URL is stored under 'url' key
                if url:
                    parsed_url = urlparse(url)
                    # Normalize URL by removing file extensions, fragments, and queries
                    path_without_extension = re.sub(r'\.\w+$', '', parsed_url.path)
                    normalized_url = urlunparse(parsed_url._replace(path=path_without_extension, fragment='', query=''))
                    
                    # Check for duplicate and invalid URLs
                    if not re.search(r'\.\w+$', normalized_url) and normalized_url not in visited_urls:
                        search_results.append((normalized_url, score))
                        visited_urls.add(normalized_url)
                else:
                    print(f"URL not found in {website} (Score: {score:.2f})")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error reading JSON file {website}: {e}")
            # If the URL is missing or there's an error, still append the website path and score
            search_results.append((website, score))

    return search_results

def main():
    # This path will change based on who it is. In your own local you have to change this
    # NOTE you will also need to change this in search.py
    main_path = "C:/Users/shake/Documents/GitHub/search_enginepy"
    document_folder = "C:/Users/shake/Documents/GitHub/search_enginepy/ANALYST"
    invertedIndexLocation = "C:/Users/shake/Documents/GitHub/search_enginepy/ii"
    shelveDirectory = "C:/Users/shake/Documents/GitHub/search_enginepy/shelve"
    setup_shelve_dir(invertedIndexLocation)

    # go recursively and get all the files in the subdirectory
    document_paths = []
    for root, dirs, files in os.walk(document_folder):
            for file in files:
                if file.endswith('.json'):
                    document_paths.append(os.path.join(root, file))

    file_mapper = fileMapper() 
    inverted_index = InvertedIndex(invertedIndexLocation)
    inverted_index = run(inverted_index, file_mapper, document_paths, invertedIndexLocation)

    parse_shelve_files(shelveDirectory,main_path+"/output/")
    return inverted_index, shelveDirectory, file_mapper
    

def top5Websites(listOfWords, index, websites, shelveDir, fileMapper):
    documentWordScores = defaultdict(float)
    websiteNames = {fileMapper.getFileById(website - 1): website for website in websites}


    # Get all of the files from the shelve directory, there is going to be 1 per thread
    files = set()
    for file in os.listdir(shelveDir):
        split = file.split('.')
        files.add(split[0] + '.db')


    for fileName in files:
        shelve_path = os.path.join(shelveDir, fileName)
        try:
            with dbm.open(shelve_path, flag='r') as shelve_db:
                for websitePath, websiteId in websiteNames.items():

                    # Some weird shelve specific thing, it has to be encoded so that you can read it.
                    docBytes = shelve_db.get(str(websiteId).encode(), None)
                    if docBytes is None:
                        # print("data is empty, this should never happen if it got up to this place. Something went wrong")
                        continue
                    
                    # Another weird shelve specific thing. Have to deserialize it, since I think its byte encoded? IDRK
                    docData = pickle.loads(docBytes)

                    filePath = docData.get('file_path')
                    if filePath is None:
                        #once again, this should never happen. if it gets inside this, something went wrong
                        continue

                    tempScore = 0
                    word_freq = docData.get('wordFreq', {})
                    for word in listOfWords:
                        tempScore += word_freq.get(word, 0)

                    documentWordScores[websitePath] += tempScore

        except dbm.error as e:
            print(f"Error opening shelve {shelve_path}: {e}")
        except Exception as e:
            print(f"Unexpected error with shelve {shelve_path}: {e}")

    # Kth largest, O(N * log(5)) instead of sorting.
    top5_docs = heapq.nlargest(5, documentWordScores.items(), key=lambda x: x[1])
    top5_websites = [tuple([website,score]) for website, score in top5_docs]

    return top5_websites


def query(stemmed, invertedIndex):

    compatible_docs = None
    for word in stemmed:
        docs = invertedIndex.get_documents(word)
        if compatible_docs is None:
            compatible_docs = docs
        else:
            compatible_docs = compatible_docs.intersection(docs)

    return compatible_docs

if __name__ == "__main__":
     # Run the setup and indexing process
    inverted_index, shelveDirectory, file_mapper = main()

    # Now call cmd_search with the setup data to avoid calling in app.py
    cmd_search(inverted_index, shelveDirectory, file_mapper)