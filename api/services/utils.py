import asyncio
from api.services.pinecone_service import query_pinecone
from typing import List

# Supporting Functions
def transform_and_sort_response(response):
    # Transform data to include text and sum of scores
    transformed_data = {
        file_path: {
            'text': details['text'],
            'score': max(details['score'])
        }
        for file_path, details in response.items()
    }

    # Sort the transformed data by score_sum in descending order
    sorted_data = dict(sorted(transformed_data.items(), key=lambda item: item[1]['score'], reverse=True))
    return sorted_data

# Helper function to handle querying and extracting matching
async def query_matching(query: str, namespace: str, top_k: int):
    """
    Queries the Pinecone service with the provided query string, namespace, and top_k value.

    Args:
        query (str): The query string to search for.
        namespace (str): The namespace in Pinecone to query against.
        top_k (int): The number of top results to return.

    Returns:
        list: A list of fund dictionaries returned from Pinecone.
    """
    return await query_pinecone(query=query, namespace=namespace, top_k=top_k)

# query filtering function
async def filtering_other_field(job_query:str, filter_list:List, namespace:str, top_k:int , max_score: float):
    tasks = [
        query_pinecone(query=job_query, namespace=namespace, top_k=top_k, filter={"source": {"$eq": name}})
        for name in filter_list
    ]

    results = []
    for completed_task in asyncio.as_completed(tasks):
        result = await completed_task
        results.append(result)  # Collect results as they complete

    flattened_results = [item for sublist in results for item in sublist]  # Flatten the list of lists

    final_results = {}

    # Filtering score
    for item in flattened_results:
        if item['score'] > max_score:
            file_name = item['metadata']['source']
            if file_name not in final_results:
                final_results[file_name] = {}
                final_results[file_name]['score'] = [item['score']]
                final_results[file_name]['reason'] = f"The field matched with the field of the candidate"
                final_results[file_name]['text'] = item['metadata']['text']
            else:
                final_results[file_name]['score'].append(item['score'])
                final_results[file_name]['text'] += " " + item['metadata']['text']

    # Transform recent dictionary
    transformed_dict = transform_and_sort_response(final_results)

    return transformed_dict

# Merging Dictionary Function
def merge_dictionaries(scoring_dict, *other_dicts):
    scoring_dict_copy = scoring_dict.copy()  # Create a copy to avoid modifying the original
    for data_dict in other_dicts:
        for filename, data in data_dict.items():
            if filename in scoring_dict_copy:
                # Append the new text to the existing text
                scoring_dict_copy[filename]['text'] += ' ' + data['text']
                # Add the new score to the existing score
                scoring_dict_copy[filename]['score'] += data['score']
            else:
                # Create a new entry if the filename does not exist in scoring_dict_copy
                scoring_dict_copy[filename]['text'] = data['text']
                scoring_dict_copy[filename]['score'] = data['score']

    for filename, value in scoring_dict_copy.items():
        print(value['score'])
        scoring_dict_copy[filename]['score'] = (value['score']) # The total best score is 1. But According to our data cleaning I am considering 0.5

    return scoring_dict_copy


# Function to Add CV Text into merged_dict
def adding_cv_text(merged_scoring_dict, batch_db):
    """
    Add the CV text and URL link into the merged_scoring_dict.

    Args:
        merged_scoring_dict (dict): The dictionary containing the scoring results.
        batch_db (Database): The database object containing the CV data.

    Returns:
        dict: The merged_scoring_dict with the CV text and URL link added.
    """
    cv_data = batch_db.cv_data
    for entry, value in cv_data.items():
        if entry in merged_scoring_dict:
            merged_scoring_dict[entry]['cv_text'] = value['cv_text']
            merged_scoring_dict[entry]['cv_url'] = value['url_link']

    return merged_scoring_dict
  
  
