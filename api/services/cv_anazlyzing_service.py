from api.models.batch import Batch
from api.models.job_post import JobPost
from api.services.chatbot.llms import evaluate_cv, extract_query_info
from api.services.chatbot.prompts import query_system_prompt, evaluation_system_prompt
from api.services.filtering_service import filtering_skill_edu_exp
from api.services.pinecone_service import tok_k_function
from api.services.utils import adding_cv_text, filtering_other_field, merge_dictionaries, transform_and_sort_response
import asyncio
from loguru import logger

async def analyzing_process(batch: Batch, job_post: JobPost, query: str, llm_model:str = "gpt-4o-2024-08-06"):

    """
    
    """

    # Extracting Data from the query
    extracted_query_info= await extract_query_info(query_system_prompt = query_system_prompt, 
                                                    query= query, 
                                                    llm_model = llm_model)
    logger.debug(f"extracted_query_info: {extracted_query_info}")

    # Saving query info in the database
    job_post.job_post_data = extracted_query_info
    job_post.save()

    # Initialize namespace 
    namespace = str(batch.id)

    # Initialize top_k
    top_k= tok_k_function(namespace= namespace)

    # Filtering Primary fields (e.g: experience, education, skill, job_task)
    pf_result= await filtering_skill_edu_exp(job_data= extracted_query_info,
                                             namespace= namespace,
                                             top_k=top_k)
    
    # transform into proper dictionary
    scoring_dict = transform_and_sort_response(pf_result)

    # Filtering against remaining fiields
    # Filter list
    filter_list = list(scoring_dict.keys())
    filtering_tasks = []

    # title_matched
    if "job_title" in extracted_query_info and extracted_query_info["job_title"]:
        filtering_tasks.append(filtering_other_field(job_query=extracted_query_info["job_title"],
                                                     filter_list=filter_list,
                                                     namespace=namespace,
                                                     top_k=top_k,
                                                     max_score=0.3))
    
    # description_matched
    if "job_description" in extracted_query_info and extracted_query_info["job_description"]:
        filtering_tasks.append(filtering_other_field(job_query=extracted_query_info["job_description"],
                                                     filter_list=filter_list,
                                                     namespace=namespace,
                                                     top_k=top_k,
                                                     max_score=0.3))
    
    # optional_responsibilities_matched
    if "job_responsibilities_optional" in extracted_query_info and extracted_query_info["job_responsibilities_optional"]:
        filtering_tasks.append(filtering_other_field(job_query=extracted_query_info["job_responsibilities_optional"],
                                                     filter_list=filter_list,
                                                     namespace=namespace,
                                                     top_k=top_k,
                                                     max_score=0.3))
    
    # degree_matched
    if "required_degree" in extracted_query_info and extracted_query_info["required_degree"]:
        filtering_tasks.append(filtering_other_field(job_query=extracted_query_info["required_degree"],
                                                     filter_list=filter_list,
                                                     namespace=namespace,
                                                     top_k=top_k,
                                                     max_score=0.3))
    
    # location_matched
    if "required_location" in extracted_query_info and extracted_query_info["required_location"]:
        filtering_tasks.append(filtering_other_field(job_query=extracted_query_info["required_location"],
                                                     filter_list=filter_list,
                                                     namespace=namespace,
                                                     top_k=top_k,
                                                     max_score=0.3))
    
    # extra_info_matched
    if "extra_info" in extracted_query_info and extracted_query_info["extra_info"]:
        filtering_tasks.append(filtering_other_field(job_query=extracted_query_info["extra_info"],
                                                     filter_list=filter_list,
                                                     namespace=namespace,
                                                     top_k=top_k,
                                                     max_score=0.3))

    # Execute all filtering tasks concurrently
    filtering_results = await asyncio.gather(*filtering_tasks)

    # Unpack results into respective variables
    title_matched, description_matched, optional_responsibilities_matched, degree_matched, location_matched, extra_info_matched = (
        filtering_results + [{}] * (6 - len(filtering_results))
    )

    # Log the results
    # logger.debug(f"title_matched: {title_matched}")
    # logger.debug(f"description_matched: {description_matched}")
    # logger.debug(f"optional_responsibilities_matched: {optional_responsibilities_matched}")
    # logger.debug(f"degree_matched: {degree_matched}")
    # logger.debug(f"location_matched: {location_matched}")
    # logger.debug(f"extra_info_matched: {extra_info_matched}")

    # Merge title_matched and description_matched into scoring_dict
    merged_scoring_dict = merge_dictionaries(scoring_dict,
                                            title_matched,
                                            description_matched,
                                            optional_responsibilities_matched,
                                            degree_matched,
                                            location_matched,
                                            extra_info_matched
                                            )
    
    # Adding Cv Text into merged dict
    merged_scoring_dict = adding_cv_text(merged_scoring_dict, batch)
    merged_scoring_dict

    # Evaluation by LLM
    final_result = await llm_evaluation(merged_scoring_dict= merged_scoring_dict, 
                                  job_post_db= job_post, 
                                  job_post= query, 
                                  evaluate_prompt= evaluation_system_prompt, 
                                  llm_model=llm_model)


    return final_result


# Helping Function:
async def llm_evaluation(merged_scoring_dict, job_post_db, job_post, evaluate_prompt, llm_model="gpt-4o-2024-08-06"):
    final_dictionary = {}

    # Creating a list of tasks to run concurrently
    tasks = [
        evaluate_cv(evaluate_prompt, job_post, value['cv_text'], llm_model= llm_model)
        for file_name, value in merged_scoring_dict.items()
    ]

    # Await all tasks concurrently
    responses = await asyncio.gather(*tasks)
    logger.debug(f"Response LLM Evaluation: {responses}")

    # Populating the final dictionary with responses
    for (file_name, value), response in zip(merged_scoring_dict.items(), responses):
        response['score'] = (response['score']//2)+value['score']  # Adding the previous score
        response['score'] = round((response['score']/5)*100, 2)                 # Max point 5
        final_dictionary[file_name] = response
        final_dictionary[file_name]['cv_text'] = value['cv_text']
        final_dictionary[file_name]['cv_url'] = value['cv_url']
        final_dictionary[file_name]['semantic_search_text'] = value['text']

    # Sorting the dictionary by score in descending order
    sorted_final_dictionary = dict(
        sorted(final_dictionary.items(), key=lambda item: item[1]['score'], reverse=True)
    )

    # Saving in database
    job_post_db.selected_cvs= sorted_final_dictionary
    job_post_db.save()

    return sorted_final_dictionary