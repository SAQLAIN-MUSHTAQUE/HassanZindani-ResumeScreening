from api.models.batch import Batch
from api.models.job_post import JobPost
from api.services.chatbot.llms import extract_query_info
from api.services.chatbot.prompts import query_system_prompt
from api.services.filtering_service import filtering_skill_edu_exp
from api.services.pinecone_service import tok_k_function
from api.services.utils import adding_cv_text, filtering_other_field, merge_dictionaries, transform_and_sort_response
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

    # Comparing job_title
    if "job_title" in extracted_query_info and (extracted_query_info["job_title"] != "" and extracted_query_info["job_title"] != None):
        query = extracted_query_info["job_title"]
        title_matched = await filtering_other_field(job_query=query, 
                                                    filter_list=filter_list, 
                                                    namespace= namespace,
                                                    top_k= top_k,
                                                    max_score=0.3)
        
        logger.debug(f"title_matched {title_matched}")
    else:
        title_matched = {}

    # Comparing job_description
    if "job_description" in extracted_query_info and (extracted_query_info["job_description"] != "" and extracted_query_info["job_description"] != None):
        query = extracted_query_info["job_description"]
        description_matched = await filtering_other_field(job_query= query, 
                                                          filter_list= filter_list,
                                                          namespace= namespace,
                                                          top_k= top_k,
                                                          max_score=0.3)
        
        logger.debug(f"description_matched {description_matched}")
    else:
        description_matched = {}

    # Comparing job_reponsibilities_optional
    if "job_responsibilities_optional" in extracted_query_info and (extracted_query_info["job_responsibilities_optional"] != "" and extracted_query_info["job_responsibilities_optional"] != None):
        query = extracted_query_info["job_responsibilities_optional"]
        optional_responsibilities_matched = await filtering_other_field(job_query=query, 
                                                                        filter_list=filter_list,
                                                                        namespace= namespace,
                                                                        top_k= top_k,
                                                                        max_score=0.3)
        
        logger.debug(f"optional_responsibilities_matched {optional_responsibilities_matched}")
    else:
        optional_responsibilities_matched = {}

    # Comparing required_degree
    if "required_degree" in extracted_query_info and (extracted_query_info["required_degree"] != "" and extracted_query_info["required_degree"] != None):
        query = extracted_query_info["required_degree"]
        degree_matched = await filtering_other_field(job_query= query,
                                                    filter_list= filter_list,
                                                    namespace= namespace,
                                                    top_k=top_k,
                                                    max_score=0.3
                                                    )
        
        logger.debug(f"degree_matched {degree_matched}")
    else:
        degree_matched = {}

    # Comparing location
    if "required_location" in extracted_query_info and (extracted_query_info["required_location"] != "" and extracted_query_info["required_location"] != None):
        query = extracted_query_info["required_location"]
        location_matched = await filtering_other_field(job_query= query, 
                                                        filter_list= filter_list,
                                                        namespace= namespace,
                                                        top_k= top_k, 
                                                        max_score=0.3)
        
        logger.debug(f"location_matched {location_matched}")
    else:
        location_matched = {}
    
    # Comparing Extra info
    if "extra_info" in extracted_query_info and (extracted_query_info["extra_info"] != "" and extracted_query_info["extra_info"] != None):
        query = extracted_query_info["extra_info"]
        extra_info_matched = await filtering_other_field(job_query=query, 
                                                         filter_list= filter_list, 
                                                         namespace=namespace,
                                                         top_k=top_k, 
                                                         max_score=0.3)
        
        logger.debug(f"extra_info_matched {extra_info_matched}")
    else:
        extra_info_matched = {}

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

    return merged_scoring_dict