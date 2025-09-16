import pytest

from app import create_app
from app.data_loader import load_songs


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    app = create_app({"TESTING": True})
    with app.test_client() as client:
        yield client


def test_list_songs(client):
    response = client.get("/api/songs")
    assert response.status_code == 200
    data = response.get_json()
    assert "songs" in data
    assert len(data["songs"]) == len(load_songs())


def test_translate_song_uses_dummy_when_no_key(client):
    song_id = load_songs()[0]["id"]
    response = client.post(f"/api/songs/{song_id}/translate", json={"target_language": "uk"})
    assert response.status_code == 200
    data = response.get_json()
    song = next(song for song in load_songs() if song["id"] == song_id)
    assert len(data["lines"]) == len(song["lyrics"])
    first_line = data["lines"][0]
    assert first_line["line_index"] == 0
    assert "translation" in first_line


def test_explain_line_structure(client):
    song_id = load_songs()[0]["id"]
    response = client.post(
        f"/api/songs/{song_id}/explain",
        json={"line_index": 0, "target_language": "uk"},
    )
    assert response.status_code == 200
    data = response.get_json()
    explanation = data["explanation"]
    assert "summary" in explanation
    assert "references" in explanation
    assert isinstance(explanation["references"], list)
