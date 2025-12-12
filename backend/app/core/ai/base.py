from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseAIProvider(ABC):
    """
    Abstract base class for AI Providers (Strategy Pattern).
    Defines the contract for analyzing network context.
    """

    @abstractmethod
    async def analyze(self, context: str, prompt_template: str) -> Dict[str, Any]:
        """
        Analyze the given context and return a structured diagnosis.

        Args:
            context (str): The data collected from the device (logs, stats, etc.) as a string.
            prompt_template (str): The system prompt or template to guide the analysis.

        Returns:
            Dict[str, Any]: Structured diagnosis including status, summary, analysis, etc.
        """
        pass
