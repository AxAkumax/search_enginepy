import shelve
import os
import dbm.dumb as dbm

shelve._dbm = dbm

def open_shelve(filename, flag='r', protocol=None, writeback=False):
    return shelve.Shelf(dbm.open(filename, flag), protocol=protocol, writeback=writeback)

def parse_shelve_files(shelve_folder, output_folder):
    total_index_documents = set()
    total_index_documents = set()
    total_unique_tokens = set()
    total_file_size = 0

    os.makedirs(output_folder, exist_ok=True)

    files = set()

    for file in os.listdir(shelve_folder):
        split = file.split('.')
        files.add(split[0] + '.db')

    def get_dir_size(path):
        total = 0
        with os.scandir(path) as allFiles:
            for file in allFiles:
                if file.is_file():
                    total += file.stat().st_size
                elif file.is_dir():
                    total += get_dir_size(file.path)
        return total

    print(f"Files to scan are: {files}")

    # Iterate over each shelve file in the directory
    for filename in files:
        shelve_path = shelve_folder + '/' + filename
        print(f"shelve path : {shelve_path}")
        output_path = os.path.join(output_folder, f"results.txt")
        
        # Open the shelve file and output text file
        try:
            with open_shelve(shelve_path, flag='r') as shelve_db, open(output_path, 'w', encoding='utf-8') as output_file:
                # Iterate through all entries in the shelve database
                for doc_id, data in shelve_db.items():
                    file_path = data.get("file_path", "Unknown path")
                    word_scores = data.get("word_scores", {})
                    word_freq = data.get("wordFreq", {})
                    total_index_documents.add(doc_id)
                    total_unique_tokens.update(word_freq.keys())

                    # Write structured data to the output file
                    output_file.write(f"Document ID: {doc_id}\n")
                    
                    output_file.write(f"File Path: {file_path}\n")

                    output_file.write("Word Scores:\n")
                    for word, score in word_scores.items():
                        output_file.write(f"  {word}: {score}\n")
                    
                    output_file.write("Word Frequencies:\n")
                    for word, freq in word_freq.items():
                        #computing tokens
                        total_unique_tokens.add(word)
                        output_file.write(f"  {word}: {freq}\n")

                    shelve_file_size = os.path.getsize(shelve_path)

                    # Convert the size to kilobytes (KB)
                    shelve_file_size_kb = shelve_file_size  # Convert bytes to KB
                    output_file.write(f"File size: {shelve_file_size_kb} KB")
                    total_file_size = shelve_file_size_kb + total_file_size
                    
                    output_file.write("\n" + "="*40 + "\n\n")  # Separator between entries

                print(f"Saved contents of {filename} to {output_path}")
        except dbm.error as e:
            #Gives errors even though it reads correctly? not really sure why and how to fixi t
            doNothing = 0
            
    print("Total index documents: ", len(total_index_documents))
    print("Total unique tokens: ", len(total_unique_tokens))
    fileSize = get_dir_size(shelve_folder) // 1024
    print("Total size: ", fileSize, " KB")
