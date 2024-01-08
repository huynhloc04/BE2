import openai
import os
from config import OPENAI_MODEL
import time, json
from typing import Any

openai.api_key = os.getenv("OPENAI_API_KEY")


class OpenAIService:
    @staticmethod
    def gpt_api(text: str):
        model: str = OPENAI_MODEL
        temp: float = 0

        print(" >>> Parsing...")

        """Request gpt api with a prompt"""
        start = time.time()
        response = openai.ChatCompletion.create(
            model = model,
            messages = [{
                    "role": "user", 
                    "content": text
                            }],
            temperature=temp
            )        
        elaps_time = time.time() - start

        print(f" >>> Request gpt api in {elaps_time}")
        return json.loads(response.choices[0].message.content)
