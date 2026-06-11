#!/usr/bin/env python
"""Dependency-free API + widget server for the DHIS/NHIS assistant prototype.

Run:
  python api_server.py
Open:
  http://127.0.0.1:8018
API:
  GET  /api/ask?q=...
  POST /api/ask {"question":"...", "debug":false, "use_model":false}
  GET  /api/estimate?q=...
  GET  /api/faq?q=...
  GET  /api/sources
  GET  /api/feedback/export
  POST /api/feedback {"feedback_label":"Wrong topic", "question":"...", "result":{...}}
  GET  /api/health
"""
from __future__ import annotations
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
from pathlib import Path
import json
import os
import sys

ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT / "src"))

from ask_router import ask
from retrieve_estimate import retrieve
from faq_retriever import answer_faq, load_faq_index
from load_sources import load_sources
from feedback_logger import append_feedback, read_feedback_rows, export_feedback_csv
from model_orchestrator import get_openai_status

DEBUG_HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>NHIS Estimate + FAQ Assistant Prototype</title>
<style>
:root {
  --blue:#075290; --blue-dark:#063b67; --light:#f4f8fb; --border:#d8e3ec;
  --text:#1f2933; --muted:#52616f; --good:#0b6b3a; --warn:#965f00; --bg:#ffffff;
}
* { box-sizing: border-box; }
body { font-family: Arial, Helvetica, sans-serif; margin: 0; background: #f7fafc; color: var(--text); }
a { color: #075290; }
.header { background: var(--blue); color: white; padding: 1.1rem 1.25rem; border-bottom: 4px solid #0d7fc2; }
.header h1 { margin:0; font-size: 1.35rem; }
.header p { margin:.35rem 0 0; opacity:.95; }
.wrap { max-width: 1120px; margin: 1.25rem auto; padding: 0 1rem 2rem; }
.grid { display:grid; grid-template-columns: 1.05fr .95fr; gap:1rem; align-items:start; }
@media (max-width: 880px) { .grid { grid-template-columns: 1fr; } }
.card { background: var(--bg); border: 1px solid var(--border); border-radius: 14px; padding: 1rem; margin-bottom: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,.05); }
.card h2 { font-size: 1rem; margin: 0 0 .55rem; }
textarea { width: 100%; min-height: 112px; font-size: 16px; padding: .8rem; border: 1px solid #b9c7d3; border-radius: 10px; resize: vertical; }
button { background: var(--blue); color: white; border: 0; border-radius: 8px; padding: .65rem 1rem; font-weight: 700; cursor: pointer; }
button:hover { background: var(--blue-dark); }
button.secondary { background:#445b6f; }
button.feedback { background:#e8f1f8; color:#093b63; border:1px solid #b8cfdf; font-weight:600; padding:.45rem .55rem; }
button.feedback:hover { background:#d7e9f5; }
input.note { width:100%; padding:.5rem; border:1px solid #b9c7d3; border-radius:8px; margin:.35rem 0 .5rem; }
.controls { display:flex; gap:.75rem; align-items:center; flex-wrap:wrap; margin-top:.75rem; }
.answer { white-space: pre-wrap; background: var(--light); border: 1px solid var(--border); padding: 1rem; border-radius: 10px; line-height: 1.45; min-height: 150px; }
.chips { display:flex; flex-wrap:wrap; gap:.35rem; margin-top:.65rem; }
.chips button { background:#e8f1f8; color:#093b63; border:1px solid #b8cfdf; font-weight:600; padding:.45rem .55rem; }
.small { font-size: 13px; color:var(--muted); }
.status { font-weight:700; margin-bottom:.45rem; display:flex; flex-wrap:wrap; gap:.35rem; }
.pill { display:inline-block; border-radius:999px; padding:.2rem .55rem; font-size:12px; border:1px solid var(--border); background:#fff; }
.pill.ok { color:var(--good); border-color:#9bd0b3; background:#f0fbf5; }
.pill.warn { color:var(--warn); border-color:#e3c17d; background:#fff8e8; }
.source-card { border:1px solid var(--border); border-radius:10px; padding:.75rem; margin:.55rem 0; background:#fff; }
.source-card h3 { margin:0 0 .25rem; font-size:.95rem; }
.source-card p { margin:.35rem 0; }
details { border:1px solid var(--border); border-radius:10px; padding:.7rem .8rem; margin-top:.75rem; background:#fff; }
summary { cursor:pointer; font-weight:700; }
pre { white-space: pre-wrap; word-break: break-word; background:#0f1720; color:#eaf2f8; padding:.75rem; border-radius:8px; max-height:380px; overflow:auto; }
.footer-note { margin-top:1rem; color:var(--muted); font-size:12px; }
</style>
</head>
<body>
<div class="header">
  <h1>NHIS Estimate + FAQ Assistant Prototype</h1>
  <p>Phase 7D: interactive follow-up support + deterministic DHIS estimates + approved NHIS/participant resource retrieval + feedback logging + optional OpenAI polishing.</p>
</div>
<div class="wrap">
  <div class="grid">
    <div>
      <div class="card">
        <h2>Ask a question</h2>
        <textarea id="q" aria-label="Question">What percent of adults had diabetes last year by SVI?</textarea>
        <div class="controls">
          <button onclick="askApi()">Ask</button>
          <button class="secondary" onclick="clearAll()">Clear / reset conversation</button>
          <label class="small"><input type="checkbox" id="debug"> show matched source details</label>
          <label class="small"><input type="checkbox" id="model"> OpenAI polishing if configured</label>
        </div>
        <div class="chips small" aria-label="Example questions">
          <button onclick="setQ('What percent of adults had current asthma last year?')">Adult asthma</button>
          <button onclick="setQ('How many kids got a flu shot last year?')">Child flu shot</button>
          <button onclick="setQ('What percent of adults got a flu shot last year by insurance for people under 65?')">Insurance under 65</button>
          <button onclick="setQ('What percent of gay men had current asthma last year?')">Sexual orientation</button>
          <button onclick="setQ('What is NHIS?')">What is NHIS?</button>
          <button onclick="setQ('Where do I get 2024 NHIS public use files?')">2024 PUF files</button>
          <button onclick="setQ('Why should I participate in NHIS?')">Why participate?</button>
          <button onclick="setQ('Is my information private and secure?')">Privacy</button>
        </div>
      </div>
      <div class="card">
        <div id="meta" class="status small"></div>
        <div id="chatLog" class="small" style="display:none; margin-bottom:.75rem;"></div>
        <div id="answer" class="answer">Answer will appear here. After the first answer, type a follow-up like “What about by sex?” or click one of the suggested follow-up buttons.</div>
        <div class="chips" id="suggestions"></div>
        <details id="whyBox" style="display:none;"><summary>Why this answer?</summary><div id="why"></div></details>
        <details id="debugBox" style="display:none;"><summary>Matched source details / raw JSON</summary><pre id="debugRaw"></pre></details>
      </div>
    </div>
    <div>
      <div class="card">
        <h2>Sources</h2>
        <div id="sources" class="small">Source cards will appear when available.</div>
      </div>
      <div class="card">
        <h2>Feedback checks</h2>
        <p class="small">Click a label to save the current question, answer, source/debug details, and optional note to <code>data/feedback/feedback_log.csv</code>.</p>
        <input id="reviewNote" class="note" placeholder="Optional reviewer note, e.g., should have matched Family income" />
        <div class="chips small">
          <button class="feedback" onclick="tag('Good answer')">Good answer</button>
          <button class="feedback" onclick="tag('Wrong topic match')">Wrong topic</button>
          <button class="feedback" onclick="tag('Wrong subgroup match')">Wrong subgroup</button>
          <button class="feedback" onclick="tag('Bad year logic')">Bad year</button>
          <button class="feedback" onclick="tag('Missing source')">Missing source</button>
          <button class="feedback" onclick="tag('Bad wording')">Bad wording</button>
          <button class="feedback" onclick="tag('Needs review')">Needs review</button>
        </div>
        <p id="tagOut" class="small"></p>
        <p class="small"><a href="/api/feedback/export" target="_blank" rel="noopener noreferrer">Export feedback CSV</a></p>
      </div>
    </div>
  </div>
  <p class="footer-note">Prototype guardrail: estimates come from the local DHIS NHIS Adult/Child Summary Health Statistics files. FAQ answers come from the local approved CDC/NCHS NHIS source index. If a source is not retrieved, the assistant should say so.</p>
</div>
<script>
let lastResult = null;
let conversationId = window.localStorage.getItem('nhis_conversation_id') || null;
let turnCount = 0;
function setQ(q) { document.getElementById('q').value = q; }
function askFollowup(q) { document.getElementById('q').value = q; askApi(); }
function clearAll() {
  conversationId=null; window.localStorage.removeItem('nhis_conversation_id'); turnCount=0;
  document.getElementById('q').value='';
  document.getElementById('answer').textContent='Answer will appear here. After the first answer, type a follow-up like “What about by sex?” or click one of the suggested follow-up buttons.';
  document.getElementById('sources').innerHTML='Source cards will appear when available.';
  document.getElementById('meta').innerHTML=''; document.getElementById('chatLog').style.display='none'; document.getElementById('chatLog').innerHTML='';
  lastResult=null; document.getElementById('whyBox').style.display='none'; document.getElementById('debugBox').style.display='none';
}
function appendTurn(q, data) {
  const log = document.getElementById('chatLog');
  turnCount += 1;
  log.style.display = 'block';
  const resolved = data.resolved_question && data.resolved_question !== data.original_question ? `<div class="small"><b>Resolved as:</b> ${esc(data.resolved_question)}</div>` : '';
  const html = `<div class="source-card"><h3>Turn ${turnCount}</h3><p><b>You:</b> ${esc(q)}</p>${resolved}<p><b>Assistant:</b> ${esc(data.answer || '').slice(0, 900)}${(data.answer || '').length > 900 ? '…' : ''}</p></div>`;
  log.innerHTML = html + log.innerHTML;
}
async function tag(t) {
  if (!lastResult) { document.getElementById('tagOut').textContent = 'Ask a question first, then save feedback.'; return; }
  const note = document.getElementById('reviewNote').value || '';
  const payload = {feedback_label:t, reviewer_note:note, question:document.getElementById('q').value, answer:lastResult.answer || '', result:lastResult};
  try {
    const res = await fetch('/api/feedback', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
    const data = await res.json();
    document.getElementById('tagOut').textContent = data.status === 'ok' ? `Saved feedback: ${t} (${data.feedback_id})` : `Feedback error: ${data.answer || data.status}`;
  } catch(e) { document.getElementById('tagOut').textContent = 'Feedback save failed: ' + e; }
}
function esc(s) { return String(s || '').replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m])); }
function renderSources(cards, citations) {
  const el = document.getElementById('sources');
  const list = (cards && cards.length) ? cards : (citations || []).map(c => ({title:c.title, url:c.url, excerpt:'', score:c.score}));
  if (!list || !list.length) { el.innerHTML = 'No source cards returned.'; return; }
  el.innerHTML = list.map(c => {
    const url = String(c.url || '');
    const linkedTitle = (url.startsWith('http://') || url.startsWith('https://'))
      ? `<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">${esc(c.title || 'Source')}</a>`
      : `${esc(c.title || 'Source')}`;
    return `
    <div class="source-card">
      <h3>${linkedTitle}</h3>
      ${c.excerpt ? `<p>${esc(c.excerpt)}</p>` : ''}
      ${c.source_category ? `<p class="small">source type: ${esc(c.source_category)}</p>` : ''}
      ${c.score !== undefined ? `<p class="small">retrieval score: ${esc(c.score)}</p>` : ''}
    </div>`;
  }).join('');
}
function renderWhy(why) {
  const box = document.getElementById('whyBox');
  const el = document.getElementById('why');
  if (!why || !why.length) { box.style.display='none'; el.innerHTML=''; return; }
  box.style.display='block';
  el.innerHTML = '<ul>' + why.map(w => `<li>${esc(w)}</li>`).join('') + '</ul>';
}

function renderSuggestions(suggestions) {
  const el = document.getElementById('suggestions');
  if (!el) return;
  if (!suggestions || !suggestions.length) { el.innerHTML = ''; return; }
  el.innerHTML = suggestions.map(s => `<button onclick="askFollowup('${esc(s).replace(/'/g, "\\'")}')">${esc(s)}</button>`).join('');
}

async function askApi() {
  const q = document.getElementById('q').value;
  const debug = document.getElementById('debug').checked;
  const use_model = document.getElementById('model').checked;
  document.getElementById('answer').textContent = 'Working...';
  document.getElementById('sources').innerHTML = 'Retrieving sources...';
  const res = await fetch('/api/ask', {
    method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify({question:q, debug:debug, use_model:use_model, conversation_id: conversationId})
  });
  const data = await res.json();
  lastResult = data;
  if (data.conversation_id) { conversationId = data.conversation_id; window.localStorage.setItem('nhis_conversation_id', conversationId); }
  const okClass = data.status === 'ok' ? 'ok' : 'warn';
  document.getElementById('meta').innerHTML = `<span class="pill ${okClass}">status=${esc(data.status || '')}</span><span class="pill">mode=${esc(data.mode || '')}</span>${data.conversation_id ? `<span class="pill">conversation=${esc(data.conversation_id.slice(0,8))}</span>` : ''}${data.resolved_question && data.resolved_question !== data.original_question ? `<span class="pill">resolved follow-up</span>` : ''}`;
  document.getElementById('answer').textContent = data.answer || JSON.stringify(data, null, 2);
  renderSources(data.source_cards, data.citations);
  renderWhy(data.why);
  renderSuggestions(data.suggested_followups);
  appendTurn(q, data);
  const dbg = document.getElementById('debugBox');
  if (debug) { dbg.style.display='block'; document.getElementById('debugRaw').textContent = JSON.stringify(data, null, 2); }
  else { dbg.style.display='none'; document.getElementById('debugRaw').textContent=''; }
}
</script>
</body>
</html>"""

PROD_HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>NHIS Assistant</title>
<style>
:root{--blue:#075290;--blue2:#063b67;--light:#f4f8fb;--border:#d8e3ec;--text:#1f2933;--muted:#52616f;}
*{box-sizing:border-box}body{font-family:Arial,Helvetica,sans-serif;margin:0;background:#f7fafc;color:var(--text)}a{color:var(--blue)}
.header{background:var(--blue);color:#fff;padding:1.2rem 1.4rem;border-bottom:4px solid #0d7fc2}.header h1{margin:0;font-size:1.45rem}.header p{margin:.35rem 0 0;opacity:.95;max-width:900px}
.wrap{max-width:980px;margin:1.25rem auto;padding:0 1rem 2rem}.card{background:#fff;border:1px solid var(--border);border-radius:14px;padding:1rem;margin-bottom:1rem;box-shadow:0 1px 3px rgba(0,0,0,.05)}
textarea{width:100%;min-height:86px;font-size:16px;padding:.8rem;border:1px solid #b9c7d3;border-radius:10px;resize:vertical}button{background:var(--blue);color:#fff;border:0;border-radius:8px;padding:.65rem 1rem;font-weight:700;cursor:pointer}button:hover{background:var(--blue2)}button.secondary{background:#445b6f}.controls,.chips{display:flex;gap:.45rem;align-items:center;flex-wrap:wrap;margin-top:.75rem}.chips button{background:#e8f1f8;color:#093b63;border:1px solid #b8cfdf;font-weight:600;padding:.45rem .55rem}.answer{white-space:pre-wrap;background:var(--light);border:1px solid var(--border);padding:1rem;border-radius:10px;line-height:1.45;min-height:140px}.small{font-size:13px;color:var(--muted)}.pill{display:inline-block;border-radius:999px;padding:.2rem .55rem;font-size:12px;border:1px solid var(--border);background:#fff;margin-right:.3rem}.source-card{border:1px solid var(--border);border-radius:10px;padding:.75rem;margin:.55rem 0;background:#fff}.source-card h3{margin:0 0 .25rem;font-size:.95rem}.source-card p{margin:.35rem 0}details{border:1px solid var(--border);border-radius:10px;padding:.7rem .8rem;margin-top:.75rem;background:#fff}summary{cursor:pointer;font-weight:700}.footer-note{margin-top:1rem;color:var(--muted);font-size:12px}
</style></head>
<body><div class="header"><h1>NHIS Assistant</h1><p>Ask about NHIS adult/child Summary Health Statistics estimates, data files, participation, privacy, or how NHIS data are used.</p></div>
<div class="wrap"><div class="card"><textarea id="q" aria-label="Question" placeholder="Ask a question, e.g., What percent of adults had diabetes last year by SVI?"></textarea><div class="controls"><button onclick="askApi()">Ask</button><button class="secondary" onclick="clearConversation()">Start over</button><label class="small"><input type="checkbox" id="model"> Use GPT-style wording if configured</label></div><div class="chips small"><button onclick="setQ('What percent of adults had diabetes last year?')">Adult diabetes</button><button onclick="setQ('What about by SVI?')">Follow-up: by SVI</button><button onclick="setQ('What percent of kids got a flu shot last year?')">Child flu shot</button><button onclick="setQ('Why should I participate in NHIS?')">Why participate?</button><button onclick="setQ('Is my information private and secure?')">Privacy</button><button onclick="setQ('Where do I get the 2024 public use files?')">2024 files</button></div></div><div class="card"><div id="meta" class="small"></div><div id="answer" class="answer">Answer will appear here. You can ask follow-up questions like “What about by sex?” or “Show last 2 years.”</div><div class="chips" id="suggestions"></div><details id="whyBox" style="display:none"><summary>Why this answer?</summary><div id="why"></div></details></div><div class="card"><h2 style="font-size:1rem;margin:0 0 .5rem">Sources</h2><div id="sources" class="small">Sources will appear when available.</div></div><p class="footer-note">Draft production UI. Estimates come from the current DHIS NHIS adult/child Summary Health Statistics files. If an estimate is not available, the assistant should say so and provide relevant NHIS resources.</p></div>
<script>
let conversationId=localStorage.getItem('nhis_conversation_id')||null;
function esc(s){return String(s||'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));}
function setQ(q){document.getElementById('q').value=q;}
function askFollowup(q){setQ(q);askApi();}
function clearConversation(){conversationId=null;localStorage.removeItem('nhis_conversation_id');document.getElementById('q').value='';document.getElementById('answer').textContent='Answer will appear here. You can ask follow-up questions like “What about by sex?” or “Show last 2 years.”';document.getElementById('sources').innerHTML='Sources will appear when available.';document.getElementById('suggestions').innerHTML='';document.getElementById('meta').innerHTML='';document.getElementById('whyBox').style.display='none';}
function renderSources(cards,citations){const el=document.getElementById('sources');const list=(cards&&cards.length)?cards:(citations||[]); if(!list.length){el.innerHTML='No source cards returned.';return;} el.innerHTML=list.map(c=>{const url=String(c.url||'');const title=esc(c.title||url||'Source');const link=url.startsWith('http')?`<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">${title}</a>`:title;return `<div class="source-card"><h3>${link}</h3>${c.excerpt?`<p>${esc(c.excerpt)}</p>`:''}</div>`}).join('');}
function renderWhy(why){const box=document.getElementById('whyBox'),el=document.getElementById('why'); if(!why||!why.length){box.style.display='none';return;} box.style.display='block';el.innerHTML='<ul>'+why.map(w=>`<li>${esc(w)}</li>`).join('')+'</ul>';}
function renderSuggestions(s){const el=document.getElementById('suggestions'); if(!s||!s.length){el.innerHTML='';return;} el.innerHTML=s.map(x=>`<button onclick="askFollowup('${esc(x).replace(/'/g,"\\'")}')">${esc(x)}</button>`).join('');}
async function askApi(){const q=document.getElementById('q').value;document.getElementById('answer').textContent='Working...';const res=await fetch('/api/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:q,debug:false,use_model:document.getElementById('model').checked,conversation_id:conversationId})});const data=await res.json();if(data.conversation_id){conversationId=data.conversation_id;localStorage.setItem('nhis_conversation_id',conversationId)}document.getElementById('meta').innerHTML=`<span class="pill">${esc(data.mode||'')}</span><span class="pill">${esc(data.status||'')}</span>${data.resolved_question&&data.resolved_question!==data.original_question?'<span class="pill">follow-up resolved</span>':''}`;document.getElementById('answer').textContent=data.answer||JSON.stringify(data,null,2);renderSources(data.source_cards,data.citations);renderWhy(data.why);renderSuggestions(data.suggested_followups);}
</script></body></html>"""

EMBED_HTML = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>NHIS Assistant Embed</title>
<style>body{font-family:Arial,Helvetica,sans-serif;margin:0;background:#fff;color:#1f2933}.widget{border:1px solid #d8e3ec;border-radius:12px;padding:12px;max-width:760px}textarea{width:100%;min-height:72px;font-size:15px;padding:10px;border:1px solid #b9c7d3;border-radius:8px;box-sizing:border-box}button{background:#075290;color:white;border:0;border-radius:7px;padding:8px 12px;font-weight:700;cursor:pointer}.chips{display:flex;gap:5px;flex-wrap:wrap;margin:8px 0}.chips button{background:#e8f1f8;color:#093b63;border:1px solid #b8cfdf;font-size:12px}.answer{white-space:pre-wrap;background:#f4f8fb;border:1px solid #d8e3ec;border-radius:8px;padding:10px;min-height:100px;line-height:1.4}.small{font-size:12px;color:#52616f}.source{font-size:12px;margin-top:8px}.source a{color:#075290}</style></head>
<body><div class="widget"><textarea id="q" placeholder="Ask an NHIS question..."></textarea><div style="margin-top:8px"><button onclick="askApi()">Ask</button> <button onclick="clearConversation()" style="background:#445b6f">Start over</button></div><div id="answer" class="answer" style="margin-top:10px">Answer will appear here.</div><div class="chips" id="suggestions"></div><div id="sources" class="source"></div></div>
<script>let conversationId=localStorage.getItem('nhis_embed_conversation_id')||null;function esc(s){return String(s||'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));}function askFollowup(q){document.getElementById('q').value=q;askApi();}function clearConversation(){conversationId=null;localStorage.removeItem('nhis_embed_conversation_id');document.getElementById('q').value='';document.getElementById('answer').textContent='Answer will appear here.';document.getElementById('suggestions').innerHTML='';document.getElementById('sources').innerHTML='';}function renderSuggestions(s){document.getElementById('suggestions').innerHTML=(s||[]).slice(0,4).map(x=>`<button onclick="askFollowup('${esc(x).replace(/'/g,"\\'")}')">${esc(x)}</button>`).join('');}function renderSources(cards){const list=cards||[];document.getElementById('sources').innerHTML=list.slice(0,3).map(c=>{const u=String(c.url||'');return u.startsWith('http')?`<div><a href="${esc(u)}" target="_blank" rel="noopener noreferrer">${esc(c.title||'Source')}</a></div>`:''}).join('');}async function askApi(){const q=document.getElementById('q').value;document.getElementById('answer').textContent='Working...';const res=await fetch('/api/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:q,debug:false,use_model:false,conversation_id:conversationId})});const data=await res.json();if(data.conversation_id){conversationId=data.conversation_id;localStorage.setItem('nhis_embed_conversation_id',conversationId)}document.getElementById('answer').textContent=data.answer||'No answer returned.';renderSuggestions(data.suggested_followups);renderSources(data.source_cards);}</script></body></html>"""


def _json_response(handler: BaseHTTPRequestHandler, code: int, payload: dict):
    body = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.end_headers()
    handler.wfile.write(body)


def _text_response(handler: BaseHTTPRequestHandler, code: int, text: str, content_type: str = "text/plain; charset=utf-8", filename: str | None = None):
    body = text.encode("utf-8")
    handler.send_response(code)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    if filename:
        handler.send_header("Content-Disposition", f'attachment; filename="{filename}"')
    handler.end_headers()
    handler.wfile.write(body)


class Handler(BaseHTTPRequestHandler):
    def _html(self, code: int, html: str):
        body = html.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        _json_response(self, 200, {"ok": True})

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0") or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        try:
            return json.loads(raw)
        except Exception:
            return {}

    def do_GET(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        q = (qs.get("q") or [""])[0]
        debug = (qs.get("debug") or ["0"])[0].lower() in {"1", "true", "yes"}
        use_model = (qs.get("use_model") or ["0"])[0].lower() in {"1", "true", "yes"}

        if parsed.path in {"/", "/index.html", "/prod", "/prod.html"}:
            return self._html(200, PROD_HTML)
        if parsed.path in {"/debug", "/debug.html"}:
            return self._html(200, DEBUG_HTML)
        if parsed.path in {"/embed", "/embed.html", "/iframe", "/iframe.html"}:
            return self._html(200, EMBED_HTML)
        if parsed.path == "/api/health":
            return _json_response(self, 200, {"status": "ok", "service": "dhis_nhis_assistant", "phase": "7e_prod_embed_router_qc_ready"})
        if parsed.path == "/api/sources":
            return _json_response(self, 200, {"estimate_sources": load_sources(), "faq_sources": load_faq_index()})
        if parsed.path == "/api/openai/status":
            return _json_response(self, 200, {"status": "ok", "openai": get_openai_status(requested=use_model)})
        if parsed.path == "/api/feedback/export":
            return _text_response(self, 200, export_feedback_csv(), content_type="text/csv; charset=utf-8", filename="feedback_log.csv")
        if parsed.path == "/api/feedback":
            limit = int((qs.get("limit") or ["100"])[0] or "100")
            return _json_response(self, 200, {"status": "ok", "rows": read_feedback_rows(limit=limit)})
        if parsed.path == "/api/ask":
            return _json_response(self, 200, ask(q, debug=debug, use_model=use_model, conversation_id=(qs.get("conversation_id") or [None])[0], reset_context=(qs.get("reset_context") or ["0"])[0].lower() in {"1", "true", "yes"}))
        if parsed.path == "/api/estimate":
            return _json_response(self, 200, retrieve(q, debug=debug))
        if parsed.path == "/api/faq":
            return _json_response(self, 200, answer_faq(q, debug=debug))
        return _json_response(self, 404, {"status": "error", "answer": "Not found"})

    def do_POST(self):
        parsed = urlparse(self.path)
        payload = self._read_json()
        q = str(payload.get("question") or payload.get("q") or "")
        debug = bool(payload.get("debug", False))
        use_model = bool(payload.get("use_model", False))
        if parsed.path == "/api/ask":
            return _json_response(self, 200, ask(q, debug=debug, use_model=use_model, conversation_id=payload.get("conversation_id"), reset_context=bool(payload.get("reset_context", False))))
        if parsed.path == "/api/estimate":
            return _json_response(self, 200, retrieve(q, debug=debug))
        if parsed.path == "/api/faq":
            return _json_response(self, 200, answer_faq(q, debug=debug))
        if parsed.path == "/api/feedback":
            return _json_response(self, 200, append_feedback(payload))
        return _json_response(self, 404, {"status": "error", "answer": "Not found"})


def run_server() -> None:
    """Run the lightweight HTTP server.

    Railway and most public hosts provide the listening port in the PORT
    environment variable and require binding to 0.0.0.0. For local work, this
    still defaults to 127.0.0.1:8018.
    """
    host = os.environ.get("HOST", "127.0.0.1")
    if os.environ.get("RAILWAY_ENVIRONMENT") or os.environ.get("PORT"):
        host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8018"))
    public_url = os.environ.get("RAILWAY_PUBLIC_DOMAIN")
    display_url = f"https://{public_url}" if public_url else f"http://{host}:{port}"
    print(f"Serving DHIS/NHIS Phase 7E prod/embed API + participant resources at {display_url}", flush=True)
    print(f"Health check: {display_url}/api/health", flush=True)
    ThreadingHTTPServer((host, port), Handler).serve_forever()


if __name__ == "__main__":
    run_server()
