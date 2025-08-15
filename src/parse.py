import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import re

class Parser:

    def __init__(self, us_agent: UserAgent) -> None:
        self.us_agent = us_agent

        self.headers = {'User-Agent': self.us_agent.random}

    def get_main_info_list(self, url: str) -> list[str]:
        
        raw_html = self._get_raw_html(url=url)
        soup = BeautifulSoup(raw_html, 'lxml')

        for tag in soup(['script', 'style', 'noscript']):
            tag.extract()

        for tag in soup.find_all(style=re.compile(r'display\s*:\s*none')):
            tag.extract()
        
        container = soup.find('div', id='allrecords')
        if container is not None:
            text = container.get_text(separator='\n')
            return [line.strip() for line in text.split('\n') if len(line.strip()) > 0]
        else:
            return []

    def _get_raw_html(self, url: str) -> str:
        res = requests.get(url, headers=self.headers)
        return res.text

