# AI speech to text transript

App records your speech and transcribes it into text, then cleans, summarizes, and translates using llm

Requirement to speak only Ukrainian 

# Project structer
- frontend (index.html, style.css, js)
- ai.py (transcription and other text processing)
- database.py (SQL connection settings)
- main.py (API endpoints and FastAPI configuration)

# Running the App 

1. open terminal and install requirements.txt using this command: 
   ### pip install -r requirements.txt 

2. run the app with this command:
   ### python3 main.py

3. open index.html in any one browser

4. On the website you will see a "Run" button, click it, now you can record audio. Click "Stop" and the audio will be automatically sent to llm.
Below you will see the result of the program. On the right you can see the history of your requests.
