import asyncio
import os
import shutil
from document_processor import process_document

# Setup dummy file
os.makedirs("documents/raw_files", exist_ok=True)
dummy_txt_path = "documents/raw_files/test_doc.txt"
with open(dummy_txt_path, "w") as f:
    f.write("This is a test document for extraction engine.\nSecond line.\n")

document_id = "test-uuid-1234"

try:
    pages_text, metadata = process_document(dummy_txt_path, document_id, ".txt")
    print("Metadata extracted:")
    print(metadata.model_dump())
    print("\nPages Extracted:")
    for page in pages_text:
        print(f"Page {page['page']}: {page['text'][:50]}...")
    
    print("\nExtraction Success!")
except Exception as e:
    print(f"Extraction failed: {e}")

# Cleanup
if os.path.exists(dummy_txt_path):
    os.remove(dummy_txt_path)
