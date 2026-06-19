from unittest.mock import MagicMock, patch

import pytest

from app import gemini_client


def _fake_client(*, fail_times=0, answer="ответ модели"):
    client = MagicMock()
    response = MagicMock()
    response.text = answer

    side_effects = [Exception("временная ошибка/квота")] * fail_times + [response]
    client.models.generate_content.side_effect = side_effects
    return client


def test_fallback_uses_next_model_when_first_fails():
    fake_client = _fake_client(fail_times=1)

    with patch.object(gemini_client, "_get_client", return_value=fake_client):
        result = gemini_client._generate_with_fallback(
            ["model-a", "model-b"],
            contents=[{"role": "user", "parts": [{"text": "вопрос"}]}],
            system_instruction="система",
            max_output_tokens=100,
        )

    assert result["model_used"] == "model-b"
    assert result["answer"] == "ответ модели"


def test_all_models_exhausted_raises():
    fake_client = _fake_client(fail_times=5)

    with patch.object(gemini_client, "_get_client", return_value=fake_client):
        with pytest.raises(gemini_client.AllModelsExhaustedError):
            gemini_client._generate_with_fallback(
                ["model-a", "model-b"],
                contents=[{"role": "user", "parts": [{"text": "вопрос"}]}],
                system_instruction="система",
                max_output_tokens=100,
            )


def test_summarize_history_skips_call_when_nothing_to_summarize():
    result = gemini_client.summarize_history("старая сводка", [])
    assert result == "старая сводка"
