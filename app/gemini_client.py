import os
import logging
from google import genai
from google.genai import errors as genai_errors

logger = logging.getLogger("gemini_client")

SYSTEM_PROMPT = """Ты — внутренний AI-ассистент команды разработки в digital-агентстве.
Твоя задача — помогать сотрудникам быстро получать практичные, применимые ответы по рабочим вопросам:
код, архитектура, процессы, дедлайны, формулировки для клиентов и подобное.

Правила ответа:
1. Отвечай по делу, без вступлений вроде "Я являюсь языковой моделью" или "Конечно, помогу!".
2. Структурируй ответ: используй короткие абзацы, нумерованные или маркированные списки, если вопрос предполагает несколько шагов или пунктов.
3. Если вопрос технический — давай конкретику (имена функций, команды, примеры кода), а не общие рассуждения.
4. Если в вопросе не хватает контекста — явно обозначь это одной строкой и дай лучший ответ при разумных предположениях, не задавай встречных вопросов вместо ответа.
5. Не упоминай, что ты Gemini или какая-либо конкретная модель — отвечай как ассистент команды.
6. Ответ должен быть емким: не растягивай на несколько экранов то, что можно сказать в нескольких пунктах.
7. Если ниже есть раздел "Контекст предыдущего разговора" или предыдущие сообщения диалога — учитывай их: не повторяй уже сказанное, ссылайся на упомянутые ранее детали, если вопрос является продолжением темы.
"""

MAIN_MODELS = [
    "gemini-2.5-flash",
    "gemini-3-flash",
    "gemini-3.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-3.1-flash-lite",
]

SUMMARY_MODELS = [
    "gemini-2.5-flash-lite",
    "gemini-3-flash",
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash",
]

CONTEXT_WINDOW = 10


class AllModelsExhaustedError(Exception):
    pass


def _get_client() -> genai.Client:
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY is not set")
    return genai.Client(api_key=api_key)


def _generate_with_fallback(model_chain: list[str], contents, system_instruction: str, max_output_tokens: int) -> dict:
    client = _get_client()
    last_error: Exception | None = None

    for model_name in model_chain:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config={
                    "system_instruction": system_instruction,
                    "temperature": 0.4,
                    "max_output_tokens": max_output_tokens,
                },
            )
            text = (response.text or "").strip()
            if not text:
                raise ValueError("Empty response from model")
            return {"answer": text, "model_used": model_name}
        except genai_errors.ClientError as e:
            logger.warning("Model %s failed (client error): %s", model_name, e)
            last_error = e
            continue
        except Exception as e:
            logger.warning("Model %s failed: %s", model_name, e)
            last_error = e
            continue

    raise AllModelsExhaustedError(
        f"Все модели в fallback-цепочке недоступны (квоты исчерпаны). Последняя ошибка: {last_error}"
    )


def _build_contents(turns: list[dict], question: str) -> list[dict]:
    contents = []
    for turn in turns:
        contents.append({"role": "user", "parts": [{"text": turn["question"]}]})
        contents.append({"role": "model", "parts": [{"text": turn["answer"]}]})
    contents.append({"role": "user", "parts": [{"text": question}]})
    return contents


def ask_ai(question: str, summary: str = "", turns: list[dict] | None = None) -> dict:
    turns = turns or []
    system_instruction = SYSTEM_PROMPT
    if summary:
        system_instruction += f"\n\nКонтекст предыдущего разговора (сводка): {summary}"

    contents = _build_contents(turns, question)
    return _generate_with_fallback(MAIN_MODELS, contents, system_instruction, max_output_tokens=1024)


def summarize_history(previous_summary: str, turns_to_summarize: list[dict]) -> str:
    if not turns_to_summarize:
        return previous_summary

    transcript = "\n\n".join(
        f"Вопрос: {t['question']}\nОтвет: {t['answer']}" for t in turns_to_summarize
    )
    prompt = (
        "Сократи диалог ниже до 3-5 предложений на русском, сохранив ключевые темы, факты и принятые решения. "
        "Это будет использоваться как сжатый контекст для последующих ответов, поэтому пиши по делу, без вступлений.\n\n"
        f"Предыдущая сводка (если есть): {previous_summary or 'нет'}\n\n"
        f"Новые сообщения диалога:\n{transcript}"
    )

    try:
        result = _generate_with_fallback(
            SUMMARY_MODELS,
            contents=[{"role": "user", "parts": [{"text": prompt}]}],
            system_instruction="Ты помогаешь сжимать историю диалога в краткую сводку для контекста.",
            max_output_tokens=300,
        )
        return result["answer"]
    except AllModelsExhaustedError as e:
        logger.warning("Summarization failed, keeping previous summary: %s", e)
        return previous_summary
