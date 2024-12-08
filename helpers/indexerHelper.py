from collections import defaultdict
import re
import threading
from time import sleep
from bs4 import BeautifulSoup
import pickle
import shelve
import os
import pprint
import math

stop_words = {'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', "aren't", 'as', 'at', 'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by', "can't", 'cannot', 'could', "couldn't", 'did', "didn't", 'do', 'does', "doesn't", 'doing', "don't", 'down', 'during', 'each', 'few', 'for', 'from', 'further', 'had', "hadn't", 'has', "hasn't", 'have', "haven't", 'having', 'he', "he'd", "he'll", "he's", 'her', 'here', "here's", 'hers', 'herself', 'him', 'himself', 'his', 'how', "how's", 'i', "i'd", "i'll", "i'm", "i've", 'if', 'in', 'into', 'is', "isn't", 'it', "it's", 'its', 'itself', "let's", 'me', 'more', 'most', "mustn't", 'my', 'myself', 'no', 'nor', 'not', 'of', 'off', 'on', 'once', 'only', 'or', 'other', 'ought', 'our', 'ours', 'ourselves', 'out', 'over', 'own', 'same', "shan't", 'she', "she'd", "she'll", "she's", 'should', "shouldn't", 'so', 'some', 'such', 'than', 'that', "that's", 'the', 'their', 'theirs', 'them', 'themselves', 'then', 'there', "there's", 'these', 'they', "they'd", "they'll", "they're", "they've", 'this', 'those', 'through', 'to', 'too', 'under', 'until', 'up', 'very', 'was', "wasn't", 'we', "we'd", "we'll", "we're", "we've", 'were', "weren't", 'what', "what's", 'when', "when's", 'where', "where's", 'which', 'while', 'who', "who's", 'whom', 'why', "why's", 'with', "won't", 'would', "wouldn't", 'you', "you'd", "you'll", "you're", "you've", 'your', 'yours', 'yourself', 'yourselves', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'}


class InvertedIndex:
    def __init__(self, pickle_dir, oII, fII, batch_size=100):
        self.pickle_dir = os.path.abspath(pickle_dir)
        if not os.path.exists(self.pickle_dir):
            os.makedirs(self.pickle_dir)

        self.batch_size = batch_size
        self.oII = oII
        self.fII = fII
        self.pklBuffer = defaultdict(lambda: defaultdict(list))
        self.thread_counters = defaultdict(int)

    def flush_all_buffers(self):
        for thread_id in self.pklBuffer.keys():
            if self.pklBuffer[thread_id]:
                self._flush_buffer(thread_id)

    def _get_pickle_path(self, thread_id):
        return os.path.join(self.pickle_dir, f'inverted_index_{thread_id}.pkl')

    def optimizeIndex(self):
        files = [f for f in os.listdir(self.pickle_dir) if f.endswith('.pkl')]

        for char in list("abcdefghijklmnopqrstuvwxyz") + ["others"]:
            sectioned_index = defaultdict(list)

            for file in files:
                path = os.path.join(self.pickle_dir, file)
                with open(path, 'rb') as f:
                    partial_index = pickle.load(f)
                    for term, postings in partial_index.items():
                        first_char = term[0].lower()
                        if char == "others" and not ('a' <= first_char <= 'z'):
                            sectioned_index[term].extend(postings)
                        elif first_char == char:
                            sectioned_index[term].extend(postings)

            output_filename = f'optimizedII_{char}.pkl' if char != "others" else 'optimizedII_others.pkl'
            output_path = os.path.join(self.oII, output_filename)
            with open(output_path, 'wb') as f:
                pickle.dump(sectioned_index, f)


    def _load_pickle(self, path):
        if os.path.exists(path):
            with open(path, 'rb') as f:
                return pickle.load(f)
        return defaultdict(list)

    def _save_pickle(self, path, data):
        with open(path, 'wb') as f:
            pickle.dump(data, f)

    def addDocument(self, doc_id, terms, thread_id, word_scores):
        for term, freq in terms.items():
            score = word_scores.get(term, 0)
            self.pklBuffer[thread_id][term].append((doc_id, freq, score))

        self.thread_counters[thread_id] += 1
        if self.thread_counters[thread_id] >= self.batch_size:
            self._flush_buffer(thread_id)

    def _flush_buffer(self, thread_id):
        path = self._get_pickle_path(thread_id)
        index = self._load_pickle(path)

        for term, postings in self.pklBuffer[thread_id].items():
            index[term].extend(postings)

        print(f"Writing batch to file {path} for thread {thread_id}")
        self._save_pickle(path, index)
        self.pklBuffer[thread_id].clear()
        self.thread_counters[thread_id] = 0

    def get_documents(self, term):

        list_of_docs = []

        first_char = term[0].lower()
        if 'a' <= first_char <= 'z':
            filename = f'optimizedII_{first_char}.pkl'
        else:
            filename = 'optimizedII_others.pkl'

        path = os.path.join(self.oII, filename)

        if os.path.exists(path):
            index = self._load_pickle(path)
            docs = index.get(term, [])
            if docs:
                list_of_docs.extend(docs)

        return list_of_docs
            
class fileMapper:
    def __init__(self):
        self.fileToId = {} # file path -> document unique id
        self.idToFile = {} # document unique id -> file path

        #may need to remove, not sure if multi threading is allowed, but makes it way faster for processing
        self.lock = threading.Lock()
        self.counter = 0

    def addFile(self,filePath):
        with self.lock:
            if filePath not in self.fileToId:
                self.fileToId[filePath] = self.counter
                self.idToFile[self.counter] = filePath
                self.counter +=1
            if (self.counter % 1000 == 0):
                print (f"amount of files iterated over: {self.counter}")
                self.save_file_mapper("file_mapper.pkl")
            return self.counter

    def getFileById(self,id):
        return self.idToFile.get(id,None)
    
    def getFileByPath(self,filePath):
        return self.fileToId.get(filePath,None)
    
    def save_file_mapper(self, filename):
        # Save the fileToId, idToFile, and counter without the lock
        data = {
            'fileToId': self.fileToId,
            'idToFile': self.idToFile,
            'counter': self.counter
        }
        with open(filename, 'wb') as f:
            pickle.dump(data, f)

    def load_file_mapper(self, filename):
        # Load the data and reinitialize the lock
        with open(filename, 'rb') as f:
            data = pickle.load(f)
        self.fileToId = data['fileToId']
        self.idToFile = data['idToFile']
        self.counter = data['counter']
        self.lock = threading.Lock()


def calculateWordScores(text, tagDict):

    #These are just made up, i guess we'll probably have to test and see which ones work best
    importanceScores = {
        "high": 8,
        "middle": 4,
        "low": 2.5,
        "text": 0.75
    }
    
    wordScores = defaultdict(float)
    
    for tag_type, tags in tagDict.items():
        if tag_type in ["h1", "title"]:
            importance = "high"
        elif tag_type in ["h2", "h3", "b", "strong", "em", "i"]:
            importance = "middle"
        elif tag_type in ["h4", "h5", "h6", "a", "p", "span"]:
            importance = "low"
        else:
            continue
        
    #count the score for the words that are in tags
    for tagText in tags:
        for word in tagText.split():
            wordScores[word] += importanceScores[importance]
    
    #count the score for the words that are just in the content
    for word, amount in text.items():
        wordScores[word] += importanceScores["text"] * amount
    
    return dict(wordScores)

def convert_response_to_words(response_content):
    try:
        if isinstance(response_content, bytes):
            response_content = response_content.decode('utf-8', errors='ignore')

        soup = BeautifulSoup(response_content, 'html.parser')
        
        # Remove tags and extract all text within HTML
        for style_or_script in soup(['script', 'style']):
            style_or_script.extract()  # Remove these tags and their content

        text = soup.get_text(separator=' ')  # Updated to get all remaining text
        words = text.split()
        
        return words

    except Exception as e:
        print(f"Error processing response content: {e}")
        return []

def filter_words(words) -> list:
    filtered_words = [word for word in words if word.lower() not in stop_words]
    return filtered_words

def tokenize(text) -> list:
    token_list = []
    token_chars = []
    for char in text.lower():
        if char.isalnum():
            token_chars.append(char)
        elif token_chars:
            token_list.append(''.join(token_chars))
            token_chars = []
    if token_chars:
        token_list.append(''.join(token_chars))  # Add last token if any
    return token_list

def compute_word_frequencies(token_list: list) -> dict:
    frequencies = {}
    for token in token_list:
        frequencies[token] = frequencies.get(token, 0) + 1
    return frequencies

file_list = ['optimized/optimizedII_a.pkl', 'optimized/optimizedII_b.pkl', 'optimized/optimizedII_c.pkl', 
             'optimized/optimizedII_d.pkl', 'optimized/optimizedII_e.pkl', 'optimized/optimizedII_f.pkl', 
             'optimized/optimizedII_g.pkl', 'optimized/optimizedII_h.pkl', 'optimized/optimizedII_i.pkl', 
             'optimized/optimizedII_j.pkl', 'optimized/optimizedII_k.pkl', 'optimized/optimizedII_l.pkl',
             'optimized/optimizedII_m.pkl', 'optimized/optimizedII_n.pkl', 'optimized/optimizedII_o.pkl', 
             'optimized/optimizedII_p.pkl', 'optimized/optimizedII_q.pkl', 'optimized/optimizedII_r.pkl',
             'optimized/optimizedII_s.pkl', 'optimized/optimizedII_t.pkl', 'optimized/optimizedII_u.pkl', 
             'optimized/optimizedII_v.pkl', 'optimized/optimizedII_w.pkl', 'optimized/optimizedII_x.pkl', 
             'optimized/optimizedII_y.pkl', 'optimized/optimizedII_z.pkl', 'optimized/optimizedII_others.pkl']

def total_documents():
    """Calculate total unique documents across all files."""
    unique_docs = set()
    for pkl_file_path in file_list:
        with open(pkl_file_path, 'rb') as pkl_file:
            data = pickle.load(pkl_file)
            for term, postings in data.items():
                for doc_id, _, _ in postings:
                    unique_docs.add(doc_id)
    return len(unique_docs)

def calculate_and_save_tf_idf():
    """Update TF-IDF scores and overwrite files."""
    total_docs = total_documents()
    
    for pkl_file_path in file_list:
        with open(pkl_file_path, 'rb') as pkl_file:
            data = pickle.load(pkl_file)
            new_data = defaultdict(list)
            
            for term, postings in data.items():
                df = len(postings)
                idf = math.log10(total_docs / df) if total_docs > 0 else -1000

                tf_idf_scores = []
                for doc_id, freq, score in postings:
                    tf = 1 + math.log10(freq) if freq > 0 else 0
                    tf_idf = tf * idf
                    tf_idf_scores.append((doc_id, tf_idf, score))
                
                # Sort tf-idf scores with tiebreaker
                tf_idf_scores.sort(key=lambda x: (x[1], -x[2]), reverse=True)
                new_data[term] = tf_idf_scores
            
            print(f"Processed file: {pkl_file_path}, terms processed: {len(new_data)}")
        
        # Overwrite the file with updated data
        with open(pkl_file_path, 'wb') as pkl_file:
            pickle.dump(new_data, pkl_file)
            print(f"Updated and overwrote: {pkl_file_path}")