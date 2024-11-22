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
        resultElement.innerHTML = `<p>The length of your query is: ${data.length}</p>`; // Update the HTML with the length
    })
    .catch(error => {
        console.error('Error:', error);
    });
});
