const songPage = document.querySelector('.song-page');

if (songPage) {
  const songId = songPage.dataset.songId;
  const translateButton = document.getElementById('translateButton');
  const languageSelect = document.getElementById('languageSelect');
  const statusEl = document.getElementById('translationStatus');
  const originalLyrics = document.getElementById('originalLyrics');
  const translatedLyrics = document.getElementById('translatedLyrics');
  const explanationPanel = document.getElementById('explanationPanel');
  const explanationCache = new Map();

  async function requestTranslation() {
    const targetLanguage = languageSelect.value;
    setStatus('Requesting translation…');
    translateButton.disabled = true;
    translatedLyrics.classList.add('placeholder');
    translatedLyrics.innerHTML = '<li>Loading translation…</li>';

    try {
      const response = await fetch(`/api/songs/${songId}/translate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target_language: targetLanguage }),
      });
      if (!response.ok) {
        throw new Error('Translation request failed');
      }
      const data = await response.json();
      renderTranslation(data.lines || []);
      setStatus('Translation ready');
    } catch (error) {
      console.error(error);
      translatedLyrics.innerHTML = '<li>Translation failed. Please try again later.</li>';
      setStatus('Error contacting GPT');
    } finally {
      translateButton.disabled = false;
    }
  }

  function renderTranslation(lines) {
    translatedLyrics.classList.remove('placeholder');
    translatedLyrics.innerHTML = '';
    if (!Array.isArray(lines) || lines.length === 0) {
      const empty = document.createElement('li');
      empty.textContent = 'GPT returned an empty translation.';
      translatedLyrics.appendChild(empty);
      return;
    }

    lines.forEach((line) => {
      const item = document.createElement('li');
      item.dataset.lineIndex = line.line_index;
      item.innerHTML = `<span class="text">${escapeHtml(line.translation || '')}</span>`;
      if (line.notes) {
        const notes = document.createElement('span');
        notes.className = 'notes';
        notes.textContent = line.notes;
        item.appendChild(notes);
      }
      translatedLyrics.appendChild(item);
    });
  }

  function setStatus(text) {
    statusEl.textContent = text;
    if (text) {
      setTimeout(() => {
        if (statusEl.textContent === text) {
          statusEl.textContent = '';
        }
      }, 4000);
    }
  }

  function escapeHtml(value) {
    const div = document.createElement('div');
    div.textContent = value;
    return div.innerHTML;
  }

  async function handleLineClick(event) {
    const item = event.target.closest('.lyric-line');
    if (!item) return;
    const lineIndex = Number.parseInt(item.dataset.lineIndex, 10);
    setActiveLine(lineIndex);
    if (Number.isNaN(lineIndex)) return;
    if (explanationCache.has(lineIndex)) {
      renderExplanation(explanationCache.get(lineIndex));
      return;
    }
    renderExplanation({ loading: true });
    try {
      const response = await fetch(`/api/songs/${songId}/explain`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ line_index: lineIndex, target_language: languageSelect.value }),
      });
      if (!response.ok) {
        throw new Error('Explanation request failed');
      }
      const data = await response.json();
      explanationCache.set(lineIndex, data.explanation);
      renderExplanation(data.explanation);
    } catch (error) {
      console.error(error);
      renderExplanation({ error: 'Unable to load explanation.' });
    }
  }

  function renderExplanation(data) {
    explanationPanel.innerHTML = '';

    if (data.loading) {
      explanationPanel.innerHTML = '<p class="placeholder">Loading explanation…</p>';
      return;
    }

    if (data.error) {
      explanationPanel.innerHTML = `<p class="placeholder">${data.error}</p>`;
      return;
    }

    const title = document.createElement('h3');
    title.textContent = 'Line context & references';
    explanationPanel.appendChild(title);

    const summary = document.createElement('p');
    summary.textContent = data.summary || 'GPT did not provide a summary for this line.';
    explanationPanel.appendChild(summary);

    if (Array.isArray(data.references) && data.references.length > 0) {
      const heading = document.createElement('h4');
      heading.textContent = 'References';
      explanationPanel.appendChild(heading);

      const list = document.createElement('ul');
      list.className = 'references';
      data.references.forEach((ref) => {
        const item = document.createElement('li');
        const title = ref.title ? `<strong>${escapeHtml(ref.title)}</strong>: ` : '';
        item.innerHTML = `${title}${escapeHtml(ref.description || '')}`;
        list.appendChild(item);
      });
      explanationPanel.appendChild(list);
    } else {
      const placeholder = document.createElement('p');
      placeholder.className = 'placeholder';
      placeholder.textContent = 'No cultural references identified for this line.';
      explanationPanel.appendChild(placeholder);
    }
  }

  function setActiveLine(index) {
    originalLyrics.querySelectorAll('.lyric-line').forEach((item) => {
      const isActive = Number.parseInt(item.dataset.lineIndex, 10) === index;
      item.classList.toggle('active', isActive);
    });
    translatedLyrics.querySelectorAll('li').forEach((item) => {
      const isActive = Number.parseInt(item.dataset.lineIndex, 10) === index;
      item.classList.toggle('active', isActive);
    });
  }

  if (translateButton) {
    translateButton.addEventListener('click', requestTranslation);
  }

  originalLyrics?.addEventListener('click', handleLineClick);
}
