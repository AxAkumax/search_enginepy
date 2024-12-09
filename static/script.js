document.getElementById('searchForm').addEventListener('submit', function(event) {
    event.preventDefault(); // Prevent the form from submitting normally

    const query = document.getElementById('searchInput').value.trim(); // Get search input value and remove extra spaces
    const resultElement = document.getElementById('result');
    
    if (!query) {
        console.error('Search query is empty!');
        resultElement.innerHTML = '';
        return;
    }

    console.log('Search query:', query);

    resultElement.innerHTML = '<p>Finding results...</p>'; // Show the loading message


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
            // Display the query response time
            const responseTimeElement = `<p>Query Response Time: ${data.responseTime} ms</p>`;
            // Display each result URL and the last value of the tuple (the second element of the nested tuple) as the score
            resultElement.innerHTML = responseTimeElement + data.results.map(item => {
                // Access the last value of the nested tuple (item[1][1])
                const lastValue = item[1][1];
                return `<p><a href="${item[0]}" target="_blank">${item[0]}</a> </br> Query Intersection: ${lastValue}</p>`;
            }).join('');
        } else {
            resultElement.innerHTML = '<p>No results found.</p>';
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
});
