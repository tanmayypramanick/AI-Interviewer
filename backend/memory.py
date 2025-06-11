import uuid
from typing import Dict, List, Optional, Tuple
from utils import extract_keywords, search_similar
from sentence_transformers import SentenceTransformer
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

_sessions: Dict[str, dict] = {}

# Defined phase order to align with prompts.py
PHASE_ORDER = [
    "greeting", "project", "project_2", "technical", "technical_2",
    "problem-solving", "coding", "behavioral", "behavioral_2", "role-fit", "closing"
]

def create_session(
    session_id: str,
    user_name: str,
    resume_chunks: List[str],
    resume_index,
    resume_text: str,
    job_desc_chunks: List[str],
    job_desc_index,
    job_desc_text: str
) -> None:
    """
    Create a new interview session.
    """
    _sessions[session_id] = {
        "user_name": user_name,
        "history": [],
        "phase": "greeting",
        "resume_chunks": resume_chunks,
        "resume_index": resume_index,
        "resume_text": resume_text,
        "job_desc_chunks": job_desc_chunks,
        "job_desc_index": job_desc_index,
        "job_desc_text": job_desc_text,
        "is_active": True,
        "awaiting_candidate_question": False,
        "model": SentenceTransformer('all-MiniLM-L6-v2') if resume_chunks else None,
        "short_answers_count": 0,
        "asked_topics": [],
        "current_project": None,
        "used_acks": [],
        "tracked_context": [],
        "used_transitions": []
    }
    logger.debug(f"Created session: {session_id}")

def get_phase(session_id: str) -> str:
    """
    Get the current phase of the session.
    """
    phase = _sessions.get(session_id, {}).get("phase", "greeting")
    logger.debug(f"Retrieved phase: {phase} for session: {session_id}")
    return phase

def set_phase(session_id: str, phase: str) -> None:
    """
    Set the phase of the session, validating against PHASE_ORDER.
    """
    if session_id in _sessions:
        if phase in PHASE_ORDER or phase == "greeting":
            _sessions[session_id]["phase"] = phase
            logger.debug(f"Set phase: {phase} for session: {session_id}")
        else:
            logger.error(f"Invalid phase: {phase}")
            raise ValueError(f"Phase {phase} not in {PHASE_ORDER}")

def log_message(session_id: str, role: str, content: str) -> None:
    """
    Log a message in the session history and track AI questions in asked_topics.
    """
    if session_id not in _sessions:
        logger.error(f"Session {session_id} not found")
        return
    
    session = _sessions[session_id]
    keywords = extract_keywords(content)
    message = {"role": role, "content": content, "keywords": keywords}
    
    # Add context from resume and job description (limited to 3 results for speed)
    resume_results = search_similar(content, session.get("resume_index"), session.get("resume_chunks"), session.get("model"))[:3] if session.get("resume_index") else []
    job_desc_results = search_similar(content, session.get("job_desc_index"), session.get("job_desc_chunks"), session.get("model"))[:3] if session.get("job_desc_index") else []
    
    message["context"] = {
        "resume": resume_results,
        "job_description": job_desc_results
    }
    
    session["history"].append(message)
    
    # Track short answers
    if role == "user" and len(content.split()) < 10:
        session["short_answers_count"] = session.get("short_answers_count", 0) + 1
    
    # Track AI questions in asked_topics to prevent repeats
    if role == "ai" and content.endswith("?"):
        if content not in session["asked_topics"]:
            session["asked_topics"].append(content)
            logger.debug(f"Added to asked_topics: {content[:50]}...")
    
    logger.debug(f"Logged {role}: {content[:50]}...")

def get_history(session_id: str) -> List[dict]:
    """
    Get the session history.
    """
    history = _sessions.get(session_id, {}).get("history", [])
    logger.debug(f"Retrieved history length: {len(history)} for session: {session_id}")
    return history

