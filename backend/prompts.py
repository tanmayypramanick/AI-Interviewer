import random
import re
from openai import OpenAI
from dotenv import load_dotenv
import os
from memory import (
    get_job_desc_index, get_phase, get_resume_index, get_short_answers_count,
    log_message, get_history, get_asked_topics, get_current_project,
    get_resume_text, get_job_desc_text, should_continue_interview, set_phase
)
from utils import search_similar, extract_keywords
from sentence_transformers import SentenceTransformer
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# Initialize DeepSeek client
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

# Initialize SentenceTransformer model
MODEL = SentenceTransformer('all-MiniLM-L6-v2')

# Random female recruiter names
RECRUITER_NAME = random.choice([
    "Emma", "Zoe", "Ava", "Sophia", "Mia", "Luna", "Olivia", "Isabella", "Charlotte", "Amelia"
])

def clean_response(text: str, is_greeting: bool = False, is_first_response: bool = False, is_feedback: bool = False) -> str:
    logger.debug(f"Raw response: {text}")
    text = text.strip()
    # Remove AI-related and robotic phrases
    text = re.sub(r"(?i)^.*\bI['’]?m an AI\b.*", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\[.*?\]", "", text)
    text = re.sub(r"(?i)(here is the output|output:|here's (my|the) (attempt|response|start)|note:).*?(?=\w|$)", "", text)
    text = re.sub(r"(?i)\(.*?(recruiter|interview|response|phase).*?\)", "", text)
    # Remove overly casual or exaggerated phrases
    text = re.sub(r"(?i)(haha|lol|like a champ|rock star|super|mega|ultra|wizardry|magic|just-works)", "", text)
    text = re.sub(r"^[^\w\s]+", "", text)
    # Remove generic fluff
    text = re.sub(r"(?i)(great question|let['’]?s get started|excited to (chat|be here)|i['’]?m (with you|excited|here).*?(today|interview)|hello)", "", text)
    text = re.sub(r"(?i)(wow|that['’]?s|this is|I['’]?m) (really |so |quite )?(amazing|impressive|fascinating|interesting|great)[^!.]*[!.]", "", text)
    text = re.sub(r"(?i)let['’]?s (dive into|jump into|explore|unpack|that |the )?", "", text)
    
    # Ensure question mark for follow-ups, but not for feedback or answers
    if not is_greeting and not is_first_response and not is_feedback and not text.endswith("?"):
        text = f"{text}?"
    
    # Limit to 1 sentence and 25 words for questions
    if not is_greeting and not is_first_response and not is_feedback:
        sentences = re.split(r'(?<=[.!?])\s+', text)
        words = text.split()
        if len(words) > 25:
            text = " ".join(words[:25]) + ( "?" if "?" not in text else "")
        if len(sentences) > 1:
            question_indices = [i for i, s in enumerate(sentences) if "?" in s]
            if question_indices:
                text = sentences[question_indices[0]]
            else:
                text = sentences[0]
    
    return re.sub(r'\s+', ' ', text).strip()

def run_deepseek_prompt(user_prompt: str, is_greeting: bool = False, is_first_response: bool = False, is_feedback: bool = False) -> str:
    system_prompt = f"""
You are {RECRUITER_NAME}, a friendly female recruiter conducting a Zoom job interview.
- Use a warm, professional, conversational tone, like chatting with a colleague (e.g., "That’s interesting!", "Nice work!").
- Avoid technical jargon unless required by the phase; prioritize natural, engaging flow.
- Ask one clear, specific question (1 sentence, max 25 words) based on candidate’s answers, resume, or job description.
- Match the phase: greeting (welcome), project (experience), technical (skills), problem-solving (challenges), coding (verbal code), behavioral (teamwork), role-fit (motivation), closing (wrap-up).
- If they ask about you, reply briefly (e.g., "Doing great, thanks!") then ask a relevant question.
- Personalize using resume/job details (e.g., Python, Hexaware projects).
- Avoid slang (e.g., "yo", "stoked"), fluff (e.g., "super impressive"), or robotic phrases.
- Never mention AI, phases, or disclaimers.
- For feedback, provide detailed, constructive comments tied to the conversation (max 150 words).
- Questions end with a question mark unless feedback.
"""
    try:
        stream = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=250 if is_feedback else 150,
            stream=True
        )
        full_response = ""
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                full_response += chunk.choices[0].delta.content
        logger.debug(f"Raw response full model output: {full_response}")
        return clean_response(full_response, is_greeting, is_first_response, is_feedback)
    except Exception as e:
        logger.error(f"Deepseek API failed: {str(e)}")
        return "Sorry, something went wrong—let’s try another question!" if not is_feedback else "Unable to generate feedback."

