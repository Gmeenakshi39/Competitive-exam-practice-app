from __future__ import annotations

import random
from datetime import datetime, timezone
from threading import RLock
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, model_validator

app = FastAPI(title="Competitive Exam Practice API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SUBJECTS = {
    "Quantitative Aptitude": [
        "Percentages", "Averages", "Ratio and Proportion", "Profit and Loss",
        "Simple Interest", "Number Series"
    ],
    "Reasoning": [
        "Number Series", "Coding-Decoding", "Analogy", "Blood Relations"
    ],
}
LEVELS = ["Beginner", "Intermediate", "Advanced"]
managed_questions: dict[str, "Question"] = {}
practice_history: list["PracticeHistoryItem"] = []
generated_question_sets: dict[str, list["Question"]] = {}
storage_lock = RLock()


class GenerateRequest(BaseModel):
    subject: str
    level: str
    topic: str = "All topics"
    count: int = Field(default=10, ge=1, le=100)
    seed: int | None = None


class Question(BaseModel):
    id: str
    subject: str
    topic: str
    level: str
    prompt: str
    options: list[str]
    answer: str
    explanation: str


class GenerateResponse(BaseModel):
    setId: str
    questions: list[Question]
    count: int
    seed: int


class ManagedQuestionInput(BaseModel):
    subject: str
    topic: str
    level: str
    prompt: str = Field(min_length=1, max_length=1000)
    options: list[str] = Field(min_length=4, max_length=4)
    answer: str = Field(min_length=1, max_length=500)
    explanation: str = Field(min_length=1, max_length=2000)

    @model_validator(mode="after")
    def validate_question(self):
        if self.subject not in SUBJECTS:
            raise ValueError("Unsupported subject.")
        if self.level not in LEVELS:
            raise ValueError("Unsupported difficulty level.")
        if self.topic not in SUBJECTS[self.subject]:
            raise ValueError("Topic does not belong to the selected subject.")
        if len(set(self.options)) != len(self.options):
            raise ValueError("Options must be unique.")
        if self.answer not in self.options:
            raise ValueError("The answer must match one of the options.")
        return self


class QuestionResult(BaseModel):
    questionId: str
    selected: str | None
    correctAnswer: str
    isCorrect: bool
    explanation: str


class GradeRequest(BaseModel):
    setId: str
    answers: dict[str, str]


class GradeResponse(BaseModel):
    attemptId: str
    createdAt: str
    correct: int
    total: int
    percentage: float
    results: list[QuestionResult]


class PracticeHistoryItem(BaseModel):
    attemptId: str
    createdAt: str
    subject: str | None
    level: str | None
    correct: int
    total: int
    percentage: float


def _mcq(rng: random.Random, correct: int, explanation: str, distractors=None):
    """Create four unique answer choices, including the known correct answer."""
    if distractors is None:
        candidates = set()
        offsets = [1, -1, 2, -2, 5, -5, 10, -10, 3, -3, 20, -20]
        rng.shuffle(offsets)
        for off in offsets:
            if correct + off >= 0 and correct + off != correct:
                candidates.add(correct + off)
            if len(candidates) >= 3:
                break
        while len(candidates) < 3:
            candidate = correct + rng.randint(1, 25)
            if candidate != correct:
                candidates.add(candidate)
        distractors = list(candidates)[:3]
    unique = []
    for item in distractors:
        text = str(item)
        if text != str(correct) and text not in unique:
            unique.append(text)
    candidate = 1
    while len(unique) < 3:
        text = str(correct + candidate if correct != 0 else candidate)
        if text != str(correct) and text not in unique:
            unique.append(text)
        candidate += 1
    choices = [str(correct)] + unique[:3]
    rng.shuffle(choices)
    return choices, str(correct)


def _format_num(n: int | float) -> str:
    if isinstance(n, float) and n.is_integer():
        n = int(n)
    return f"{n:,}" if isinstance(n, int) else str(n)


