# Save the information chatgpt will need.
from pathlib import Path
from pdfminer.high_level import extract_text
from fileEM.chatgpt.client import gptCilent
import json

def extractDoi(cilent, path):
    # Extract first two pages to get the doi number
    path = Path(path).expanduser().resolve()
    pdf = extract_text(path, maxpages=3)
    messages=[{"role": "system", 
               "content": 'You are a literature information extraction assistant. Please extract the doi of the paper. The only thing you should return is doi, don\'t add anything!'},
              {"role": "user",
               "content": pdf}]
    response = cilent.query(messages)
    return response.choices[0].message.content

tools = [
    {
        "type": "function",
        "function": {
            "name": 'getPath',
            "description": 'Get the path and doi from the article.',
            "parameters": {
                'type': 'object',
                'properties': {
                    "path": {
                        "type": "string",
                        "description": "The path of the article."
                    },
                },
                "required": ['path'],
                "additionalProperties" : False,
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": 'query',
            "description": 'Query the articles according to the information.',
            "parameters": {
                'type': 'object',
                'properties': {
                    "authors": {
                        "type": ["string", "null"],
                        "description": "Name of all the authors. Separate each author with a |, e.g. qu | ja."
                    },
                    "title": {
                        "type": ["string", "null"],
                        "description": "The article title contains this part. Separate each word with |, e.g. qu | ja."
                    },
                    "journal": {
                        "type": ["string", "null"],
                        "description": "The journal name contains this part. "
                    },
                    "fields": {
                        "type": ["string", "null"],
                        "description": "The fields of the article. Separate each word with |, e.g. mechanics | fluid."
                    },
                },
                "additionalProperties" : False,
            },
        }
    },

]
