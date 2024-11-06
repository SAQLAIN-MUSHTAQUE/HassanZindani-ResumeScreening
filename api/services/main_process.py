# services/main_process.py


from typing import List, Tuple, Dict, Any
from api.models.batch import Batch 
import asyncio
from services.file_processor import process_single_file

async def main_process(files: List[Tuple[bytes, str]], batch: Batch, vision_model: str) -> Tuple[Dict[str, Any], Dict[str, str], float, float]:
    """
    Orchestrate the processing of multiple files.
    :param files: List of tuples containing file bytes and filename.
    :param vision_model: The OpenAI vision model to use.
    :return: loaded_docs, all_raw_text, total_tokens, total_cost
    """
    loaded_docs = {}
    all_raw_text = {}
    total_tokens = 0.0
    total_cost = 0.0

    tasks = [process_single_file(file_bytes, filename, vision_model) for file_bytes, filename in files]
    results = await asyncio.gather(*tasks)

    for key, result, raw_text in results:
        loaded_docs[key] = result['splitted_docs']
        all_raw_text[key] = raw_text
        total_tokens += result['total_tokens']
        total_cost += result['total_cost']

        # Update database with processed data
        

    return loaded_docs, all_raw_text, total_tokens, total_cost
