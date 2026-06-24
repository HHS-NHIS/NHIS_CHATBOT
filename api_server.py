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
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>NHIS Assistant</title>
<style>
:root{--blue:#075290;--blue2:#063b67;--bg:#f6f9fc;--card:#fff;--border:#d8e3ec;--text:#1f2933;--muted:#52616f;--user:#e7f1fb;--assistant:#fff;--chip:#e8f1f8}*{box-sizing:border-box}body{font-family:Arial,Helvetica,sans-serif;margin:0;background:var(--bg);color:var(--text)}a{color:#075290}.top{background:var(--blue);color:white;padding:18px 22px;border-bottom:4px solid #0d7fc2}.top h1{font-size:1.35rem;margin:0}.top p{margin:.35rem 0 0;opacity:.95}.app{max-width:960px;margin:0 auto;height:calc(100vh - 86px);display:flex;flex-direction:column;padding:14px}.notice{font-size:12px;color:var(--muted);background:white;border:1px solid var(--border);border-radius:10px;padding:8px 10px;margin-bottom:10px}.chat{flex:1;overflow-y:auto;background:white;border:1px solid var(--border);border-radius:14px;padding:16px;box-shadow:0 1px 4px rgba(0,0,0,.04)}.msg{display:flex;margin:12px 0;gap:10px}.msg.user{justify-content:flex-end}.bubble{max-width:78%;border:1px solid var(--border);border-radius:14px;padding:11px 13px;line-height:1.45;white-space:pre-wrap}.user .bubble{background:var(--user);border-color:#bdd5ec}.assistant .bubble{background:var(--assistant)}.avatar{width:30px;height:30px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:bold;font-size:12px;background:#e9eef3;color:#334}.user .avatar{order:2;background:#d4e8fa;color:#073b67}.meta{font-size:11px;color:var(--muted);margin-top:6px}.chips{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0 0 40px}.chips button{background:var(--chip);color:#093b63;border:1px solid #b8cfdf;border-radius:999px;padding:7px 10px;font-size:12px;cursor:pointer}.sources{font-size:12px;margin-top:8px;border-top:1px solid #edf2f7;padding-top:7px}.sources a{display:block;margin:3px 0}.composer{background:white;border:1px solid var(--border);border-radius:14px;margin-top:10px;padding:10px;box-shadow:0 1px 4px rgba(0,0,0,.05)}textarea{width:100%;min-height:62px;border:1px solid #b9c7d3;border-radius:10px;padding:10px;font-size:15px;resize:vertical}.controls{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-top:8px}button.primary{background:var(--blue);color:#fff;border:0;border-radius:8px;padding:9px 14px;font-weight:bold;cursor:pointer}button.secondary{background:#445b6f;color:#fff;border:0;border-radius:8px;padding:9px 12px;font-weight:bold;cursor:pointer}.examples{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}.examples button{background:#f3f8fc;color:#093b63;border:1px solid #c9ddeb;border-radius:999px;padding:6px 9px;font-size:12px}.small{font-size:12px;color:var(--muted)}@media(max-width:650px){.app{height:calc(100vh - 112px);padding:8px}.bubble{max-width:88%}.top{padding:14px}.chips{margin-left:0}}
</style></head><body><div class="top"><h1>NHIS Assistant Prototype</h1><p>Natural-language access to NHIS SHS estimates and approved NHIS resources. Estimates remain deterministic and source-controlled.</p></div><main class="app"><div class="notice">V2 local test: GPT-like chat transcript, stronger follow-up context, editable approved-resource index workflow. Use /debug for router details.</div><section id="chat" class="chat" aria-live="polite"></section><section class="composer"><textarea id="q" placeholder="Ask an NHIS question or follow-up..."></textarea><div class="controls"><button class="primary" onclick="askApi()">Ask</button><button class="secondary" onclick="clearConversation()">Start over</button><label class="small"><input type="checkbox" id="model"> OpenAI polishing if configured</label></div><div class="examples"><button onclick="askFollowup('What percent of adults had diabetes last year?')">Adult diabetes</button><button onclick="askFollowup('Why should I participate in NHIS?')">Why participate?</button><button onclick="askFollowup('Is my information private?')">Privacy</button><button onclick="askFollowup('What percent of teens had asthma last year?')">Teen estimate</button></div></section></main><script>
let conversationId=localStorage.getItem('nhis_v2_conversation_id')||null;let turn=0;const chat=document.getElementById('chat');function esc(s){return String(s||'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));}function scrollBottom(){chat.scrollTop=chat.scrollHeight;}function addMsg(role,text,extra=''){const div=document.createElement('div');div.className='msg '+role;div.innerHTML=`<div class="avatar">${role==='user'?'You':'NHIS'}</div><div class="bubble">${esc(text)}${extra}</div>`;chat.appendChild(div);scrollBottom();return div;}function renderSources(cards){const list=(cards||[]).filter(c=>c&&c.url).slice(0,3);if(!list.length)return '';return `<div class="sources"><b>Sources:</b>${list.map(c=>`<a href="${esc(c.url)}" target="_blank" rel="noopener noreferrer">${esc(c.title||c.url)}</a>`).join('')}</div>`}function addSuggestions(s){if(!s||!s.length)return;const div=document.createElement('div');div.className='chips';div.innerHTML=s.slice(0,6).map(x=>`<button onclick="askFollowup('${esc(x).replace(/'/g,"\'")}')">${esc(x)}</button>`).join('');chat.appendChild(div);scrollBottom();}function askFollowup(q){document.getElementById('q').value=q;askApi();}function clearConversation(){conversationId=null;localStorage.removeItem('nhis_v2_conversation_id');turn=0;chat.innerHTML='';document.getElementById('q').value='';addMsg('assistant','Hi — ask me an NHIS estimate question, a participation/resource question, or a follow-up like “tell me more,” “show by SVI,” or “explain the confidence interval.”');}async function askApi(){const q=document.getElementById('q').value.trim();if(!q)return;turn++;addMsg('user',q);document.getElementById('q').value='';const wait=addMsg('assistant','Working...');try{const res=await fetch('/api/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:q,debug:false,use_model:document.getElementById('model').checked,conversation_id:conversationId})});const data=await res.json();if(data.conversation_id){conversationId=data.conversation_id;localStorage.setItem('nhis_v2_conversation_id',conversationId)}const meta=`<div class="meta">${esc(data.mode||'')} · ${esc(data.status||'')}${data.context_resolution&&data.context_resolution.used_followup_context?' · follow-up context used':''}</div>`;wait.querySelector('.bubble').innerHTML=esc(data.answer||JSON.stringify(data,null,2))+meta+renderSources(data.source_cards);addSuggestions(data.suggested_followups);}catch(e){wait.querySelector('.bubble').textContent='Error: '+e;}scrollBottom();}clearConversation();document.getElementById('q').addEventListener('keydown',e=>{if(e.key==='Enter'&&(e.ctrlKey||e.metaKey)){askApi();}});
</script></body></html>"""

EMBED_HTML = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>NHIS Assistant Embed</title><style>body{font-family:Arial,Helvetica,sans-serif;margin:0;background:#fff;color:#1f2933}.widget{height:100vh;display:flex;flex-direction:column;border:1px solid #d8e3ec;border-radius:12px;overflow:hidden}.head{background:#075290;color:#fff;padding:10px 12px;font-weight:bold}.chat{flex:1;overflow-y:auto;padding:10px;background:#f7fafc}.msg{margin:8px 0}.msg.user{text-align:right}.bubble{display:inline-block;text-align:left;max-width:88%;white-space:pre-wrap;background:#fff;border:1px solid #d8e3ec;border-radius:12px;padding:9px 10px;line-height:1.38}.user .bubble{background:#e7f1fb}.composer{border-top:1px solid #d8e3ec;padding:8px;background:#fff}textarea{width:100%;min-height:52px;border:1px solid #b9c7d3;border-radius:8px;padding:8px;font-size:14px;box-sizing:border-box}button{background:#075290;color:white;border:0;border-radius:7px;padding:7px 10px;font-weight:700;cursor:pointer}.chips{display:flex;gap:5px;flex-wrap:wrap;margin-top:6px}.chips button{background:#e8f1f8;color:#093b63;border:1px solid #b8cfdf;font-size:12px}.source{font-size:11px;margin-top:6px}.source a{display:block;color:#075290}</style></head><body><div class="widget"><div class="head">NHIS Assistant</div><div id="chat" class="chat"></div><div class="composer"><textarea id="q" placeholder="Ask an NHIS question..."></textarea><div style="margin-top:6px"><button onclick="askApi()">Ask</button> <button onclick="clearConversation()" style="background:#445b6f">Start over</button></div></div></div><script>let conversationId=localStorage.getItem('nhis_embed_v2_conversation_id')||null;const chat=document.getElementById('chat');function esc(s){return String(s||'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));}function scrollBottom(){chat.scrollTop=chat.scrollHeight;}function add(role,text,extra=''){const d=document.createElement('div');d.className='msg '+role;d.innerHTML=`<span class="bubble">${esc(text)}${extra}</span>`;chat.appendChild(d);scrollBottom();return d;}function sources(cards){const list=(cards||[]).filter(c=>c&&c.url).slice(0,2);return list.length?`<div class="source">${list.map(c=>`<a href="${esc(c.url)}" target="_blank">${esc(c.title||'Source')}</a>`).join('')}</div>`:''}function chips(s){if(!s||!s.length)return;const d=document.createElement('div');d.className='chips';d.innerHTML=s.slice(0,4).map(x=>`<button onclick="askFollowup('${esc(x).replace(/'/g,"\'")}')">${esc(x)}</button>`).join('');chat.appendChild(d);scrollBottom();}function askFollowup(q){document.getElementById('q').value=q;askApi();}function clearConversation(){conversationId=null;localStorage.removeItem('nhis_embed_v2_conversation_id');chat.innerHTML='';document.getElementById('q').value='';add('assistant','Ask me an NHIS question or follow-up.');}async function askApi(){const q=document.getElementById('q').value.trim();if(!q)return;add('user',q);document.getElementById('q').value='';const wait=add('assistant','Working...');try{const res=await fetch('/api/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:q,debug:false,use_model:false,conversation_id:conversationId})});const data=await res.json();if(data.conversation_id){conversationId=data.conversation_id;localStorage.setItem('nhis_embed_v2_conversation_id',conversationId)}wait.querySelector('.bubble').innerHTML=esc(data.answer||'No answer returned.')+sources(data.source_cards);chips(data.suggested_followups);}catch(e){wait.querySelector('.bubble').textContent='Error: '+e;}scrollBottom();}clearConversation();</script></body></html>"""


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
            return _json_response(self, 200, {"status": "ok", "service": "dhis_nhis_assistant", "phase": "v2a_v2b_local_test"})
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
    print(f"Serving DHIS/NHIS V2A/B local test API + participant resources at {display_url}", flush=True)
    print(f"Health check: {display_url}/api/health", flush=True)
    ThreadingHTTPServer((host, port), Handler).serve_forever()


if __name__ == "__main__":
    run_server()
