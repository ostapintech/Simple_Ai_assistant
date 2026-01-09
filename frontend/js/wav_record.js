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

    try {
        const response = await fetch("http://localhost:8000/api/audio", {
            method: "POST",
            body: formData
        });

        if (!response.ok) throw new Error("Upload failed");

        statusDiv.textContent = "✅ Audio successfully recordered!";
        statusDiv.style.color = "green";
        console.log("Audio sent to backend");
    } catch (err) {
        console.error("Upload failed:", err);
        statusDiv.textContent = "❌ Audio recording error!";
        statusDiv.style.color = "red";
    }
}
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