def _quant_question(rng: random.Random, topic: str, level: str):
    if topic == "Percentages":
        pct = rng.choice([5, 10, 12, 15, 20, 25, 30, 40, 50]) if level == "Beginner" else rng.choice([12, 16, 18, 22, 27, 35, 45, 60])
        base = rng.choice([120, 160, 200, 240, 300, 360, 400, 500]) if level == "Beginner" else rng.choice([180, 250, 320, 450, 560, 720, 840, 960])
        answer = base * pct / 100
        answer = int(answer) if answer.is_integer() else round(answer, 2)
        choices, correct = _mcq(rng, answer, f"{pct}% of {base} = {base} × {pct}/100 = {_format_num(answer)}.")
        return f"What is {pct}% of {base}?", choices, correct, f"{pct}% of {base} = {base} × {pct}/100 = {_format_num(answer)}."

    if topic == "Averages":
        # Construct values symmetrically around a base so the mean is always an integer.
        base = rng.randint(12, 30)
        if level == "Beginner":
            spread = rng.randint(2, 10)
            values = [base - spread, base, base + spread]
        else:
            a, b = rng.randint(1, 8), rng.randint(1, 8)
            values = [base - a, base - b, base + b, base + a]
        rng.shuffle(values)
        total, answer = sum(values), base
        explanation = f"Average = total ÷ count = {total} ÷ {len(values)} = {answer}."
        choices, correct = _mcq(rng, answer, explanation)
        return f"Find the average of {', '.join(map(str, values))}.", choices, correct, explanation

    if topic == "Ratio and Proportion":
        a = rng.randint(2, 8)
        b = rng.randint(2, 9)
        multiplier = rng.randint(3, 12)
        total = (a + b) * multiplier
        answer = a * multiplier
        choices, correct = _mcq(rng, answer, f"The ratio has {a+b} total parts. One part = {total} ÷ {a+b} = {multiplier}; required share = {a} × {multiplier} = {answer}.")
        return f"₹{total} is divided in the ratio {a}:{b}. What is the first share?", choices, correct, f"The ratio has {a+b} total parts. One part = {total} ÷ {a+b} = {multiplier}; required share = {a} × {multiplier} = {answer}."

    if topic == "Profit and Loss":
        cost = rng.choice([200, 250, 400, 500, 600, 800, 1000])
        pct = rng.choice([5, 10, 12, 15, 20, 25])
        if level == "Advanced" and rng.choice([True, False]):
            selling = cost * (100 - pct) // 100
            answer = cost - selling
            prompt = f"An item costing ₹{cost} is sold at a loss of {pct}%. What is the loss?"
            explanation = f"Loss = {pct}% of ₹{cost} = ₹{answer}."
        else:
            answer = cost * (100 + pct) // 100
            prompt = f"An item costs ₹{cost} and is sold at a profit of {pct}%. Find its selling price."
            explanation = f"Selling price = cost × (100 + profit%)/100 = ₹{cost} × {100+pct}/100 = ₹{answer}."
        choices, correct = _mcq(rng, answer, explanation)
        return prompt, choices, correct, explanation

    if topic == "Simple Interest":
        principal = rng.choice([1000, 1500, 2000, 2500, 4000, 5000])
        rate = rng.choice([4, 5, 6, 8, 10, 12])
        years = rng.randint(2, 5) if level != "Beginner" else rng.randint(1, 3)
        answer = principal * rate * years // 100
        explanation = f"Simple interest = P × R × T / 100 = {principal} × {rate} × {years} / 100 = ₹{answer}."
        choices, correct = _mcq(rng, answer, explanation)
        return f"Find the simple interest on ₹{principal} at {rate}% per annum for {years} year(s).", choices, correct, explanation

    # Number Series
    if level == "Beginner":
        start, step = rng.randint(2, 15), rng.randint(2, 9)
        seq = [start + step * i for i in range(4)]
        answer = start + step * 4
        explanation = f"Each term increases by {step}; the next number is {seq[-1]} + {step} = {answer}."
    elif level == "Medium":
        start, step = rng.randint(1, 8), rng.randint(2, 6)
        seq = [start]
        for i in range(1, 4):
            seq.append(seq[-1] + step * i)
        answer = seq[-1] + step * 4
        explanation = f"The increments are {step}, {step*2}, {step*3}, then {step*4}; the next number is {answer}."
    else:
        start, multiplier = rng.randint(1, 4), rng.choice([2, 3])
        seq = [start]
        for _ in range(3):
            seq.append(seq[-1] * multiplier + 1)
        answer = seq[-1] * multiplier + 1
        explanation = f"Multiply by {multiplier} and add 1 each time. The next number is {seq[-1]} × {multiplier} + 1 = {answer}."
    choices, correct = _mcq(rng, answer, explanation)
    return f"Find the next number: {', '.join(map(str, seq))}, ?", choices, correct, explanation


