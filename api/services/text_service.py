# services/text_service.py

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from typing import List, Tuple

def split_text(documents: List[Document]) -> List[Document]:
    """Split documents into smaller chunks."""
    text_splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n\n\n", "\n\n\n", "\n\n", "\n• ", "\n○ ", "\n- ", "\t", "\n"],
        chunk_size=100,
        chunk_overlap=15,
    )
    return text_splitter.split_documents(documents)

def load_texts_with_sources(text_source_pairs: List[Tuple[str, str]]) -> List[Document]:
    """Convert text and source pairs into Langchain Document objects."""
    return [Document(page_content=text, metadata={"source": source}) for text, source in text_source_pairs]
