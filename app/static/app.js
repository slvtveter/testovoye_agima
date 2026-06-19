const questionEl = document.getElementById("question");
const charCountEl = document.getElementById("charCount");
const askBtn = document.getElementById("askBtn");
const btnText = askBtn.querySelector(".btn-text");
const spinner = askBtn.querySelector(".spinner");
const errorBox = document.getElementById("errorBox");
const answerSection = document.getElementById("answerSection");
const answerText = document.getElementById("answerText");
const modelBadge = document.getElementById("modelBadge");
const copyBtn = document.getElementById("copyBtn");
const historyList = document.getElementById("historyList");
const historyPanel = document.getElementById("historyPanel");
const historyOverlay = document.getElementById("historyOverlay");
const historyToggleBtn = document.getElementById("historyToggleBtn");
const historyCloseBtn = document.getElementById("historyCloseBtn");

const MAX_LEN = 2000;

function openHistoryPanel() {
  historyPanel.classList.add("open");
  historyPanel.setAttribute("aria-hidden", "false");
  historyOverlay.hidden = false;
  requestAnimationFrame(() => historyOverlay.classList.add("visible"));
}

function closeHistoryPanel() {
  historyPanel.classList.remove("open");
  historyPanel.setAttribute("aria-hidden", "true");
  historyOverlay.classList.remove("visible");
  setTimeout(() => {
    historyOverlay.hidden = true;
  }, 250);
}

historyToggleBtn.addEventListener("click", openHistoryPanel);
historyCloseBtn.addEventListener("click", closeHistoryPanel);
historyOverlay.addEventListener("click", closeHistoryPanel);
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") closeHistoryPanel();
});

questionEl.addEventListener("input", () => {
  const len = questionEl.value.length;
  charCountEl.textContent = `${len} / ${MAX_LEN}`;
});

function setLoading(isLoading) {
  askBtn.disabled = isLoading;
  spinner.hidden = !isLoading;
  btnText.textContent = isLoading ? "Думаю..." : "Спросить AI";
}

function showError(message) {
  errorBox.textContent = message;
  errorBox.hidden = false;
}

function hideError() {
  errorBox.hidden = true;
}

function formatTime(isoString) {
  const d = new Date(isoString);
  return d.toLocaleString("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function renderAnswer(entry) {
  answerText.textContent = entry.answer;
  modelBadge.textContent = entry.model_used;
  answerSection.hidden = false;
  copyBtn.classList.remove("copied");
  copyBtn.innerHTML = '<span class="copy-icon">⧉</span> Копировать';
}

function renderHistory(items) {
  if (!items.length) {
    historyList.innerHTML = '<p class="history-empty">Пока нет запросов — задайте первый вопрос выше.</p>';
    return;
  }
  historyList.innerHTML = items
    .map(
      (item) => `
      <div class="history-item">
        <div class="history-question">${escapeHtml(item.question)}</div>
        <div class="history-answer">${escapeHtml(item.answer)}</div>
        <div class="history-time">${formatTime(item.created_at)} · ${escapeHtml(item.model_used)}</div>
      </div>
    `
    )
    .join("");
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

async function loadHistory() {
  try {
    const res = await fetch("/api/history");
    if (!res.ok) return;
    const items = await res.json();
    renderHistory(items);
  } catch (e) {
    console.error("Failed to load history", e);
  }
}

async function askQuestion() {
  const question = questionEl.value.trim();
  if (!question) {
    showError("Введите вопрос перед отправкой.");
    return;
  }

  hideError();
  setLoading(true);

  try {
    const res = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });

    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.detail || "Не удалось получить ответ. Попробуйте снова.");
    }

    const entry = await res.json();
    renderAnswer(entry);
    await loadHistory();
    questionEl.value = "";
    charCountEl.textContent = `0 / ${MAX_LEN}`;
  } catch (e) {
    showError(e.message);
  } finally {
    setLoading(false);
  }
}

askBtn.addEventListener("click", askQuestion);

questionEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
    askQuestion();
  }
});

copyBtn.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(answerText.textContent);
    copyBtn.classList.add("copied");
    copyBtn.innerHTML = '<span class="copy-icon">✓</span> Скопировано';
    setTimeout(() => {
      copyBtn.classList.remove("copied");
      copyBtn.innerHTML = '<span class="copy-icon">⧉</span> Копировать';
    }, 1800);
  } catch (e) {
    console.error("Copy failed", e);
  }
});

loadHistory();
