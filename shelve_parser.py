import shelve
import os
import dbm

# Define the paths
shelve_folder = '/Users/akshitaakumalla/search_enginepy/shelve'  # Folder containing shelve files
output_folder = '/Users/akshitaakumalla/search_enginepy/output'  # Folder to save text output

# Ensure the output folder exists
os.makedirs(output_folder, exist_ok=True)

# Iterate over each shelve file in the directory
for filename in os.listdir(shelve_folder):
    if filename.endswith('.db'):
        shelve_path = os.path.join(shelve_folder, filename)
        output_path = os.path.join(output_folder, f"{filename}.txt")
        
        # Open the shelve file and output text file
        try:
            with shelve.open(shelve_path, flag='r', writeback=True) as shelve_db, open(output_path, 'w') as output_file:
                # Iterate through all entries in the shelve database
                for doc_id, data in shelve_db.items():
                    file_path = data.get("file_path", "Unknown path")
                    word_scores = data.get("word_scores", {})
                    word_freq = data.get("wordFreq", {})

                    # Write structured data to the output file
                    output_file.write(f"Document ID: {doc_id}\n")
                    output_file.write(f"File Path: {file_path}\n")
                    output_file.write("Word Scores:\n")
                    for word, score in word_scores.items():
                        output_file.write(f"  {word}: {score}\n")
                    
                    output_file.write("Word Frequencies:\n")
                    for word, freq in word_freq.items():
                        output_file.write(f"  {word}: {freq}\n")
                    
                    output_file.write("\n" + "="*40 + "\n\n")  # Separator between entries

                print(f"Saved contents of {filename} to {output_path}")
        
        except dbm.error as e:
            print(f"Error reading shelve file {shelve_path}: {e}")
