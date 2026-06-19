from app import database


def test_save_query_returns_saved_entry(temp_db):
    entry = database.save_query("Вопрос?", "Ответ.", "gemini-2.5-flash")
    assert entry["question"] == "Вопрос?"
    assert entry["answer"] == "Ответ."
    assert entry["model_used"] == "gemini-2.5-flash"
    assert entry["id"] == 1


def test_get_last_queries_returns_only_last_five_newest_first(temp_db):
    for i in range(7):
        database.save_query(f"Вопрос {i}", f"Ответ {i}", "gemini-2.5-flash")

    last = database.get_last_queries(limit=5)

    assert len(last) == 5
    assert [item["question"] for item in last] == [
        "Вопрос 6",
        "Вопрос 5",
        "Вопрос 4",
        "Вопрос 3",
        "Вопрос 2",
    ]


def test_conversation_state_roundtrip(temp_db):
    database.save_query("Q1", "A1", "gemini-2.5-flash")
    database.update_conversation_state("краткая сводка", 1)

    state = database.get_conversation_state()

    assert state["summary"] == "краткая сводка"
    assert state["summarized_up_to_id"] == 1
    assert database.get_queries_after(1) == []
