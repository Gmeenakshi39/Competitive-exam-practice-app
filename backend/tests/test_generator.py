import pytest
from fastapi.testclient import TestClient

from app.main import (
    GenerateRequest,
    app,
    generate_questions,
    generated_question_sets,
    managed_questions,
    practice_history,
    storage_lock,
    SUBJECTS,
)


@pytest.fixture
def client():
    with storage_lock:
        managed_questions.clear()
        practice_history.clear()
        generated_question_sets.clear()
    yield TestClient(app)
    with storage_lock:
        managed_questions.clear()
        practice_history.clear()
        generated_question_sets.clear()


def test_questions_have_four_unique_options_and_answer():
    for subject, topics in SUBJECTS.items():
        for topic in topics:
            for level in ["Beginner", "Medium", "Advanced"]:
                result = generate_questions(GenerateRequest(
                    subject=subject, level=level, topic=topic, count=10, seed=12345
                ))
                assert len(result.questions) == 10
                for q in result.questions:
                    assert len(q.options) == 4
                    assert len(set(q.options)) == 4 
                    assert q.answer in q.options
                    assert q.explanation
def test_different_seeds_change_generated_set():
    a = generate_questions(GenerateRequest(
        subject="Quantitative Aptitude", level="Beginner", topic="Percentages", count=5, seed=10
    ))
    b = generate_questions(GenerateRequest(
        subject="Quantitative Aptitude", level="Beginner", topic="Percentages", count=5, seed=20
    ))
    assert [q.prompt for q in a.questions] != [q.prompt for q in b.questions]


def test_admin_question_crud_and_validation(client):
    question_data = {
        "subject": "Quantitative Aptitude",
        "topic": "Percentages",
        "level": "Beginner",
        "prompt": "What is 10% of 200?",
        "options": ["10", "20", "30", "40"],
        "answer": "20",
        "explanation": "10% of 200 is 20.",
    }

    created = client.post("/api/admin/questions", json=question_data)
    assert created.status_code == 201
    question_id = created.json()["id"]
    assert client.get("/api/admin/questions").json()[0]["id"] == question_id

    updated_data = {**question_data, "prompt": "Updated prompt"}
    updated = client.put(f"/api/admin/questions/{question_id}", json=updated_data)
    assert updated.status_code == 200
    assert updated.json()["prompt"] == "Updated prompt"

    invalid_data = {**question_data, "answer": "50"}
    assert client.post("/api/admin/questions", json=invalid_data).status_code == 422

    assert client.delete(f"/api/admin/questions/{question_id}").status_code == 204
    assert client.delete(f"/api/admin/questions/{question_id}").status_code == 404
    assert client.get("/api/admin/questions").json() == []


def test_grading_records_recent_practice_history(client):
    question_set = client.post("/api/generate", json={
        "subject": "Quantitative Aptitude",
        "level": "Beginner",
        "topic": "Percentages",
        "count": 2,
        "seed": 123,
    }).json()
    answers = {question["id"]: question["answer"] for question in question_set["questions"]}

    graded = client.post(
        "/api/grade",
        json={"setId": question_set["setId"], "answers": answers},
    )
    assert graded.status_code == 200
    result = graded.json()
    assert result["correct"] == result["total"] == 2
    assert result["percentage"] == 100
    assert result["attemptId"]

    history = client.get("/api/history").json()
    assert len(history) == 1
    assert history[0]["attemptId"] == result["attemptId"]
    assert history[0]["subject"] == "Quantitative Aptitude"
    assert history[0]["level"] == "Beginner"


def test_grading_rejects_unknown_question_sets(client):
    response = client.post("/api/grade", json={"setId": "unknown", "answers": {}})
    assert response.status_code == 404
