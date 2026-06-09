# 🤖 AI Interviewer

This project is a **full-stack AI-powered mock interview platform**, built to simulate real technical and behavioral interviews, generate dynamic questions based on the role, and provide automated feedback on candidate responses.

It showcases an **end-to-end agentic interview pipeline** with a Python/FastAPI backend, a React frontend, LLM-powered question generation, and structured evaluation logic.

---

## 🚀 Features

- 🎯 Role-specific interview question generation using an LLM
- 💬 Interactive Q&A interface with real-time response capture
- 🧠 AI-powered feedback and scoring on candidate responses
- 📋 Session management — track and review past interview sessions
- 🔁 Follow-up question generation based on candidate answers
- 📊 Structured evaluation report at the end of each session

---

## 📦 Folder Structure

```
AI-Interviewer/
│
├── backend/
│   ├── app.py                # FastAPI entry point
│   ├── routes/               # API route handlers
│   ├── services/             # LLM integration, question gen, evaluation
│   ├── models/               # Pydantic schemas
│   └── requirements.txt      # Python dependencies
│
├── frontend/
│   ├── src/
│   │   ├── components/       # UI components (question card, feedback view)
│   │   ├── pages/            # App pages (home, interview, results)
│   │   └── App.js            # Root component
│   ├── public/
│   └── package.json
│
└── README.md
```

---

## ⚙️ Tech Stack

- Python 3.11+
- FastAPI
- OpenAI / LLM API
- React.js
- JavaScript (ES6+)
- HTML + CSS

---

## 🛠️ Installation

```bash
git clone https://github.com/tanmayypramanick/AI-Interviewer.git
cd AI-Interviewer
```

### Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Environment Setup

Create a `.env` file in `backend/`:

```
OPENAI_API_KEY=your_openai_api_key
```

### Frontend Setup

```bash
cd frontend
npm install
```

---

## 🧪 How to Run

### 1. Start the Backend

```bash
cd backend
uvicorn app:app --reload
```

The API will be available at `http://localhost:8000`.

### 2. Start the Frontend

```bash
cd frontend
npm start
```

Open `http://localhost:3000` in your browser.

---

## 🧠 How It Works

1. **User selects** a role and interview type (technical / behavioral)
2. **Backend generates** dynamic questions using an LLM
3. **User responds** to each question through the chat interface
4. **Follow-up questions** are generated based on the previous answer
5. **Evaluation engine** scores each response for clarity, depth, and relevance
6. **Results page** displays a full feedback report with improvement suggestions

---

## 👤 Author

**Developed by Tanmay Pramanick**

📧 tanmaypramanick06@gmail.com
🔗 https://www.linkedin.com/in/tanmaypramanick/
🔗 https://tanmaypramanick.vercel.app

---

## 🙏 Attribution

If you use or adapt this codebase, please credit the original author.

Drop a ⭐ on GitHub if this project helped you!

---

## 🧠 Inspiration

This project demonstrates a practical application of **LLM-driven agentic workflows** for interview preparation — generating contextual questions, handling dynamic follow-ups, and providing structured feedback automatically.

If you're hiring a Software / AI Engineer passionate about LLMs + full-stack development, reach out!
