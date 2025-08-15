from dotenv import load_dotenv
import os
from assistant import EoraAssistant
from google import genai
from parse import Parser
from fake_useragent import UserAgent

load_dotenv()

def get_eora_assistant(genai_client: genai.Client, 
                       parser: Parser) -> EoraAssistant:
    return EoraAssistant(genai_client=genai_client, parser=parser)


def get_genai_client() -> genai.Client:

    api_key = os.environ.get('API_KEY')
    if not api_key:
        raise ValueError('Нет API_KEY')
    
    return genai.Client(api_key=api_key)


def get_parser(user_agent: UserAgent):
    return Parser(us_agent=user_agent)
