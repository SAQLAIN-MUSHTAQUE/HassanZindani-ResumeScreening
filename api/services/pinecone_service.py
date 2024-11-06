from pinecone import Pinecone
import asyncio
from concurrent.futures import ThreadPoolExecutor
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


# Query Pinecone 
async def query_pinecone(query: str, namespace: str , top_k: int, filter: dict = None, index = index) -> list:
    """
    Query the Pinecone index with the given parameters.

    Args:
        query: The query string to be embedded and searched.
        namespace: The namespace to query within.
        top_k: The number of top results to return.
        filter: Optional dictionary for metadata filtering.

    Returns:
        list:The query responses from Pinecone.
    """
    # Embed the query string
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as pool:
        # Embedding in thread pool
        embedded = await loop.run_in_executor(pool, embedding_model.embed_query, query)

        # Pinecone query in thread pool
        query_params = {
            "namespace": namespace,
            "vector": embedded,
            "top_k": top_k,
            "include_metadata": True,
        }
        if filter:
            query_params["filter"] = filter

        try:
            responses = await loop.run_in_executor(pool, lambda: index.query(**query_params))
        except Exception as e:
            print(f"Error during Pinecone query: {e}")
            return []

    # Extract essential data
    results = []
    for match in responses["matches"]:
        # print (f"{query} \n {match['id']}")
        results.append({
            "id": match["id"],
            "score": match["score"],
            "metadata": match["metadata"],
            "values":match["values"]
        })
    return results  # Return a list of dictionaries instead of Pinecone matches

# Namespace total state function
def tok_k_function(namespace:str, index= index):
    # Calculating top-k using index
    stats = index.describe_index_stats()
    # check the namespaces and their vector counts
    namespace_stats = stats['namespaces']
    namespace= namespace
    experience_top_k= namespace_stats.get(namespace,{}).get('vector_count', 0)

    return experience_top_k