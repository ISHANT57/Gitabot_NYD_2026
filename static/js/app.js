'use strict';

// ── State ──────────────────────────────────────────────────────────────
let activeFilter = '';
let isLoading = false;

// ── DOM refs ───────────────────────────────────────────────────────────
const messagesEl  = document.getElementById('messages');
const chatInput   = document.getElementById('chatInput');
const sendBtn     = document.getElementById('sendBtn');
const statsToggle = document.getElementById('statsToggle');
const statsPanel  = document.getElementById('statsPanel');
const initDbBtn   = document.getElementById('initDb');
const verseLookupBtn = document.getElementById('verseLookup');
const verseModal  = document.getElementById('verseModal');
const modalClose  = document.getElementById('modalClose');

// ── Helpers ────────────────────────────────────────────────────────────
function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function formatAnswer(text) {
  // Bold **text**
  text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  // Italic *text*
  text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
  // Newlines to paragraphs
  const paras = text.split(/\n{2,}/);
  return paras.map(p => `<p>${p.replace(/\n/g, '<br/>')}</p>`).join('');
}

function scrollToBottom() {
  messagesEl.scrollTo({ top: messagesEl.scrollHeight, behavior: 'smooth' });
}

function setLoading(val) {
  isLoading = val;
  sendBtn.disabled = val;
  chatInput.disabled = val;
}

// ── Message builders ───────────────────────────────────────────────────
function appendUserMessage(text) {
  const el = document.createElement('div');
  el.className = 'message user-message';
  el.innerHTML = `
    <div class="user-avatar">🙏</div>
    <div class="message-bubble">${escapeHtml(text)}</div>
  `;
  messagesEl.appendChild(el);
  scrollToBottom();
}

function appendTypingIndicator() {
  const el = document.createElement('div');
  el.className = 'message bot-message typing-indicator';
  el.id = 'typingIndicator';
  el.innerHTML = `
    <div class="bot-avatar"><span>ॐ</span></div>
    <div class="message-bubble">
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
    </div>
  `;
  messagesEl.appendChild(el);
  scrollToBottom();
}

function removeTypingIndicator() {
  const el = document.getElementById('typingIndicator');
  if (el) el.remove();
}

function appendBotMessage(answer, confidence, contextUsed) {
  const el = document.createElement('div');
  el.className = 'message bot-message';

  const confPct = confidence != null ? Math.round(confidence * 100) : null;
  let confHtml = '';
  if (confPct !== null && confPct > 0) {
    const color = confPct >= 70 ? '#D4A017' : confPct >= 40 ? '#FF6B00' : '#7B1D1D';
    confHtml = `
      <div class="confidence-bar">
        <span class="confidence-label">Relevance</span>
        <div class="confidence-track">
          <div class="confidence-fill" style="width:${confPct}%; background: linear-gradient(90deg, ${color}, ${color}cc);"></div>
        </div>
        <span class="confidence-pct">${confPct}%</span>
      </div>`;
  }

  el.innerHTML = `
    <div class="bot-avatar"><span>ॐ</span></div>
    <div class="message-bubble">
      ${formatAnswer(answer)}
      ${confHtml}
    </div>
  `;
  messagesEl.appendChild(el);
  scrollToBottom();
}

function appendErrorMessage(msg) {
  const el = document.createElement('div');
  el.className = 'message bot-message error-message';
  el.innerHTML = `
    <div class="bot-avatar"><span>ॐ</span></div>
    <div class="message-bubble"><p>⚠️ ${escapeHtml(msg)}</p></div>
  `;
  messagesEl.appendChild(el);
  scrollToBottom();
}

// ── API calls ──────────────────────────────────────────────────────────
async function sendQuestion(question) {
  if (!question.trim() || isLoading) return;
  setLoading(true);
  appendUserMessage(question);
  appendTypingIndicator();

  try {
    const res = await fetch('/api/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question: question.trim(),
        source_filter: activeFilter || null
      })
    });
    const data = await res.json();
    removeTypingIndicator();

    if (data.error) {
      appendErrorMessage(data.error);
    } else {
      appendBotMessage(data.answer, data.confidence, data.context_used);
    }
  } catch (err) {
    removeTypingIndicator();
    appendErrorMessage('Could not reach the server. Please check your connection.');
  } finally {
    setLoading(false);
  }
}

