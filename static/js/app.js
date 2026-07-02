'use strict';

// ── State ─────────────────────────────────────────────────────────────────
let activeFilter = '';
let isLoading = false;

// ── DOM ───────────────────────────────────────────────────────────────────
const messagesEl    = document.getElementById('messages');
const chatInput     = document.getElementById('chatInput');
const sendBtn       = document.getElementById('sendBtn');
const charCount     = document.getElementById('charCount');
const statsToggle   = document.getElementById('statsToggle');
const statsDrawer   = document.getElementById('statsDrawer');
const initDbBtn     = document.getElementById('initDb');
const verseLookupBtn= document.getElementById('verseLookup');
const verseModal    = document.getElementById('verseModal');
const modalClose    = document.getElementById('modalClose');
const sidebarToggle = document.getElementById('sidebarToggle');
const sidebar       = document.getElementById('sidebar');
const clearChat     = document.getElementById('clearChat');
const statusDot     = document.getElementById('statusDot');
const statusText    = document.getElementById('statusText');
const breadcrumbFilter = document.getElementById('breadcrumbFilter');

// ── Utilities ─────────────────────────────────────────────────────────────
function escHtml(s) {
  return String(s)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function formatAnswer(text) {
  text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
  const paras = text.split(/\n{2,}/);
  return paras.map(p => `<p>${p.replace(/\n/g,'<br/>')}</p>`).join('');
}

function scrollToBottom() {
  messagesEl.scrollTo({ top: messagesEl.scrollHeight, behavior: 'smooth' });
}

function setLoading(val) {
  isLoading = val;
  sendBtn.disabled = val;
  chatInput.disabled = val;
}

// ── Message builders ──────────────────────────────────────────────────────
function appendUserMsg(text) {
  const el = document.createElement('div');
  el.className = 'message user-message';
  el.innerHTML = `
    <div class="user-avatar">👤</div>
    <div class="msg-bubble">${escHtml(text)}</div>`;
  messagesEl.appendChild(el);
  scrollToBottom();
}

function appendTyping() {
  const el = document.createElement('div');
  el.className = 'message bot-message typing-indicator';
  el.id = 'typingEl';
  el.innerHTML = `
    <div class="bot-avatar">ॐ</div>
    <div class="msg-bubble">
      <div class="t-dot"></div>
      <div class="t-dot"></div>
      <div class="t-dot"></div>
    </div>`;
  messagesEl.appendChild(el);
  scrollToBottom();
}

function removeTyping() {
  document.getElementById('typingEl')?.remove();
}

const SOURCE_LABELS = {
  'bhagavad_gita_qa':             'Bhagavad Gita',
  'processed_gita':               'Bhagavad Gita',
  'ramayana_verses_comprehensive': 'Ramayana',
  'ramayana_iyd_dataset':         'Ramayana',
  'ramayana_characters':          'Ramayana Characters',
  'mahabharata_characters':       'Mahabharata Characters',
};

function buildSourcesHtml(sources) {
  if (!sources || !sources.length) return '';
  const uid = 'src-' + Date.now();
  const rows = sources.map((s, i) => {
    const label = SOURCE_LABELS[s.source] || s.source;
    const ref   = (s.chapter && s.verse) ? `Ch.${s.chapter} · Vs.${s.verse}` : (s.chapter ? `Ch.${s.chapter}` : '');
    const snip  = s.translation || s.text || '';
    const pct   = Math.round((s.score || 0) * 100);
    return `
      <div class="src-card">
        <div class="src-card-head">
          <div class="src-card-meta">
            <span class="src-tag">${escHtml(label)}</span>
            ${ref ? `<span class="src-ref">${escHtml(ref)}</span>` : ''}
          </div>
          <span class="src-score">${pct}%</span>
        </div>
        ${snip ? `<p class="src-snip">${escHtml(snip.slice(0, 240))}${snip.length > 240 ? '…' : ''}</p>` : ''}
      </div>`;
  }).join('');

  return `
    <div class="sources-section">
      <button class="sources-toggle" data-target="${uid}">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>
        View ${sources.length} Source${sources.length > 1 ? 's' : ''}
      </button>
      <div class="sources-list" id="${uid}">${rows}</div>
    </div>`;
}

function appendBotMsg(answer, confidence, contextUsed, sources) {
  const el = document.createElement('div');
  el.className = 'message bot-message';

  const pct = confidence != null ? Math.round(confidence * 100) : 0;
  let metaHtml = '';
  if (pct > 0) {
    metaHtml = `
      <div class="msg-meta">
        <span class="meta-label">Relevance</span>
        <div class="conf-track">
          <div class="conf-fill" style="width:${pct}%"></div>
        </div>
        <span class="conf-pct">${pct}%</span>
        ${contextUsed ? `<span class="ctx-badge">${contextUsed} docs used</span>` : ''}
      </div>`;
  }

  el.innerHTML = `
    <div class="bot-avatar">ॐ</div>
    <div class="msg-bubble">
      ${formatAnswer(answer)}
      ${metaHtml}
      ${buildSourcesHtml(sources)}
    </div>`;

  // Wire up sources toggle after inserting into DOM
  el.querySelectorAll('.sources-toggle').forEach(btn => {
    btn.addEventListener('click', () => {
      const target = document.getElementById(btn.dataset.target);
      const open   = target.classList.toggle('open');
      btn.classList.toggle('open', open);
    });
  });

  messagesEl.appendChild(el);
  scrollToBottom();
}

function appendErrorMsg(msg) {
  const el = document.createElement('div');
  el.className = 'message bot-message';
  el.innerHTML = `
    <div class="bot-avatar">ॐ</div>
    <div class="msg-bubble error-bubble"><p>⚠ ${escHtml(msg)}</p></div>`;
  messagesEl.appendChild(el);
  scrollToBottom();
}

// ── API ───────────────────────────────────────────────────────────────────
async function sendQuestion(q) {
  if (!q.trim() || isLoading) return;
  setLoading(true);
  appendUserMsg(q);
  appendTyping();

  try {
    const res = await fetch('/api/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: q.trim(), source_filter: activeFilter || null })
    });
    const data = await res.json();
    removeTyping();
    if (data.error) appendErrorMsg(data.error);
    else appendBotMsg(data.answer, data.confidence, data.context_used, data.sources);
  } catch {
    removeTyping();
    appendErrorMsg('Network error — could not reach the server.');
  } finally {
    setLoading(false);
  }
}

