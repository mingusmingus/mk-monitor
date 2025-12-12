import json
import logging
import aiohttp
from typing import Dict, Any
from .base import BaseAIProvider
from ...config import Config

logger = logging.getLogger(__name__)

class DeepSeekProvider(BaseAIProvider):
    """
    Concrete implementation of BaseAIProvider for DeepSeek.
    """
    def __init__(self):
        self.api_key = Config.DEEPSEEK_API_KEY
        self.api_url = Config.DEEPSEEK_API_URL or "https://api.deepseek.com/v1/chat/completions"
        self.model = Config.DEEPSEEK_MODEL or "deepseek-chat"

    async def analyze(self, context: str, prompt_template: str) -> Dict[str, Any]:
        """
        Analyze the context using DeepSeek API.
        """
        if not self.api_key:
            logger.warning("DeepSeek API Key is missing. Returning mock response.")
            return self._mock_response(error="API Key missing")

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": prompt_template},
                {"role": "user", "content": f"Analyze this Mikrotik forensic data:\n{context}"}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        # Detailed logging before request
        logger.info("[DeepSeek] Payload sent (partial):")
        logger.info(json.dumps({k: v for k, v in payload.items() if k != "messages"}, indent=2))
        logger.info(f"[DeepSeek] Messages count: {len(payload['messages'])}")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, json=payload, headers=headers, timeout=30) as response:
                    status_code = response.status
                    raw_body = await response.text()

                    # Detailed logging after request
                    logger.info(f"[DeepSeek] Status Code received: {status_code}")
                    logger.info(f"[DeepSeek] Raw Response Body: {raw_body}")

                    if status_code != 200:
                         logger.error(f"[DeepSeek] Request failed with status {status_code}")
                         return self._mock_response(error=f"HTTP {status_code}: {raw_body}")

                    try:
                        result = json.loads(raw_body)
                        content = result['choices'][0]['message']['content']

                        # Robust parsing of content
                        try:
                            parsed_content = json.loads(content)
                            return parsed_content
                        except json.JSONDecodeError:
                            logger.error("[DeepSeek] Failed to parse content as JSON. Attempting repair.")
                            return self._fallback_parsing(content)

                    except (KeyError, json.JSONDecodeError) as e:
                        logger.error(f"[DeepSeek] Failed to parse API response structure: {e}")
                        return self._mock_response(error=f"Response parsing error: {str(e)}")

        except Exception as e:
            logger.error(f"[DeepSeek] API request failed: {e}")
            return self._mock_response(error=str(e))

    def _fallback_parsing(self, content: str) -> Dict[str, Any]:
        try:
            start = content.find('{')
            end = content.rfind('}') + 1
            if start != -1 and end != -1:
                return json.loads(content[start:end])
        except Exception:
            pass

        return {
            "status": "WARNING",
            "summary": "AI Parsing Error",
            "technical_analysis": f"The AI response could not be parsed as JSON. Raw output: {content[:200]}...",
            "security_audit": "Unknown",
            "recommendations": ["Check AI logs"],
            "confidence_score": 0.0
        }

    def _mock_response(self, error: str = None) -> Dict[str, Any]:
        return {
            "status": "WARNING" if error else "HEALTHY",
            "summary": "AI Analysis Unavailable" if error else "System Healthy (Mock)",
            "technical_analysis": f"Could not contact DeepSeek. Reason: {error}" if error else "No anomalies detected in local analysis.",
            "security_audit": "N/A",
            "recommendations": ["Check internet connection", "Verify API Key"],
            "confidence_score": 0.0
        }
