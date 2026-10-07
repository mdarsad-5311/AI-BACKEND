"""
PDF Text Extraction Service for DocuSense AI.

Handles safe page-by-page text extraction from uploaded PDF documents using pypdf.
Preserves page numbers, page ordering, and empty-page structures without executing PDF content.
"""

import io
from typing import Dict, Any, List
from pypdf import PdfReader
from pypdf.errors import PdfReadError


class PDFExtractionError(Exception):
    """Custom exception raised when PDF text extraction cannot be completed."""
    pass


def extract_text_from_pdf(file_obj) -> Dict[str, Any]:
    """
    Safely extract page-by-page text and metadata from a PDF file stream or path.

    Args:
        file_obj: A file-like object (e.g. Django FieldFile, InMemoryUploadedFile, open file)

    Returns:
        Dict with keys:
            - "text": Full concatenated text of document
            - "pages": List of dicts [{"page_number": int, "text": str}]
            - "page_count": Total number of pages

    Raises:
        PDFExtractionError: If PDF is invalid, corrupted, or cannot be read.
    """
    try:
        # If file_obj has open/seek methods, rewind to beginning
        if hasattr(file_obj, 'seek'):
            file_obj.seek(0)

        # Read bytes to ensure safe isolated in-memory processing
        if hasattr(file_obj, 'read'):
            raw_bytes = file_obj.read()
            # Rewind file_obj if possible
            if hasattr(file_obj, 'seek'):
                file_obj.seek(0)
            stream = io.BytesIO(raw_bytes)
        else:
            stream = file_obj

        reader = PdfReader(stream)
        total_pages = len(reader.pages)

        if total_pages == 0:
            raise PDFExtractionError("PDF contains 0 pages.")

        pages_data: List[Dict[str, Any]] = []
        full_text_parts: List[str] = []

        for idx, page in enumerate(reader.pages, start=1):
            try:
                page_text = page.extract_text() or ""
            except Exception as e:
                # Handle subtle page decoding errors gracefully without failing whole document
                page_text = ""

            cleaned_text = page_text.strip()
            pages_data.append({
                "page_number": idx,
                "text": cleaned_text
            })
            if cleaned_text:
                full_text_parts.append(cleaned_text)

        full_document_text = "\n\n".join(full_text_parts)

        return {
            "text": full_document_text,
            "pages": pages_data,
            "page_count": total_pages
        }

    except PdfReadError as e:
        raise PDFExtractionError(f"Corrupted or invalid PDF format: {str(e)}")
    except PDFExtractionError:
        raise
    except Exception as e:
        raise PDFExtractionError(f"Unexpected error while extracting PDF: {str(e)}")
