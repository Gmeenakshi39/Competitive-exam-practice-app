# Competitive Exam Practice App

A starter web app for SSC, RRB NTPC and state government competitive-exam practice.

## Features in this MVP
- React + Vite frontend
- FastAPI backend
- Randomized quantitative aptitude and reasoning questions
- Beginner, Medium and Advanced difficulty levels
- Topic filters and adjustable question count
- Multiple-choice answers, scoring and explanations
- In-memory question management and practice-result history APIs
- Compact two-column print layout; use browser Print → Save as PDF
- Backend answer validation and tests for generated question integrity

## Requirements
- Python 3.10+
- Node.js 18+

## Run the backend
```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
API docs: http://127.0.0.1:8000/docs

## Run the frontend (second terminal)
```bash
cd frontend
npm install
npm run dev
```
Open the URL printed by Vite (usually http://localhost:5173).

## Run backend tests
From the `backend` folder:
```bash
python -m pytest
```

## Backend API
- `GET /api/health` and `GET /api/topics`
- `POST /api/generate` to generate a validated question set
- `POST /api/grade` with a server-issued `setId` and selected answers to grade a set and record the attempt
- `GET /api/history?limit=20` to list recent attempts (limit: 1–100)
- `GET`, `POST`, `PUT`, and `DELETE /api/admin/questions` to manage a separate question bank

Question management, generated question sets, and practice history are stored in process memory. They are cleared when the backend restarts, and admin-managed questions are not included in `/api/generate`. Grading uses server-issued question sets rather than trusting question answers submitted by the browser. The admin endpoints have no authentication by design for this local-only MVP. Run Uvicorn on its default `127.0.0.1` interface; do not expose this backend to a network or deploy it publicly without adding authentication and persistent storage.

## Important scope notes
This is a functional starter, not a complete exam question bank. Generated questions come from validated templates; the admin-managed question bank is separate. Advanced seating-arrangement puzzles and full-length exam simulations are planned for later phases. Before production use, expand the templates, verify syllabus coverage against current official notifications, add accessibility and security review, and use persistent storage for managed questions and practice history.

## PDF printing
Use **Print worksheet** in the app and select **Save as PDF** in the browser print dialog. The print stylesheet hides navigation and controls, uses compact typography and two columns, and keeps each question together where possible.
