from pdfminer.high_level import extract_text
from typing import Any, Sequence
from pprint import pprint
import openai
import json
import time
import sys
import argparse

openai.api_key = "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"

#   Read resume as text file and add prompt to it
def extract_resume(filename: str) -> str:
    text = extract_text(f"resume/{filename}.pdf")
    with open("prompt.txt") as prompt:
        for line in prompt:
            text += line
    return text


def gpt_api(model: str, text: str) -> Any: 

    start = time.time()

    response = openai.ChatCompletion.create(
        model = model,
        messages = [
                        {"role": "user", 
                         "content": text}
                   ],
        temperature=0
        ).choices[0].message.content
    
    elaps_time = time.time() - start
    return json.loads(response), elaps_time


if __name__ == "__main__":

    # Instantiate the parser
    parser = argparse.ArgumentParser(description='Optional app description!!!')
    parser.add_argument("--filename", type=str, help="Name of your resume.")
    parser.add_argument("--temp", type=float, default=0.3, help="Temperature in Completion.")

    args = parser.parse_args()

    model = "gpt-3.5-turbo-16k"    
    raw_text = extract_resume(args.filename)
    
    output, elaps = gpt_api(model, raw_text, args.temp)

    #   Write results to json file
    with open(f'results/{args.filename}.json', 'w') as f:
        json.dump(output, f)

    #   Show results as json format
    with open(f"results/{args.filename}.json", 'r') as file:
        data = json.load(file)
        pprint(data)
    
    print(f"  >>> Elaps time: {round(elaps, 1)}s.")


