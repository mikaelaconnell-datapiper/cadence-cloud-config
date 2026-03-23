"""
Station 1: PDF Text Extraction
================================
This file does ONE thing: takes a PDF file and returns all the text inside it.

WHY DO WE NEED THIS?
The AI (Gemini) can't read PDF files directly. It only understands plain text.
So before we can ask the AI to analyze a SOW document, we need to convert
the PDF into a string of text.

HOW IT WORKS:
1. Open the PDF file
2. Go through each page
3. Pull out all the text from each page
4. Combine it all into one big string
5. Return that string

LIBRARY WE USE:
- PyMuPDF (imported as 'fitz') — a Python library that can open and read PDFs.
  "fitz" is just the internal name, don't worry about why it's called that.
"""

import fitz  # This is PyMuPDF — the library that reads PDFs


def extract_text_from_pdf(pdf_path):
    """
    Takes a file path to a PDF and returns all the text inside it.

    Parameters:
        pdf_path (str): The path to the PDF file, like "data/eval_sows/sow_nimbus.pdf"

    Returns:
        str: All the text from the PDF, page by page
    """

    # Open the PDF file
    # Think of this like double-clicking a PDF to open it
    doc = fitz.open(pdf_path)

    # This list will hold the text from each page
    all_text = []

    # Loop through every page in the PDF
    # (most SOWs are multi-page documents)
    for page_number in range(len(doc)):

        # Get one page
        page = doc[page_number]

        # Extract the text from that page
        # This pulls out all readable text — paragraphs, tables, headers, etc.
        page_text = page.get_text()

        # Add it to our list
        all_text.append(page_text)

    # Close the PDF (good practice, like closing a file when you're done)
    doc.close()

    # Join all pages together with a newline between each page
    # "\n" means "new line" — like hitting Enter
    full_text = "\n".join(all_text)

    return full_text


def extract_text_from_txt(txt_path):
    """
    For our demo, the sample SOWs are .txt files (not real PDFs).
    This function reads a plain text file.

    On dev day with real Cadence data, you'd use extract_text_from_pdf() instead.
    """
    with open(txt_path, "r") as f:
        return f.read()


def extract_text(file_path):
    """
    Smart function that checks the file type and uses the right extraction method.

    This is the function the rest of the app will call — it handles both
    PDFs and text files so we can test with .txt files now and swap to
    real PDFs on dev day without changing any other code.
    """
    if file_path.endswith(".pdf"):
        return extract_text_from_pdf(file_path)
    elif file_path.endswith(".txt"):
        return extract_text_from_txt(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_path}")


# ---- TESTING ----
# This block only runs if you execute this file directly:
#   python3 extract_pdf.py
# It does NOT run when another file imports this one.

if __name__ == "__main__":
    # Test it on one of our sample SOWs
    text = extract_text("data/reference_sows/sow_acme_corp.txt")

    # Print the first 500 characters so we can see it worked
    print("=== Extracted Text (first 500 chars) ===\n")
    print(text[:500])
    print(f"\n=== Total length: {len(text)} characters ===")