async function lookupVerse(ch, vs) {
  try {
    const res = await fetch(`/api/verse/${encodeURIComponent(ch)}/${encodeURIComponent(vs)}`);
    const data = await res.json();
    if (!data.found) { alert(`Verse ${ch}.${vs} not found.`); return; }

    document.getElementById('modalRef').textContent = `Chapter ${ch} · Verse ${vs}`;
    const body = document.getElementById('modalBody');
    body.innerHTML = '';

    const fields = [
      { label: 'Source', val: data.source },
      { label: 'Sanskrit', val: data.sanskrit },
      { label: 'Translation', val: data.translation, cls: 'translation' },
      { label: 'Commentary', val: data.explanation },
    ];
    fields.forEach(f => {
      if (!f.val) return;
      const div = document.createElement('div');
      div.className = 'verse-field';
      div.innerHTML = `
        <div class="vf-label">${f.label}</div>
        <div class="vf-val ${f.cls||''}">${escHtml(f.val)}</div>`;
      body.appendChild(div);
    });
    verseModal.classList.add('open');
  } catch { alert('Error looking up verse.'); }
}

async function loadStats() {
  try {
    const res = await fetch('/api/stats');
    const d = await res.json();
    document.getElementById('statDocs').textContent    = (d.total_documents ?? 0).toLocaleString();
    document.getElementById('statIndexed').textContent = (d.indexed_documents ?? 0).toLocaleString();
    document.getElementById('statStatus').textContent  = d.status ?? '—';
    const online = (d.total_documents ?? 0) > 0;
    statusDot.className = 'status-dot ' + (online ? 'online' : 'offline');
    statusText.textContent = online ? `${(d.total_documents).toLocaleString()} docs` : 'Empty DB';
    const chip = document.getElementById('docCountChip');
    if (chip) chip.textContent = online ? `${(d.total_documents).toLocaleString()} Documents` : 'Empty DB — Initialize';
  } catch {
    statusDot.className = 'status-dot offline';
    statusText.textContent = 'Offline';
  }
}

