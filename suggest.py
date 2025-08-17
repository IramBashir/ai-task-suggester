import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta, date
from typing import Optional, List
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
import json

load_dotenv()
router = APIRouter()

HF_API_TOKEN = os.getenv("HF_API_TOKEN")
HF_MODEL = "google/gemma-2-2b-it"

if not HF_API_TOKEN:
    raise RuntimeError("Missing HF_API_TOKEN in environment variables")

client = InferenceClient(api_key=HF_API_TOKEN)

class SuggestRequest(BaseModel):
    task: str
    deadline_pref: Optional[str] = None
    extra_info: Optional[str] = None
    goal: Optional[str] = "default"  # e.g., "efficiency", "learning", "detailed"
    max_tokens: Optional[int] = 400
    temperature: Optional[float] = 0.5

class SuggestResponse(BaseModel):
    main_task: str
    category: str
    suggested_deadline: str
    subtasks: List[str]

def build_system_prompt(goal: str) -> str:
    base_prompt = (
        "You are a productivity assistant that helps users manage tasks efficiently.\n"
        "Your job:\n"
        "1. Break down the main task into smaller subtasks.\n"
        "2. Suggest a realistic deadline.\n"
        "3. Assign a category (Work, Personal, Shopping, Study, Miscellaneous).\n"
        "4. Return ONLY valid JSON in this format:\n"
        "{\n"
        '  "main_task": "string",\n'
        '  "category": "string",\n'
        '  "suggested_deadline": "YYYY-MM-DD",\n'
        '  "subtasks": ["string", "string", ...]\n'
        "}"
    )
    if goal == "efficiency":
        base_prompt += "\nFocus on the fastest way to complete the task with minimal steps."
    elif goal == "learning":
        base_prompt += "\nFocus on learning outcomes, detailed explanations in subtasks."
    elif goal == "detailed":
        base_prompt += "\nBreak subtasks into the smallest actionable steps."
    return base_prompt

@router.post("/suggest", response_model=SuggestResponse)
async def suggest(req: SuggestRequest):
    system_prompt = build_system_prompt(req.goal)

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": f"Task: {req.task}\nDeadline preference: {req.deadline_pref or 'none'}\nExtra info: {req.extra_info or 'none'}"
        }
    ]

    try:
        completion = client.chat.completions.create(
            model=HF_MODEL,
            messages=messages,
            max_tokens=req.max_tokens,
            temperature=req.temperature
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"HF API error: {str(e)}")

    try:
        generated_text = completion.choices[0].message["content"]
        json_start = generated_text.find("{")
        json_end = generated_text.rfind("}") + 1
        result = json.loads(generated_text[json_start:json_end])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse HF output: {str(e)}")

    # Clamp suggested_deadline within 30 days
    try:
        suggested = result.get("suggested_deadline")
        if suggested:
            sd = datetime.fromisoformat(suggested).date()
            max_date = date.today() + timedelta(days=30)
            if sd > max_date:
                result["suggested_deadline"] = max_date.isoformat()
    except Exception:
        pass

    return result
