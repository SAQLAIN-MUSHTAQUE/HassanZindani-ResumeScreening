import json
import os
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Load environment variables from.env file
load_dotenv(override=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# OpenAI Client
client = AsyncOpenAI(api_key = OPENAI_API_KEY)


async def extract_query_info(query_system_prompt, query, llm_model = "gpt-4o-2024-08-06"):


   # User message
    user_message = f"""Extract the information from the job post text: {query}"""

    # Generate the completion
    completion = await client.chat.completions.create(
        model=llm_model,
        messages=[
            {"role": "system", "content": query_system_prompt},
            {"role": "user", "content": user_message},
        ],
        response_format={ "type": "json_object" },
    )

    # Get the response message
    json_message = completion.choices[0].message.content
    message = json.loads(json_message)

    return message