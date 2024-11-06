# services/file_processor.py

import io
import os
import tempfile
from typing import Tuple, Dict, Any, List
from langchain_community.document_loaders import Docx2txtLoader
from api.services.pdf_service import pdf_page_to_images
from api.services.openai_service import send_image_to_openai
from api.services.text_service import load_texts_with_sources, split_text
from PIL import Image
from langchain.schema import Document

async def process_image_text(images: List[Image.Image], vision_model: str, filename: str) -> Tuple[List[Document], float, float]:
    """Process images and extract text as DocumentPage objects with metadata."""
    total_tokens = 0
    total_cost = 0
    all_text = ""

    for image in images:
        with io.BytesIO() as img_buffer:
            image.save(img_buffer, format="PNG")
            img_bytes = img_buffer.getvalue()

        # Send image to OpenAI
        result = await send_image_to_openai(img_bytes, model=vision_model)

        all_text += result["content"] + "\n"
        total_tokens += result["total_tokens"]
        total_cost += result["total_cost"]

    # Convert into text pair
    text_source_pairs = [(all_text, filename)]

    # Convert into Langchain document
    documents = load_texts_with_sources(text_source_pairs)

    # Split documents
    splitted_docs = split_text(documents)

    return splitted_docs, total_tokens, total_cost

def load_docx(file_bytes: bytes) -> List[Document]:
    """Load DOCX file bytes into Langchain Documents."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as temp_file:
        temp_file.write(file_bytes)
        temp_file_path = temp_file.name

    loader = Docx2txtLoader(temp_file_path)
    loaded = loader.load()

    os.remove(temp_file_path)

    return loaded

async def process_single_file(file_bytes: bytes, filename: str, vision_model: str) -> Tuple[str, Dict[str, Any], str]:
    """Process a single file (PDF or DOCX) and extract text."""
    _, ext = os.path.splitext(filename)
    ext = ext.lower()

    total_tokens = 0.0
    total_cost = 0.0
    all_text = ""
    splitted_docs = []

    if ext == ".docx":
        langchain_documents = load_docx(file_bytes)
        print(f"Loaded DOCX file: {filename}")
        
    elif ext == ".pdf":
        # Process PDF
        images = pdf_page_to_images(file_bytes)
        print(f"Converted PDF to images: {filename}")

        # Extract text from images
        langchain_documents, total_tokens, total_cost = await process_image_text(images, vision_model, filename)
        print(f"Extracted text from PDF: {filename}")
    else:
        raise ValueError("Unsupported file type")

    # Raw Text
    all_text= ""
    for doc in langchain_documents:
      all_text += doc.page_content + "\n"

    # Splitting document
    splitted_docs = split_text(langchain_documents)

    # Key to store extracted data (could be S3 URL)
    key = filename

    result = {
        "splitted_docs": splitted_docs,
        "total_tokens": total_tokens,
        "total_cost": total_cost
    }

    return key, result, all_text
