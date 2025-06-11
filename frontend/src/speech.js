// src/speech.js
let recognition;
let mediaRecorder;
let audioChunks = [];

export function startListening(onResult) {
  if (!('webkitSpeechRecognition' in window)) {
    alert("Speech Recognition not supported in your browser. Try Chrome.");
    return;
  }
  recognition = new window.webkitSpeechRecognition();
  recognition.continuous = true;
  recognition.interimResults = true;
  recognition.lang = "en-US";

  recognition.onresult = (event) => {
    const transcript = Array.from(event.results)
      .map(result => result[0])
      .map(result => result.transcript)
      .join('');
    onResult(transcript);
  };
  recognition.start();
}

export function stopListening() {
  if (recognition) {
    recognition.stop();
    recognition = null;
  }
}

export async function speakText(text) {
  const fd = new FormData();
  fd.append("text", text);

  const res = await fetch("http://localhost:8000/generate-audio", {
    method: "POST",
    body: fd
  });
  const { audio_url } = await res.json();
  
  const audio = new Audio(audio_url);
  audio.play();
}
