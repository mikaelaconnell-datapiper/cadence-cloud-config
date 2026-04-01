"""
Text Sanitizer — PII Redaction
================================
This file strips sensitive customer data from SOW text before it is sent to
the AI model.

PURPOSE:
Data privacy is a primary concern. Cadence SOWs contain customer names,
addresses, contact info, billing details, signatures, payment information,
and contract terms. None of that should reach the model.

WHAT GETS PRESERVED:
- Chamber configuration details (platform, location, instance types)
- Hardware requirements (vCPUs, RAM, storage)
- Software/license information (product names, quantities)
- User counts and locations
- PDK requirements

WHAT GETS REDACTED (based on Cadence's "Information to avoid" list):
- SOW headings with order numbers
- Customer addresses and billing addresses
- Cadence addresses
- Customer point of contact and signatures
- Email addresses and phone numbers
- Terms and conditions
- Payment schedule/information
- Account holder details
- Cadence signatures
- Footer text with document IDs
"""

import re


# ---- Patterns based on Cadence's "Information to avoid" list ----

# Matches email addresses: lei_yan@genexic.com
EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")

# Matches phone numbers: (555) 123-4567, +1 555-123-4567
PHONE_PATTERN = re.compile(r"(\+\d{1,2}\s)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}")

# Matches street addresses: 123 Main Street, 450 Park Avenue
ADDRESS_PATTERN = re.compile(
    r"\b\d{1,5}\s+[A-Za-z0-9.\- ]+\s(?:Street|St|Road|Rd|Avenue|Ave|Drive|Dr|Lane|Ln|Boulevard|Blvd|Way|Place|Pl|Suite)\b",
    re.IGNORECASE,
)

# Matches order/contract numbers: Order #C-GNX01, Contract Number: 98765
ORDER_PATTERN = re.compile(
    r"\b(?:Order|Contract|Agreement)\s*(?:#|No|Number|ID)\s*[:#-]?\s*[A-Z0-9-]{3,}\b",
    re.IGNORECASE,
)

# Matches SOW document IDs in footers: 2025 390951, SF-STD-KB
FOOTER_PATTERN = re.compile(
    r"(?im)^.*(?:Cadence Managed Cloud, Order and SOW|SF-STD-KB).*$"
)

# Matches "Attn:" lines: Attn: Lei Yan
ATTN_PATTERN = re.compile(r"(?im)^Attn\s*:.*$")

# Matches "Email:" lines: Email: lei_yan@genexic.com
EMAIL_LINE_PATTERN = re.compile(r"(?im)^Email\s*:.*$")

# Matches customer/billing address sections
ADDRESS_SECTION_PATTERN = re.compile(
    r"(?im)^(?:Customer Address|Billing Address|Cadence Address|Ship To|Bill To)\s*:?.*$"
)

# Matches signature/contact sections
SIGNATURE_PATTERN = re.compile(
    r"(?im)^(?:Customer Signature|Cadence Signature|Customer Point of Contact|Account Holder|Authorized Signatory)\s*:?.*$"
)

# Matches terms and conditions / payment sections
TERMS_PATTERN = re.compile(
    r"(?im)^(?:Terms and Conditions|Payment Schedule|Payment Information|Payment Terms).*$"
)

# Matches lines with client/customer name labels
CLIENT_FIELD_PATTERN = re.compile(
    r"(?im)^(Client Name|Customer Name|Company|Customer|Primary Contact|Prepared For|Prepared By)\s*:\s*.+$"
)

# Matches pricing/budget lines
PRICING_PATTERN = re.compile(
    r"(?im)^.*(?:price|pricing|cost|budget|annual spend|monthly spend|total amount|invoice|payment due).*$"
)

# Matches SOW heading lines with evaluation/order references
SOW_HEADING_PATTERN = re.compile(
    r"(?im)^.*(?:Cadence Manage[d]? Cloud.*Order|Evaluation Order for|ChipStart).*$"
)

# Matches account/contract ID patterns
ACCOUNT_PATTERN = re.compile(
    r"\b(?:account|contract|customer)[ _-]?(?:id|number|no)\s*[:#-]?\s*[A-Z0-9-]{4,}\b",
    re.IGNORECASE,
)


def sanitize_text(text):
    """
    Takes raw SOW text and returns a sanitized version with PII redacted.

    All customer-identifying info is replaced with [REDACTED_*] tags.
    Chamber configuration details, hardware specs, software licenses,
    and user requirements are preserved.

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
    sanitized = ORDER_PATTERN.sub("[REDACTED_ORDER_ID]", sanitized)
    sanitized = FOOTER_PATTERN.sub("[REDACTED_FOOTER]", sanitized)
    sanitized = ATTN_PATTERN.sub("[REDACTED_CONTACT]", sanitized)
    sanitized = EMAIL_LINE_PATTERN.sub("[REDACTED_CONTACT]", sanitized)
    sanitized = ADDRESS_SECTION_PATTERN.sub("[REDACTED_ADDRESS_SECTION]", sanitized)
    sanitized = SIGNATURE_PATTERN.sub("[REDACTED_SIGNATURE]", sanitized)
    sanitized = TERMS_PATTERN.sub("[REDACTED_TERMS]", sanitized)
    sanitized = CLIENT_FIELD_PATTERN.sub(
        lambda match: f"{match.group(1)}: [REDACTED]", sanitized
    )
    sanitized = PRICING_PATTERN.sub("[REDACTED_PRICING]", sanitized)
    sanitized = SOW_HEADING_PATTERN.sub("[REDACTED_SOW_HEADING]", sanitized)
    sanitized = ACCOUNT_PATTERN.sub("[REDACTED_ACCOUNT_ID]", sanitized)

    # Clean up extra blank lines
    sanitized = re.sub(r"\n{3,}", "\n\n", sanitized)
    return sanitized.strip()


# ---- TESTING ----
if __name__ == "__main__":
    sample = """Cadence Managed Cloud Evaluation Order for ChipStart EU Order #C-GNX01
Customer Name: GenExIC GmbH
Customer Address: Berliner Str 45, 10713 Berlin, Germany
Billing Address: Same as above
Attn: Lei Yan
Email: lei_yan@genexic.com

Chamber Configuration Section
Platform Provider: AWS
Chamber Location: AWS Frankfurt
Total number of Users: 10
5 accounts in Berlin Germany
5 accounts in Istanbul Turkiye

Hardware requirements:
1 interactive server
16 vCPUs, 64 GB RAM
M6i.4xlarge instance type
1000 GB backup project storage

Software/Licensed Materials:
3 Virtuoso(R) Schematic Editor L
9 Spectre(R) MMSIM with Spectre X Simulator

Terms and Conditions: Standard Cadence terms apply.
Payment Schedule: Net 30 days
Customer Signature: _______________
Cadence Managed Cloud, Order and SOW 2025 390951
SF-STD-KB
"""
    print("=== Original ===")
    print(sample)
    print("\n=== Sanitized ===")
    print(sanitize_text(sample))
