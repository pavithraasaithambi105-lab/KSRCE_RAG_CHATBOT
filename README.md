# RAG Chatbot (FastAPI + Expo)

A college assistant with two tabs:
- **Assistant** — answers questions from the K.S.R.C.E. Handbook PDF using RAG (`/chat`).
- **Student Info** — an AI agent that looks up students, attendance, marks and arrears in a SQLite
  database (`/students/assistant`).

## Quick start

What's included: `app/` (FastAPI backend), `mobile/` (Expo React Native app), `data/` (ready-made
handbook index and student database, so nothing has to be rebuilt).

1. **Backend** (Python 3.9+):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate          # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env               # then put your own OpenRouter key in LLM_API_KEY
   uvicorn app.main:app --reload --host 0.0.0.0
   ```
   Get a key at https://openrouter.ai/keys. Open http://127.0.0.1:8000/docs to try the API.
2. **Mobile app** (Node 20+):
   ```bash
   cd mobile
   npm install
   ```
   Edit `mobile/constants/config.ts` and set `API_URL` to your computer's IP address
   (e.g. `http://192.168.1.10:8000`; find it with `ipconfig` on Windows or `ipconfig getifaddr en0` on Mac),
   then run `npx expo start` and open it in Expo Go on a phone on the same Wi-Fi (or press `w` for web).
3. To rebuild the data yourself: `python -m app.ingest app/pdf_data/Handbook.pdf` (handbook index,
   uses a few cents of OpenRouter credit) and `python -m app.seed` (student database, free).

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Run

```bash
uvicorn app.main:app --reload
```

- API docs: http://127.0.0.1:8000/docs
- Health: `GET /health`
- Upload & index a PDF: `POST /documents` (multipart field `file`)
- List indexed PDFs: `GET /documents`
- Remove a PDF: `DELETE /documents/{name}`
- Chat: `POST /chat` with `{"question": "..."}` → `{"answer": "...", "sources": [...]}`

Or index from the command line: `python -m app.ingest app/pdf_data/Handbook.pdf`

## How the RAG pipeline works (`app/rag/`)

```
PDF ─► loader.py   headings, text, tables (Markdown), figures — in reading order
    ─► figures.py  diagrams → text (curated .figures.md first, then a vision model)
    ─► chunker.py  section-aware chunks with overlap; tables and figures kept whole
    ─► embedder.py OpenRouter embeddings
    ─► store.py    data/index/ + hybrid search (embeddings + BM25 keywords)
question ─► retrieve top-k ─► llm.py (gpt-4o answers from the chunks, cites pages)
```

- **Text**: chunked per section (`CHUNK_SIZE` characters, `CHUNK_OVERLAP` overlap), ending on
  paragraph/sentence boundaries. Every chunk starts with its section path, e.g.
  `Section: 9. ADMINISTRATIVE SET UP > 9.1 Chairman`. Running headers/footers are removed.
- **Tables**: detected with PyMuPDF and stored as Markdown with their title. Tables that continue
  onto the next page are joined to the previous header; big tables are split by rows with the
  header repeated.
- **Figures** (org charts, flowcharts): a chunker can't read pictures, so each figure becomes a
  text description. Hand-checked descriptions live in `app/pdf_data/<pdf name>.figures.md`
  (`## Page <n> | <title>` sections) and always win. Figures without one are described by
  `VISION_MODEL` (cached in `data/index/figure_cache.json`); set it to `""` to turn this off.
- **Search**: embeddings find chunks with similar meaning, BM25 finds exact words ("HOD-CSE",
  "CGPA"); the two rankings are merged and the best `TOP_K` chunks go to the LLM.

After editing a `.figures.md` file or any chunking setting, re-run the ingest command.

## Student database (dummy data for the agent)

```bash
python -m app.seed   # (re)creates data/college.db — same data every run
```

SQLite file `data/college.db`, generated with Faker. Academic year 2026-27, odd semester
(1st years in sem 1, 2nd in sem 3, 3rd in sem 5, 4th in sem 7); 5 departments (CSE, ECE, EEE,
IT, MECH) × 4 years × 2 sections × 30 students.

| Table | Rows | Contents |
|---|---|---|
| `students` | 1,200 | `student_id` (STU10001), `roll_number` (24CS015 = batch 2024, CSE, no. 15), name, department, year, section, batch, contact, parent, address, blood group, admission type, Hosteller/Day Scholar, CGPA |
| `subjects` | 137 | subject code, name, department (`ALL` = common 1st-year), semester, credits |
| `attendance` | 75,300 | one row per student per working day this semester: Present / Absent / OD |
| `marks` | 19,800 | every completed semester: internal (/40), external (/60), total, grade (O … C, U = fail), PASS/FAIL |
| `arrears` | 2,093 | failed subjects: attempts, Pending / Cleared, session cleared |
| `attendance_summary` (view) | — | per-student working days, present, absent, OD and attendance % |

Open it with `sqlite3 data/college.db` or any SQLite viewer.

## Student endpoints (separate from the handbook `/chat`)

**Student Info tab** — direct database lookups, no AI:

| Endpoint | Returns |
|---|---|
| `GET /students/{roll_or_id}` | full profile, e.g. `/students/24CS015` or `/students/STU10615` |
| `GET /students?department=CSE&year=3&section=A` | class list (`sort_by=cgpa&descending=true` for toppers) |
| `GET /students/search?name=Hema` | students whose name matches |
| `GET /students/{roll_or_id}/attendance` | working days, present, absent, OD, %, shortage, absent dates |
| `GET /students/{roll_or_id}/marks?semester=3` | marks per subject + semester summary + CGPA |
| `GET /students/{roll_or_id}/arrears` | pending and cleared arrears |

**Assistant tab** — `POST /students/assistant` with
`{"question": "...", "history": [{"role": "user"|"assistant", "content": "..."}]}` →
`{"answer": "...", "steps": [{"tool": "...", "arguments": {...}}]}`.

The agent (`app/students/agent.py`, model `AGENT_MODEL`) gets the question plus a list of tools
(`app/students/tools.py`). It chooses a tool and its arguments, we run that fixed SQL query
(`app/students/queries.py`), and it answers from the returned rows, calling more tools if needed.
It never writes SQL itself. `steps` shows which tools it chose. Tools: `find_student`,
`list_students`, `get_attendance`, `attendance_report`, `attendance_on_date`, `get_marks`,
`get_arrears`, `arrears_report`, `subject_performance`, `list_subjects`, `class_summary`.
