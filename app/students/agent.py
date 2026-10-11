"""Student assistant agent: the model picks database tools, we run them, it answers from the results."""
import json
from datetime import date
from typing import List

from app.config import settings
from app.llm import client
from app.students.queries import data_range, student_card
from app.students.tools import TOOLS, run_tool

MAX_STEPS = 6  # tool-calling rounds before we stop
MAX_CARDS = 5  # student cards returned to the app per answer

SYSTEM_PROMPT = """You are the Student Info assistant for K.S.R. College of Engineering.
You answer questions about students using ONLY the database tools provided. Never guess or invent data.

Database facts:
- Departments: CSE, ECE, EEE, IT, MECH. Years 1-4, sections A and B, 30 students per section.
- Academic year 2026-27, odd semester: year 1 = semester 1, year 2 = sem 3, year 3 = sem 5, year 4 = sem 7.
- Roll number format: 24CS015 = joined 2024, CSE, number 015. Student ID format: STU10615.
- Attendance is recorded daily for the current semester ({attendance_from} to {attendance_to}).
  OD (on duty) counts as present. Below 75% is attendance shortage.
- Marks: internal /40 + external /60 = total /100. Grades O, A+, A, B+, B, C; U = fail (an arrear).
  First-year students have no marks yet. A subject taught in semester N was taken by students who are now
  in later years (e.g. semester 3 subjects were taken by today's 3rd and 4th years).
Today is {today}.

How to work:
1. Pick the most specific tool for the question. Call several tools if needed (e.g. a class list, then details).
   Filters are optional: to cover all departments, years or sections, leave that filter out and make ONE call
   instead of repeating the same tool for each value.
2. If a tool returns an error (e.g. student not found), tell the user plainly.
3. Your answer is shown in a small mobile chat bubble: write plain text, short sentences, "•" bullets for
   lists (one student per line, e.g. "• 25EC047 Saravanan M - 57.75%"). No Markdown tables, headings or **bold**.
4. When you look up a single student, the app also shows a card with their name, roll number, department,
   year, attendance %, CGPA, pending arrears and email - don't repeat those. For a general "details of" request,
   write one short intro sentence and add the useful details NOT on the card (section, batch, residence, city,
   phone, parent name and phone, blood group, admission type). Otherwise just answer the actual question.
5. Mention totals when a list is cut off (total_matching vs returned)."""


def _system_prompt() -> str:
    return SYSTEM_PROMPT.format(today=date.today().isoformat(), **data_range())


def run_agent(question: str, history: List[dict] = ()) -> dict:
    messages = [{"role": "system", "content": _system_prompt()}, *history, {"role": "user", "content": question}]
    steps = []
    student_ids: List[str] = []  # students looked up individually, for the app's cards
    for _ in range(MAX_STEPS):
        response = client.chat.completions.create(
            model=settings.agent_model,
            max_tokens=settings.llm_max_tokens,
            messages=messages,
            tools=TOOLS,
        )
        message = response.choices[0].message
        if not message.tool_calls:
            cards = [student_card(sid) for sid in student_ids[:MAX_CARDS]]
            return {"answer": message.content, "steps": steps, "students": cards}

        messages.append({
            "role": "assistant",
            "content": message.content,
            "tool_calls": [
                {"id": c.id, "type": "function", "function": {"name": c.function.name, "arguments": c.function.arguments}}
                for c in message.tool_calls
            ],
        })
        for call in message.tool_calls:
            try:
                args = json.loads(call.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            result = run_tool(call.function.name, args)
            steps.append({"tool": call.function.name, "arguments": args, "error": result.get("error")})
            sid = _single_student(result)
            if sid and sid not in student_ids:
                student_ids.append(sid)
            messages.append({"role": "tool", "tool_call_id": call.id, "content": json.dumps(result, default=str)})

    return {
        "answer": "Sorry, I couldn't finish answering that within the step limit. Please ask more specifically.",
        "steps": steps,
        "students": [],
    }


def _single_student(result: dict):
    """The student ID if this tool result is about exactly one student."""
    if "student_id" in result:  # get_attendance / get_marks / get_arrears
        return result["student_id"]
    if "student" in result:  # find_student by roll number / ID
        return result["student"]["student_id"]
    if result.get("matches") == 1:  # find_student by name, one match
        return result["students"][0]["student_id"]
    return None
