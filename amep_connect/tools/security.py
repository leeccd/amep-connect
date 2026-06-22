"""
Security features for AMEP Connect
PII Masking and data protection
"""

import re
from typing import Dict, List, Tuple

# Common PII patterns
PII_PATTERNS = {
    "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    "phone": r'\b\d{10}\b|\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b',
    "address": r'\b\d+\s+[A-Za-z]+\s+(?:Street|St|Road|Rd|Avenue|Ave|Drive|Dr|Lane|Ln|Court|Ct)\b',
    "australian_visa": r'\b(?:[A-Z]{1,2}\d{6,8})\b',
    "name": r'\b(?:[A-Z][a-z]+)\s+(?:[A-Z][a-z]+)\b',  # Simple name detection
}

class PIICleaner:
    """
    Cleans Personally Identifiable Information from text.
    """
    
    def __init__(self):
        self.patterns = PII_PATTERNS
    
    def mask_pii(self, text: str, replace_with: str = "[REDACTED]") -> Tuple[str, Dict]:
        """
        Mask PII in text and return cleaned text with summary.
        """
        masked_text = text
        found_pii = {}
        total_masks = 0
        
        for pii_type, pattern in self.patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                found_pii[pii_type] = matches
                # Count matches for this type
                count = len(matches)
                total_masks += count
                # Replace each match with [REDACTED]
                for match in matches:
                    masked_text = masked_text.replace(match, replace_with)
        
        summary = {
            "total_masks": total_masks,
            "pii_types_found": list(found_pii.keys()),
            "details": found_pii
        }
        
        return masked_text, summary
    
    def scan_for_pii(self, text: str) -> Dict:
        """
        Scan text for PII without masking.
        """
        found_pii = {}
        total_found = 0
        
        for pii_type, pattern in self.pii_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                found_pii[pii_type] = matches
                total_found += len(matches)
        
        return {
            "total_found": total_found,
            "pii_types": list(found_pii.keys()),
            "details": found_pii
        }
    
    def is_safe_to_process(self, text: str) -> bool:
        """
        Check if text contains PII that should block processing.
        """
        scan = self.scan_for_pii(text)
        return scan["total_found"] == 0

# Simplified version for easy import
def mask_pii(text: str) -> str:
    """
    Quick function to mask PII in text.
    """
    cleaner = PIICleaner()
    masked, summary = cleaner.mask_pii(text)
    return masked

def is_safe_text(text: str) -> bool:
    """
    Quick check if text is safe to process.
    """
    cleaner = PIICleaner()
    return cleaner.is_safe_to_process(text)

# Test the security features
def test_security():
    """Test the security features."""
    print("=" * 50)
    print("SECURITY - PII MASKING TEST")
    print("=" * 50)
    
    # Test text with PII
    test_text = """
    My name is John Smith and my email is john.smith@gmail.com.
    My phone number is 0400123456 and I live at 123 Main Street.
    My visa number is AB123456.
    """
    
    print("\n📝 Original Text:")
    print(test_text)
    
    print("\n🔒 Masked Text:")
    masked, summary = PIICleaner().mask_pii(test_text)
    print(masked)
    
    print("\n📊 PII Summary:")
    print(f"  Total Masks: {summary['total_masks']}")
    print(f"  PII Types Found: {summary['pii_types_found']}")
    
    print("\n🔍 Scan Only:")
    scan = PIICleaner().scan_for_pii(test_text)
    print(f"  Total Found: {scan['total_found']}")
    print(f"  PII Types: {scan['pii_types']}")
    
    print("\n✅ Security test completed!")

if __name__ == "__main__":
    test_security()