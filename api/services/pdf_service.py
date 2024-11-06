# services/pdf_service.py

from pdf2image import convert_from_bytes
from PIL import Image
from typing import List
import io

def pdf_page_to_images(pdf_bytes: bytes) -> List[Image.Image]:
    """Convert PDF bytes to a list of PIL Image objects."""
    return convert_from_bytes(pdf_bytes, dpi=300)
