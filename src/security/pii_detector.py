"""PII detection and masking."""
import re
from typing import Dict, List
from enum import Enum


class SensitivityLevel(str, Enum):
    """Data sensitivity levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class PIIDetector:
    """Detect and mask personally identifiable information."""

    # Patterns
    EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    PHONE_PATTERN = r'\b(?:\+?\d{1,3}[-.\s]?)?\(?(?:\d{3})\)?[-.\s]?(?:\d{3})[-.\s]?(?:\d{4})\b'
    PASSPORT_PATTERN = r'\b[A-Z]{1,2}\d{6,9}\b'
    ID_PATTERN = r'\b\d{9,12}\b'  # ID numbers
    AMOUNT_PATTERN = r'\$\s*[\d,]+(?:\.\d{2})?|\b[\d,]+(?:\.\d{2})?\s*(?:USD|VND|EUR|GBP)\b'
    ACCOUNT_PATTERN = r'\b(?:Account|Acct)[\s#:]*[A-Z0-9]{8,20}\b'

    @staticmethod
    def detect_pii(text: str) -> Dict[str, List[str]]:
        """
        Detect PII in text.

        Args:
            text: Text to analyze

        Returns:
            Dictionary of PII types and findings
        """
        findings = {
            "emails": re.findall(PIIDetector.EMAIL_PATTERN, text),
            "phones": re.findall(PIIDetector.PHONE_PATTERN, text),
            "passports": re.findall(PIIDetector.PASSPORT_PATTERN, text),
            "ids": re.findall(PIIDetector.ID_PATTERN, text),
            "amounts": re.findall(PIIDetector.AMOUNT_PATTERN, text),
            "accounts": re.findall(PIIDetector.ACCOUNT_PATTERN, text, re.IGNORECASE)
        }

        # Count findings
        total = sum(len(v) for v in findings.values())
        findings["total_pii_found"] = total
        findings["has_sensitive_data"] = total > 0

        return findings

    @staticmethod
    def mask_pii(text: str) -> str:
        """
        Mask PII in text.

        Args:
            text: Text to mask

        Returns:
            Text with PII masked
        """
        text = re.sub(PIIDetector.EMAIL_PATTERN, "[EMAIL_MASKED]", text)
        text = re.sub(PIIDetector.PHONE_PATTERN, "[PHONE_MASKED]", text)
        text = re.sub(PIIDetector.PASSPORT_PATTERN, "[PASSPORT_MASKED]", text)
        text = re.sub(PIIDetector.ID_PATTERN, "[ID_MASKED]", text)
        text = re.sub(PIIDetector.AMOUNT_PATTERN, "[AMOUNT_MASKED]", text)
        text = re.sub(PIIDetector.ACCOUNT_PATTERN, "[ACCOUNT_MASKED]", text, flags=re.IGNORECASE)

        return text

    @staticmethod
    def detect_sensitivity_level(text: str) -> SensitivityLevel:
        """
        Determine sensitivity level of text.

        Args:
            text: Text to analyze

        Returns:
            Sensitivity level
        """
        pii = PIIDetector.detect_pii(text)

        if pii["has_sensitive_data"]:
            if pii["emails"] or pii["phones"] or pii["passports"] or pii["ids"]:
                return SensitivityLevel.CRITICAL
            if pii["amounts"] or pii["accounts"]:
                return SensitivityLevel.HIGH

        # Check for keywords
        critical_keywords = ["password", "secret", "token", "api_key", "private_key"]
        high_keywords = ["salary", "revenue", "profit", "algorithm", "patent"]

        text_lower = text.lower()
        if any(k in text_lower for k in critical_keywords):
            return SensitivityLevel.CRITICAL
        if any(k in text_lower for k in high_keywords):
            return SensitivityLevel.HIGH

        return SensitivityLevel.MEDIUM


class AuditLogger:
    """Log security events."""

    @staticmethod
    def log_query(user_id: str, query: str, has_pii: bool, severity: str):
        """Log a query for audit."""
        import json
        from datetime import datetime

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "query_length": len(query),
            "has_pii": has_pii,
            "severity": severity,
            "action": "query_submitted"
        }

        # In production, write to database/file
        print(f"[AUDIT] {json.dumps(log_entry)}")

        return log_entry

    @staticmethod
    def log_response(user_id: str, query_id: str, has_pii: bool, confidence: float):
        """Log a response for audit."""
        import json
        from datetime import datetime

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "query_id": query_id,
            "has_pii": has_pii,
            "confidence": confidence,
            "action": "response_generated"
        }

        print(f"[AUDIT] {json.dumps(log_entry)}")

        return log_entry
