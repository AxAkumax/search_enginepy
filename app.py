from flask import Flask, request, jsonify, render_template
from search import *

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

#sample function
def process_query(query):
    # Return the length of the query string
    return len(query)

@app.route('/search', methods=['POST'])
def search():
    try:
        # Get the JSON data from the request body
        data = request.get_json()

        # Extract the query from the incoming data
        query = data.get('query')

        if not query:
            return jsonify({'error': 'No query provided'}), 400

        # Perform the search operation using the query
        results = search.web_search(query)

        if results is not None:
            # Return the results as a JSON response
            return jsonify({'results': results}), 200
        else:
            # Return an appropriate message if no results are found
            return jsonify({'message': 'No results found'}), 404

    except Exception as e:
        # Return an error message with proper HTTP status
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
