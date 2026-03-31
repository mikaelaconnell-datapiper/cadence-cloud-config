"""
Station 1: PDF Text Extraction
================================
This file does one thing: takes a PDF file and returns all the text inside it.

PURPOSE:
AI models like Gemini can read PDFs directly, but if the goal is to redact
sensitive information before the model sees the content, the text needs to be
extracted first. Extracting to plain text allows the sanitizer to find and
replace PII using pattern matching.

HOW IT WORKS:
1. Try PyMuPDF first (better at handling tables and complex layouts)
2. If PyMuPDF returns nothing, fall back to pypdf (pure Python, more portable)
3. Normalize the whitespace so it's clean for downstream processing
4. Return the text string

LIBRARIES USED:
- PyMuPDF (imported as 'fitz') — best quality extraction
- pypdf — backup option, pure Python so it always works
"""

import logging
import re
from typing import List

logger = logging.getLogger(__name__)


def _normalize_whitespace(text):
    """
    Cleans up messy whitespace that PDF extraction often produces.

    PDFs store text in inconsistent ways — sometimes there are null characters,
    extra spaces from column layouts, or excessive blank lines. This function
    tidies that up so the text is clean for the sanitizer and the AI prompt.
    """
    # Replace null characters (sometimes hidden in PDFs) with spaces
    text = text.replace("\x00", " ")
    # Collapse multiple spaces/tabs into a single space
    text = re.sub(r"[ \t]+", " ", text)
    # Collapse 3+ newlines into just 2 (keeps paragraph breaks, removes excess)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _extract_with_pymupdf(filepath):
    """
    Primary extraction using PyMuPDF.

    PyMuPDF is the best PDF text extractor — it handles tables, columns,
    and complex layouts better than most alternatives. This is tried first.
    """
    try:
        import fitz  # PyMuPDF — "fitz" is just its internal package name
    except ImportError:
        logger.warning("PyMuPDF is not installed; skipping primary extraction.")
        return ""

    # Open the PDF file
    document = fitz.open(filepath)
    pages = []

    # Loop through every page and extract the text
    for page_number, page in enumerate(document, start=1):
        page_text = page.get_text("text").strip()
        if page_text:
            # Label each page so it's clear where the text came from
            pages.append(f"Page {page_number}\n{page_text}")

    document.close()
    return "\n\n".join(pages)


def _extract_with_pypdf(filepath):
    """
    Fallback extraction using pypdf.

    If PyMuPDF fails or returns empty text, pypdf is tried as a backup.
    It's pure Python so it always works, but produces slightly lower
    quality output for complex PDFs.
    """
    try:
        from pypdf import PdfReader
    except ImportError:
        logger.warning("pypdf is not installed; skipping fallback extraction.")
        return ""

    reader = PdfReader(filepath)
    text_content = []

    for page_number, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""
        if page_text.strip():
            text_content.append(f"Page {page_number}\n{page_text.strip()}")

    return "\n\n".join(text_content)


def extract_text_from_pdf(pdf_path):
    """
    Extracts text from a PDF using PyMuPDF with pypdf as a fallback.

    Parameters:
        pdf_path (str): The path to the PDF file

    Returns:
        str: All the text from the PDF, cleaned up and ready for processing
    """
    try:
        # Try PyMuPDF first (better quality)
        primary_text = _extract_with_pymupdf(pdf_path)
        normalized = _normalize_whitespace(primary_text)
        if normalized:
            return normalized

        # If PyMuPDF returned nothing, try pypdf as backup
        fallback_text = _extract_with_pypdf(pdf_path)
        normalized_fallback = _normalize_whitespace(fallback_text)
        if normalized_fallback:
            logger.warning("PyMuPDF extraction was empty; used pypdf fallback.")
            return normalized_fallback

        # Neither worked — the PDF might be scanned images (not text)
        logger.error("PDF extraction returned no usable text for %s", pdf_path)
        return ""
    except Exception as exc:
        logger.error("Failed to extract text from %s: %s", pdf_path, exc)
        return ""


def extract_text_from_txt(txt_path):
    """
    Reads a plain text SOW file.

    The sample SOWs in the data/ directory are .txt files.
    On dev day with real Cadence data, extract_text_from_pdf() handles the PDFs.
    """
    with open(txt_path, "r") as f:
        return f.read()


def extract_text(file_path):
    """
    Routes to the correct extraction method based on file type.

    This is the function the rest of the app calls — it handles both
    PDFs and text files so testing can use .txt files and dev day can use
    real PDFs without changing any other code.
    """
    if file_path.endswith(".pdf"):
        return extract_text_from_pdf(file_path)
    elif file_path.endswith(".txt"):
        return extract_text_from_txt(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_path}")


# ---- TESTING ----
# This block only runs when executing this file directly:
#   python3 extract_pdf.py
# It does NOT run when another file imports this module.

if __name__ == "__main__":
    text = extract_text("data/reference_sows/sow_acme_corp.txt")
    print("=== Extracted Text (first 500 chars) ===\n")
    print(text[:500])
    print(f"\n=== Total length: {len(text)} characters ===")
