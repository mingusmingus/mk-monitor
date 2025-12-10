# AI System Improvement Report

## 1. Inspection Findings

During the initial inspection of the `ai_analysis_service` and `monitoring_service`, the following issues were identified:

*   **Prompt Quality:** The existing prompt was basic and did not establish an expert role. It lacked specific instructions for Mikrotik log analysis and did not enforce a strict JSON output structure.
*   **Data Handling:** The system was passing raw log strings to the AI, stripping valuable context like timestamps and log levels.
*   **Output Parsing:** The parsing logic was limited to a simple list of `severity` and `message`, missing other critical fields like `recommended_action`, `affected_services`, and `title`.
*   **Heuristics:** The fallback heuristics were very basic (only detecting "login failed" and excessive "pppoe reconnect").
*   **Compliance:** The implementation did not fully meet the "intelligent and accurate incident detection" goal outlined in `plan_general.txt` due to the lack of depth in analysis.

## 2. Improvements Made

We have refactored the AI system to align with the "Senior Network & Telecommunications Engineer" persona. Key improvements include:

*   **Expert System Prompt:** Added a system prompt that establishes the AI as a specialist in Mikrotik Routing & Switching.
*   **Structured Input:** Modified `monitoring_service` and `ai_analysis_service` to pass structured log data (timestamp, level, message, equipment name) to the AI, enabling time-sensitive and context-aware analysis.
*   **Comprehensive Output Schema:** The AI now returns a detailed JSON object for each alert, including:
    *   `title`, `severity`, `alert_class`
    *   `description` (technical details)
    *   `affected_services` (list of impacted services)
    *   `recommended_action` (remediation steps)
    *   `log_excerpt` (evidence)
    *   `detected_date`
*   **Robust Parsing:** Implemented robust JSON parsing that handles markdown code blocks and validates the output structure.
*   **Model Configuration:** Configured DeepSeek with `temperature=0.3` for deterministic results and `max_tokens=4096` to handle detailed responses.
*   **Metric Instrumentation:** Added calls to track AI request success/failure rates and fallback usage.

## 3. Compliance Status

*   **Incident Detection:** The system now identifies specific issues like interface flapping, auth failures, and resource exhaustion with high precision.
*   **Alert Severity:** Alerts are mapped to the correct application severity levels (`Aviso`, `Alerta Menor`, `Alerta Severa`, `Alerta Crítica`).
*   **Goals Alignment:** The solution directly supports the goal of "generating actionable alerts (what happened and what to do)" mentioned in `plan_general.txt`.
*   **Performance:** The system is optimized for batch processing of logs and includes timeouts and error handling.

## 4. Performance & Recommendations

*   **Current Metrics:**
    *   AI Timeout: Configured to 30s.
    *   Max Log Lines: Limited to 120 per batch to stay within context windows.
*   **Recommendations:**
    *   **Async Processing:** Move the `analyze_and_generate_alerts` call to a background worker (e.g., Celery) to avoid blocking the main thread during AI inference.
    *   **Streaming:** For very large log volumes, implement streaming response parsing to handle alerts as they are generated.
    *   **Feedback Loop:** Implement a mechanism for users to mark alerts as "False Positive" to fine-tune the prompt or fine-tune a custom model in the future.
