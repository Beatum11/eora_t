from settings import cases_urls
from fake_useragent import UserAgent
from utils import get_eora_assistant, get_genai_client, get_parser

def main():
    user_a = UserAgent()

    genai_client = get_genai_client()
    parser = get_parser(user_a)
    eora_assistant = get_eora_assistant(genai_client, parser)


    eora_assistant.add_documents_from_urls(urls=cases_urls)


    print('Добрый день! Что вас интересует?\nЕсли нужно выйти из диалога, нажмите 1\n\n')
    while True:
        query = input('Введите свой вопрос: ')
        if query == 1:
            break
        print(eora_assistant.get_answer(query=query))


if __name__ == '__main__':
    main()