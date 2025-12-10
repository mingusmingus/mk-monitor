"""
Base Interface for AI Providers.

This module defines the contract that any AI provider (DeepSeek, Gemini, GPT-4, etc.)
must implement to be used by the analysis service.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List

class AIProvider(ABC):
    """
    Abstract base class for AI Providers.
    """

    @abstractmethod
    def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyzes the provided context using the AI model.

        Args:
            context: A structured dictionary containing:
                     - system_info: Dict (Identity, resources, etc.)
                     - health: Dict (Voltage, temperature)
                     - interfaces: Dict (Stats, errors, cable diagnostics)
                     - l3_topology: Dict (IPs, neighbors, routes)
                     - security: Dict (Firewall stats)
                     - logs: List (Recent logs)
                     - heuristics: List (Pre-processed findings)

        Returns:
            A structured dictionary conforming to the forensic output schema:
            {
              "context": { "model": "...", "ros_version": "...", "uptime": "..." },
              "telemetry": { "critical_logs": [], "interface_errors": {}, "resource_stress": "..." },
              "analysis": "Root cause...",
              "recommendations": ["..."]
            }
        """
        pass
