import re
import unicodedata
import os
from collections import Counter

try:
    from unstructured.partition.auto import partition
except ImportError:
    partition = None


def extract_text(file_path: str) -> str:
    """
    Extracts text from PDF, DOCX, TXT, etc.
    Uses unstructured library if available for robust extraction.
    Fallback for simple txt files if unstructured is not installed.
    """
    if partition and os.path.exists(file_path):
        try:
            elements = partition(filename=file_path)
            return "\n".join([str(el) for el in elements])
        except Exception as e:
            print(f"Error using unstructured partition: {e}")
            pass

    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()


def normalize_unicode(text: str) -> str:
    """Step 1: Normalize Unicode characters."""
    return unicodedata.normalize("NFKD", text)


def fix_broken_lines(text: str) -> str:
    """Step 2: Fix words broken across lines by hyphenation.
    Fixes: 'trans-\\nforming' → 'transforming'
    """
    return re.sub(r'-\n(\w)', r'\1', text)


def remove_page_numbers(text: str) -> str:
    """Step 3: Remove page number patterns."""
    text = re.sub(r'(?i)\bPage\s+\d+\b', '', text)
    text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'\b\d+\s+of\s+\d+\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'-\s*\d+\s*-', '', text)
    return text


def remove_separator_lines(text: str) -> str:
    """Step 4: Remove separator lines like ----, ====, ____"""
    return re.sub(r'^[-=_]{3,}\s*$', '', text, flags=re.MULTILINE)


def remove_repeated_headers_footers(text: str) -> str:
    """Step 5: Detect and remove frequently repeated lines."""
    lines = text.split('\n')
    line_counts = Counter(line.strip() for line in lines if line.strip())
    repeated = {
        line for line, count in line_counts.items()
        if count > 2 and len(line) > 3
    }
    cleaned_lines = [line for line in lines if line.strip() not in repeated]
    return '\n'.join(cleaned_lines)


def remove_copyright_lines(text: str) -> str:
    """Step 6: Remove copyright and legal boilerplate."""
    text = text.replace("All Rights Reserved", "")
    text = re.sub(r'(?i)Copyright\s*©?\s*\d{4}.*', '', text)
    text = re.sub(r'©\s*\d{4}.*', '', text)
    text = re.sub(r'XYZ University Research Report', '', text)
    return text


def remove_urls(text: str) -> str:
    """Step 7: Remove URLs from text."""
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'www\.\S+', '', text)
    return text


def remove_emails(text: str) -> str:
    """Step 8: Remove email addresses from text."""
    return re.sub(r'\S+@\S+', '', text)


def remove_special_symbols(text: str) -> str:
    """Step 9: Remove unwanted special symbols."""
    return re.sub(r'[^a-zA-Z0-9\s.,!?;:()\-\'\"\n]', '', text)


def fix_joined_words(text: str) -> str:
    """Step 10: Fix words incorrectly joined due to PDF extraction.
    Fixes: 'transformingIndustries' → 'transforming Industries'
    """
    return re.sub(r'([a-z])([A-Z])', r'\1 \2', text)


def normalize_whitespace(text: str) -> str:
    """Step 11: Normalize multiple spaces and blank lines."""
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text


def clean_text(text: str) -> str:
    """
    Master text cleaning function for RAG pipeline.

    Workflow:
    Raw Text
        ↓ Step 1:  Normalize Unicode
        ↓ Step 2:  Fix broken hyphenated lines
        ↓ Step 3:  Remove page numbers
        ↓ Step 4:  Remove separator lines
        ↓ Step 5:  Remove repeated headers/footers
        ↓ Step 6:  Remove copyright lines
        ↓ Step 7:  Remove URLs
        ↓ Step 8:  Remove emails
        ↓ Step 9:  Remove special symbols
        ↓ Step 10: Fix joined words
        ↓ Step 11: Normalize whitespace
        ↓ Step 12: Final strip
    Clean Text (ready for chunking)
    """
    if not text or not text.strip():
        return ""

    text = normalize_unicode(text)
    text = fix_broken_lines(text)
    text = remove_page_numbers(text)
    text = remove_separator_lines(text)
    text = remove_repeated_headers_footers(text)
    text = remove_copyright_lines(text)
    text = remove_urls(text)
    text = remove_emails(text)
    text = remove_special_symbols(text)
    text = fix_joined_words(text)
    text = normalize_whitespace(text)
    return text.strip()


def process_document(input_path: str, output_path: str):
    """
    Full pipeline to extract, clean, and save document text.
    Input:  raw_document.txt / .pdf / .docx
    Output: clean_document.txt
    """
    print(f"Extracting text from {input_path}...")
    raw_text = extract_text(input_path)

    print("Cleaning text...")
    cleaned_text = clean_text(raw_text)

    print(f"Saving cleaned text to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(cleaned_text)

    print(f"Done!")
    print(f"Raw length:    {len(raw_text)} characters")
    print(f"Clean length:  {len(cleaned_text)} characters")
    print(f"Noise removed: {round((1 - len(cleaned_text)/max(len(raw_text),1))*100, 1)}%")


if __name__ == "__main__":
    import sys

    input_file = "raw_document.txt"
    output_file = "clean_document.txt"

    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]

    if os.path.exists(input_file):
        process_document(input_file, output_file)
    else:
        print(f"Warning: {input_file} not found.")
        print("Running sample test...\n")

        sample = """Page 1

Research Paper on Artificial Intelligence

====================================

Introduction

Artificial    Intelligence is trans-
forming industries.

Page 2

Research Paper on Artificial Intelligence

Visit https://example.com
Contact: abc@gmail.com

Copyright © 2026 All Rights Reserved

@@@@ Special Section ####
"""
        print("--- RAW TEXT ---")
        print(sample)
        print("\n--- CLEANED TEXT ---")
        print(clean_text(sample))