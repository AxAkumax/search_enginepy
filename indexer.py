from urllib.parse import urlparse, urlunparse
from parser import convert_response_to_words, compute_word_frequencies
from nltk.stem import PorterStemmer
from bs4 import BeautifulSoup
import lxml
import nltk
import json
import os
from helpers.indexerHelper import *
from concurrent.futures import ThreadPoolExecutor, as_completed, ProcessPoolExecutor
import shelve
import dbm.dumb as dbm
from shelve_parser import parse_shelve_files
import time
import heapq
import pickle

import pprint

stemmer = PorterStemmer()

shelve._dbm = dbm

print(nltk.__version__)

def isBuilt(location):
    files = set()
    for file in os.listdir(location):
        files.add(file)
    return len(files) > 0


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

    #Get the important information from the file. The text and the tagDict that will be used in later portions, like m2/3
    parsed_data = json_parse(file_path)

    if parsed_data == "":
        print(f"[{thread_name}] No content found in {file_path}")
        return None

    text = parsed_data["text"]
    tagDict = parsed_data["tagDict"]

    wordFreq = convert_freq_stemming(text)
    wordScores = calculateWordScores(wordFreq, tagDict)

    doc_id = file_mapper.addFile(file_path)

    # try:
    #     with open_shelve(shelve_filename, flag='c', protocol=2, writeback=True) as shelve_db:
    #         shelve_db[str(doc_id)] = {
    #             "file_path": file_path,
    #             "word_scores": word_scores,
    #             "wordFreq": wordFreq
    #         }
    # except Exception as e:
    #     print(f"Error processing file {file_path}: {e}")

    inverted_index.addDocument(doc_id, wordFreq, thread_id, wordScores)

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

def main():
    # This path will change based on who it is. In your own local you have to change this

    main_path = "/Users/akshitaakumalla/search_enginepy"
    document_folder = "/Users/akshitaakumalla/search_enginepy/DEV"
    invertedIndexLocation = "/Users/akshitaakumalla/search_enginepy/ii"
    invertedIndexOptimized = "/Users/akshitaakumalla/search_enginepy/optimized"
    invertedIndexCombined= "/Users/akshitaakumalla/search_enginepy/combined"
    shelveDirectory = "/Users/akshitaakumalla/search_enginepy/shelve"
    setup_shelve_dir(invertedIndexLocation)

    # go recursively and get all the files in the subdirectory
    document_paths = []
    for root, dirs, files in os.walk(document_folder):
            for file in files:
                if file.endswith('.json'):
                    document_paths.append(os.path.join(root, file))

    file_mapper = fileMapper() 
    inverted_index = InvertedIndex(invertedIndexLocation, invertedIndexOptimized, invertedIndexCombined)
    if (not isBuilt(invertedIndexLocation)):
        print('inverted index is not built, building it right now')
        inverted_index = run(inverted_index, file_mapper, document_paths, invertedIndexLocation)
        inverted_index.flush_all_buffers()
        inverted_index.optimizeIndex()
        calculate_and_save_tf_idf()
    
    # else:
    #     #add renewed optimized index with tf-df sorted list of doc-id
    #     calculate_and_save_tf_idf()
    
    try:
        file_mapper.load_file_mapper("file_mapper.pkl")
        print("File mapper loaded successfully.")
    except FileNotFoundError:
        print("file_mapper.pkl not found, starting with an empty file mapper.")

    parse_shelve_files(invertedIndexLocation,main_path+"/output/")
    return inverted_index, file_mapper, invertedIndexOptimized

