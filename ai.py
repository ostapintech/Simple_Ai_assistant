from groq import Groq
from langchain.chat_models import init_chat_model

class AIService:
    def __init__(self):
        self.whisper = Groq()
        self.gpt = init_chat_model(
            model='groq:openai/gpt-oss-20b',
            temperature=0.3,
        )
        self.llama = init_chat_model(model='groq:llama-3.1-8b-instant')

    def speech_to_text(self, filename: str) -> str:
        with open(filename, "rb") as f:
            transcription = self.whisper.audio.transcriptions.create(
                file=f,
                model="whisper-large-v3-turbo",
                language="uk",
            )

        return transcription.text

    def text_processing(self, text: str) -> dict:
        clean_messages = [{'role': 'system', 'content': 'You are a professional Ukrainian language teacher'},
                          {'role': 'user', 'content': f"""
                               INSTRUCTIONS:
                               - If text has syntaxis errors, correct it
                               - If there any unreadable words, try to correct them
                               - If there any language except Ukrainian and English. Output: Applications work only with Uk and En 
                               - Output only corrected text

                               TEXT:
                               {text}"""}
                          ]
        clean = self.gpt.invoke(clean_messages)

        summ_messages = [
            {'role': 'system', 'content': 'You are a helpful assistant that summarize text in Ukrainian'},
            {'role': 'user', 'content': f"""
                               INSTRUCTIONS:
                               - Output only summarized text, without anything else

                               TEXT:
                               {clean}"""}
        ]
        summarize = self.gpt.invoke(summ_messages)

        translate_messages = [
            {'role': 'system', 'content': 'You are a translator from Ukrainian to English'},
            {'role': 'user', 'content': f"""
                               INSTRUCTIONS:
                               - Translate clearly given text
                               - Output only translated text

                               TEXT:
                               {summarize.content}"""}
        ]
        translate = self.llama.invoke(translate_messages)

        return {
            'transcription': clean.content,
            'summary': summarize.content,
            'translation': translate.content
        }