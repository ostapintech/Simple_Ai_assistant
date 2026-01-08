from fastapi import FastAPI
from pydantic import BaseModel
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

load_dotenv()
app = FastAPI(title='AI assistant')

# Для локального тесту
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

class AIRequest(BaseModel):
    text: str

@app.post('/api/process')
def text_processing(req: AIRequest):
    prompt = req.text
    try:
        gpt = init_chat_model(model='groq:openai/gpt-oss-20b')
        messages = [
            {'role': 'system', 'content': 'You are a helpful assistant that summarize text in Ukrainian'},
            {'role': 'user', 'content': prompt}
        ]
        summarize = gpt.invoke(messages)

        llama = init_chat_model(model='groq:llama-3.1-8b-instant')
        messages = [
            {'role': 'system', 'content': 'You are a translator from Ukrainian to English'},
            {'role': 'user', 'content': f"""
                INSTRUCTIONS:
                - Translate clearly given text
                - Output only translated text

                TEXT:
                {summarize.content}"""}
        ]
        translate = llama.invoke(messages)

        return ({'summary': summarize.content, 'translation': translate.content})


    except Exception as e:
            print({'error': f'Виникла проблема з API: {e}'})


if __name__ == '__main__':
    import uvicorn
    uvicorn.run("main:app", reload=True, host='0.0.0.0', port=8000)
