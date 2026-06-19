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
"""

FALLBACK_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-3.1-flash-lite",
]


class AllModelsExhaustedError(Exception):
    pass


def ask_ai(question: str) -> dict:
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY is not set")

    client = genai.Client(api_key=api_key)

    last_error: Exception | None = None
    for model_name in FALLBACK_MODELS:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=question,
                config={
                    "system_instruction": SYSTEM_PROMPT,
                    "temperature": 0.4,
                    "max_output_tokens": 1024,
                },
            )
            text = (response.text or "").strip()
            if not text:
                raise ValueError("Empty response from model")
            return {"answer": text, "model_used": model_name}
        except genai_errors.ClientError as e:
            status = getattr(e, "status_code", None) or getattr(e, "code", None)
            logger.warning("Model %s failed (client error, status=%s): %s", model_name, status, e)
            last_error = e
            if status == 429 or "RESOURCE_EXHAUSTED" in str(e):
                continue
            continue
        except Exception as e:
            logger.warning("Model %s failed: %s", model_name, e)
            last_error = e
            continue

    raise AllModelsExhaustedError(
        f"Все модели в fallback-цепочке недоступны (квоты исчерпаны). Последняя ошибка: {last_error}"
    )
