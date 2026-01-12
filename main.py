import os
import uvicorn
import tempfile
from contextlib import asynccontextmanager
from pydantic import BaseModel
from fastapi import FastAPI, UploadFile, File, HTTPException
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from database import SessionLocal, TranscriptionEntry, init_db

from ai import AIService

load_dotenv()
ai_service: AIService = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global ai_service
    ai_service = AIService()
    init_db()

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
        results = ai_service.text_processing(input_text)

        db = SessionLocal()
        new_entry = TranscriptionEntry(
            cleaned_text=results['transcription'],
            summary=results['summary'],
            translation=results['translation']
        )
        db.add(new_entry)
        db.commit()
        db.refresh(new_entry)
        db.close()

        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/history")
async def get_history():
    db = SessionLocal()
    entries = db.query(TranscriptionEntry).order_by(TranscriptionEntry.created_at.desc()).limit(10).all()
    db.close()
    return entries

if __name__ == '__main__':
    uvicorn.run("main:app", reload=True, host='0.0.0.0', port=8000)