def _reasoning_question(rng: random.Random, topic: str, level: str):
    if topic == "Number Series":
        # Arithmetic sequence: always a single, clearly defined rule.
        start = rng.randint(2, 20)
        step = rng.randint(2, 8) if level == "Beginner" else rng.randint(3, 12)
        seq = [start + i * step for i in range(4)]
        answer = seq[-1] + step
        explanation = f"The sequence increases by {step} each time, so {seq[-1]} + {step} = {answer}."
        choices, correct = _mcq(rng, answer, explanation)
        return f"Find the next number: {', '.join(map(str, seq))}, ?", choices, correct, explanation

    if topic == "Coding-Decoding":
        word = rng.choice(["CAT", "DOG", "PEN", "SUN", "MAP", "BAT"])
        shift = 1 if level == "Beginner" else rng.choice([2, 3])
        coded = "".join(chr((ord(c) - 65 + shift) % 26 + 65) for c in word)
        target = rng.choice(["CUP", "HEN", "BOX", "RAT", "TOP"])
        answer = "".join(chr((ord(c) - 65 + shift) % 26 + 65) for c in target)
        explanation = f"Each letter moves forward by {shift} position(s). {target} becomes {answer}."
        choices, correct = _mcq(rng, 0, explanation, distractors=[answer + "X", answer[:-1] + "Z", answer[::-1]])
        # For string options, ensure the correct answer is present and unique.
        choices = [answer, answer + "X", answer[::-1], target]
        choices = list(dict.fromkeys(choices))
        while len(choices) < 4:
            choices.append(answer + chr(65 + len(choices)))
        rng.shuffle(choices)
        return f"If {word} is coded as {coded}, using the same rule, how is {target} coded?", choices, answer, explanation

    if topic == "Analogy":
        pairs = [
            ("Bird", "Nest", "Bee", "Hive", "Web"),
            ("Puppy", "Dog", "Kitten", "Cat", "Calf"),
            ("Book", "Read", "Food", "Eat", "Write"),
            ("Day", "Night", "Hot", "Cold", "Warm"),
        ]
        a, b, c, answer, distractor = rng.choice(pairs)
        explanation = f"The relationship is {a} to {b}; applying the same relationship, {c} corresponds to {answer}."
        choices = [answer, distractor, c, b]
        choices = list(dict.fromkeys(choices))
        while len(choices) < 4:
            choices.append("None")
        rng.shuffle(choices)
        return f"{a} is to {b} as {c} is to ____.", choices, answer, explanation

    # Blood relations: carefully defined single relationship.
    if rng.choice([True, False]):
        prompt = "Ravi is the brother of Meena. Meena is the mother of Kiran. How is Ravi related to Kiran?"
        answer, explanation = "Maternal uncle", "Meena is Kiran's mother; her brother Ravi is Kiran's maternal uncle."
        choices = ["Maternal uncle", "Father", "Brother", "Grandfather"]
    else:
        prompt = "Anu is the daughter of Sita. Sita is the sister of Mohan. How is Mohan related to Anu?"
        answer, explanation = "Maternal uncle", "Sita is Anu's mother and Mohan is Sita's brother, so Mohan is Anu's maternal uncle."
        choices = ["Maternal uncle", "Father", "Cousin", "Nephew"]
    rng.shuffle(choices)
    return prompt, choices, answer, explanation


