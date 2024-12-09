# Information Retrieval Fall 2024 Assignment 3 M3
Team Members
-------------------
* Phuong Luong
* Akshita Akumalla
* Santiago Ferreyra
* Tyler H. Nguyen

# How to run search engine

1. Make sure all utils/modules listed in requirement.txt are installed.
2. make sure you got "inverted_index.json" and "doc_id.json" ready in the "IR24W-A3-G15" folder. If not, please follow the guidiance below to generate it:
    (1)Place the developer.zip file into the "IR24W-A3-G15" folder. (or manually change line 169 in indexer.py to <PATH-to-developer.zip>)
    (2)On your terminal, Run the following scripts: "python indexer.py"
    (3)Try "Python3 indexer.py" if step2 does not working
    (4)In roughly 20-30 minute, "inverted_index.json" and "doc_id.json" would be generated and placed into "IR24W-A3-G15" folder
   
3. Running the GUI search engine using the following command: "python webGUI.py", a link will soon provided into the bash_prompt/terminal, click the link and you will be able to use the search engine. Press "ctrl-c" on terminal to exit the program

Optional step for text-based UI search engine:
The text based UI got more information and data, which is useful for debugging.
To access the test based UI, simply type "python search.py" and a text-based search engine would appear. use either 'ctrl-c" or type q to ends the program.