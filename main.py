import os
import uvicorn
from groq import Groq
from fastapi import FastAPI, UploadFile, File, HTTPException
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()
app = FastAPI(title='AI assistant')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:63342"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
text = ''

@app.post("/api/audio")
async def speech_to_text(file: UploadFile = File(...)):
    client = Groq()

    try:
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
        return ({'result': text})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/api/process')
def text_processing():
    prompt = text
    try:
        gpt = init_chat_model(
            model='groq:openai/gpt-oss-20b',
            temperature=0.3,
        )
        llama = init_chat_model(model='groq:llama-3.1-8b-instant')

        clean_messages = [{'role': 'system', 'content': 'You are a professional Ukrainian language teacher'},
                    {'role': 'user', 'content': f"""
                        INSTRUCTIONS:
                        - If text has syntaxis errors, correct it
                        - If there any unreadable words, try to correct them
                        - If there any language except Ukrainian and English. Output: Applications work only with Uk and En 
                        - Output only corrected text

                        TEXT:
                        {prompt}"""}
                    ]
        clean = gpt.invoke(clean_messages)

        summ_messages = [
            {'role': 'system', 'content': 'You are a helpful assistant that summarize text in Ukrainian'},
            {'role': 'user', 'content': f"""
                        INSTRUCTIONS:
                        - Output only summarized text, without anything else

                        TEXT:
                        {clean}"""}
        ]
        summarize = gpt.invoke(summ_messages)


        translate_messages = [
            {'role': 'system', 'content': 'You are a translator from Ukrainian to English'},
            {'role': 'user', 'content': f"""
                        INSTRUCTIONS:
                        - Translate clearly given text
                        - Output only translated text

                        TEXT:
                        {summarize.content}"""}
        ]
        translate = llama.invoke(translate_messages)

        return {
            'transcription': clean.content,
            'summary': summarize.content,
            'translation': translate.content
        }


    except Exception as e:
        print({'error': f'API error: {e}'})


if __name__ == '__main__':
    uvicorn.run("main:app", reload=True, host='0.0.0.0', port=8000)