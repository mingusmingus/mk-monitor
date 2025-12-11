import json
import logging
import requests
from typing import Dict, Any
from .base import AIProvider
from ...config import Config

logger = logging.getLogger(__name__)

class DeepSeekProvider(AIProvider):
    """
    Concrete implementation of AIProvider for DeepSeek.
    """
    def __init__(self):
        # We assume the API key is stored in Config
        self.api_key = Config.DEEPSEEK_API_KEY
        self.api_url = "https://api.deepseek.com/v1/chat/completions" # Example URL, verify actual
        self.model = "deepseek-chat" # Verify model name

    def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        if not self.api_key:
            logger.warning("DeepSeek API Key is missing. Returning mock response.")
            return self._mock_response()

        system_prompt = self._build_system_prompt()
        user_message = json.dumps(context, indent=2)

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze this Mikrotik forensic data:\n{user_message}"}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()

            result = response.json()
            content = result['choices'][0]['message']['content']

            # Robust parsing
            try:
                parsed_content = json.loads(content)
                return parsed_content
            except json.JSONDecodeError:
                logger.error("Failed to parse DeepSeek response as JSON. Attempting repair or fallback.")
                return self._fallback_parsing(content)

        except requests.RequestException as e:
            logger.error(f"DeepSeek API request failed: {e}")
            return self._mock_response(error=str(e)) # Fail safe to mock or error response

    def _build_system_prompt(self) -> str:
        return """
You are a MTCINE (MikroTik Certified Inter-networking Engineer) and a Lead Network Security Architect.
Your goal is to analyze deep forensic data from a MikroTik router and provide a structured diagnosis.

Input: JSON containing:
- hardware_health: Voltage, Temperature, CPU, Memory.
- interface_errors: Stats for interfaces with traffic or errors.
- security_posture: Open ports/services.
- recent_logs: Sanitized system logs.
- topology: Neighbors and routes.

Output: Strict JSON format with the following keys:
{
  "status": "CRITICAL" | "WARNING" | "HEALTHY",
  "summary": "Short title of the problem (e.g., Cable Failure on Ether2)",
  "technical_analysis": "Detailed explanation of why...",
  "security_audit": "Analysis of open ports (e.g., Close Telnet)",
  "recommendations": ["Step 1", "Step 2"],
  "confidence_score": 0.95
}

Rules:
1. Be precise and technical but clear.
2. If you see 'fcs-error', suspect Layer 1 (cable/connector).
3. If you see Telnet/FTP enabled, flag as SECURITY RISK.
4. If CPU is high, check for loops or heavy firewall rules.
5. If voltage is low (<10V for 12V systems), flag as power issue.
6. Ignore minor log noise. Focus on warnings, errors, and critical state changes.
"""

    def _fallback_parsing(self, content: str) -> Dict[str, Any]:
        # Simple fallback: try to find the first '{' and last '}'
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
            "technical_analysis": f"Could not contact AI Provider. Reason: {error}" if error else "No anomalies detected in local analysis.",
            "security_audit": "N/A",
            "recommendations": ["Check internet connection", "Verify API Key"],
            "confidence_score": 0.0
        }

class MockProvider(AIProvider):
    def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "HEALTHY",
            "summary": "Mock Analysis - All Good",
            "technical_analysis": "This is a local mock response. No real analysis was performed.",
            "security_audit": "Telnet is enabled (Mock check).",
            "recommendations": ["Buy more credits", "Deploy to production"],
            "confidence_score": 1.0
        }
