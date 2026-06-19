import logging
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.database import init_db, save_query, get_last_queries
from app.gemini_client import ask_ai, AllModelsExhaustedError

load_dotenv()
logging.basicConfig(level=logging.INFO)

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="AI Team Assistant")
init_db()

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


@app.get("/")
def index():
    return FileResponse(BASE_DIR / "templates" / "index.html")


@app.post("/api/ask")
def ask(payload: AskRequest):
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Вопрос не может быть пустым")

    try:
        result = ask_ai(question)
    except AllModelsExhaustedError:
        raise HTTPException(
            status_code=503,
            detail="Все доступные модели сейчас перегружены или квота исчерпана. Попробуйте через минуту.",
        )
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    entry = save_query(question, result["answer"], result["model_used"])
    return entry


@app.get("/api/history")
def history():
    return get_last_queries(limit=5)
