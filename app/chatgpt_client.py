from __future__ import annotations

import json
import logging
import os
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)

try:  # pragma: no cover - import guard
    from openai import OpenAI  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    OpenAI = None  # type: ignore


class BaseChatGPTClient(ABC):
    """Interface used by the Flask app to talk with GPT models."""

    @abstractmethod
    def translate_song(self, song: dict[str, Any], target_language: str) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def explain_line(
        self, song: dict[str, Any], line_index: int, target_language: str
    ) -> dict[str, Any]:
        raise NotImplementedError


class DummyChatGPTClient(BaseChatGPTClient):
    """Fallback client used in tests or when no API key is provided."""

    def translate_song(self, song: dict[str, Any], target_language: str) -> list[dict[str, Any]]:
        translations = []
        for idx, line in enumerate(song["lyrics"]):
            translations.append(
                {
                    "line_index": idx,
                    "original": line,
                    "translation": f"{line} — перекладено українською" if target_language == "uk" else f"{line} ({target_language})",
                    "notes": "Автоматично згенерований демо-переклад без контексту GPT.",
                }
            )
        return translations

    def explain_line(
        self, song: dict[str, Any], line_index: int, target_language: str
    ) -> dict[str, Any]:
        original = song["lyrics"][line_index]
        return {
            "summary": (
                "Це демонстраційне пояснення для рядка: "
                f"\"{original}\". Реальні пояснення з'являться після підключення ключа OpenAI."
            ),
            "references": [
                {
                    "type": "demo",
                    "title": "Приклад посилання",
                    "description": "У production-версії тут буде опис мемів, культурних відсилок та жаргонізмів.",
                }
            ],
        }


class OpenAIChatGPTClient(BaseChatGPTClient):
    """Client that uses the official OpenAI SDK."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        if OpenAI is None:  # pragma: no cover - guarded above
            raise RuntimeError("openai package is not available")
        self._client = OpenAI(api_key=api_key)
        self.model = model
        self._fallback = DummyChatGPTClient()

    def translate_song(self, song: dict[str, Any], target_language: str) -> list[dict[str, Any]]:
        lyrics = song["lyrics"]
        prompt = self._build_translation_prompt(song, target_language)
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                temperature=0.3,
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a bilingual music translator."
                            " Return JSON with key 'lines' - a list matching the number of lyric lines."
                            " Each item must contain line_index (int), translation (string in the target language),"
                            " and optional notes describing contextual choices."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
            )
            content = response.choices[0].message.content
            data = json.loads(content)
            lines = data.get("lines", [])
            if len(lines) != len(lyrics):
                raise ValueError("Model returned incorrect number of lines")
            normalized = []
            for idx, (line, payload) in enumerate(zip(lyrics, lines)):
                normalized.append(
                    {
                        "line_index": idx,
                        "original": line,
                        "translation": payload.get("translation", ""),
                        "notes": payload.get("notes", ""),
                    }
                )
            return normalized
        except Exception as exc:  # pragma: no cover - network dependent
            logger.warning("Falling back to dummy translation due to error: %s", exc)
            return self._fallback.translate_song(song, target_language)

    def explain_line(
        self, song: dict[str, Any], line_index: int, target_language: str
    ) -> dict[str, Any]:
        prompt = self._build_explanation_prompt(song, line_index, target_language)
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                temperature=0.4,
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a cultural expert who explains song lyrics."
                            " Return JSON with keys summary (string in the listener's language) and references"
                            " (list of objects with title and description)."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
            )
            content = response.choices[0].message.content
            data = json.loads(content)
            summary = data.get("summary", "")
            references = data.get("references", [])
            return {
                "summary": summary,
                "references": references,
            }
        except Exception as exc:  # pragma: no cover - network dependent
            logger.warning("Falling back to dummy explanation due to error: %s", exc)
            return self._fallback.explain_line(song, line_index, target_language)

    def _build_translation_prompt(self, song: dict[str, Any], target_language: str) -> str:
        lyrics_text = "\n".join(f"{idx+1}. {line}" for idx, line in enumerate(song["lyrics"]))
        return (
            "Translate the following song lyrics to {lang} preserving slang, metaphor, and tone."
            " Provide concise context notes when needed."
            " Respond in JSON.\n\n"
            "Song title: {title}\n"
            "Artist: {artist}\n"
            "Original language: {language}\n"
            "Target language: {lang}\n"
            "Lyrics (numbered):\n{lyrics}\n"
        ).format(
            lang=target_language,
            title=song["title"],
            artist=song["artist"],
            language=song["language"],
            lyrics=lyrics_text,
        )

    def _build_explanation_prompt(
        self, song: dict[str, Any], line_index: int, target_language: str
    ) -> str:
        context_lines = []
        for offset in (-1, 0, 1):
            idx = line_index + offset
            if 0 <= idx < len(song["lyrics"]):
                context_lines.append(f"{idx+1}. {song['lyrics'][idx]}")
        context = "\n".join(context_lines)
        return (
            "Provide cultural, linguistic, and internet-culture explanations for the highlighted line"
            " from a song. Reference memes, slang, or past songs when relevant."
            " Respond in JSON with summary and references (each reference should have title and description).\n\n"
            "Song title: {title}\n"
            "Artist: {artist}\n"
            "Listener language: {lang}\n"
            "Highlighted line number: {num}\n"
            "Context lyrics (numbered):\n{context}\n"
        ).format(
            title=song["title"],
            artist=song["artist"],
            lang=target_language,
            num=line_index + 1,
            context=context,
        )


def build_chatgpt_client() -> BaseChatGPTClient:
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    if api_key and OpenAI is not None:
        try:
            return OpenAIChatGPTClient(api_key=api_key, model=model)
        except Exception as exc:  # pragma: no cover - fallback only
            logger.warning("Could not initialize OpenAI client, using dummy instead: %s", exc)
    else:
        if not api_key:
            logger.info("OPENAI_API_KEY not set, using dummy GPT client")
        if OpenAI is None:
            logger.info("openai package unavailable, using dummy GPT client")
    return DummyChatGPTClient()