def generate_greeting(user_name: str) -> str:
    logger.debug(f"Generating greeting for user: {user_name}")
    prompt = f"""
As {RECRUITER_NAME}, greet candidate {user_name} for a Zoom interview.
- Start with "Hi {user_name}" for a personal touch.
- Keep it warm, concise, natural (e.g., "Hi {user_name}, nice to meet you! How’s your day going?").
- One sentence, max 25 words.
"""
    response = run_deepseek_prompt(prompt, is_greeting=True)
    if not re.search(rf"\b{user_name}\b", response, re.IGNORECASE):
        logger.warning(f"User name '{user_name}' not in greeting: {response}")
        response = f"Hi {user_name}, {response.lstrip('Hi ,')}"
    return response

def generate_first_response_after_greeting(session_id: str, user_response: str) -> str:
    user_response_clean = user_response.strip().lower()
    asked_how = bool(re.search(r'\bhow\s+(are\s+you|you\s+doing|about\s+you)\b\??', user_response_clean))
    logger.debug(f"Asked how: {asked_how}, User response: {user_response}")

    resume_text = get_resume_text(session_id)
    r_idx, r_chunks = get_resume_index(session_id)
    resume_keywords = extract_keywords(resume_text)[:5]
    resume_ctx = [r["text"] for r in search_similar(", ".join(resume_keywords), r_idx, r_chunks, MODEL)] if r_idx else []
    context_str = "\n".join(resume_ctx)
    logger.debug(f"Resume context for first response: {context_str}")

    prompt = f"""
As {RECRUITER_NAME}, reply to candidate’s greeting: "{user_response}".
- Use a warm, conversational tone (e.g., "Glad you're doing well!").
- If they asked about you, respond briefly (e.g., "I'm good, thanks!").
- Ask about a specific project or skill from resume (e.g., Python, Hexaware).
- Resume context: {context_str}
- One sentence, max 25 words, ending with a question mark.
"""
    return run_deepseek_prompt(prompt, is_first_response=True)

