"""
AI Discovery Scanner — Classification Engine

The Classification Engine maps raw findings to meaningful AI categories
with confidence scores and risk levels.

Classes:
    ClassificationEngine — Rule-based finding classifier
"""

from __future__ import annotations

import logging

from scanner.models import Finding, FindingCategory, RiskLevel

logger = logging.getLogger(__name__)


class ClassificationEngine:
    """Classifies raw scanner findings into AI categories."""

    def __init__(self) -> None:
        """Initialize the Classification Engine."""
        logger.info("Classification Engine initialized")

    def classify_single(self, finding: Finding) -> Finding:
        """Classify a single raw finding using rule-based heuristics.

        Args:
            finding: The raw finding to classify.

        Returns:
            The classified finding.
        """
        logger.debug("Classifying finding: '%s' (Source: %s, Module: %s)", finding.title, finding.source, finding.module_name)
        
        # If the finding already has classification, use it as a default baseline
        category = finding.category if finding.category else FindingCategory.UNKNOWN
        risk_level = finding.risk_level if finding.risk_level else RiskLevel.INFO
        confidence = finding.confidence if finding.confidence > 0 else 0.5

        title_lower = finding.title.lower()
        desc_lower = finding.description.lower()
        source_lower = finding.source.lower()

        # ── Rule 1: API Keys & Secrets (API Scanner) ────────────────────
        if "api_key" in title_lower or "api-key" in title_lower or "key" in source_lower or finding.module_name == "APIScanner":
            category = FindingCategory.CONFIGURATION
            # Exposing API keys is a significant risk
            risk_level = RiskLevel.HIGH
            confidence = 0.95
            provider = "Unknown"
            if "openai" in title_lower or "openai" in desc_lower or "openai" in source_lower:
                category = FindingCategory.CONFIGURATION
                finding.details["provider"] = "OpenAI"
                provider = "OpenAI"
            elif "anthropic" in title_lower or "anthropic" in desc_lower or "anthropic" in source_lower:
                category = FindingCategory.CONFIGURATION
                finding.details["provider"] = "Anthropic"
                provider = "Anthropic"
            elif "google" in title_lower or "google" in desc_lower or "google" in source_lower:
                category = FindingCategory.CONFIGURATION
                finding.details["provider"] = "Google"
                provider = "Google"
            logger.info("  [MATCH] Rule 1 (API Keys & Secrets) -> Category: %s, Risk: %s, Confidence: %.2f (Provider: %s)", category, risk_level, confidence, provider)

        # ── Rule 2: AI Models & Weights (File Scanner) ──────────────────
        elif finding.module_name == "FileScanner" or any(ext in source_lower for ext in [".gguf", ".safetensors", ".pt", ".pth", ".onnx", ".ckpt", ".h5"]):
            category = FindingCategory.AI_MODEL
            confidence = 0.95
            # Set risk level based on model size or path
            if "download" in source_lower:
                risk_level = RiskLevel.MEDIUM  # Unmanaged downloads of AI models
            elif "cache" in source_lower:
                risk_level = RiskLevel.LOW     # Normal framework caches (e.g. HuggingFace)
            else:
                risk_level = RiskLevel.INFO
            logger.info("  [MATCH] Rule 2 (AI Models & Weights) -> Category: %s, Risk: %s, Confidence: %.2f", category, risk_level, confidence)

        # ── Rule 3: LLM Runtimes (Runtime Scanner / Process Scanner) ────
        elif finding.module_name in ["RuntimeScanner", "ProcessScanner"] or any(kw in title_lower or kw in desc_lower for kw in ["ollama", "lmstudio", "lm studio", "vllm", "llama.cpp"]):
            category = FindingCategory.LLM_RUNTIME
            confidence = 0.90
            # Active runtimes listening on ports or running locally
            if "port" in desc_lower or "active" in desc_lower or "running" in desc_lower:
                risk_level = RiskLevel.MEDIUM
            else:
                risk_level = RiskLevel.LOW
            logger.info("  [MATCH] Rule 3 (LLM Runtimes) -> Category: %s, Risk: %s, Confidence: %.2f", category, risk_level, confidence)

        # ── Rule 4: ML/AI Libraries & Frameworks (Package Scanner) ──────
        elif finding.module_name == "PackageScanner" or any(kw in title_lower for kw in ["torch", "tensorflow", "transformers", "scikit-learn", "keras"]):
            # Differentiate core frameworks from agent frameworks
            if any(agent_kw in title_lower for agent_kw in ["langchain", "crewai", "autogen"]):
                category = FindingCategory.AI_AGENT
            else:
                category = FindingCategory.ML_FRAMEWORK
            confidence = 0.90
            risk_level = RiskLevel.INFO
            logger.info("  [MATCH] Rule 4 (ML/AI Libraries & Frameworks) -> Category: %s, Risk: %s, Confidence: %.2f", category, risk_level, confidence)

        # ── Rule 5: AI Agents & Frameworks (Agent Scanner) ─────────────
        elif finding.module_name == "AgentScanner" or any(kw in title_lower or kw in desc_lower for kw in ["agent", "crew", "crewai", "autogen", "langchain", "llama-index"]):
            category = FindingCategory.AI_AGENT
            confidence = 0.85
            risk_level = RiskLevel.MEDIUM  # Agents have execution capabilities
            logger.info("  [MATCH] Rule 5 (AI Agents) -> Category: %s, Risk: %s, Confidence: %.2f", category, risk_level, confidence)

        # ── Rule 6: System Info Fallback (System Scanner) ────────────────
        elif finding.module_name == "SystemScanner" or category == FindingCategory.SYSTEM_INFO:
            category = FindingCategory.SYSTEM_INFO
            risk_level = RiskLevel.INFO
            confidence = 1.0
            logger.info("  [MATCH] Rule 6 (System Info Fallback) -> Category: %s, Risk: %s, Confidence: %.2f", category, risk_level, confidence)
        
        else:
            logger.debug("  [NO MATCH] Finding default classification preserved -> Category: %s, Risk: %s, Confidence: %.2f", category, risk_level, confidence)

        # Update the finding fields
        finding.category = category
        finding.risk_level = risk_level
        finding.confidence = confidence

        return finding

    def classify(self, findings: list[Finding]) -> list[Finding]:
        """Classify a list of raw findings.

        Args:
            findings: Raw findings from the Discovery Engine.

        Returns:
            The list of findings with category, risk_level, and confidence populated.
        """
        logger.info("Classification Engine: Starting classification of %d raw findings...", len(findings))
        classified = []
        for finding in findings:
            classified.append(self.classify_single(finding))

        # Log a simple breakdown
        category_counts = {}
        for f in classified:
            category_counts[f.category.value] = category_counts.get(f.category.value, 0) + 1
        
        logger.info("Classification Engine: Completed. Breakdown by category: %s", category_counts)
        return classified


