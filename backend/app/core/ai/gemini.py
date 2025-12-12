import json
import logging
import aiohttp
from typing import Dict, Any
from .base import BaseAIProvider
from ...config import Config

logger = logging.getLogger(__name__)

class GeminiProvider(BaseAIProvider):
    """
    Concrete implementation of BaseAIProvider for Google Gemini.
    """
    def __init__(self):
        self.api_key = Config.GEMINI_API_KEY
        # Using HTTP REST API for Gemini to avoid heavy dependencies if preferred,
        # or we could use google-generativeai. User said:
        # "Implement the base structure using google.generativeai (or prepare it for HTTP requests if you prefer not to add heavy dependencies yet)."
        # I will use HTTP requests for now to keep it lightweight as requested alternative.
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={self.api_key}"

    async def analyze(self, context: str, prompt_template: str) -> Dict[str, Any]:
        """
        Analyze the context using Google Gemini API.
        """
        if not self.api_key:
            logger.error("Gemini Provider selected but GEMINI_API_KEY is not configured.")
            raise ValueError("Provider not configured: GEMINI_API_KEY missing")

        # Gemini expects a different payload structure
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"{prompt_template}\n\nAnalyze this Mikrotik forensic data:\n{context}"
                }]
            }],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json"
            }
        }

        headers = {
            "Content-Type": "application/json"
        }

        logger.info("[Gemini] Payload sent (partial):")
        logger.info(json.dumps({k: v for k, v in payload.items() if k != "contents"}, indent=2))

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, json=payload, headers=headers, timeout=30) as response:
                    status_code = response.status
                    raw_body = await response.text()

                    logger.info(f"[Gemini] Status Code received: {status_code}")
                    logger.info(f"[Gemini] Raw Response Body: {raw_body}")

                    if status_code != 200:
                         logger.error(f"[Gemini] Request failed with status {status_code}")
                         return self._mock_response(error=f"HTTP {status_code}: {raw_body}")

                    try:
                        result = json.loads(raw_body)
                        # Extract text from Gemini response structure
                        # { "candidates": [ { "content": { "parts": [ { "text": "..." } ] } } ] }
                        if 'candidates' in result and len(result['candidates']) > 0:
                            content = result['candidates'][0]['content']['parts'][0]['text']
                            return json.loads(content)
                        else:
                            logger.error("[Gemini] No candidates in response")
                            return self._mock_response(error="No candidates returned")

                    except (KeyError, json.JSONDecodeError) as e:
                        logger.error(f"[Gemini] Failed to parse API response: {e}")
                        return self._mock_response(error=f"Response parsing error: {str(e)}")

        except Exception as e:
            logger.error(f"[Gemini] API request failed: {e}")
            return self._mock_response(error=str(e))

    def _mock_response(self, error: str = None) -> Dict[str, Any]:
        return {
            "status": "WARNING",
            "summary": "AI Analysis Unavailable (Gemini)",
            "technical_analysis": f"Could not contact Gemini. Reason: {error}",
            "security_audit": "N/A",
            "recommendations": ["Check API Key", "Verify internet connection"],
            "confidence_score": 0.0
        }
