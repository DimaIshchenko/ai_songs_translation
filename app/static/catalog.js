const searchInput = document.getElementById('searchInput');
const songList = document.getElementById('songList');

async function fetchSongs(query = '') {
  const params = new URLSearchParams();
  if (query) {
    params.append('q', query);
  }
  const response = await fetch(`/api/songs?${params.toString()}`);
  if (!response.ok) {
    console.error('Failed to load songs');
    return;
  }
  const data = await response.json();
  renderSongs(data.songs);
}

function renderSongs(songs) {
  songList.innerHTML = '';
  if (songs.length === 0) {
    const empty = document.createElement('li');
    empty.textContent = 'No songs found. Try another search.';
    empty.className = 'song-card empty-state';
    songList.appendChild(empty);
    return;
  }
  songs.forEach((song) => {
    const item = document.createElement('li');
    item.className = 'song-card';
    item.dataset.songId = song.id;
    item.innerHTML = `
      <a href="/song/${song.id}">
        <h2>${song.title}</h2>
        <p class="artist">${song.artist} · ${song.language}</p>
        <p class="description">Click to open the side-by-side translation.</p>
      </a>`;
    songList.appendChild(item);
  });
}

if (searchInput) {
  let debounceHandle;
  searchInput.addEventListener('input', (event) => {
    clearTimeout(debounceHandle);
    const query = event.target.value.trim();
    debounceHandle = setTimeout(() => fetchSongs(query), 200);
  });
}