def generate_followup_question(session_id: str, history: list) -> str:
    phase = get_phase(session_id)
    short_ct = get_short_answers_count(session_id)
    
    if short_ct >= 2:
        prompt = f"""
As {RECRUITER_NAME}, notice candidate’s short answers.
- Ask an open-ended question to encourage detail (e.g., "What’s a project you’re proud of?").
- Keep it warm, conversational.
- One sentence, max 25 words.
"""
        return run_deepseek_prompt(prompt)

    r_idx, r_chunks = get_resume_index(session_id)
    j_idx, j_chunks = get_job_desc_index(session_id)
    recent = "\n".join(f"{m['role'].capitalize()}: {m['content']}" for m in history[-2:])
    asked_topics = get_asked_topics(session_id)
    current_project = get_current_project(session_id)
    resume_text = get_resume_text(session_id)
    job_desc_text = get_job_desc_text(session_id)

    latest_answer = history[-1]["content"] if history and history[-1]["role"] == "user" else ""
    answer_keywords = extract_keywords(latest_answer)
    
    resume_keywords = answer_keywords[:3] + extract_keywords(resume_text)[:3] + extract_keywords(job_desc_text)[:2]
    resume_keywords = list(dict.fromkeys(resume_keywords))[:8]
    resume_ctx = [r["text"] for r in search_similar(", ".join(resume_keywords), r_idx, r_chunks, MODEL)] if r_idx else []
    jd_ctx = [r["text"] for r in search_similar(", ".join(resume_keywords), j_idx, j_chunks, MODEL)] if j_idx else []

    logger.debug(f"Resume context: {resume_ctx}")
    logger.debug(f"Job description context: {jd_ctx}")

    focus_options = {
        "project": "Ask about a specific project or role from resume (e.g., What did you do at Hexaware?).",
        "project_2": "Ask about a different project or experience from resume.",
        "technical": "Ask about a technical skill (e.g., How did you use Python?).",
        "technical_2": "Ask about applying a skill in a scenario (e.g., Optimizing a query?).",
        "problem-solving": "Ask about a challenge they overcame (e.g., Solving a tough bug?).",
        "coding": "Ask a verbal coding question (e.g., Design a function for...).",
        "behavioral": "Ask about teamwork or collaboration (e.g., Working with a team?).",
        "behavioral_2": "Ask about leadership or initiative (e.g., Leading a project?).",
        "role-fit": "Ask about motivation for the role (e.g., Why this job?).",
        "closing": "Thank them and ask if they have questions about the role."
    }
    focus = focus_options.get(phase, "Ask about a detail from their answer or resume.")

    # Avoid repeating topics
    if recent.split("\n")[-1].startswith("Ai:"):
        last_question = recent.split("\n")[-1].replace("Ai: ", "").strip()
        if last_question in asked_topics:
            logger.warning(f"Repeated question detected: {last_question}")
            focus = f"Ask about a new topic from resume or job description, avoiding {', '.join(asked_topics)}."

    context_str = "\n".join(resume_ctx + jd_ctx)
    logger.debug(f"Session: {session_id}, Phase: {phase}, Recent: {recent}, Keywords: {answer_keywords}")

    prompt = f"""
As {RECRUITER_NAME}, ask a follow-up question in a Zoom interview.
Latest exchange:
{recent}

Resume/job context:
{context_str}

Topics discussed:
{', '.join(asked_topics)}

Current project:
{current_project or 'None'}

Ask one question (1 sentence, max 25 words):
- Focus: {focus}
- Use details from answer (e.g., {', '.join(answer_keywords) or 'none'}), resume, or job description.
- Sound warm, conversational (e.g., "That’s interesting! How...").
- Avoid repeats, slang, fluff.
- End with a question mark.
"""
    response = run_deepseek_prompt(prompt)
    return response

def generate_end_of_interview_question() -> str:
    prompt = f"""
As {RECRUITER_NAME}, wrap up the Zoom interview.
- Thank the candidate warmly and ask if they have questions about the role or team.
- Example: "Thanks for chatting! Any questions about the role?"
- One sentence, max 25 words.
"""
    return run_deepseek_prompt(prompt)

def generate_answer_to_candidate(candidate_question: str, history: list, session_id: str) -> str:
    convo = "\n".join(f"{m['role'].capitalize()}: {m['content']}" for m in history[-4:])
    job_desc_text = get_job_desc_text(session_id)
    prompt = f"""
As {RECRUITER_NAME}, answer candidate’s question: "{candidate_question}".
Recent convo:
{convo}
Job description:
{job_desc_text}

Reply in 1-2 sentences, max 40 words:
- Use a warm, conversational tone, like answering a colleague.
- Tie to the role, team, or job description if relevant (e.g., "We use agile sprints...").
- End with: "Any other questions?"
"""
    response = run_deepseek_prompt(prompt)
    if not response.endswith("Any other questions?"):
        response += " Any other questions?"
    set_phase(session_id, "closing")
    return response

def generate_feedback(history: list) -> str:
    convo = "\n".join(f"{m['role'].capitalize()}: {m['content']}" for m in history)
    prompt = f"""
As {RECRUITER_NAME}, provide detailed feedback after a Zoom interview.
Conversation:
{convo}

- Summarize performance across: project (experience), technical (skills), problem-solving (challenges), coding (code explanation), behavioral (teamwork), role-fit (motivation).
- Highlight 2-3 strengths with specific examples (e.g., "Your Python script explanation was clear").
- Suggest 1-2 improvements with actionable tips (e.g., "Add specific teamwork examples").
- Provide a score (1-10) based on clarity, relevance, engagement.
- Use a warm, constructive tone, like a friendly email.
- Max 150 words.
"""
    return run_deepseek_prompt(prompt, is_feedback=True)