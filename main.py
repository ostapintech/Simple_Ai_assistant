import os
import uvicorn
import tempfile
from contextlib import asynccontextmanager
from pydantic import BaseModel
from fastapi import FastAPI, UploadFile, File, HTTPException
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

from ai import AIService

load_dotenv()
ai_service: AIService = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global ai_service
    ai_service = AIService()

    yield

class TextSchema(BaseModel):
    text: str

app = FastAPI(title='AI assistant', lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:63342"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.post("/api/audio")
async def speech_to_text(file: UploadFile = File(...)):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            text = ai_service.speech_to_text(tmp_path)
            return {"text": text}
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

@app.post('/api/process')
def text_processing(prompt: TextSchema):
    input_text = prompt.text
    try:
        result = ai_service.text_processing(input_text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Error: {str(e)}")


if __name__ == '__main__':
    uvicorn.run("main:app", reload=True, host='0.0.0.0', port=8000)