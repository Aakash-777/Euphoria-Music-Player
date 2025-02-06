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

        searchResults.innerHTML = '<div class="loading">Searching...</div>';

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
        
        if (results.length === 0) {
            searchResults.innerHTML = '<div class="no-results">No results found</div>';
            return;
        }

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

    async function playSong(song) {
        currentSong.textContent = 'Loading...';
        
        try {
            const response = await fetch('/get_audio', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ videoId: song.videoId })
            });
            
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Set the audio source to our streaming endpoint
            audioPlayer.src = data.url;
            audioPlayer.load();
            
            const playPromise = audioPlayer.play();
            if (playPromise !== undefined) {
                playPromise
                    .then(() => {
                        currentSong.textContent = song.title;
                    })
                    .catch(e => {
                        console.error('Playback failed:', e);
                        handleError(e);
                    });
            }
        } catch (error) {
            handleError(error);
        }
    }

    function handleError(error) {
        console.error('Error:', error);
        
        const errorMessage = document.createElement('div');
        errorMessage.className = 'error-message';
        errorMessage.textContent = `Error: ${error.message}`;
        searchResults.insertAdjacentElement('beforebegin', errorMessage);
        
        currentSong.textContent = 'Error playing song';
        
        setTimeout(() => {
            errorMessage.remove();
        }, 5000);
    }

    audioPlayer.addEventListener('error', (e) => {
        console.error('Audio player error:', e);
        handleError(new Error('Failed to play audio. Please try again.'));
    });
});