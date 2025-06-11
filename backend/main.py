from fastapi import FastAPI, File, Form, UploadFile, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from memory import create_session, get_phase, set_phase, log_message, get_history, should_continue_interview, mark_interview_over, mark_awaiting_candidate_question, is_candidate_questioning, get_all_session_ids, clear_session
from prompts import generate_greeting, generate_first_response_after_greeting, generate_followup_question, generate_end_of_interview_question, generate_answer_to_candidate, generate_feedback
from utils import extract_text_from_pdf, chunk_text, create_index, search_similar, extract_keywords
import uuid
import logging
import re

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/sessions")
async def list_sessions():
    """List all active session IDs."""
    return {"sessions": get_all_session_ids()}

@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session by ID."""
    clear_session(session_id)
    return {"message": f"Session {session_id} deleted"}

@app.post("/start-interview")
async def start_interview(request: Request, name: str = Form(...), resume: UploadFile = File(...), job_description: str = Form(None)):
    """Start a new interview session."""
    try:
        logger.debug(f"Request headers: {dict(request.headers)}")
        try:
            raw_body = await request.body()
            logger.debug(f"Raw request body (first 100 bytes): {raw_body[:100]}")
        except Exception as e:
            logger.error(f"Failed to read raw body: {str(e)}")
        
        if not resume.filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Resume must be a PDF file")
        
        session_id = str(uuid.uuid4())
        
        resume_bytes = await resume.read()
        resume_text = extract_text_from_pdf(resume_bytes)
        if not resume_text:
            raise HTTPException(status_code=400, detail="Failed to extract text from resume")
        
        resume_chunks = chunk_text(resume_text)
        resume_index, resume_chunks = create_index(resume_chunks)
        if resume_index is None:
            raise HTTPException(status_code=500, detail="Failed to create index for resume")
        
        job_desc_text = job_description if job_description else ""
        job_desc_chunks = chunk_text(job_desc_text) if job_desc_text else []
        job_desc_index = create_index(job_desc_chunks)[0] if job_desc_chunks else None
        
        create_session(
            session_id=session_id,
            user_name=name,
            resume_chunks=resume_chunks,
            resume_index=resume_index,
            resume_text=resume_text,
            job_desc_chunks=job_desc_chunks,
            job_desc_index=job_desc_index,
            job_desc_text=job_desc_text
        )
        set_phase(session_id, "greeting")
        
        greeting = generate_greeting(name)
        log_message(session_id, "ai", greeting)
        
        logger.debug(f"Started session: {session_id}, Question: {greeting}")
        return {
            "session_id": session_id,
            "question": greeting,
            "is_interview_over": False,
            "audio_url": None
        }
    
    except ValueError as e:
        logger.error(f"Form validation error: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid form data: {str(e)}. Ensure request is multipart/form-data with 'name' (string), 'resume' (PDF file), and optional 'job_description' (string)."
        )

@app.post("/next-question")
async def next_question(session_id: str = Form(...), answer: str = Form(...)):
    """Generate the next question or handle candidate question."""
    if session_id not in get_all_session_ids():
        raise HTTPException(status_code=404, detail="Session not found")
    
    history = get_history(session_id)
    log_message(session_id, "user", answer)
    
    # Check if the answer is a question
    is_question = bool(re.search(r'\?$|\b(how|what|why|when|where|who|can you|could you|tell me|does|do you)\b', answer.lower().strip(), re.IGNORECASE))
    current_phase = get_phase(session_id)
    
    # Handle closing phase or candidate questions
    if current_phase == "closing" or is_candidate_questioning(session_id):
        if answer.lower().strip() in ["no", "nah", "i'm good", "none", "nothing"]:
            mark_interview_over(session_id)
            feedback = generate_feedback(history)
            logger.debug(f"Generated feedback: {feedback}")
            return {
                "question": "Thanks for your time! Here's your feedback below.",
                "feedback": feedback,
                "is_interview_over": True,
                "audio_url": None
            }
        if is_question:
            response = generate_answer_to_candidate(answer, history, session_id)
            log_message(session_id, "ai", response)
            mark_awaiting_candidate_question(session_id, done=False)
            logger.debug(f"Generated candidate answer: {response}")
            return {
                "question": response,
                "is_interview_over": False,
                "audio_url": None
            }
    
    # Generate next question based on phase
    if not history or current_phase == "greeting":
        response = generate_first_response_after_greeting(session_id, answer)
        set_phase(session_id, "project")
    elif should_continue_interview(session_id, history):
        response = generate_followup_question(session_id, history)
        phase_map = {
            1: "project",
            2: "project_2",
            3: "technical",
            4: "technical_2",
            5: "problem-solving",
            6: "coding",
            7: "behavioral",
            8: "behavioral_2",
            9: "role-fit",
            10: "closing"
        }
        question_count = len([m for m in history if m["role"] == "ai" and m["content"].endswith("?")])
        next_phase = phase_map.get(question_count + 1, "closing")
        set_phase(session_id, next_phase)
    else:
        response = generate_end_of_interview_question()
        set_phase(session_id, "closing")
        mark_awaiting_candidate_question(session_id)
    
    log_message(session_id, "ai", response)
    logger.debug(f"Generated question: {response}, Phase: {current_phase}")
    
    return {
        "question": response,
        "is_interview_over": False,
        "audio_url": None
    }

@app.post("/feedback")
async def get_feedback(session_id: str = Form(...)):
    """Generate feedback for a completed interview."""
    if session_id not in get_all_session_ids():
        raise HTTPException(status_code=404, detail="Session not found")
    
    history = get_history(session_id)
    if not history or get_phase(session_id) != "closing":
        raise HTTPException(status_code=400, detail="Interview not completed")
    
    feedback = generate_feedback(history)
    logger.debug(f"Generated feedback: {feedback}")
    return {
        "feedback": feedback,
        "is_interview_over": True,
        "audio_url": None
    }

@app.post("/generate-audio")
async def generate_audio(text: str = Form(...)):
    """Generate audio for the given text (Vapi integration placeholder)."""
    logger.debug(f"Generating audio for text: {text[:50]}...")
    audio_url = "https://example.com/audio.mp3"
    return {"audio_url": audio_url}