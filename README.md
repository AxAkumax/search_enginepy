# Information Retrieval Fall 2024 Assignment 3 M3

## Team Members

* Phuong Luong
* Akshita Akumalla
* Santiago Ferreyra
* Tyler H. Nguyen

## How to run search engine

1. Make sure all utils/modules listed in requirement.txt are installed along with other dependencies.
2. Make sure you initialize the following folder in at root:
    * ii for inverted index
    * optimized (this is where the actual inverted index will be)
    * combined
    * shelve
    * and the developer folder
3. Change all file paths to your own local path
4. In roughly 40-50 minute, "ii" and "optimized" will be populated along with all necessary files.
5. Running the GUI search engine using the following command: "python app.py", a link will soon provided into the bash_prompt/terminal, click the link and you will be able to use the search engine. Press "ctrl-c" on terminal to exit the program

Optional step for text-based UI search engine:
The text based UI got more information and data, which is useful for debugging.
To access the test based UI, simply type "python search.py" and a text-based search engine would appear. use either 'ctrl-c" or type q to ends the program.

## Set of Queries

Here are queries we used to test our search engine:

10 Queries that performed Well:

1. master of informatics
2. professor
3. how to build a search engine
4. ics irvine lab work while attending full time
5. category identify swam in the lake at \~
6. anazji daf 83 2 j aaa >></.,\ 43
7. hello irvine
8. hello and a i stop more swin swimmer path direct
9. 123 jump for the sky 08 now< . 
10. can will went for ^ * i. o. l+

10 Queries that performed poorly:

1. a b 0 1 3 4 6
2. 0 1 2 3 4 5 6 7 8 9 
3. Ö#  @ hello university of irvine 9 3 5 7 3
4. university of 1 2 3 1 califronia irvine
5. irvine professor 1 66 923 48 3
6. 9 8 7 6 5 432 1 1
7. search 1 874 find 0 3 92
8. hello and a i stop more swin swimmer path direct 9 3 1 4 76 4
9. 1 12 23 34 45 56 7
10. can will went for ^ * i. o. l+ 12 4 3 8 

Issues: One of the main issues we had was with inputs that were primarily numbers had performed poorly compared to inputs with just words.
We would want to improve the way we built the inverted index such as using a positional index and this can significantly help the performance and reduce the overall query time for our search engine.
