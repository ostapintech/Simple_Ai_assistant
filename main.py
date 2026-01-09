import os
import uvicorn
from groq import Groq
from fastapi import FastAPI, UploadFile, File
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()
app = FastAPI(title='AI assistant')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
text = ''

@app.post("/api/audio")
async def speech_to_text(file: UploadFile = File(...)):
    client = Groq()

    filename = os.path.join(os.path.dirname(__file__), "audio.wav")
    with open(filename, "wb") as f:
        f.write(await file.read())

    with open(filename, "rb") as f:
        transcription = client.audio.transcriptions.create(
            file=f,
            model="whisper-large-v3-turbo",
            language="uk"
        )
    global text
    text = transcription.text
    return {"text": transcription.text}

@app.get('/api/process')
def text_processing():
    prompt = text
    try:
        gpt = init_chat_model(model='groq:openai/gpt-oss-20b')
        messages = [{'role': 'system', 'content': 'You are a professional Ukrainian language teacher'},
        {'role': 'user', 'content': f"""
                INSTRUCTIONS:
                - If text has syntaxis errors, correct it
                - If there any unreadable words, try to correct them
    
                TEXT:
                {prompt}"""}
        ]
        clean = gpt.invoke(messages)

        messages = [
            {'role': 'system', 'content': 'You are a helpful assistant that summarize text in Ukrainian'},
            {'role': 'user', 'content': f"""
                INSTRUCTIONS:
                - Output only summarized text, without anything else
    
                TEXT:
                {clean}"""}
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

        return ({'transcription': clean.content, 'summary': summarize.content, 'translation': translate.content})


    except Exception as e:
            print({'error': f'API error: {e}'})


if __name__ == '__main__':
    uvicorn.run("main:app", reload=True, host='0.0.0.0', port=8000)
