const API_BASE = ""; // same origin as FastAPI, e.g. http://localhost:8000

// ---------- Helpers ----------
function setStatus(el, message, type) {
  el.textContent = message || "";
  el.className = "status" + (type ? " " + type : "");
}

function formatDate(value) {
  if (!value) return "";
  const d = new Date(value);
  if (isNaN(d.getTime())) return String(value);
  return d.toLocaleString();
}

async function apiFetch(path, options) {
  const res = await fetch(API_BASE + path, options);
  let data = null;
  try {
    data = await res.json();
  } catch (e) {
    data = null;
  }
  if (!res.ok) {
    const detail = (data && (data.detail || data.message)) || `Request failed (${res.status})`;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return data;
}

// ---------- Health check ----------
async function checkHealth() {
  const dot = document.getElementById("healthDot");
  try {
    await apiFetch("/health");
    dot.classList.remove("bad");
    dot.classList.add("ok");
    dot.title = "Server is online";
  } catch (e) {
    dot.classList.remove("ok");
    dot.classList.add("bad");
    dot.title = "Server unreachable";
  }
}

// ---------- Documents ----------
async function loadDocuments() {
  const list = document.getElementById("documentList");
  const select = document.getElementById("docSelect");

  try {
    const data = await apiFetch("/documents");
    const documents = (data && data.documents) || [];

    // Rebuild list
    list.innerHTML = "";
    if (documents.length === 0) {
      list.innerHTML = '<li class="empty">No documents loaded yet.</li>';
    } else {
      documents.forEach((doc) => {
        const li = document.createElement("li");
        li.innerHTML = `
          <span class="doc-name">${escapeHtml(doc.name || "Untitled")}</span>
          <span class="doc-meta">${doc.chunk_count ?? "?"} chunks &middot; ${formatDate(doc.upload_time)}</span>
          <span class="doc-id">${escapeHtml(doc.doc_id || "")}</span>
        `;
        list.appendChild(li);
      });
    }

    // Rebuild select dropdown, preserving current selection if possible
    const previousValue = select.value;
    select.innerHTML = '<option value="">All documents</option>';
    documents.forEach((doc) => {
      const opt = document.createElement("option");
      opt.value = doc.doc_id;
      opt.textContent = doc.name || doc.doc_id;
      select.appendChild(opt);
    });
    if ([...select.options].some((o) => o.value === previousValue)) {
      select.value = previousValue;
    }
  } catch (e) {
    list.innerHTML = `<li class="empty">Failed to load documents: ${escapeHtml(e.message)}</li>`;
  }
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// ---------- Upload ----------
async function handleUpload(event) {
  event.preventDefault();
  const fileInput = document.getElementById("fileInput");
  const statusEl = document.getElementById("uploadStatus");
  const btn = document.getElementById("uploadBtn");

  if (!fileInput.files.length) {
    setStatus(statusEl, "Please choose a file first.", "error");
    return;
  }

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);

  btn.disabled = true;
  setStatus(statusEl, "Uploading and indexing...", "");

  try {
    const data = await apiFetch("/documents", {
      method: "POST",
      body: formData, // browser sets multipart/form-data boundary automatically
    });
    setStatus(
      statusEl,
      `Uploaded successfully — ${data.chunk_count} chunks indexed (id: ${data.doc_id}).`,
      "success"
    );
    fileInput.value = "";
    await loadDocuments();
  } catch (e) {
    setStatus(statusEl, `Upload failed: ${e.message}`, "error");
  } finally {
    btn.disabled = false;
  }
}

// ---------- Ask ----------
async function handleAsk(event) {
  event.preventDefault();
  const question = document.getElementById("questionInput").value.trim();
  const docId = document.getElementById("docSelect").value || null;
  const k = parseInt(document.getElementById("kInput").value, 10) || 5;
  const statusEl = document.getElementById("askStatus");
  const answerTextEl = document.getElementById("answerText");
  const answerBox = document.getElementById("answerBox");
  const btn = document.getElementById("askBtn");

  if (!question) {
    setStatus(statusEl, "Please enter a question.", "error");
    return;
  }

  btn.disabled = true;
  setStatus(statusEl, "Thinking...", "");
  answerBox.innerHTML = "";
  answerTextEl.textContent = "";
  answerTextEl.classList.remove("visible");

  try {
    const data = await apiFetch("/answer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, doc_id: docId, k }),
    });

    setStatus(statusEl, "Done.", "success");

    if (data.answer) {
      answerTextEl.textContent = data.answer;
      answerTextEl.classList.add("visible");
    }

    renderResults(data.results, answerBox);
    await loadHistory();
  } catch (e) {
    setStatus(statusEl, `Request failed: ${e.message}`, "error");
  } finally {
    btn.disabled = false;
  }
}

function renderResults(results, container) {
  if (!results || (Array.isArray(results) && results.length === 0)) {
    container.innerHTML = '<p class="status">No results found.</p>';
    return;
  }

  const items = Array.isArray(results) ? results : [results];

  const heading = document.createElement("p");
  heading.className = "status";
  heading.textContent = "Sources";
  container.appendChild(heading);

  items.forEach((item, idx) => {
    const card = document.createElement("div");
    card.className = "result-card";

    // Try to gracefully handle whatever shape the search() function returns
    const text =
      item.text ?? item.chunk ?? item.content ?? (typeof item === "string" ? item : JSON.stringify(item, null, 2));
    const score = item.score ?? item.similarity ?? item.distance;
    const filename = item.filename ?? item.doc_name ?? item.source;
    const docId = item.doc_id;

    const metaParts = [];
    metaParts.push(`#${idx + 1}`);
    if (filename) metaParts.push(escapeHtml(filename));
    if (score !== undefined) metaParts.push(`score: ${Number(score).toFixed ? Number(score).toFixed(4) : score}`);
    if (docId) metaParts.push(`doc: ${escapeHtml(docId)}`);

    card.innerHTML = `
      <div class="result-meta">${metaParts.join(" &middot; ")}</div>
      <div class="result-text">${escapeHtml(text)}</div>
    `;
    container.appendChild(card);
  });
}

// ---------- History ----------
async function loadHistory() {
  const list = document.getElementById("historyList");
  try {
    const data = await apiFetch("/history?limit=15&offset=0");
    const history = (data && data.history) || [];

    if (history.length === 0) {
      list.innerHTML = '<li class="empty">No history yet.</li>';
      return;
    }

    list.innerHTML = "";
    history.forEach((item) => {
      const li = document.createElement("li");
      li.innerHTML = `
        <span class="doc-name">${escapeHtml(item.question)}</span>
        <span class="hist-meta">
          ${item.doc_id ? "doc: " + escapeHtml(item.doc_id) : "all docs"} &middot;
          ${item.latency_ms ? Math.round(item.latency_ms) + " ms" : ""} &middot;
          ${formatDate(item.created_at)}
        </span>
      `;
      list.appendChild(li);
    });
  } catch (e) {
    list.innerHTML = `<li class="empty">Failed to load history: ${escapeHtml(e.message)}</li>`;
  }
}

// ---------- Init ----------
document.addEventListener("DOMContentLoaded", () => {
  checkHealth();
  loadDocuments();
  loadHistory();

  document.getElementById("uploadForm").addEventListener("submit", handleUpload);
  document.getElementById("askForm").addEventListener("submit", handleAsk);
  document.getElementById("refreshDocsBtn").addEventListener("click", loadDocuments);
  document.getElementById("refreshHistoryBtn").addEventListener("click", loadHistory);

  // periodic health re-check
  setInterval(checkHealth, 15000);
});
