import os
import logging
from typing import Optional
from .base import BaseAIProvider
from .deepseek import DeepSeekProvider
from .gemini import GeminiProvider
from ...config import Config

logger = logging.getLogger(__name__)

class AIFactory:
    @staticmethod
    def get_ai_provider() -> BaseAIProvider:
        """
        Returns the configured AI Provider instance based on environment variables.
        Priority: AI_PROVIDER > AI_ANALYSIS_PROVIDER > Default (DeepSeek)
        """
        # Read from Config first (which reads env), or direct env if not in Config yet
        provider_name = os.getenv("AI_PROVIDER", Config.AI_ANALYSIS_PROVIDER).lower()

        logger.info(f"Selecting AI Provider: {provider_name}")

        if provider_name == "gemini":
            return GeminiProvider()
        elif provider_name == "deepseek":
            return DeepSeekProvider()
        elif provider_name == "auto":
             # Legacy logic: prioritize DeepSeek if key exists
             if Config.DEEPSEEK_API_KEY:
                 return DeepSeekProvider()
             elif getattr(Config, 'GEMINI_API_KEY', None):
                 return GeminiProvider()
             else:
                 # Default fallback
                 logger.warning("Auto provider selection failed. Defaulting to DeepSeek (mock mode if no key).")
                 return DeepSeekProvider()
        else:
            logger.warning(f"Unknown provider '{provider_name}'. Defaulting to DeepSeek.")
            return DeepSeekProvider()

def get_ai_provider() -> BaseAIProvider:
    return AIFactory.get_ai_provider()
