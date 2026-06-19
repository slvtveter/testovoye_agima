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

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function inlineFormat(text) {
  let result = escapeHtml(text);
  result = result.replace(/`([^`]+)`/g, "<code>$1</code>");
  result = result.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  result = result.replace(/(?<!\*)\*([^*]+)\*(?!\*)/g, "<em>$1</em>");
  return result;
}

function renderMarkdown(raw) {
  const lines = raw.replace(/\r\n/g, "\n").split("\n");
  let html = "";
  let inCode = false;
  let codeBuffer = [];
  let listType = null;
  let listBuffer = [];
  let paraBuffer = [];

  const flushPara = () => {
    if (paraBuffer.length) {
      html += `<p>${inlineFormat(paraBuffer.join(" "))}</p>`;
      paraBuffer = [];
    }
  };
  const flushList = () => {
    if (listType) {
      html += `<${listType}>${listBuffer.map((item) => `<li>${inlineFormat(item)}</li>`).join("")}</${listType}>`;
      listType = null;
      listBuffer = [];
    }
  };

  for (const line of lines) {
    const trimmed = line.trim();

    if (trimmed.startsWith("```")) {
      if (!inCode) {
        flushPara();
        flushList();
        inCode = true;
        codeBuffer = [];
      } else {
        html += `<pre><code>${escapeHtml(codeBuffer.join("\n"))}</code></pre>`;
        inCode = false;
      }
      continue;
    }
    if (inCode) {
      codeBuffer.push(line);
      continue;
    }

    if (trimmed === "") {
      flushPara();
      flushList();
      continue;
    }

    const headingMatch = trimmed.match(/^(#{1,3})\s+(.*)$/);
    if (headingMatch) {
      flushPara();
      flushList();
      const level = headingMatch[1].length;
      html += `<h${level}>${inlineFormat(headingMatch[2])}</h${level}>`;
      continue;
    }

    const ulMatch = trimmed.match(/^[-*]\s+(.*)$/);
    const olMatch = trimmed.match(/^\d+\.\s+(.*)$/);

    if (ulMatch) {
      flushPara();
      if (listType !== "ul") {
        flushList();
        listType = "ul";
      }
      listBuffer.push(ulMatch[1]);
      continue;
    }
    if (olMatch) {
      flushPara();
      if (listType !== "ol") {
        flushList();
        listType = "ol";
      }
      listBuffer.push(olMatch[1]);
      continue;
    }

    flushList();
    paraBuffer.push(trimmed);
  }

  flushPara();
  flushList();
  if (inCode && codeBuffer.length) {
    html += `<pre><code>${escapeHtml(codeBuffer.join("\n"))}</code></pre>`;
  }

  return html;
}

function renderAnswer(entry) {
  answerText.innerHTML = renderMarkdown(entry.answer);
  modelBadge.textContent = entry.model_used;
  answerSection.hidden = false;
  copyBtn.classList.remove("copied");
  copyBtn.innerHTML = '<span class="copy-icon">⧉</span> Копировать';
}

let lastHistoryItems = [];

function renderHistory(items) {
  lastHistoryItems = items;
  if (!items.length) {
    historyList.innerHTML = '<p class="history-empty">Пока нет запросов — задайте первый вопрос выше.</p>';
    return;
  }
  historyList.innerHTML = items
    .map(
      (item, index) => `
      <div class="history-item" data-index="${index}" tabindex="0" role="button">
        <div class="history-question">${escapeHtml(item.question)}</div>
        <div class="history-answer">${escapeHtml(item.answer)}</div>
        <div class="history-time">${formatTime(item.created_at)} · ${escapeHtml(item.model_used)}</div>
      </div>
    `
    )
    .join("");
}

function openHistoryEntry(index) {
  const entry = lastHistoryItems[index];
  if (!entry) return;
  renderAnswer(entry);
  closeHistoryPanel();
  answerSection.scrollIntoView({ behavior: "smooth", block: "start" });
}

historyList.addEventListener("click", (e) => {
  const itemEl = e.target.closest(".history-item");
  if (!itemEl) return;
  openHistoryEntry(Number(itemEl.dataset.index));
});

historyList.addEventListener("keydown", (e) => {
  if (e.key !== "Enter" && e.key !== " ") return;
  const itemEl = e.target.closest(".history-item");
  if (!itemEl) return;
  e.preventDefault();
  openHistoryEntry(Number(itemEl.dataset.index));
});

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
