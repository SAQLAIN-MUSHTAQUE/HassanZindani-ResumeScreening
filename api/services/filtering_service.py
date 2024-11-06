
from api.services.pinecone_service import query_pinecone
import asyncio

# Filtering Primary fields (e.g: experience, education, skill, job_task)
async def filtering_skill_edu_exp(job_data, namespace: str, top_k:int):

    # Create asynchronous tasks for fund queries
    if 'required_experience' in job_data and job_data['required_experience'] != "":
        query = job_data['required_experience']
        task1 = [query_pinecone(query = query, namespace= namespace, top_k= top_k)]
    else:
        task1 = []

        # 'skill_matching': query_matching(diversity_focused, "funds-diversity-focus", top_k_diversity_focus),
    if 'required_education' in job_data and job_data['required_education'] != "":
        query = job_data['required_education']

        task2 = [query_pinecone(query = query, namespace= namespace, top_k= top_k)]
    else:
        task2 = []

    if 'required_skills' in job_data and job_data['required_skills'] != "":
        query = job_data['required_skills']
        task3 = [query_pinecone(query = query, namespace= namespace, top_k= top_k)]
    else:
        task3 = []

    if 'job_responsibilities_required' in job_data and job_data['job_responsibilities_required'] != "":
        query = job_data['job_responsibilities_required']
        task4 = [query_pinecone(query = query, namespace= namespace, top_k= top_k)]
    else:
        task4 = []

    # Run task1 and task2 concurrently
    raw_results1, raw_results2, raw_results3, raw_results4 = await asyncio.gather(
        asyncio.gather(*task1),  # Gather all results from task1
        asyncio.gather(*task2),  # Gather all results from task2
        asyncio.gather(*task3),   # Gather all results from task3
        asyncio.gather(*task4)   # Gather all results from task4
    )
    results1 = [item for sublist in raw_results1 for item in sublist]  # Flatten the list of lists
    results2 = [item for sublist in raw_results2 for item in sublist]  # Flatten the list of lists
    results3 = [item for sublist in raw_results3 for item in sublist]  # Flatten the list of lists
    results4 = [item for sublist in raw_results4 for item in sublist]  # Flatten the list of lists

    final_results = {}

    for r1 in results1:
        file_name = r1['metadata']['source']
        if r1['score'] >=0.5:
            if file_name not in final_results:
                final_results[file_name] = {}
                final_results[file_name]['score'] = [r1['score']]
                final_results[file_name]['reason'] = f"The job experience field matched with the experience of the candidate"
                final_results[file_name]['text'] = r1['metadata']['text']
            else:
                final_results[file_name]['score'].append(r1['score'])
                final_results[file_name]['text'] += " " + r1['metadata']['text']

    for r2 in results2:
        file_name = r1['metadata']['source']
        if r2['score'] >=0.5:
            if file_name not in final_results:
                final_results[file_name] = {}
                final_results[file_name]['score'] = [r2['score']]
                final_results[file_name]['reason'] = f"The education matched with the education of the candidate"
                final_results[file_name]['text'] = r2['metadata']['text']
            else:
                final_results[file_name]['score'].append(r2['score'])
                final_results[file_name]['text'] += " " + r2['metadata']['text']

    for r3 in results3:
        file_name = r3['metadata']['source']
        if r3['score'] >=0.5:
            if file_name not in final_results:
                final_results[file_name] = {}
                final_results[file_name]['score'] = [r3['score']]
                final_results[file_name]['reason'] = f"The skills matched with the skills of the candidate"
                final_results[file_name]['text'] = r3['metadata']['text']
            else:
                final_results[file_name]['score'].append(r3['score'])
                final_results[file_name]['text'] += " " + r3['metadata']['text']

    for r4 in results4:
        file_name = r4['metadata']['source']
        if r4['score'] >=0.5:
            if file_name not in final_results:
                final_results[file_name] = {}
                final_results[file_name]['score'] =[r4['score']]
                final_results[file_name]['reason'] = f"The responsibilities matched with the responsibilities of the candidate"
                final_results[file_name]['text'] = " " + r4['metadata']['text']
            else:
                final_results[file_name]['score'].append(r4['score'])
                final_results[file_name]['text'] += r4['metadata']['text']

    return final_results