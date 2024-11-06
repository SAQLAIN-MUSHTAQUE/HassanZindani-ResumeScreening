from pinecone import Pinecone
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
import os
from dotenv import load_dotenv
from typing import Iterable, Iterator, List, Dict, TypeVar
from itertools import islice
from loguru import logger

load_dotenv(override=True)

# Pinecoe Credentials
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_URL = os.getenv("PINECONE_INDEX_URL")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")


# Defining Index
pc = Pinecone(PINECONE_API_KEY)
index = pc.Index(host=PINECONE_INDEX_URL)

# Load Embedding Model
embedding_model = OpenAIEmbeddings(model=EMBEDDING_MODEL)

# Upload Pitch deck text to pinecone
async def upload_to_pinecone(batch_id:str, splitted_docs:Dict):
    """
    Upload pitch deck text to Pinecone.

    Args:
        pitch_deck_id (str): The ID of the pitch deck document.
        pitch_object_key (str): The key of the pitch deck document.
        pitch_deck_text (str): The text content of the pitch deck document.

    Returns:
        str: Message indicating successful upload to Pinecone.
    """
    try:

        # namespace is same as pitch deck document's ID
        namespace = str(batch_id)

        # Uploading To Pinecone
        response = upload_data(splitted_docs, index, embedding_model, namespace)
        logger.debug(f"Pinecone Response: {response}")

        return f"The CVs Data have been successfully uploaded to Pinecone under the namespace '{batch_id}'."


    except Exception as e:
        print(f"Error while uploading to Pinecone: {e}")


# Helper Functions
# Pinecone Upload Fuction
T = TypeVar("T")

def batch_iterate(size: int, iterable: Iterable[T]) -> Iterator[List[T]]:
    """Utility batching function."""
    it = iter(iterable)
    while True:
        chunk = list(islice(it, size))
        if not chunk:
            return
        yield chunk
        
def upload_data(loaded_docs, index, embedding_model, namespace):
    embedding_chunk_size = 150
    batch_size = 70 # size of batch (length of chunks in one go.)

    ids_value = 0
    metadata_list = []
    texts = []
    ids = []

    for key, value in loaded_docs.items():
      texts.extend([page.page_content for page in value])
      metadata_list.extend([page.metadata for page in value])
      ids.extend([str(ids_value + i) for i in range(len(texts))])
      ids_value += len(texts)

    for metadata, text in zip(metadata_list, texts):
      metadata["text"] = text

    for i in range(0, len(texts), embedding_chunk_size):
      chunk_texts = texts[i : i + embedding_chunk_size]
      chunk_ids = ids[i : i + embedding_chunk_size]
      chunk_metadatas = metadata_list[i : i + embedding_chunk_size]
      embeddings = embedding_model.embed_documents(chunk_texts)

      # uploading asynchronously
      async_res = [
          index.upsert(
              vectors=batch,
              async_req=True,
              namespace=namespace
          )
          for batch in batch_iterate(
              batch_size, zip(chunk_ids, embeddings, chunk_metadatas)
          )
      ]
      [res.get() for res in async_res]
    
    return "Pinecone upload completed successfully."