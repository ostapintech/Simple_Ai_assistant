let audioContext;
let mediaStream;
let processor;
let input;
let audioData = [];

let isRecording = false;
const btn = document.getElementById("recordBtn");

btn.addEventListener("click", async () => {
    if (!isRecording) {
        await startRecording();
        btn.textContent = "⏹ Stop";
        isRecording = true;
        statusDiv.textContent = "Recording...";
        statusDiv.style.color = "black";
    } else {
        await stopRecording();
        btn.textContent = "🎙 Start";
        isRecording = false;
    }
});


async function startRecording() {
    audioData = [];
    audioContext = new AudioContext({ sampleRate: 16000 });
    mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });

    input = audioContext.createMediaStreamSource(mediaStream);
    processor = audioContext.createScriptProcessor(4096, 1, 1);

    processor.onaudioprocess = e => {
        audioData.push(new Float32Array(e.inputBuffer.getChannelData(0)));
    };

    input.connect(processor);
    processor.connect(audioContext.destination);

    console.log("Recording started");
}

const statusDiv = document.getElementById("statusMessage");

async function stopRecording() {
    if (!processor) return;

    processor.disconnect();
    input.disconnect();
    mediaStream.getTracks().forEach(track => track.stop());

    const wavBlob = encodeWAV(audioData, audioContext.sampleRate);
    const formData = new FormData();
    formData.append("file", wavBlob, "audio.wav");

    statusDiv.textContent = "⏳ Transcribing..."; // Міняємо статус на процес розпізнавання

    try {
        const response = await fetch("http://localhost:8000/api/audio", {
            method: "POST",
            body: formData
        });

        if (!response.ok) throw new Error("Upload failed");

        // 1. Отримуємо текст від бекенду
        const data = await response.json();
        const recognizedText = data.text; // Сервер повертає {"text": "..."}

        console.log("Recognized text:", recognizedText);
        statusDiv.textContent = "✅ Transcription received!";

        // 2. КЛЮЧОВИЙ КРОК: Передаємо цей текст у функцію обробки
        // Це той самий ланцюжок, який ми обговорювали
        sendPrompt(recognizedText);

    } catch (err) {
        console.error("Upload failed:", err);
        statusDiv.textContent = "❌ Error processing audio!";
        statusDiv.style.color = "red";
    }
}
async function sendPrompt(textFromAudio) {
    const resultDiv = document.getElementById("result");

    // Якщо тексту немає, не продовжуємо
    if (!textFromAudio) {
        resultDiv.textContent = "❌ Немає тексту для обробки";
        return;
    }

    resultDiv.textContent = "🤖 ШІ обробляє текст...";

    try {
        const response = await fetch("http://localhost:8000/api/process", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                text: textFromAudio // Тепер тут точно є рядок, а не undefined
            })
        });

        const data = await response.json();

        resultDiv.innerHTML = `
            <p><b>📝 Оригінал:</b> ${data.transcription}</p>
            <p><b>📌 Summary:</b> ${data.summary}</p>
            <p><b>🌍 Переклад:</b> ${data.translation}</p>
        `;

    } catch (error) {
        resultDiv.textContent = "❌ Помилка ШІ: " + error.message;
    }
    loadHistory();
}
async function loadHistory() {
    const historyDiv = document.getElementById("historyList");

    // Показуємо статус завантаження
    historyDiv.innerHTML = "⏳ Завантаження історії...";

    try {
        const response = await fetch("http://localhost:8000/api/history");

        if (!response.ok) throw new Error("Не вдалося завантажити історію");

        const historyData = await response.json(); // Отримуємо масив записів

        if (historyData.length === 0) {
            historyDiv.innerHTML = "Історія порожня.";
            return;
        }

        // Очищуємо контейнер перед виводом
        historyDiv.innerHTML = "";

        // Створюємо картку для кожного запису
        historyData.forEach(item => {
            const date = new Date(item.created_at).toLocaleString('uk-UA');

            const card = document.createElement("div");
            card.className = "history-card";
            card.innerHTML = `
                <div style="border: 1px solid #ddd; padding: 10px; margin-bottom: 10px; border-radius: 8px;">
                    <small style="color: gray;">${date}</small>
                    <p><b>📌 Summary:</b> ${item.summary}</p>
                    <p><b>🌍 Переклад:</b> ${item.translation}</p>
                </div>
            `;
            historyDiv.appendChild(card);
        });

    } catch (error) {
        historyDiv.innerHTML = "❌ Помилка історії: " + error.message;
    }
}

// Викликаємо функцію відразу при завантаженні сторінки
window.onload = loadHistory;
// --- WAV encoding ---
function encodeWAV(buffers, sampleRate) {
    const length = buffers.reduce((sum, b) => sum + b.length, 0);
    const data = new Float32Array(length);
    let offset = 0;
    for (let b of buffers) { data.set(b, offset); offset += b.length; }

    const buffer = new ArrayBuffer(44 + data.length * 2);
    const view = new DataView(buffer);

    function writeString(view, offset, string) {
        for (let i = 0; i < string.length; i++) view.setUint8(offset + i, string.charCodeAt(i));
    }

    writeString(view, 0, 'RIFF');
    view.setUint32(4, 36 + data.length * 2, true);
    writeString(view, 8, 'WAVE');
    writeString(view, 12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    view.setUint16(22, 1, true);
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * 2, true);
    view.setUint16(32, 2, true);
    view.setUint16(34, 16, true);
    writeString(view, 36, 'data');
    view.setUint32(40, data.length * 2, true);

    let pos = 44;
    for (let i = 0; i < data.length; i++, pos += 2) {
        const s = Math.max(-1, Math.min(1, data[i]));
        view.setInt16(pos, s < 0 ? s*0x8000 : s*0x7fff, true);
    }

    return new Blob([view], { type: 'audio/wav' });
}
