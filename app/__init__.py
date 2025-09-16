from flask import Flask, jsonify, render_template, request, abort

from .data_loader import load_songs
from .chatgpt_client import build_chatgpt_client


def create_app(test_config: dict | None = None) -> Flask:
    """Application factory."""
    app = Flask(__name__, instance_relative_config=False)

    if test_config:
        app.config.update(test_config)

    songs = load_songs()
    song_lookup = {song["id"]: song for song in songs}
    chat_client = build_chatgpt_client()

    @app.route("/")
    def index():
        return render_template("index.html", songs=songs)

    @app.route("/song/<song_id>")
    def song_details(song_id: str):
        song = song_lookup.get(song_id)
        if not song:
            abort(404)
        return render_template("song.html", song=song)

    @app.get("/api/songs")
    def api_songs():
        query = request.args.get("q", "").strip().lower()
        filtered = songs
        if query:
            filtered = [
                song
                for song in songs
                if query in song["title"].lower()
                or query in song["artist"].lower()
                or any(query in line.lower() for line in song["lyrics"])
            ]
        return jsonify({
            "songs": [
                {
                    "id": song["id"],
                    "title": song["title"],
                    "artist": song["artist"],
                    "language": song["language"],
                }
                for song in filtered
            ]
        })

    @app.get("/api/songs/<song_id>")
    def api_song(song_id: str):
        song = song_lookup.get(song_id)
        if not song:
            abort(404)
        return jsonify(song)

    @app.post("/api/songs/<song_id>/translate")
    def translate_song(song_id: str):
        song = song_lookup.get(song_id)
        if not song:
            abort(404)
        payload = request.get_json(silent=True) or {}
        target_language = payload.get("target_language", "uk").strip()
        if not target_language:
            abort(400, description="target_language is required")
        translation = chat_client.translate_song(song, target_language)
        return jsonify({
            "song_id": song_id,
            "target_language": target_language,
            "lines": translation,
        })

    @app.post("/api/songs/<song_id>/explain")
    def explain_line(song_id: str):
        song = song_lookup.get(song_id)
        if not song:
            abort(404)
        payload = request.get_json(silent=True) or {}
        line_index = payload.get("line_index")
        target_language = payload.get("target_language", "uk").strip()
        if line_index is None or not isinstance(line_index, int):
            abort(400, description="line_index must be provided as integer")
        if line_index < 0 or line_index >= len(song["lyrics"]):
            abort(400, description="line_index is out of range")
        explanation = chat_client.explain_line(song, line_index, target_language)
        return jsonify({
            "song_id": song_id,
            "line_index": line_index,
            "explanation": explanation,
        })

    return app
