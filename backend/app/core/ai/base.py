from abc import ABC, abstractmethod
from typing import Dict, Any

class AIProvider(ABC):
    """
    Abstract base class for AI Providers (Strategy Pattern).
    Defines the contract for analyzing network context.
    """

    @abstractmethod
    def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze the given context and return a structured diagnosis.

        Args:
            context (Dict[str, Any]): The data collected from the device (logs, stats, etc.)

        Returns:
            Dict[str, Any]: Structured diagnosis including status, summary, analysis, etc.
        """
        pass
