const BASE = "http://localhost:8000";

export async function startInterview(name, resumeFile, jobDesc) {
  const fd = new FormData();
  fd.append("name", name);
  fd.append("resume", resumeFile);
  if (jobDesc) {
    fd.append("job_description", jobDesc);
  }

  const res = await fetch(`${BASE}/start-interview`, {
    method: "POST",
    body: fd,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({}));
    throw new Error(`Failed to start interview: ${error.detail || res.statusText}`);
  }
  return res.json();
}

export async function nextQuestion(sessionId, answer) {
  const fd = new FormData();
  fd.append("session_id", sessionId);
  fd.append("answer", answer);

  const res = await fetch(`${BASE}/next-question`, {
    method: "POST",
    body: fd,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({}));
    throw new Error(`Failed to get next question: ${error.detail || res.statusText} (${res.status})`);
  }
  return res.json();
}

export async function getFeedback(sessionId) {
  const fd = new FormData();
  fd.append("session_id", sessionId);

  const res = await fetch(`${BASE}/feedback`, {
    method: "POST",
    body: fd,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({}));
    throw new Error(`Failed to get feedback: ${error.detail || res.statusText} (${res.status})`);
  }
  return res.json();
}

export async function getAudio(text) {
  const fd = new FormData();
  fd.append("text", text);

  const res = await fetch(`${BASE}/generate-audio`, {
    method: "POST",
    body: fd,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({}));
    throw new Error(`Failed to get audio: ${error.detail || res.statusText} (${res.status})`);
  }
  const { audio_url } = await res.json();
  return audio_url;
}