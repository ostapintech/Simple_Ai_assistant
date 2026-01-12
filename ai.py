from groq import Groq
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

class AIService:
    def __init__(self):
        self.whisper = Groq()
        self.llama = init_chat_model(
            model='groq:llama-3.1-8b-instant',
            temperature = 0.3
        )

    def speech_to_text(self, filename: str) -> str:
        with open(filename, "rb") as f:
            transcription = self.whisper.audio.transcriptions.create(
                file=f,
                model="whisper-large-v3-turbo",
                language="uk",
            )

        return transcription.text

    def text_processing(self, text: str) -> dict:

        prompt = ChatPromptTemplate.from_messages([
            ('system', """You are professional editor and translator.
            Process text from user and return ONLY JSON object with the following keys:
            "transcription" - corrected Ukrainian text (punctuation, grammar),
            "summary" - summary in Ukrainian,
            "translation" - high-quality translation of the summary into English.

            Important: Don't write anything except JSON"""),
            ('user', '{input_text}')
        ])

        chain = prompt | self.llama | JsonOutputParser()

        try:
            return chain.invoke({"input_text": text})
        except Exception as e:
            print(f"Chain error: {e}")
            return {
                "transcription": text,
                "summary": "Помилка обробки",
                "translation": "Processing error"
            }