# use to search index through cmd for debugging
def cmd_search(inverted_index, file_mapper, invertedIndexOptimized):
    while True:
        user_input = input("Enter your inputs (Q to quit): ")

        if user_input.lower() != "q":
            # Stem the user's input
            stemmed_words = [stemmer.stem(word) for word in user_input.split()]
            print(stemmed_words)
            
            if not stemmed_words:
                print("No valid search terms provided!")
                continue

            start_time = time.time()
            # Use top5Websites to score and rank the websites
            top_results = top5Websites(stemmed_words, inverted_index, file_mapper, invertedIndexOptimized)
            search_time = (time.time() - start_time) * 100
            print(f"This search took {search_time:.2f} ms")

            if not top_results:
                print("No results found after ranking!!!")
                continue
            
            visited_urls = set()
            print(f"Top 5 search results for '{user_input}':")
            printed_results = 0  # Track the number of valid results printed

            for rank, (website_path, score_tuple) in enumerate(top_results, start=1):
                if printed_results >= 5:
                    break
                score = score_tuple[1]
                
                try:
                    with open(website_path, 'r', encoding='utf-8') as json_file:
                        json_data = json.load(json_file)
                        url = json_data.get('url')
                        if url:
                            parsed_url = urlparse(url)
                            # Normalize URL by removing file extensions, fragments, and queries
                            path_without_extension = re.sub(r'\.\w+$', '', parsed_url.path)
                            normalized_url = urlunparse(parsed_url._replace(path=path_without_extension, fragment='', query=''))
                            
                            # Check for duplicate and invalid URLs
                            if not re.search(r'\.\w+$', normalized_url) and normalized_url not in visited_urls:
                                print(f"{printed_results + 1}. {normalized_url} (Query Intersection: {score:.2f})")
                                visited_urls.add(normalized_url)
                                printed_results += 1 
                            else:
                                continue 
                        else:
                            continue 
                except (FileNotFoundError, json.JSONDecodeError) as e:
                    print(f"Error reading JSON file {website_path}: {e}")
                    print(f"{printed_results + 1}. {website_path} (Query Intersection: {score:.2f})")
                    printed_results += 1 

        else:
            print("Exiting search...")
            break

def web_search(user_input, inverted_index, file_mapper, invertedIndexOptimized):
    # Preprocess user input into stemmed words
    stemmed_words = [stemmer.stem(word) for word in user_input.split()]

    if not stemmed_words:
        print("No valid search terms provided!")
    
    start_time = time.time()
    # Use top5Websites to score and rank the websites
    top_websites = top5Websites(stemmed_words, inverted_index, file_mapper, invertedIndexOptimized)
    search_time = (time.time() - start_time) * 100
    print(f"This search took {search_time:.2f} ms")

    if not top_websites:
        print("No results found after ranking!!!")
    
    search_results = []
    visited_urls = set()
    printed_results = 0

    # Format the top websites for output
    for website, score in top_websites:
        if printed_results >= 5:
            break
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
                        printed_results += 1
                    else:
                                #print("invalid link")
                                continue
                else:
                    continue
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error reading JSON file {website}: {e}")
            # If the URL is missing or there's an error, still append the website path and score
            search_results.append((website, score))

    return search_results, search_time

def top5Websites(stemmed, invertedIndex, file_mapper, optimizedIndex):
    documentWordScores = defaultdict(list)  # Use list to store tuples
    websiteNames = set()
    websiteData = {}

    for token in stemmed:
        token_docs = invertedIndex.get_documents(token)
        #print(f"Token: {token}, Documents: {token_docs}")
        for doc_id, freq, wordScore in token_docs:
            file_path = file_mapper.getFileById(doc_id - 1)
            websiteNames.add(file_path)
            if file_path not in websiteData:
                websiteData[file_path] = []
            # Append frequency and token as a tuple to websiteData
            websiteData[file_path].append((freq, token))

    # Get all pickle files from the optimizedIndex directory
    files = [f for f in os.listdir(optimizedIndex) if f.endswith(".pkl")]

    for fileName in files:
        shelve_path = os.path.join(optimizedIndex, fileName)

        if not os.path.exists(shelve_path):
            print(f"Pickle file {shelve_path} does not exist.")
            continue

        try:
            with open(shelve_path, "rb") as f:
                data = pickle.load(f)

                for website in websiteNames:
                    if website not in websiteData:
                        print(f"Website {website} not found in websiteData!")
                        continue

                    # Combine scores for each token related to the website
                    for freq, token in websiteData[website]:
                        documentWordScores[website].append((freq, token))

        except Exception as e:
            print(f"Error opening pickle file {shelve_path}: {e}")

    # Aggregate scores and sort by relevance
    aggregated_scores = {
        website: (sum(freq for freq, _ in scores), len(set(token for _, token in scores)))
        for website, scores in documentWordScores.items()
    }

    # Get top 5 websites based on aggregated scores
    top5_docs = heapq.nlargest(10, aggregated_scores.items(), key=lambda x: x[1])
    top5_websites = [tuple([website, score]) for website, score in top5_docs]

    return top5_websites

if __name__ == "__main__":
    # Run the setup and indexing process
    inverted_index, file_mapper, invertedIndexOptimized = main()
    
    # Start the search functionality
    cmd_search(inverted_index, file_mapper, invertedIndexOptimized)
