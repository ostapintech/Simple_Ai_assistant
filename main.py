# from fastapi import FastAPI
# import uvicorn
from langchain_core.messages import AIMessage
from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv


load_dotenv()
def text_processing(prompt):
    try:
        gpt = init_chat_model(model = 'groq:openai/gpt-oss-20b')

        messages = [
            {'role': 'system', 'content': 'You are a helpful assistant that summarize text in Ukrainian'},
            {'role': 'user', 'content': ''}
        ]

        messages[1].update({'content': prompt})
        summarize = gpt.invoke(messages)

        llama = init_chat_model(model = 'groq:llama-3.1-8b-instant')

        messages = [
            {'role': 'system', 'content': 'You are a translator from Ukrainian to English'},
            {'role': 'user', 'content': f'{summarize.content}'}
        ]

        translate = llama.invoke(messages)
        return translate.content

    except Exception as e:
        print(f'Виникла проблема з API: {e}')

if __name__ == '__main__':
    prompt = input("Введіть текст для обробки: ")
    if prompt.strip():
        print(text_processing(prompt))
    else:
        print("Введіть текст")