async function initDb() {
  initDbBtn.disabled = true;
  initDbBtn.textContent = 'Initializing…';
  try {
    const res = await fetch('/api/initialize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ force_reload: false })
    });
    const d = await res.json();
    if (d.error) alert('Error: ' + d.error);
    else { await loadStats(); }
  } catch { alert('Failed to initialize.'); }
  finally {
    initDbBtn.disabled = false;
    initDbBtn.innerHTML = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>Initialize DB`;
  }
}

// ── Event listeners ───────────────────────────────────────────────────────

// Send
sendBtn.addEventListener('click', () => {
  const q = chatInput.value.trim();
  if (q) { sendQuestion(q); chatInput.value = ''; autoResize(); charCount.textContent = '0'; }
});

chatInput.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    const q = chatInput.value.trim();
    if (q) { sendQuestion(q); chatInput.value = ''; autoResize(); charCount.textContent = '0'; }
  }
  if (e.key === 'Escape') { chatInput.value = ''; autoResize(); charCount.textContent = '0'; }
});

chatInput.addEventListener('input', () => {
  autoResize();
  charCount.textContent = chatInput.value.length;
});

function autoResize() {
  chatInput.style.height = 'auto';
  chatInput.style.height = Math.min(chatInput.scrollHeight, 140) + 'px';
}

// Sidebar toggle
sidebarToggle.addEventListener('click', () => sidebar.classList.toggle('collapsed'));

// Stats
statsToggle.addEventListener('click', () => {
  statsDrawer.classList.toggle('open');
  if (statsDrawer.classList.contains('open')) loadStats();
});

// Clear
clearChat.addEventListener('click', () => {
  messagesEl.innerHTML = '';
  const card = document.createElement('div');
  card.className = 'welcome-card';
  card.innerHTML = `
    <div class="welcome-om">ॐ</div>
    <h1 class="welcome-title">Hindu Sacred Texts Intelligence</h1>
    <p class="welcome-sub">Powered by RAG · Mixtral 8x7B · FAISS Vector Search</p>
    <div class="welcome-chips">
      <span class="chip">Bhagavad Gita</span>
      <span class="chip">Ramayana</span>
      <span class="chip">Mahabharata</span>
      <span class="chip" id="docCountChip">Loading…</span>
    </div>
    <p class="welcome-desc">Ask questions about characters, verses, philosophical concepts, or the teachings of these sacred epics.</p>`;
  messagesEl.appendChild(card);
  loadStats();
});

// Filter
document.querySelectorAll('.nav-item').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    activeFilter = btn.dataset.val;
    const labels = { '': 'All Texts', 'bhagavad_gita_qa': 'Bhagavad Gita', 'ramayana_verses_comprehensive': 'Ramayana', 'mahabharata_characters': 'Mahabharata' };
    breadcrumbFilter.textContent = labels[activeFilter] || 'All Texts';
  });
});

// Prompts
document.querySelectorAll('.prompt-item').forEach(item => {
  item.addEventListener('click', () => sendQuestion(item.dataset.q));
});

// Verse
verseLookupBtn.addEventListener('click', () => {
  const ch = document.getElementById('verseChapter').value;
  const vs = document.getElementById('verseVerse').value;
  if (!ch || !vs) { alert('Enter both chapter and verse.'); return; }
  lookupVerse(ch, vs);
});

// Modal
modalClose.addEventListener('click', () => verseModal.classList.remove('open'));
verseModal.addEventListener('click', e => { if (e.target === verseModal) verseModal.classList.remove('open'); });
document.addEventListener('keydown', e => { if (e.key === 'Escape') verseModal.classList.remove('open'); });

// Init DB
initDbBtn.addEventListener('click', initDb);

// ── Boot ──────────────────────────────────────────────────────────────────
loadStats();
