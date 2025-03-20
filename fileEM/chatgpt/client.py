import openai
import yaml
from pypdf import PdfReader
from pdfminer.high_level import extract_text
from fileEM.utils.path import path
from fileEM import __path__ as config_prefix

class gptCilent(object):
    '''
    Chatgpt Client
    '''
    def __init__(self, url, api, model):
        self.model = model
        self._client = openai.Client(
            api_key=api,
            base_url=url
        )

    def query(self, request, **kwargs):
        return self._client.chat.completions.create(
            model=self.model,
            messages=request,
            **kwargs
        )

