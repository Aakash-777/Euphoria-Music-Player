document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    const searchButton = document.getElementById('searchButton');
    const searchResults = document.getElementById('searchResults');
    const audioPlayer = document.getElementById('audioPlayer');
    const currentSong = document.getElementById('currentSong');

    searchButton.addEventListener('click', performSearch);
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            performSearch();
        }
    });

    function performSearch() {
        const query = searchInput.value.trim();
        if (!query) return;

        fetch('/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query: query })
        })
        .then(response => response.json())
        .then(displayResults)
        .catch(handleError);
    }

    function displayResults(results) {
        searchResults.innerHTML = '';
        
        results.forEach(result => {
            const songItem = document.createElement('div');
            songItem.className = 'song-item';
            songItem.innerHTML = `
                <img src="${result.thumbnail}" alt="Thumbnail">
                <div class="song-info">
                    <div class="song-title">${result.title}</div>
                </div>
            `;
            
            songItem.addEventListener('click', () => playSong(result));
            searchResults.appendChild(songItem);
        });
    }

    function playSong(song) {
        fetch('/get_audio', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ videoId: song.videoId })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            audioPlayer.src = data.url;
            audioPlayer.play();
            currentSong.textContent = song.title;
        })
        .catch(handleError);
    }

    function handleError(error) {
        const errorMessage = document.createElement('div');
        errorMessage.className = 'error-message';
        errorMessage.textContent = `Error: ${error.message}`;
        searchResults.insertAdjacentElement('beforebegin', errorMessage);
        
        setTimeout(() => {
            errorMessage.remove();
        }, 5000);
    }
});