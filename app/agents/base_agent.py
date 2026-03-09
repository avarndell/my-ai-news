import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


class BaseAgent:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAPI_API_KEY"))
        self.model = os.getenv("OPENAPI_MODEL")
