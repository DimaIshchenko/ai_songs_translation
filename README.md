# AI Songs Translation

A Flask-powered web application that mirrors song lyrics side-by-side with GPT-assisted translations and cultural reference notes. The experience is inspired by Genius and Amalgama but focuses on real-time contextual translations with explanations sourced from the ChatGPT API.

## Features

- 🎵 **Song catalog & search** – browse curated demo tracks or search by title, artist, or lyrics.
- 🌐 **Side-by-side translation** – request a contextual translation (Ukrainian by default) powered by the ChatGPT API.
- 💡 **Interactive explanations** – click any line to see references to memes, slang, and cultural context explained by GPT.
- 🛟 **Offline-friendly fallback** – if no `OPENAI_API_KEY` is provided, the app gracefully falls back to deterministic demo responses so the UI and tests continue to work.

## Getting started

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **(Optional) provide OpenAI credentials**
   ```bash
   export OPENAI_API_KEY="sk-..."
   # optionally choose a different model
   export OPENAI_MODEL="gpt-4o-mini"
   ```

3. **Run the development server**
   ```bash
   flask --app run.py --debug run
   ```
   or simply:
   ```bash
   python run.py
   ```

4. Open `http://127.0.0.1:5000` in your browser.

When the API key is set, translations and explanations will be generated live with GPT. Without a key, the application still runs with illustrative stub responses so you can explore the UI.

## Running tests

```bash
pytest
```

## Project structure

```
app/
  __init__.py          # Flask application factory and API routes
  chatgpt_client.py    # OpenAI integration with a fallback dummy client
  data/songs.json      # Demo catalog of original songs
  static/              # CSS and JavaScript assets
  templates/           # Jinja2 templates for catalog and song pages
run.py                 # Entry point for running the app locally
requirements.txt       # Python dependencies
```

## Extending the catalog

Add more songs to `app/data/songs.json` with the following structure:

```json
{
  "id": "unique_identifier",
  "title": "Song Title",
  "artist": "Artist",
  "language": "Original language",
  "description": "Short teaser for the song",
  "lyrics": [
    "First line",
    "Second line"
  ]
}
```

Restart the server to load the updated catalog.

---

> **Note**: Remember that calling the real OpenAI API incurs costs according to your plan. Use the dummy fallback or add caching if you plan to experiment heavily.
