"""
Text Sanitizer — PII Redaction
================================
This file strips sensitive customer data from SOW text before it is sent to
the AI model.

PURPOSE:
Data privacy is a primary concern. Customer SOWs contain real names, emails,
phone numbers, addresses, account IDs, and pricing info. None of that should
reach the model.

WHAT GETS PRESERVED:
- Service counts ("14 microservices")
- Storage requirements ("500 GB of SSD storage")
- Environment references ("production", "staging")
- HA/DR language ("high availability required")
- Region references ("us-central1")

WHAT GETS REDACTED:
- Email addresses
- Phone numbers
- Street addresses
- Account/contract IDs
- Client/customer names
- Pricing/budget lines
"""

import re


# Each pattern matches a specific type of sensitive data

# Matches: john.doe@company.com
EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")

# Matches: (555) 123-4567, +1 555-123-4567
PHONE_PATTERN = re.compile(r"(\+\d{1,2}\s)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}")

# Matches: 123 Main Street, 456 Oak Blvd
ADDRESS_PATTERN = re.compile(
    r"\b\d{1,5}\s+[A-Za-z0-9.\- ]+\s(?:Street|St|Road|Rd|Avenue|Ave|Drive|Dr|Lane|Ln|Boulevard|Blvd)\b",
    re.IGNORECASE,
)

# Matches: Account ID: ABC-1234, Contract Number: 98765
ACCOUNT_PATTERN = re.compile(
    r"\b(?:account|contract|customer)[ _-]?(?:id|number|no)\s*[:#-]?\s*[A-Z0-9-]{4,}\b",
    re.IGNORECASE,
)

# Matches lines like: "Client Name: Acme Corp" or "Customer: John Smith"
CLIENT_FIELD_PATTERN = re.compile(
    r"(?im)^(Client Name|Customer Name|Company|Customer|Primary Contact)\s*:\s*.+$"
)

# Matches lines containing pricing/budget info
PRICING_PATTERN = re.compile(
    r"(?im)^.*(?:price|pricing|cost|budget|annual spend|monthly spend).*$"
)


def sanitize_text(text):
    """
    Takes raw SOW text and returns a sanitized version with PII redacted.

    All customer-identifying info is replaced with [REDACTED_*] tags.
    Sizing-relevant details needed for config generation are preserved.

    Parameters:
        text (str): The raw text extracted from the SOW PDF

    Returns:
        str: The sanitized text with PII replaced by [REDACTED_*] tags
    """
    if not text:
        return ""

    # Apply each redaction pattern in order
    sanitized = EMAIL_PATTERN.sub("[REDACTED_EMAIL]", text)
    sanitized = PHONE_PATTERN.sub("[REDACTED_PHONE]", sanitized)
    sanitized = ADDRESS_PATTERN.sub("[REDACTED_ADDRESS]", sanitized)
    sanitized = ACCOUNT_PATTERN.sub("[REDACTED_ACCOUNT_ID]", sanitized)
    sanitized = CLIENT_FIELD_PATTERN.sub(
        lambda match: f"{match.group(1)}: [REDACTED]", sanitized
    )
    sanitized = PRICING_PATTERN.sub("[REDACTED_PRICING_LINE]", sanitized)

    # Clean up extra blank lines
    sanitized = re.sub(r"\n{3,}", "\n\n", sanitized)
    return sanitized.strip()


# ---- TESTING ----
if __name__ == "__main__":
    sample = """Client Name: Acme Corporation
Contact: john.doe@acme.com
Phone: (555) 123-4567
Address: 123 Main Street, Suite 400

The solution requires 14 microservices with 500 GB of SSD storage.
Environment: production
Budget: $45,000/month
Account ID: ACME-2024-001
High availability is required.
"""
    print("=== Original ===")
    print(sample)
    print("\n=== Sanitized ===")
    print(sanitize_text(sample))