def generate_questions(request: GenerateRequest) -> GenerateResponse:
    if request.subject not in SUBJECTS:
        raise HTTPException(status_code=400, detail="Unsupported subject.")
    if request.level not in LEVELS:
        raise HTTPException(status_code=400, detail="Unsupported difficulty level.")
    topics = SUBJECTS[request.subject]
    if request.topic != "All topics" and request.topic not in topics:
        raise HTTPException(status_code=400, detail="Topic does not belong to the selected subject.")

    seed = request.seed if request.seed is not None else random.SystemRandom().randrange(1, 2**31)
    rng = random.Random(seed)
    questions = []
    for index in range(request.count):
        topic = request.topic if request.topic != "All topics" else rng.choice(topics)
        if request.subject == "Quantitative Aptitude":
            prompt, options, answer, explanation = _quant_question(rng, topic, request.level)
        else:
            prompt, options, answer, explanation = _reasoning_question(rng, topic, request.level)

        # Defensive integrity check: every question must have exactly four unique options
        # and exactly one option matching the answer.
        options = [str(o) for o in options]
        if len(options) != 4 or len(set(options)) != 4 or str(answer) not in options:
            raise RuntimeError(f"Question template failed validation: {topic}")
        questions.append(Question(
            id=f"{seed}-{index+1}",
            subject=request.subject,
            topic=topic,
            level=request.level,
            prompt=prompt,
            options=options,
            answer=str(answer),
            explanation=explanation,
        ))
    return GenerateResponse(
        setId=uuid4().hex,
        questions=questions,
        count=len(questions),
        seed=seed,
    )


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "competitive-exam-practice-api"}


@app.get("/api/topics")
def topics():
    return SUBJECTS


@app.post("/api/generate", response_model=GenerateResponse)
def generate(request: GenerateRequest):
    try:
        result = generate_questions(request)
        with storage_lock:
            generated_question_sets[result.setId] = result.questions
            if len(generated_question_sets) > 500:
                del generated_question_sets[next(iter(generated_question_sets))]
        return result
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/admin/questions", response_model=list[Question])
def list_managed_questions():
    with storage_lock:
        return list(managed_questions.values())


@app.post(
    "/api/admin/questions",
    response_model=Question,
    status_code=status.HTTP_201_CREATED,
)
def create_managed_question(request: ManagedQuestionInput):
    question = Question(id=uuid4().hex, **request.model_dump())
    with storage_lock:
        managed_questions[question.id] = question
    return question


@app.put("/api/admin/questions/{question_id}", response_model=Question)
def update_managed_question(question_id: str, request: ManagedQuestionInput):
    with storage_lock:
        if question_id not in managed_questions:
            raise HTTPException(status_code=404, detail="Question not found.")
        question = Question(id=question_id, **request.model_dump())
        managed_questions[question_id] = question
    return question


@app.delete(
    "/api/admin/questions/{question_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_managed_question(question_id: str):
    with storage_lock:
        if managed_questions.pop(question_id, None) is None:
            raise HTTPException(status_code=404, detail="Question not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/api/grade", response_model=GradeResponse)
def grade(request: GradeRequest):
    with storage_lock:
        questions = generated_question_sets.get(request.setId)
    if questions is None:
        raise HTTPException(status_code=404, detail="Question set not found or expired.")

    correct = 0
    results = []
    for question in questions:
        selected = request.answers.get(question.id)
        is_correct = selected == question.answer
        correct += int(is_correct)
        results.append(QuestionResult(
            questionId=question.id,
            selected=selected,
            correctAnswer=question.answer,
            isCorrect=is_correct,
            explanation=question.explanation,
        ))
    total = len(questions)
    created_at = datetime.now(timezone.utc).isoformat()
    attempt = GradeResponse(
        attemptId=uuid4().hex,
        createdAt=created_at,
        correct=correct,
        total=total,
        percentage=round((correct / total) * 100, 1) if total else 0,
        results=results,
    )
    first_question = questions[0] if questions else None
    history_item = PracticeHistoryItem(
        attemptId=attempt.attemptId,
        createdAt=attempt.createdAt,
        subject=first_question.subject if first_question else None,
        level=first_question.level if first_question else None,
        correct=attempt.correct,
        total=attempt.total,
        percentage=attempt.percentage,
    )
    with storage_lock:
        practice_history.append(history_item)
    return attempt


@app.get("/api/history", response_model=list[PracticeHistoryItem])
def get_practice_history(limit: int = Query(default=20, ge=1, le=100)):
    with storage_lock:
        return list(reversed(practice_history[-limit:]))