async function lookupVerse(chapter, verse) {
  try {
    const res = await fetch(`/api/verse/${encodeURIComponent(chapter)}/${encodeURIComponent(verse)}`);
    const data = await res.json();

    if (!data.found) {
      alert(`Verse ${chapter}.${verse} was not found in the database.`);
      return;
    }

    document.getElementById('modalRef').textContent = `Chapter ${chapter} · Verse ${verse}`;
    const body = document.getElementById('modalBody');
    body.innerHTML = '';

    const fields = [
      { label: 'Source', val: data.source, cls: '' },
      { label: 'Sanskrit', val: data.sanskrit, cls: '' },
      { label: 'Translation', val: data.translation, cls: 'translation' },
      { label: 'Commentary', val: data.explanation, cls: '' },
    ];

    fields.forEach(f => {
      if (!f.val) return;
      const lbl = document.createElement('div');
      lbl.className = 'verse-field-label';
      lbl.textContent = f.label;
      const val = document.createElement('div');
      val.className = `verse-field-val ${f.cls}`;
      val.textContent = f.val;
      body.appendChild(lbl);
      body.appendChild(val);
    });

    verseModal.classList.add('open');
  } catch (err) {
    alert('Error looking up verse.');
  }
}

async function loadStats() {
  try {
    const res = await fetch('/api/stats');
    const data = await res.json();
    document.getElementById('statDocs').textContent = data.total_documents?.toLocaleString() ?? '0';
    document.getElementById('statIndexed').textContent = data.indexed_documents?.toLocaleString() ?? '0';
    document.getElementById('statStatus').textContent = data.status ?? '—';
  } catch (_) {
    document.getElementById('statStatus').textContent = 'Offline';
  }
}

async function initDatabase() {
  initDbBtn.disabled = true;
  initDbBtn.textContent = 'Initializing…';
  try {
    const res = await fetch('/api/initialize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ force_reload: false })
    });
    const data = await res.json();
    if (data.error) alert('Error: ' + data.error);
    else { alert('Database initialized successfully!'); loadStats(); }
  } catch (_) {
    alert('Failed to initialize database.');
  } finally {
    initDbBtn.disabled = false;
    initDbBtn.innerHTML = `
      <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none"
        stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/>
        <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
      </svg>
      Initialize Database`;
  }
}

// ── Event Listeners ────────────────────────────────────────────────────

// Send on button click
sendBtn.addEventListener('click', () => {
  const q = chatInput.value.trim();
  if (q) { sendQuestion(q); chatInput.value = ''; autoResize(); }
});

// Enter key (Shift+Enter = new line)
chatInput.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    const q = chatInput.value.trim();
    if (q) { sendQuestion(q); chatInput.value = ''; autoResize(); }
  }
});

// Auto-resize textarea
function autoResize() {
  chatInput.style.height = 'auto';
  chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
}
chatInput.addEventListener('input', autoResize);

// Stats toggle
statsToggle.addEventListener('click', () => {
  statsPanel.classList.toggle('open');
  if (statsPanel.classList.contains('open')) loadStats();
});

// Close stats panel if clicking outside
document.addEventListener('click', e => {
  if (!statsPanel.contains(e.target) && !statsToggle.contains(e.target)) {
    statsPanel.classList.remove('open');
  }
});

// Init DB
initDbBtn.addEventListener('click', initDatabase);

// Filter options
document.querySelectorAll('.filter-opt').forEach(opt => {
  opt.addEventListener('click', () => {
    document.querySelectorAll('.filter-opt').forEach(o => o.classList.remove('active'));
    opt.classList.add('active');
    activeFilter = opt.dataset.val;
  });
});

// Suggestions
document.querySelectorAll('.suggestion-item').forEach(item => {
  item.addEventListener('click', () => {
    sendQuestion(item.dataset.q);
  });
});

// Verse lookup
verseLookupBtn.addEventListener('click', () => {
  const ch = document.getElementById('verseChapter').value;
  const vs = document.getElementById('verseVerse').value;
  if (!ch || !vs) { alert('Please enter both chapter and verse numbers.'); return; }
  lookupVerse(ch, vs);
});

// Modal close
modalClose.addEventListener('click', () => verseModal.classList.remove('open'));
verseModal.addEventListener('click', e => {
  if (e.target === verseModal) verseModal.classList.remove('open');
});
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') verseModal.classList.remove('open');
});
