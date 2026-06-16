"""
AI Discovery Scanner — Classification Engine (Stub)

The Classification Engine maps raw findings to meaningful AI categories
with confidence scores. This is a Day 1 stub that passes findings through
unmodified. Full rule-based classification will be implemented on Day 2.

Classes:
    ClassificationEngine — Rule-based finding classifier
"""

from __future__ import annotations

import logging

from scanner.models import Finding

logger = logging.getLogger(__name__)


class ClassificationEngine:
    """Classifies raw scanner findings into AI categories.

    Day 1 stub — passes findings through without modification.
    Full rule-based classification with confidence scoring on Day 2.
    """

    def __init__(self) -> None:
        """Initialize the Classification Engine."""
        logger.info("Classification Engine initialized (stub mode)")

    def classify(self, findings: list[Finding]) -> list[Finding]:
        """Classify a list of raw findings.

        Args:
            findings: Raw findings from the Discovery Engine.

        Returns:
            The same findings with category and confidence fields populated.

        Note:
            Day 1 stub — returns findings unmodified. Full implementation on Day 2.
        """
        logger.info(
            "Classification Engine: Processing %d findings (stub - passthrough)...",
            len(findings),
        )
        # Stub: return findings as-is. Day 2 will add rule-based classification.
        return findings
