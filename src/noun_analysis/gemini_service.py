"""Google Gemini API client for long-context text analysis.

Provides async client for Gemini 1.5+ models which support 1M+ token contexts.
Useful for analyzing large amounts of parliamentary speech text.
"""

import asyncio
import json
import os
from typing import Any

import httpx


class GeminiClient:
    """Async client for Google Gemini API."""

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
    DEFAULT_MODEL = "gemini-2.5-flash"

    def __init__(self, api_key: str | None = None):
        """Initialize client.

        Args:
            api_key: Gemini API key. Falls back to GEMINI_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API key required (pass api_key or set GEMINI_API_KEY)")
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "GeminiClient":
        self._client = httpx.AsyncClient(timeout=300.0)  # 5 min for large requests
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()

    async def generate(
        self,
        prompt: str,
        model: str | None = None,
        system_instruction: str | None = None,
        max_retries: int = 3,
    ) -> str:
        """Generate text from prompt.

        Args:
            prompt: The user prompt/input text
            model: Model ID (default: gemini-1.5-flash)
            system_instruction: Optional system instruction
            max_retries: Number of retries for transient errors

        Returns:
            Generated text response
        """
        model = model or self.DEFAULT_MODEL
        url = f"{self.BASE_URL}/models/{model}:generateContent?key={self.api_key}"

        request_body: dict[str, Any] = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.1,  # Low temp for structured output
                "maxOutputTokens": 65536,  # Max for Gemini 2.5 Flash
            },
        }

        if system_instruction:
            request_body["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        for attempt in range(max_retries):
            try:
                response = await self._client.post(
                    url,
                    json=request_body,
                    headers={"Content-Type": "application/json"},
                )

                if response.status_code == 429:
                    wait_time = 2 ** attempt
                    await asyncio.sleep(wait_time)
                    continue

                response.raise_for_status()
                data = response.json()

                candidates = data.get("candidates", [])
                if candidates:
                    content = candidates[0].get("content", {})
                    parts = content.get("parts", [])
                    if parts:
                        return parts[0].get("text", "")

                return ""

            except (httpx.ReadError, httpx.ConnectError, httpx.TimeoutException):
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)

        return ""

    async def analyze_text(
        self,
        text: str,
        prompt: str,
        model: str | None = None,
    ) -> str:
        """Analyze text with a specific prompt.

        Args:
            text: The text to analyze
            prompt: Analysis instructions
            model: Model ID (default: gemini-1.5-flash)

        Returns:
            Analysis result
        """
        full_prompt = f"{prompt}\n\n---\n\n{text}"
        return await self.generate(full_prompt, model=model)

    async def analyze_long_context(
        self,
        texts: list[str],
        prompt: str,
        model: str = "gemini-1.5-pro",
    ) -> str:
        """Analyze multiple texts in a single long-context request.

        Uses Gemini 1.5 Pro for its 1M+ token context window.

        Args:
            texts: List of texts to analyze together
            prompt: Analysis instructions
            model: Model ID (default: gemini-1.5-pro for long context)

        Returns:
            Analysis result
        """
        combined = "\n\n---\n\n".join(texts)
        return await self.analyze_text(combined, prompt, model=model)

    async def summarize_speeches(
        self,
        speeches: list[dict],
        focus: str = "main themes and positions",
    ) -> str:
        """Summarize parliamentary speeches.

        Args:
            speeches: List of speech dicts with 'text', 'speaker', 'party' keys
            focus: What aspect to focus the summary on

        Returns:
            Summary text
        """
        formatted = []
        for speech in speeches:
            speaker = speech.get("speaker", "Unknown")
            party = speech.get("party", "?")
            text = speech.get("text", "")[:2000]
            formatted.append(f"[{speaker} ({party})]\n{text}")

        prompt = f"""Analyze these German Bundestag speeches and summarize the {focus}.
Respond in German. Be concise but comprehensive."""

        return await self.analyze_long_context(formatted, prompt)


async def test_connection(api_key: str | None = None) -> bool:
    """Test Gemini API connection."""
    try:
        async with GeminiClient(api_key) as client:
            result = await client.generate("Say 'OK' if you can read this.", max_retries=1)
            return len(result) > 0
    except Exception as e:
        print(f"Gemini connection failed: {e}")
        return False
