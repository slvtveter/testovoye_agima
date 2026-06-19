from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.gemini_client import AllModelsExhaustedError

client = TestClient(app)


def test_ask_with_empty_question_returns_400(temp_db):
    response = client.post("/api/ask", json={"question": "   "})
    assert response.status_code == 400


def test_ask_with_question_over_char_limit_returns_422(temp_db):
    response = client.post("/api/ask", json={"question": "x" * 2001})
    assert response.status_code == 422


def test_ask_success_saves_entry_and_appears_in_history(temp_db):
    fake_result = {"answer": "Тестовый ответ", "model_used": "gemini-2.5-flash"}

    with patch("app.main.ask_ai", return_value=fake_result):
        response = client.post("/api/ask", json={"question": "Тестовый вопрос"})

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "Тестовый ответ"
    assert body["model_used"] == "gemini-2.5-flash"

    history = client.get("/api/history").json()
    assert len(history) == 1
    assert history[0]["question"] == "Тестовый вопрос"


def test_ask_returns_503_when_all_models_exhausted(temp_db):
    with patch("app.main.ask_ai", side_effect=AllModelsExhaustedError("квота кончилась")):
        response = client.post("/api/ask", json={"question": "Вопрос"})

    assert response.status_code == 503
