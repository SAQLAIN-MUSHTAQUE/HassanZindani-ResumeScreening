# services/openai_service.py

import aiohttp
import base64
import tiktoken
from typing import Dict
from dotenv import load_dotenv
import os 

load_dotenv(override=True)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") 

async def encode_image(image_bytes: bytes) -> str:
    """Encode image bytes as a base64 string."""
    return base64.b64encode(image_bytes).decode("utf-8")

async def count_tokens(text: str, model: str = "gpt-4o-mini") -> int:
    """Count the number of tokens in a text using tiktoken."""
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))

async def send_image_to_openai(image_bytes: bytes, model: str = "gpt-4o-mini") -> Dict:
    """Send an image to OpenAI API and receive the extracted text."""
    base64_image = await encode_image(image_bytes)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }

    prompt = "Extract the exact text from the provided image without adding any additional lines at the beginning."

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 1200
    }

    async with aiohttp.ClientSession() as session:
        async with session.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload) as response:
            response_data = await response.json()
            output_text = response_data['choices'][0]['message']['content']

    # Calculate tokens used
    input_tokens = await count_tokens(prompt, model=model)
    output_tokens = await count_tokens(output_text, model=model)
    total_tokens = input_tokens + output_tokens

    # Pricing details
    cost_per_input_token = 0.150 / 1_000_000  # $ per input token
    cost_per_output_token = 0.600 / 1_000_000  # $ per output token
    cost_per_image = 0.01275  # $ per image (300x300 px)

    # Calculate total cost
    input_cost = input_tokens * cost_per_input_token
    output_cost = output_tokens * cost_per_output_token
    total_cost = cost_per_image + input_cost + output_cost

    return {
        "content": output_text,
        "total_tokens": total_tokens,
        "total_cost": total_cost
    }