def should_continue_interview(session_id: str, history: List[dict]) -> bool:
    """
    Determine if the interview should continue based on phase and questions.
    """
    if session_id not in _sessions:
        logger.error(f"Session {session_id} not found")
        return False
    
    phase = get_phase(session_id)
    question_count = len([m for m in history if m["role"] == "ai" and m["content"].endswith("?")])
    awaiting_question = is_candidate_questioning(session_id)
    
    # Continue if not in closing, or in closing with candidate questions
    result = (phase != "closing" or awaiting_question) and question_count < 12  # Allow extra for Q&A
    logger.debug(f"Should continue: {result}, phase: {phase}, questions: {question_count}, awaiting: {awaiting_question}")
    return result

def mark_interview_over(session_id: str) -> None:
    """
    Mark the interview as over.
    """
    if session_id in _sessions:
        _sessions[session_id]["is_active"] = False
        _sessions[session_id]["awaiting_candidate_question"] = False
        logger.debug(f"Marked interview over: {session_id}")

def mark_awaiting_candidate_question(session_id: str, done: bool = False) -> None:
    """
    Mark the session as awaiting candidate questions.
    """
    if session_id in _sessions:
        _sessions[session_id]["awaiting_candidate_question"] = not done
        logger.debug(f"Awaiting candidate question: {not done} for session: {session_id}")

def is_candidate_questioning(session_id: str) -> bool:
    """
    Check if the session is in candidate questioning phase.
    """
    status = _sessions.get(session_id, {}).get("awaiting_candidate_question", False)
    logger.debug(f"Candidate questioning: {status} for session: {session_id}")
    return status

def get_all_session_ids() -> List[str]:
    """
    Get all active session IDs.
    """
    return list(_sessions.keys())

def clear_session(session_id: str) -> None:
    """
    Clear a session.
    """
    if session_id in _sessions:
        del _sessions[session_id]
        logger.debug(f"Cleared session: {session_id}")

def get_resume_index(session_id: str) -> Tuple[Optional[object], List[str]]:
    """
    Get the resume index and chunks for the session.
    """
    session = _sessions.get(session_id, {})
    return session.get("resume_index"), session.get("resume_chunks", [])

def get_job_desc_index(session_id: str) -> Tuple[Optional[object], List[str]]:
    """
    Get the job description index and chunks for the session.
    """
    session = _sessions.get(session_id, {})
    return session.get("job_desc_index"), session.get("job_desc_chunks", [])

def get_short_answers_count(session_id: str) -> int:
    """
    Get the count of short answers in the session.
    """
    return _sessions.get(session_id, {}).get("short_answers_count", 0)

def get_asked_topics(session_id: str) -> List[str]:
    """
    Get the list of topics discussed in the session.
    """
    return _sessions.get(session_id, {}).get("asked_topics", [])

def get_current_project(session_id: str) -> Optional[str]:
    """
    Get the current project being discussed.
    """
    return _sessions.get(session_id, {}).get("current_project", None)

def get_used_acks(session_id: str) -> List[str]:
    """
    Get the list of used acknowledgments.
    """
    return _sessions.get(session_id, {}).get("used_acks", [])

def add_tracked_context(session_id: str, topic: str) -> None:
    """
    Add a topic to the tracked context.
    """
    if session_id in _sessions:
        topics = _sessions[session_id].get("tracked_context", [])
        if topic not in topics:
            topics.append(topic)
            _sessions[session_id]["tracked_context"] = topics
            logger.debug(f"Added tracked context: {topic}")

def track_used_transition(session_id: str, transition: str) -> None:
    """
    Track a used transition.
    """
    if session_id in _sessions:
        transitions = _sessions[session_id].get("used_transitions", [])
        if transition not in transitions:
            transitions.append(transition)
            _sessions[session_id]["used_transitions"] = transitions
            logger.debug(f"Tracked transition: {transition}")

def get_tracked_context(session_id: str) -> List[str]:
    """
    Get the tracked context topics.
    """
    return _sessions.get(session_id, {}).get("tracked_context", [])

def get_resume_text(session_id: str) -> str:
    """
    Get the resume text for the session.
    """
    return _sessions.get(session_id, {}).get("resume_text", "")

def get_job_desc_text(session_id: str) -> str:
    """
    Get the job description text for the session.
    """
    return _sessions.get(session_id, {}).get("job_desc_text", "")