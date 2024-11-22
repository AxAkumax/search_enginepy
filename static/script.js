document.getElementById('searchForm').addEventListener('submit', function(event) {
    event.preventDefault(); // Prevent the form from submitting normally

    const query = document.getElementById('searchInput').value.trim(); // Get search input value and remove extra spaces

    if (!query) {
        console.error('Search query is empty!');
        return;
    }

    console.log('Search query:', query);

    fetch('/search', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: query }),
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json(); // Parse JSON response
    })
    .then(data => {
        console.log('Response from server:', data);

        // Check if there's an error in the response
        if (data.error) {
            console.error('Server Error:', data.error);
            return;
        }

        const resultElement = document.getElementById('result');
        if (data.results && data.results.length > 0) {
            // Display each result URL on a new line
            resultElement.innerHTML = data.results.map(item => `<p><a href="${item[0]}" target="_blank">${item[0]}</a> - Score: ${item[1]}</p>`).join('');
        } else {
            resultElement.innerHTML = '<p>No results found.</p>';
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
});
