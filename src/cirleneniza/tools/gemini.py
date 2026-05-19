from typing import Any
from loguru import logger
import google.genai as genai
from cirleneniza.config import get_settings


class GeminiClient:
    """Gemini LLM client for Canal Cirlene Niza agents."""

    def __init__(self, model: str = "gemini-2.5-flash"):
        settings = get_settings()
        self.model = model
        self.client = genai.Client(api_key=settings.gemini_api_key)

    def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
    ) -> str:
        """Generate text from Gemini."""
        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }
        contents = [prompt]
        if system:
            contents.insert(0, system)

        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=generation_config,
        )
        return response.text

    def generate_structured(
        self,
        prompt: str,
        schema: dict[str, Any],
        system: str | None = None,
    ) -> dict[str, Any]:
        """Generate structured output matching a Pydantic schema."""
        import json

        response = self.client.models.generate_content(
            model=self.model,
            contents=[system, prompt] if system else [prompt],
            config={
                "response_mime_type": "application/json",
                "response_schema": schema,
            },
        )
        return json.loads(response.text)