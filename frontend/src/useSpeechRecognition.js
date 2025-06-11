// src/useSpeechRecognition.js
import { useState } from "react";

export default function useSpeechRecognition() {
  const [transcript, setTranscript] = useState("");

  const recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const recog = new recognition();
  recog.lang = "en-US";
  recog.interimResults = true;
  recog.continuous = true;

  recog.onresult = (event) => {
    const result = event.results[event.results.length - 1][0].transcript;
    setTranscript(result);
  };

  const startListening = () => recog.start();
  const stopListening = () => recog.stop();
  const resetTranscript = () => setTranscript("");

  return { transcript, startListening, stopListening, resetTranscript };
}
