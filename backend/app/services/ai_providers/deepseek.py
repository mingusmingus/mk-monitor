"""
DeepSeek AI Provider Implementation.

Implements the AIProvider interface using DeepSeek's API.
"""
import json
import logging
import requests
from typing import Dict, Any, List

from .base import AIProvider
from ...config import Config

logger = logging.getLogger(__name__)

class DeepSeekProvider(AIProvider):
    """
    Concrete implementation of AIProvider for DeepSeek.
    """

    def __init__(self):
        self.api_key = Config.DEEPSEEK_API_KEY
        self.api_url = Config.DEEPSEEK_API_URL or "https://api.deepseek.com/v1/chat/completions"
        self.model = Config.DEEPSEEK_MODEL or "deepseek-chat"
        self.timeout = Config.AI_TIMEOUT_SEC or 30
        self.max_tokens = Config.AI_MAX_TOKENS or 4096

    def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sends the forensic context to DeepSeek and parses the response.
        """
        if not self.api_key:
            logger.error("DeepSeekProvider: Missing API Key.")
            return self._empty_response()

        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(context)

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.3,
            "max_tokens": self.max_tokens,
            "stream": False,
            "response_format": {"type": "json_object"} # Force JSON if supported, otherwise handled in prompt
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()
            content = data["choices"][0]["message"]["content"]

            return self._parse_json_response(content)

        except requests.exceptions.RequestException as e:
            logger.error(f"DeepSeekProvider: Network error: {e}")
            return self._empty_response(error=str(e))
        except (ValueError, KeyError, json.JSONDecodeError) as e:
            logger.error(f"DeepSeekProvider: Parsing error: {e}")
            return self._empty_response(error=str(e))

    def _build_system_prompt(self) -> str:
        return (
            "You are a Senior Network Architect & Forensic Analyst (MTCINE). "
            "Your job is to analyze deep telemetry from Mikrotik routers to find root causes of failures. "
            "You do not simply report stats; you correlate CPU, Interface Errors, Logs, and Voltage to diagnose physical, layer 2, or logical issues. "
            "Output MUST be strict JSON."
        )

    def _build_user_prompt(self, context: Dict[str, Any]) -> str:
        # Serialize context to JSON for the prompt
        context_json = json.dumps(context, indent=2)
        return f"""
Analyze the following forensic data collected from a Mikrotik Router.

DATA CONTEXT:
{context_json}

REQUIREMENTS:
1. Correlate "Physical Health" (Voltage/Temp) with Reboots/Logs.
2. Correlate "Interface Stats" (FCS, Drops) with Logs/CPU. FCS errors almost always mean bad cable/connector.
3. Correlate "Resource" (CPU) with PPS and Firewall activity (DDoS/Loop).
4. Review "Heuristics" provided in the input.

OUTPUT FORMAT (Strict JSON):
{{
  "context": {{ "model": "...", "ros_version": "...", "uptime": "..." }},
  "telemetry": {{ "critical_logs": [], "interface_errors": {{}}, "resource_stress": "..." }},
  "analysis": "Detailed root cause analysis...",
  "recommendations": ["Step 1...", "Step 2..."]
}}

Do not include markdown formatting (```json). Just the JSON string.
"""

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """Cleans and parses the JSON response."""
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Attempt recovery
            start = content.find("{")
            end = content.rfind("}")
            if start != -1 and end != -1:
                try:
                    return json.loads(content[start:end+1])
                except json.JSONDecodeError:
                    pass
            logger.error(f"DeepSeekProvider: Failed to parse JSON: {content[:100]}...")
            return self._empty_response(error="Invalid JSON response from AI")

    def _empty_response(self, error: str = None) -> Dict[str, Any]:
        return {
            "context": {},
            "telemetry": {},
            "analysis": f"AI Analysis Failed. Error: {error}" if error else "AI Analysis Failed.",
            "recommendations": ["Check connectivity", "Review logs manually"]
        }
