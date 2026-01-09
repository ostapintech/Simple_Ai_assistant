async function sendPrompt() {
   const resultDiv = document.getElementById("result");

    resultDiv.textContent = "⏳ Loading...";

    try {

        const response = await fetch("http://localhost:8000/api/process");

        if (!response.ok) {
            throw new Error("Server error");
        }

        const data = await response.json();

        resultDiv.textContent =
            "Text: \n" + data.transcription + "\n\n" +
            "📌 Summary:\n" + data.summary + "\n\n" +
            "🌍 Translation:\n" + data.translation;

    } catch (error) {
        resultDiv.textContent = "❌ Error: " + error.message;
    }
}