import time
import json
from typing import Any
from loguru import logger
import anthropic
from cirleneniza.config import get_settings


class MiniMaxClient:
    """MiniMax M2.7 client via Anthropic-compatible API — drop-in for GeminiClient."""

    BASE_URL = "https://api.minimax.io/anthropic"
    DEFAULT_MODEL = "MiniMax-M2.7"

    def __init__(self, model: str = DEFAULT_MODEL):
        settings = get_settings()
        self.model = model
        self.client = anthropic.Anthropic(
            api_key=settings.minimax_api_key,
            base_url=self.BASE_URL,
        )

    def _call_with_retry(self, fn, *args, retries: int = 4, **kwargs):
        """Retry on 503/429 with exponential backoff."""
        delay = 5
        for attempt in range(retries):
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                msg = str(e)
                is_retryable = "503" in msg or "429" in msg or "overloaded" in msg.lower()
                if is_retryable and attempt < retries - 1:
                    logger.warning(
                        f"MiniMax {e.__class__.__name__} (tentativa {attempt+1}/{retries}), aguardando {delay}s..."
                    )
                    time.sleep(delay)
                    delay *= 2
                else:
                    raise

    MIN_TOKENS = 512  # M2.7 uses tokens for thinking — never go below this

    def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
    ) -> str:
        """Generate text from MiniMax M2.7. Same interface as GeminiClient.generate()."""

        def _call():
            kwargs: dict[str, Any] = {
                "model": self.model,
                "max_tokens": max(max_tokens, self.MIN_TOKENS),
                "messages": [{"role": "user", "content": prompt}],
            }
            if system:
                kwargs["system"] = system
            if temperature != 1.0:
                kwargs["temperature"] = temperature
            response = self.client.messages.create(**kwargs)
            # M2.7 returns ThinkingBlock before TextBlock — filter by type
            for block in response.content:
                if getattr(block, "type", None) == "text":
                    return block.text
            raise ValueError(f"No text block in response: {response.content}")

        return self._call_with_retry(_call)

    def generate_structured(
        self,
        prompt: str,
        schema: dict[str, Any],
        system: str | None = None,
    ) -> dict[str, Any]:
        """Generate structured JSON output. Same interface as GeminiClient.generate_structured()."""
        schema_hint = json.dumps(schema, ensure_ascii=False, indent=2)
        structured_system = (
            (system + "\n\n" if system else "")
            + f"Return ONLY valid JSON matching this schema — no markdown, no prose:\n{schema_hint}"
        )

        def _call():
            response = self.client.messages.create(
                model=self.model,
                max_tokens=8192,
                system=structured_system,
                messages=[{"role": "user", "content": prompt}],
            )
            text = next(b.text for b in response.content if getattr(b, "type", None) == "text").strip()
            # strip markdown code fences if present
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            return json.loads(text)

        return self._call_with_retry(_call)
