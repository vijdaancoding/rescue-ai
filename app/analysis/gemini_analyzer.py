"""
Gemini 2.5 Flash analysis for spam probability and urgency detection.

Uses the google-genai SDK (replaces deprecated google-generativeai).
Sends the accumulated call transcript to Gemini and returns a structured JSON
with spam_score and urgency classification. Runs fully async so it never blocks
the voice pipeline.

On 429 rate-limit errors the retry_delay from the API response is respected before
retrying once. All other errors fall back to safe defaults immediately.
"""
import asyncio
import json
import logging
import os
import re

from google import genai
from google.genai import types
from google.api_core.exceptions import ResourceExhausted

from app.core.config import settings

logger = logging.getLogger(__name__)

_MODEL_NAME = "gemini-2.5-flash"
_MAX_RETRY_WAIT = 60  # cap retry sleep at 60s so we don't stall the pipeline

_SYSTEM_PROMPT = """You are an AI analyst for a Pakistani emergency rescue call center (1122/911).
Analyze the provided call transcript and return ONLY valid JSON with this exact structure:

{
  "spam_score": <float 0.0-1.0, probability this is a prank or spam call>,
  "spam_label": <"spam" if spam_score >= 0.5 else "not_spam">,
  "urgency_score": <float 0.0-1.0, how urgent the emergency is>,
  "urgency_label": <"critical" | "high" | "medium" | "low">,
  "reasoning": <one concise sentence explaining your assessment>,
  "dispatch_recommendation": <array of zero or more of: "police", "ambulance", "firefighters">
}

Urgency thresholds:
- critical (0.85–1.0): life-threatening, multiple casualties, active fire or accident in progress
- high (0.60–0.85): serious injury, single casualty, medical emergency
- medium (0.35–0.60): property damage, non-life-threatening situation, minor injury
- low (0.0–0.35): minor incident, general inquiry, non-emergency

Dispatch recommendation rules:
- Fire, explosion, smoke → include "firefighters" (add "ambulance" if injuries mentioned)
- Medical emergency, injury, unconscious person → include "ambulance"
- Crime, violence, robbery, threat, suspicious person → include "police"
- Road accident → include "ambulance" (add "firefighters" if vehicle fire/entrapment)
- Spam / prank call → empty array []
- Multiple hazards → include all relevant services

Spam indicators: laughter, repeated nonsense words, testing the line, children prank-calling,
obvious fictional scenarios, caller contradicting themselves with jokes.

The transcript may be in Urdu. Analyze the content regardless of language."""

_FALLBACK = {
    "spam_score": 0.0,
    "spam_label": "not_spam",
    "urgency_score": 0.5,
    "urgency_label": "medium",
    "reasoning": "Analysis unavailable — defaulting to medium urgency.",
    "dispatch_recommendation": [],
}


def _get_client() -> genai.Client:
    api_key = settings.GOOGLE_API_KEY or os.getenv("GOOGLE_API_KEY", "")
    return genai.Client(api_key=api_key)


def _parse_retry_delay(exc: Exception) -> float:
    match = re.search(r"retry_delay\s*\{\s*seconds:\s*(\d+)", str(exc))
    if match:
        return min(float(match.group(1)), _MAX_RETRY_WAIT)
    return 5.0


_client: genai.Client | None = None


async def analyze(transcript: str) -> dict:
    """
    Async Gemini call. Returns a dict with spam and urgency fields.
    Retries once on 429 (respecting the API-suggested retry_delay).
    On any other error, returns a safe fallback so the pipeline never crashes.
    """
    global _client
    if _client is None:
        _client = _get_client()

    config = types.GenerateContentConfig(
        system_instruction=_SYSTEM_PROMPT,
        response_mime_type="application/json",
        temperature=0.1,
        max_output_tokens=512,
        # Disable thinking — unnecessary for structured JSON output and would
        # consume the entire token budget before the actual response is emitted.
        thinking_config=types.ThinkingConfig(thinking_budget=0),
    )
    prompt = f"Call transcript:\n\n{transcript}"

    for attempt in range(2):
        try:
            response = await _client.aio.models.generate_content(
                model=_MODEL_NAME,
                contents=prompt,
                config=config,
            )
            text = response.text or ""
            if not text.strip():
                raise ValueError("Empty response from Gemini")
            result = json.loads(text)
            for key in ("spam_score", "spam_label", "urgency_score", "urgency_label", "reasoning", "dispatch_recommendation"):
                if key not in result:
                    raise ValueError(f"Missing key in Gemini response: {key}")
            return result

        except ResourceExhausted as exc:
            if attempt == 0:
                delay = _parse_retry_delay(exc)
                logger.warning("Gemini 429 rate-limit — retrying in %.0fs", delay)
                await asyncio.sleep(delay)
            else:
                logger.warning("Gemini analysis failed after retry: %s", exc)
                return {**_FALLBACK, "reasoning": f"Rate limit exceeded: {str(exc)[:120]}"}

        except Exception as exc:
            logger.warning("Gemini analysis failed: %s", exc)
            return {**_FALLBACK, "reasoning": f"Analysis error: {str(exc)[:120]}"}
