"""Render the catalog to a single self-contained static HTML page.

Design: a transit **departure board** — free AI opportunities are departures,
deadlines are boarding times, the top AI labs are operators. On top of the board
the page gives a true beginner an on-ramp: a "Start here" itinerary, relevance-
sorted sections (fundamentals first), clickable topic + cost filters, level
chips, and split learn-vs-compete deadline boards. Two pages are generated:
index.html (live) and archive.html (departed). Single file each, no server.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from .models import Resource

_TYPE_ORDER = [
    "course", "tutorial", "video", "book",
    "tool", "dataset", "paper", "community", "newsletter", "article", "event", "other",
]
_TYPE_LABEL = {
    "course": "Courses",
    "tutorial": "Tutorials & guides",
    "video": "Videos & lectures",
    "book": "Books",
    "tool": "Tools & playgrounds",
    "dataset": "Datasets",
    "paper": "Papers",
    "community": "Communities",
    "newsletter": "Newsletters",
    "article": "Articles",
    "event": "Events",
    "other": "Other",
}

_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Free AI · Departure Board — free ways to learn, use & understand AI</title>
<meta name="description" content="A living board of free resources to learn, use and understand AI — with the time-sensitive ones (live cohorts, deadlines, hackathons) flagged so you never find out after they're gone.">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Ctext y='50' font-size='52'%3E%E2%9C%88%EF%B8%8F%3C/text%3E%3C/svg%3E">
<meta property="og:type" content="website">
<meta property="og:title" content="Free AI · Departure Board">
<meta property="og:description" content="Free ways to learn, use and understand AI — catch the time-sensitive ones before they board.">
<meta property="og:image" content="og.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Free AI · Departure Board">
<meta name="twitter:description" content="Free ways to learn, use and understand AI — catch them before they board.">
<meta name="twitter:image" content="og.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  :root {
    --void:#090b10; --panel:#11141d; --panel2:#161a25; --line:#252b3a;
    --ink:#ece7d6; --dim:#8a92a6; --amber:#ffb627; --mint:#5fe3c0;
    --disp:"Space Grotesk",system-ui,sans-serif;
    --mono:"IBM Plex Mono",ui-monospace,Menlo,monospace;
  }
  * { box-sizing:border-box; }
  html { scroll-behavior:smooth; }
  body {
    margin:0; color:var(--ink); font-family:var(--disp); font-size:15px; line-height:1.55;
    background:
      linear-gradient(rgba(120,140,200,.035) 1px, transparent 1px) 0 0/100% 30px,
      radial-gradient(1200px 520px at 50% -10%, rgba(255,182,39,.10), transparent 60%),
      radial-gradient(900px 600px at 100% 110%, rgba(95,227,192,.08), transparent 60%),
      var(--void);
    background-attachment:fixed;
  }
  a { color:inherit; }
  .wrap { max-width:1120px; margin:0 auto; padding:0 22px; }
  .mono { font-family:var(--mono); }
  .eyebrow { font-family:var(--mono); font-size:12px; letter-spacing:.34em; text-transform:uppercase; color:var(--mint); }

  /* ---------- Masthead ---------- */
  header { padding:54px 0 26px; border-bottom:1px solid var(--line); }
  .brandline { display:flex; align-items:center; gap:14px; flex-wrap:wrap; }
  .brandline .rule { flex:1; height:1px; min-width:30px;
    background:repeating-linear-gradient(90deg,var(--line) 0 6px,transparent 6px 12px); }
  .xlink { font-family:var(--mono); font-size:12px; text-decoration:none; color:var(--mint);
    border:1px solid var(--line); border-radius:6px; padding:5px 11px; white-space:nowrap; transition:.14s; }
  .xlink:hover { border-color:var(--mint); background:rgba(95,227,192,.08); }
  h1 { font-weight:700; font-size:clamp(26px,4.4vw,46px); line-height:1.02; letter-spacing:-.02em;
    margin:18px 0 4px; max-width:16ch; }
  h1 .em { color:var(--amber); }
  .lede { color:var(--dim); max-width:56ch; margin:0 0 30px; }
  .readout { display:grid; grid-template-columns:auto auto auto; gap:14px; align-items:end; }
  .cell .k { font-family:var(--mono); font-size:11px; letter-spacing:.28em; text-transform:uppercase; color:var(--dim); }
  .cell .v { font-family:var(--mono); font-weight:700; line-height:1; }
  .cell.date .v { font-size:clamp(38px,8.5vw,76px); color:var(--amber); text-shadow:0 0 26px rgba(255,182,39,.35); }
  .cell.small .v { font-size:clamp(20px,3vw,30px); color:var(--ink); padding-bottom:6px; }
  .flap { display:inline-block; transform-origin:50% 100%; }

  /* ---------- Filters: operators + topics + cost ---------- */
  .filters { padding:26px 0 4px; }
  .filters .grp { margin-top:14px; }
  .filters .glabel { font-family:var(--mono); font-size:11px; letter-spacing:.28em; text-transform:uppercase; color:var(--dim); margin-bottom:9px; }
  .chiprow { display:flex; flex-wrap:wrap; gap:8px; }
  .op, .top { cursor:pointer; font-family:var(--mono); font-size:13px; font-weight:600; color:var(--ink);
    background:var(--panel); border:1px solid var(--line); border-radius:6px; padding:6px 12px;
    display:inline-flex; align-items:center; gap:8px; transition:.14s; }
  .op .dot { width:9px; height:9px; border-radius:2px; background:var(--c); box-shadow:0 0 10px var(--c); }
  .op .n, .top .n { color:var(--dim); font-weight:500; }
  .op:hover { border-color:var(--c); transform:translateY(-1px); }
  .op.active { background:var(--c); color:#0a0a0a; border-color:var(--c); }
  .op.active .n { color:rgba(0,0,0,.65); } .op.active .dot { background:#0a0a0a; box-shadow:none; }
  .top.active { background:var(--mint); color:#0a0a0a; border-color:var(--mint); }
  .top.active .n { color:rgba(0,0,0,.6); }

  .toolbar { padding:22px 0 6px; display:flex; gap:10px; align-items:center; flex-wrap:wrap; }
  #q { flex:1; min-width:240px; max-width:520px; font-family:var(--mono); font-size:14px; color:var(--ink);
    background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:11px 14px; }
  #q::placeholder { color:var(--dim); }
  #freeToggle { cursor:pointer; font-family:var(--mono); font-size:13px; color:var(--ink);
    background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:10px 13px; white-space:nowrap; transition:.14s; }
  #freeToggle.active { background:var(--mint); color:#0a0a0a; border-color:var(--mint); }
  .status { font-family:var(--mono); font-size:12.5px; color:var(--dim); padding:6px 0 0; min-height:20px; }
  .status b { color:var(--ink); }
  .status .clear { cursor:pointer; color:var(--amber); border:0; background:none; font-family:var(--mono); font-size:12.5px; padding:0 0 0 10px; }
  .status .clear:hover { text-decoration:underline; }

  /* ---------- Sticky board nav ---------- */
  nav.jump { position:sticky; top:0; z-index:20; margin-top:18px; padding:9px 0;
    background:rgba(9,11,16,.86); backdrop-filter:blur(10px);
    border-top:1px solid var(--line); border-bottom:1px solid var(--line); }
  nav.jump .row { display:flex; flex-wrap:wrap; gap:6px; }
  nav.jump a { font-family:var(--mono); font-size:12.5px; text-decoration:none; color:var(--dim);
    border:1px solid transparent; border-radius:6px; padding:4px 10px; white-space:nowrap; }
  nav.jump a:hover { color:var(--ink); border-color:var(--line); }
  nav.jump a.board { color:var(--amber); } nav.jump a.path { color:var(--mint); }
  nav.jump a .nb { opacity:.6; margin-left:5px; }

  section.sec { padding-top:40px; scroll-margin-top:60px; }
  .sechead { display:flex; align-items:baseline; gap:12px; }
  .sechead .ix { font-family:var(--mono); font-size:12px; color:var(--mint); letter-spacing:.2em; }
  .sechead h2 { font-size:21px; font-weight:600; margin:0; letter-spacing:-.01em; }
  .sechead .sub { font-family:var(--mono); font-size:12px; color:var(--dim); }
  .sechead .ct { font-family:var(--mono); font-size:12px; color:var(--dim); margin-left:auto; }

  /* ---------- Start-here itinerary (signature on-ramp) ---------- */
  .route { margin-top:16px; border:1px solid var(--line); border-radius:12px; overflow:hidden;
    background:linear-gradient(180deg,rgba(95,227,192,.07),var(--panel)); }
  .stop { display:grid; grid-template-columns:54px 1fr auto; gap:16px; align-items:center;
    padding:15px 18px; text-decoration:none; border-bottom:1px solid var(--line); transition:background .14s; position:relative; }
  .stop:last-child { border-bottom:0; }
  .stop:hover { background:rgba(95,227,192,.06); }
  .stop .num { font-family:var(--mono); font-weight:700; font-size:20px; color:var(--mint);
    border:1px solid var(--mint); border-radius:50%; width:40px; height:40px; display:grid; place-items:center; }
  .stop .body .st { font-weight:600; font-size:16px; }
  .stop .body .why { color:var(--dim); font-size:13.5px; margin-top:3px; }
  .stop .go { font-family:var(--mono); font-size:12px; color:var(--mint); opacity:0; transition:.14s; }
  .stop:hover .go { opacity:1; }
  .stop.disabled { opacity:.5; cursor:default; }
  .stop.disabled .num { border-style:dashed; color:var(--dim); border-color:var(--dim); }
  .legend { display:flex; flex-wrap:wrap; gap:16px; margin-top:12px; font-family:var(--mono); font-size:11.5px; color:var(--dim); }
  .more { margin-top:12px; }
  .more > summary { cursor:pointer; font-family:var(--mono); font-size:12.5px; color:var(--dim); padding:8px 0; list-style:none; }
  .more > summary::before { content:"▸ "; } .more[open] > summary::before { content:"▾ "; }
  .more > summary:hover { color:var(--ink); }
  .more .grid { margin-top:8px; }

  /* ---------- Departure board ---------- */
  .board { margin-top:16px; border:1px solid var(--line); border-radius:10px; overflow:hidden;
    background:linear-gradient(180deg,var(--panel2),var(--panel)); }
  .board .head, .brow { display:grid; grid-template-columns:1fr 132px 92px; gap:14px; align-items:start; padding:12px 16px; }
  .board .head { font-family:var(--mono); font-size:10.5px; letter-spacing:.22em; text-transform:uppercase;
    color:var(--dim); border-bottom:1px solid var(--line); background:rgba(0,0,0,.25); align-items:center; }
  .brow { border-bottom:1px solid var(--line); text-decoration:none; transition:background .14s; transform-origin:50% 0; }
  .brow:last-child { border-bottom:0; } .brow:hover { background:rgba(255,182,39,.06); }
  .brow .dest .t { font-weight:600; font-size:15.5px; }
  .brow .bdesc { font-family:var(--mono); font-size:11.5px; color:var(--dim); margin-top:5px; line-height:1.5; }
  .brow .dep { font-family:var(--mono); font-size:13px; color:var(--ink); padding-top:2px; }
  .brow .cd { font-family:var(--mono); font-size:12px; font-weight:700; text-align:center; color:#0a0a0a;
    background:var(--amber); border-radius:5px; padding:5px 0; }
  .brow .cd.soon { background:#ff6b5e; color:#fff; } .brow .cd.past { background:#2a313e; color:var(--dim); }

  /* ---------- Tickets ---------- */
  .grid { display:grid; gap:13px; margin-top:16px; grid-template-columns:repeat(auto-fill,minmax(300px,1fr)); }
  .grid.feat { grid-template-columns:repeat(auto-fill,minmax(260px,1fr)); }
  .card { position:relative; background:var(--panel); border:1px solid var(--line); border-radius:10px;
    padding:15px 16px; transition:transform .14s, border-color .14s, box-shadow .14s; overflow:hidden; }
  .card:hover { transform:translateY(-3px); border-color:var(--mint); box-shadow:0 14px 34px rgba(0,0,0,.4); }
  .card.feat { background:linear-gradient(165deg, color-mix(in srgb,var(--c) 16%, var(--panel)), var(--panel)); }
  .card.feat::before { content:""; position:absolute; inset:0 auto 0 0; width:3px; background:var(--c); }
  .row1 { display:flex; flex-wrap:wrap; gap:6px; align-items:center; margin-bottom:9px; }
  .opx { display:inline-block; font-family:var(--mono); font-size:10.5px; font-weight:700; letter-spacing:.06em; padding:2px 8px; border-radius:5px; }
  .cost { font-family:var(--mono); font-size:11px; font-weight:700; letter-spacing:.05em; padding:2px 7px; border-radius:5px; }
  .cost.free { background:rgba(95,227,192,.16); color:var(--mint); }
  .cost.acct { background:#222836; color:var(--dim); }
  .cost.freemium { background:rgba(255,182,39,.16); color:var(--amber); }
  .lvl { font-family:var(--mono); font-size:11px; font-weight:700; letter-spacing:.05em; padding:2px 7px; border-radius:5px;
    background:rgba(124,156,255,.16); color:#9fb4ff; }
  .newb { font-family:var(--mono); font-size:11px; font-weight:700; letter-spacing:.08em; color:#0a0a0a;
    background:var(--mint); border-radius:5px; padding:2px 7px; box-shadow:0 0 14px rgba(95,227,192,.45); }
  .curated { font-family:var(--mono); font-size:11px; font-weight:700; letter-spacing:.05em; padding:2px 7px;
    border-radius:5px; border:1px solid rgba(95,227,192,.5); color:var(--mint); }
  .card a.t { font-weight:600; font-size:15.5px; text-decoration:none; letter-spacing:-.01em; }
  .card:hover a.t { color:var(--mint); }
  .card .meta { font-family:var(--mono); font-size:11.5px; color:var(--dim); margin-top:6px; letter-spacing:.02em; }
  .card .meta .dep { color:var(--amber); }
  .card .desc { font-size:13.5px; color:#c6cdda; margin-top:8px; }
  .card .why { font-family:var(--mono); font-size:11.5px; color:var(--dim); margin-top:8px; padding-left:10px; border-left:2px solid var(--line); }
  .card .tags { margin-top:10px; display:flex; gap:6px; flex-wrap:wrap; }
  .tag { font-family:var(--mono); font-size:11px; color:var(--dim); border:1px solid var(--line);
    border-radius:5px; padding:1px 7px; cursor:pointer; transition:.12s; }
  .tag:hover { color:var(--mint); border-color:var(--mint); }
  .empty { color:var(--dim); font-family:var(--mono); text-align:center; padding:48px; }
  footer { border-top:1px solid var(--line); margin-top:48px; padding:26px 0; color:var(--dim); font-family:var(--mono); font-size:12px; }

  @media (max-width:680px){
    .readout { grid-template-columns:1fr 1fr; } .cell.date { grid-column:1 / -1; }
    .board .head { display:none; }
    .brow { grid-template-columns:1fr 70px; gap:8px 12px; }
    .brow .dep { grid-column:1; } .brow .cd { grid-column:2; grid-row:1; align-self:start; }
    .stop { grid-template-columns:40px 1fr; } .stop .go { display:none; }
  }
  @media (prefers-reduced-motion:reduce){ .flap,.brow,.card:hover::after{animation:none!important} .sec.reveal{opacity:1;transform:none} }
  :focus-visible { outline:2px solid var(--mint); outline-offset:2px; }

  /* card shine + reveal */
  .sec.reveal { opacity:0; transform:translateY(22px); transition:opacity .55s ease, transform .55s ease; }
  .sec.reveal.in { opacity:1; transform:none; }
  @keyframes flipcd { 0%,100%{transform:rotateX(0)} 50%{transform:rotateX(90deg)} }
  .card::after { content:""; position:absolute; top:0; left:-65%; width:48%; height:100%;
    background:linear-gradient(100deg,transparent,rgba(255,255,255,.08),transparent); transform:skewX(-16deg); pointer-events:none; }
  .card:hover::after { animation:shine .7s ease; }
  @keyframes shine { to{left:135%} }

  /* Printable: flatten to a readable list with URLs (#3) */
  @media print {
    body { background:#fff; color:#000; }
    nav.jump, .filters, .toolbar, .status, footer, .legend, .more, .stop .go, .card::after { display:none !important; }
    .sec.reveal { opacity:1 !important; transform:none !important; }
    .card, .brow, .stop { break-inside:avoid; border:1px solid #bbb; background:#fff; color:#000; }
    .card a.t, .brow .dest .t, .stop .st { color:#000; }
    a[href^="http"]::after { content:" — " attr(href); font-size:9px; color:#666; word-break:break-all; }
  }
  .noscript { padding:18px 22px; font-family:var(--mono); font-size:13.5px; color:var(--ink); }
  .noscript ol { margin:10px 0 0; padding-left:22px; } .noscript a { color:var(--mint); }
</style>
</head>
<body>
<header><div class="wrap">
  <div class="brandline"><span class="eyebrow">Free AI · Departure Board</span>
    <span class="rule"></span><a class="xlink" id="xlink" href="__XHREF__">__XTEXT__</a></div>
  <h1>Catch free AI <span class="em">before it leaves the gate.</span></h1>
  <p class="lede">Built after we found a great free course the week <em>after</em> it closed — so here the
    time-sensitive ones board first and nothing good slips by unseen. New to AI? Take the 5-stop route below.</p>
  <div class="readout">
    <div class="cell date"><div class="k">Board updated</div><div class="v" id="datev"></div></div>
    <div class="cell small"><div class="k">On board</div><div class="v">__COUNT__</div></div>
    <div class="cell small"><div class="k">Boarding soon</div><div class="v" id="soonv">—</div></div>
  </div>
</div></header>

<noscript><div class="noscript wrap">__NOSCRIPT__</div></noscript>

<div class="filters"><div class="wrap">
  <div class="grp"><div class="glabel">Learn by topic</div><div class="chiprow" id="topics"></div></div>
  <div class="grp" id="opsgrp"><div class="glabel">Operators · top AI labs</div><div class="chiprow" id="ops"></div></div>
</div></div>

<div class="toolbar wrap">
  <input id="q" placeholder="search the board…">
  <button id="freeToggle">◇ 100% free only</button>
</div>
<div class="status wrap" id="status"></div>

<nav class="jump"><div class="wrap"><div class="row" id="nav"></div></div></nav>

<main class="wrap" id="list"></main>
<div class="empty wrap" id="empty" style="display:none">No departures match. Clear the filters to see the full board.</div>
<footer><div class="wrap">free-yolo · open data · the board refreshes daily, scouts the web weekly.</div></footer>

<script>
const DATA = __DATA__;
const TODAY = "__TODAY__";
const MODE = "__MODE__";
const TYPE_ORDER = __TYPE_ORDER__;
const TYPE_LABEL = __TYPE_LABEL__;

const BRANDS = [
  {key:'anthropic',      label:'Anthropic',      color:'#d97757', match:['anthropic'],               top:true},
  {key:'deeplearningai', label:'DeepLearning.AI', color:'#f43f5e', match:['deeplearning'],            top:true},
  {key:'huggingface',    label:'Hugging Face',   color:'#ffd21e', match:['hugging face','huggingface'], top:true},
  {key:'openai',         label:'OpenAI',         color:'#10a37f', match:['openai'],                  top:true},
  {key:'google',         label:'Google',         color:'#4285f4', match:['google','deepmind','kaggle'], top:true},
  {key:'microsoft',      label:'Microsoft',      color:'#3bb1ff', match:['microsoft'],               top:true},
  {key:'meta',           label:'Meta',           color:'#0866ff', match:['meta'],                    top:true},
  {key:'nvidia',         label:'NVIDIA',         color:'#76b900', match:['nvidia'],                  top:true},
  {key:'stanford',       label:'Stanford',       color:'#b1322f', match:['stanford'],                top:false},
  {key:'mit',            label:'MIT',            color:'#c2415a', match:['mit'],                     top:false},
  {key:'fastai',         label:'fast.ai',        color:'#9a6bff', match:['fast.ai'],                 top:false},
];
function brandFor(p){ p=(p||'').toLowerCase(); return BRANDS.find(b=>b.match.some(m=>p.includes(m)))||null; }
const esc = s => (s||'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const onDark = hex => { const n=parseInt(hex.slice(1),16),l=(0.299*(n>>16)+0.587*((n>>8)&255)+0.114*(n&255)); return l>150?'#0a0a0a':'#fff'; };
function days(d){ return Math.round((new Date(d)-new Date(TODAY))/86400000); }

// level + cost helpers (#5, #3)
const ADV=['fine-tuning','mlops','evals','agents','rag'];
function levelOf(r){ if((r.topics||[]).includes('fundamentals')) return 'Beginner';
  if((r.topics||[]).some(t=>ADV.includes(t))) return 'Intermediate'; return ''; }
function costBadge(r){ const c=r.cost||'free';
  if(c==='free') return '<span class="cost free">FREE</span>';
  if(c==='free-account') return '<span class="cost acct">FREE · SIGN-UP</span>';
  return '<span class="cost freemium">FREEMIUM</span>'; }

// "new this week" (#8 freshness) — found_at first-seen, excluding the catalog birth day
// Baseline = the bulk-import day (most common found_at); only items added AFTER it
// (and within 7 days) count as new — robust to multiple import days, not just the min.
const _fc={}; DATA.forEach(r=>{ if(r.found_at) _fc[r.found_at]=(_fc[r.found_at]||0)+1; });
const BASELINE = (Object.entries(_fc).sort((a,b)=>b[1]-a[1]||a[0].localeCompare(b[0]))[0]||[''])[0];
function isNew(r){ return MODE!=='archive' && r.found_at && r.found_at > BASELINE
  && Math.round((new Date(TODAY)-new Date(r.found_at))/86400000) <= 7; }

// recurring hint from notes (#6/#8)
function recurs(r){ const n=(r.notes||'').toLowerCase();
  return /(recur|twice a year|next cohort|watch |~nov|~spring|annual|monthly)/.test(n); }

const esc2 = s => esc(s).replace(/\n/g,' ');
function opTag(br){ return br?`<span class="opx" style="background:${br.color};color:${onDark(br.color)}">${esc(br.label)}</span>`:''; }

// ---------- card / row renderers ----------
function dataAttrs(r){
  const br=brandFor(r.provider);
  const blob=(r.title+' '+r.provider+' '+r.description+' '+(r.topics||[]).join(' ')).toLowerCase();
  return `data-s="${esc(blob)}" data-brand="${br?br.key:''}" data-topics="${esc((r.topics||[]).join(' '))}" data-cost="${esc(r.cost||'free')}"`;
}

function boardRow(r){
  const br=brandFor(r.provider), n=days(r.event_date);
  const cd = MODE==='archive' ? (Math.abs(n)+'d ago') : (n<=0?'NOW':('T-'+n+'d'));
  const cdcls = MODE==='archive' ? 'past' : (n<=10?'soon':'');
  const why = r.notes ? esc2(r.notes) : esc2(r.description);
  const cur = r.source==='seed' ? ' <span class="curated">✦ curated</span>' : '';
  const tail = (recurs(r) ? ' <span class="opx" style="background:#222836;color:#9fb4ff">↻ recurs</span>' : '') + cur;
  return `<a class="brow card" href="${esc(r.url)}" target="_blank" rel="noopener" ${dataAttrs(r)} aria-label="${esc(r.title)} — departs ${r.event_date}, ${cd}">
    <span class="dest"><span class="t">${esc(r.title)}</span> ${opTag(br)} ${costBadge(r)}${tail}
      ${why?`<span class="bdesc">${why}</span>`:''}</span>
    <span class="dep">${r.event_date}</span>
    <span class="cd ${cdcls}">${cd}</span>
  </a>`;
}

function ticket(r,feat){
  const br=brandFor(r.provider), lvl=levelOf(r);
  const dep=r.event_date?(MODE==='archive'
    ? ` · <span class="dep">departed ${r.event_date}</span>`
    : ` · <span class="dep">DEP ${r.event_date} · T-${Math.max(0,days(r.event_date))}d</span>`):'';
  const added=isNew(r)?` · added ${r.found_at}`:'';   // only when it actually signals freshness (#2)
  const meta=[(!br&&r.provider)?esc(r.provider.toUpperCase()):'', r.type.toUpperCase()].filter(Boolean).join(' · ')+dep+added;
  const tags=(r.topics||[]).map(t=>`<span class="tag" data-topic="${esc(t)}">${esc(t)}</span>`).join('');
  const style=(feat&&br)?` style="--c:${br.color}"`:'';
  const cur=r.source==='seed'?'<span class="curated">✦ curated</span>':'';
  const row1=[isNew(r)?'<span class="newb">NEW</span>':'', cur, opTag(br), costBadge(r), lvl?`<span class="lvl">${lvl}</span>`:''].filter(Boolean).join(' ');
  const why=(r.event_date&&r.notes)?`<div class="why">${esc2(r.notes)}</div>`:'';
  return `<div class="card ${feat?'feat':''}"${style} ${dataAttrs(r)}>
    <div class="row1">${row1}</div>
    <a class="t" href="${esc(r.url)}" target="_blank" rel="noopener">${esc(r.title)}</a>
    <div class="meta">${meta}</div>
    ${(!feat&&r.description)?`<div class="desc">${esc(r.description)}</div>`:''}
    ${why}
    ${tags?`<div class="tags">${tags}</div>`:''}
  </div>`;
}

// ---------- #1 Start-here itinerary (curated order, #8) ----------
const PATH=[
  {name:'Elements of AI',                  match:['elements of ai'],               why:'No code, no math — just understand what AI is and is not.'},
  {name:'3Blue1Brown — Neural Networks',   match:['3blue1brown'],                  why:'See, visually, how a neural network actually works.'},
  {name:'Google ML Crash Course',          match:['machine learning crash course'],why:'Your first hands-on ML, right in the browser.'},
  {name:'Hugging Face LLM Course',         match:['llm course'],                   why:'Cross from AI user to AI builder with language models.'},
  {name:'Practical Deep Learning (fast.ai)', match:['practical deep learning','course.fast'], why:'Build and ship real models, code-first.'},
];
// Always render the full intended ladder; missing stops become disabled placeholders (#8).
const pathStops=PATH.map(p=>{ const r=DATA.find(x=>p.match.some(m=>(x.title+' '+x.url).toLowerCase().includes(m)));
  return r ? {r,why:p.why} : {placeholder:true,name:p.name,why:p.why}; });

// ---------- #6 split dated board into learn vs compete ----------
function isCompete(r){ return /(hackathon|agenthack|xprize|competition|playground|kaggle competitions|devpost|hack )/i.test(r.title+' '+r.url+' '+(r.provider||'')); }
const dated=DATA.filter(r=>r.event_date);
const bySoon=(a,b)=> MODE==='archive' ? b.event_date.localeCompare(a.event_date) : a.event_date.localeCompare(b.event_date);
const learnDates=dated.filter(r=>!isCompete(r)).slice().sort(bySoon);
const competeDates=dated.filter(isCompete).slice().sort(bySoon);
// "Boarding soon" = dated items actually closing within 2 weeks (#2), not all dated.
const soonCount = MODE==='archive' ? dated.length
  : dated.filter(r=>{const n=days(r.event_date); return n>=0 && n<=14;}).length;
const _soonEl=document.getElementById('soonv'); _soonEl.textContent=soonCount||'0';
if(MODE!=='archive' && soonCount>0) _soonEl.style.color='#ff6b5e';

// ---------- #2 relevance sort ----------
function relevance(a,b){
  const fa=(a.topics||[]).includes('fundamentals'), fb=(b.topics||[]).includes('fundamentals');
  if(fa!==fb) return fa?-1:1;
  const sa=a.source==='seed'?0:1, sb=b.source==='seed'?0:1;   // curated leads, feed chatter sinks (#4)
  if(sa!==sb) return sa-sb;
  const ca=a.cost==='free'?0:1, cb=b.cost==='free'?0:1;
  if(ca!==cb) return ca-cb;
  return a.title.localeCompare(b.title);
}

// featured (beginner-leaning: prefer fundamentals among seed picks)
const FEATURED_ORDER=['google','openai','anthropic','huggingface','microsoft','meta','deeplearningai','nvidia'];
const RANK={course:0,tutorial:1,tool:2,video:3,book:4};
const featured=[];
for(const k of FEATURED_ORDER){
  const it=DATA.filter(r=>{const b=brandFor(r.provider);return b&&b.key===k&&r.source==='seed'&&r.type!=='event';}).sort(relevance);
  featured.push(...it.slice(0,2));
}
const fresh=DATA.filter(isNew).sort((a,b)=>b.found_at.localeCompare(a.found_at)).slice(0,24);

// ---------- assemble sections ----------
const sections=[];
if(MODE!=='archive' && pathStops.length) sections.push({id:'start',label:'New to AI? Board here first',sub:'a 5-stop route from zero',items:pathStops.map(s=>s.r),kind:'path',stops:pathStops});
if(MODE==='archive'){
  if(dated.length){ // recurring chances first — they come back, watch for the next one (#4)
    const all=learnDates.concat(competeDates).slice().sort((a,b)=>(recurs(b)?1:0)-(recurs(a)?1:0));
    sections.push({id:'board',label:'Departed',items:all,kind:'board'}); }
}else{
  if(learnDates.length)   sections.push({id:'board',label:'Learning deadlines',sub:'cohorts & intensives — catchable now',items:learnDates,kind:'board',cls:'board'});
  if(competeDates.length) sections.push({id:'compete',label:'Compete & build',sub:'hackathons & contests (optional, not step one)',items:competeDates,kind:'board',cls:'board'});
}
if(fresh.length)    sections.push({id:'new',label:'Just added this week',items:fresh,kind:'grid'});
if(featured.length) sections.push({id:'featured',label:'From the top AI labs',items:featured,kind:'feat'});
TYPE_ORDER.forEach(t=>{
  const it=DATA.filter(r=>r.type===t).sort(relevance);
  if(it.length) sections.push({id:'type-'+t,label:TYPE_LABEL[t],items:it,kind:'grid',gate:true});
});

const FIRST_BOARD=(sections.find(s=>s.kind==='board')||{}).id;
const LEGEND='<div class="legend"><span>🟠 boarding</span><span>🔴 ≤10 days</span><span>◇ 100% free</span><span>↻ runs again</span><span>✦ hand-picked</span></div>';
// Untagged OR clickbait-y feed items (emoji / #hashtags / junk markup) read as social noise (#4).
const isNoise=r=>/^rss/.test(r.source||'') && (
  !(r.topics&&r.topics.length) || /\p{Extended_Pictographic}/u.test(r.title)
  || /(^|\s)#\w/.test(r.title) || /[<>]/.test(r.title));

function sectionHTML(s,n){
  const sub=s.sub?`<span class="sub">${esc(s.sub)}</span>`:'';
  const head=`<div class="sechead"><span class="ix">${String(n+1).padStart(2,'0')}</span><h2>${esc(s.label)}</h2>${sub}<span class="ct">${s.items.length}</span></div>`;
  if(s.kind==='path'){
    const stops=s.stops.map((st,i)=>{
      if(st.placeholder){
        return `<div class="stop disabled" aria-label="Stop ${i+1}: ${esc(st.name)} — not free right now, check back">
          <span class="num" aria-hidden="true">${i+1}</span>
          <span class="body"><span class="st">${esc(st.name)} <span class="cost acct">CHECK BACK</span></span><span class="why">${esc(st.why)}</span></span></div>`;
      }
      return `<a class="stop" href="${esc(st.r.url)}" target="_blank" rel="noopener" ${dataAttrs(st.r)} aria-label="Stop ${i+1}: ${esc(st.r.title)}">
        <span class="num" aria-hidden="true">${i+1}</span>
        <span class="body"><span class="st">${esc(st.r.title)} ${costBadge(st.r)}</span><span class="why">${esc(st.why)}</span></span>
        <span class="go" aria-hidden="true">board →</span></a>`;
    }).join('');
    return `<section class="sec reveal" id="${s.id}">${head}<div class="route">${stops}</div></section>`;
  }
  if(s.kind==='board'){
    const dh = MODE==='archive'?'Departed':'Countdown';
    const legend = s.id===FIRST_BOARD ? LEGEND : '';
    return `<section class="sec reveal" id="${s.id}">${head}${legend}
      <div class="board"><div class="head"><span>Destination</span><span>Departs</span><span>${dh}</span></div>
      ${s.items.map(boardRow).join('')}</div></section>`;
  }
  // grid / feat — quality-gate untagged RSS items into a collapsed "More from the feeds" (#1)
  const feat=s.kind==='feat';
  const primary = s.gate ? s.items.filter(r=>!isNoise(r)) : s.items;
  const extra   = s.gate ? s.items.filter(isNoise) : [];
  const grid=`<div class="grid ${feat?'feat':''}">${primary.map(r=>ticket(r,feat)).join('')}</div>`;
  const more=extra.length?`<details class="more"><summary>More from the feeds (${extra.length}) — auto-scouted, untagged</summary>
    <div class="grid">${extra.map(r=>ticket(r,false)).join('')}</div></details>`:'';
  return `<section class="sec reveal" id="${s.id}">${head}${grid}${more}</section>`;
}

document.getElementById('list').innerHTML=sections.map(sectionHTML).join('');
document.getElementById('nav').innerHTML=sections.map(s=>{
  const cls=s.kind==='path'?'path':(s.cls==='board'||s.id==='board'?'board':'');
  return `<a href="#${s.id}" data-sec="${s.id}" class="${cls}">${esc(s.label)}<span class="nb">${s.items.length}</span></a>`;
}).join('');

// ---------- #4 topic chips ----------
const topicCounts={};
DATA.forEach(r=>(r.topics||[]).forEach(t=>topicCounts[t]=(topicCounts[t]||0)+1));
// Order chips as a beginner→advanced learning ladder, not by raw frequency (#6).
const TOPIC_LADDER=['fundamentals','ml-math','deep-learning','computer-vision','nlp','prompting','llm','rag','agents','fine-tuning','mlops','evals','safety','data'];
const topTopics=Object.entries(topicCounts).sort((a,b)=>{
  const ia=TOPIC_LADDER.indexOf(a[0]), ib=TOPIC_LADDER.indexOf(b[0]);
  return (ia<0?99:ia)-(ib<0?99:ib) || b[1]-a[1];
}).slice(0,12);
const TOPIC_HUMAN={fundamentals:'the basics',llm:'large language models',rag:'retrieval (RAG)',agents:'AI agents','ml-math':'math for ML','deep-learning':'deep learning',nlp:'language (NLP)','computer-vision':'vision (images)',prompting:'writing good prompts','fine-tuning':'fine-tuning models',mlops:'running ML in production',evals:'measuring quality',safety:'AI safety',data:'datasets & data'};
document.getElementById('topics').innerHTML=topTopics.map(([t,c])=>
  `<button class="top" data-t="${esc(t)}" title="${esc(TOPIC_HUMAN[t]||t)}">${esc(t)}<span class="n">${c}</span></button>`).join('');

// ---------- operators ----------
const present=BRANDS.filter(b=>b.top).map(b=>({...b,count:DATA.filter(r=>brandFor(r.provider)?.key===b.key).length})).filter(b=>b.count>0);
document.getElementById('ops').innerHTML=present.map(b=>
  `<button class="op" data-b="${b.key}" style="--c:${b.color}"><span class="dot"></span>${esc(b.label)}<span class="n">${b.count}</span></button>`).join('');
// In the archive, keep topic filters (browse the past by subject) — hide only operators (#4).
if(MODE==='archive') document.getElementById('opsgrp').style.display='none';


// ---------- #3 #4 #7 filtering ----------
let activeBrand='', activeTopic='', onlyFree=false;
const q=document.getElementById('q'), empty=document.getElementById('empty'), status=document.getElementById('status');
const TOTAL=DATA.length;
function applyFilter(){
  const term=q.value.toLowerCase(); let total=0;
  document.querySelectorAll('.sec').forEach(sec=>{
    let vis=0;
    sec.querySelectorAll('.card, .stop').forEach(c=>{
      const m=(!term||(c.dataset.s||'').includes(term))
        && (!activeBrand||c.dataset.brand===activeBrand)
        && (!activeTopic||(' '+(c.dataset.topics||'')+' ').includes(' '+activeTopic+' '))
        && (!onlyFree||c.dataset.cost==='free');
      c.style.display=m?'':'none'; if(m)vis++;
    });
    total+=vis; sec.style.display=vis?'':'none';
    const ct=sec.querySelector('.ct'); if(ct)ct.textContent=vis;
    const nav=document.querySelector(`nav a[data-sec="${sec.id}"]`);
    if(nav){nav.style.display=vis?'':'none'; const nb=nav.querySelector('.nb'); if(nb)nb.textContent=vis;}
  });
  empty.style.display=total?'none':'';
  const active=term||activeBrand||activeTopic||onlyFree;
  status.innerHTML = active
    ? `showing <b>${total}</b> of ${TOTAL}<button class="clear" id="clr">✕ clear filters</button>`
    : '';
  const clr=document.getElementById('clr'); if(clr) clr.onclick=resetFilters;
  writeHash();
}
// #3 shareable/bookmarkable filter state in the URL hash
function writeHash(){
  const p=new URLSearchParams();
  if(q.value) p.set('q',q.value);
  if(activeBrand) p.set('brand',activeBrand);
  if(activeTopic) p.set('topic',activeTopic);
  if(onlyFree) p.set('free','1');
  const s=p.toString();
  history.replaceState(null,'', s?('#'+s):(location.pathname+location.search));
}
function parseHash(){
  const p=new URLSearchParams(location.hash.slice(1));
  q.value=p.get('q')||''; activeBrand=p.get('brand')||''; activeTopic=p.get('topic')||''; onlyFree=p.get('free')==='1';
  document.querySelectorAll('.op').forEach(o=>o.classList.toggle('active',o.dataset.b===activeBrand));
  document.querySelectorAll('.top').forEach(o=>o.classList.toggle('active',o.dataset.t===activeTopic));
  document.getElementById('freeToggle').classList.toggle('active',onlyFree);
}
function resetFilters(){
  activeBrand=''; activeTopic=''; onlyFree=false; q.value='';
  document.querySelectorAll('.op,.top').forEach(o=>o.classList.remove('active'));
  document.getElementById('freeToggle').classList.remove('active');
  applyFilter();
}
q.addEventListener('input',applyFilter);
document.getElementById('ops').addEventListener('click',e=>{ const b=e.target.closest('.op'); if(!b)return;
  activeBrand=activeBrand===b.dataset.b?'':b.dataset.b;
  document.querySelectorAll('.op').forEach(o=>o.classList.toggle('active',o.dataset.b===activeBrand)); applyFilter(); });
function setTopic(t){ activeTopic=activeTopic===t?'':t;
  document.querySelectorAll('.top').forEach(o=>o.classList.toggle('active',o.dataset.t===activeTopic)); applyFilter(); }
document.getElementById('topics').addEventListener('click',e=>{ const b=e.target.closest('.top'); if(b)setTopic(b.dataset.t); });
document.getElementById('list').addEventListener('click',e=>{ const t=e.target.closest('.tag'); if(t){e.preventDefault(); setTopic(t.dataset.topic);} });
document.getElementById('freeToggle').addEventListener('click',function(){ onlyFree=!onlyFree; this.classList.toggle('active',onlyFree); applyFilter(); });

// archive framing
if(MODE==='archive'){
  document.querySelector('.eyebrow').textContent='Free AI · Departure Board · Archive';
  document.querySelector('h1').innerHTML='Departed. <span class="em">The chances that already sailed.</span>';
  document.querySelector('.lede').textContent='Free AI opportunities whose deadline has passed — kept for reference.';
  const ks=document.querySelectorAll('.cell .k'); if(ks[1])ks[1].textContent='In archive'; if(ks[2])ks[2].textContent='Departed';
  document.title='Free AI · Departed (Archive)';
  const setMeta=(s,v)=>{const e=document.querySelector(s); if(e)e.setAttribute('content',v);};
  setMeta('meta[property="og:title"]','Free AI · Departed (Archive)');
  setMeta('meta[property="og:description"]','Past free AI opportunities, kept for reference.');
  if(!dated.length){ empty.style.display=''; empty.textContent='Nothing has departed yet — everything on the board is still catchable.'; }
}

// ---------- dynamics ----------
const reduce=matchMedia('(prefers-reduced-motion:reduce)').matches;
const datev=document.getElementById('datev');
TODAY.split('').forEach((ch,i)=>{ const s=document.createElement('span'); s.className='flap'; s.textContent=ch;
  if(!reduce){ s.style.animation='flap .5s cubic-bezier(.2,.8,.2,1) both'; s.style.animationDelay=(i*55)+'ms'; } datev.appendChild(s); });
const _kf=document.createElement('style'); _kf.textContent='@keyframes flap{from{transform:rotateX(-90deg);opacity:0}to{transform:rotateX(0);opacity:1}}'; document.head.appendChild(_kf);

if(!reduce){
  const io=new IntersectionObserver(es=>es.forEach(e=>{ if(e.isIntersecting){ e.target.classList.add('in'); io.unobserve(e.target); } }),{threshold:.06,rootMargin:'0px 0px -8% 0px'});
  document.querySelectorAll('.sec.reveal').forEach(s=>io.observe(s));
}else{ document.querySelectorAll('.sec.reveal').forEach(s=>s.classList.add('in')); }

// #7 solari flip — skip when the lead deadline is urgent so the real number stays readable
const lead=document.querySelector('.brow .cd');
const leadSoon=lead && lead.classList.contains('soon');
if(lead && !reduce && MODE!=='archive' && !leadSoon){
  const orig=lead.textContent; let flipped=false;
  setInterval(()=>{ if(getComputedStyle(lead.closest('.brow')).display==='none') return;
    lead.style.animation='flipcd .55s ease';
    setTimeout(()=>{ flipped=!flipped; lead.textContent=flipped?'BOARD':orig; },270);
    setTimeout(()=>{ lead.style.animation=''; },580);
  },3800);
}

parseHash();
applyFilter();
</script>
</body>
</html>
"""


_NOSCRIPT_PATH = [
    (["elements of ai"], "Elements of AI — what AI is, no code"),
    (["3blue1brown"], "3Blue1Brown — how neural nets work"),
    (["machine learning crash course"], "Google ML Crash Course"),
    (["llm course"], "Hugging Face LLM Course"),
    (["practical deep learning", "course.fast"], "Practical Deep Learning (fast.ai)"),
]


def _noscript(resources: list[Resource]) -> str:
    """A non-blank fallback when JS is off/blocked: the beginner route as plain links."""
    import html as _h
    lis = []
    for matches, name in _NOSCRIPT_PATH:
        hit = next((r for r in resources
                    if any(m in f"{r.title} {r.url}".lower() for m in matches)), None)
        if hit:
            lis.append(f'<li><a href="{_h.escape(hit.url)}">{_h.escape(name)}</a></li>')
    return ("<strong>Free AI Resources.</strong> The full board needs JavaScript for search "
            "and filters. To start your AI journey right now, these are free:<ol>"
            + "".join(lis) + "</ol>")


def render(resources: list[Resource], mode: str = "live",
           xhref: str = "", xtext: str = "") -> str:
    payload = [
        {
            "title": r.title, "url": r.url, "description": r.description,
            "type": r.type, "topics": r.topics, "provider": r.provider,
            "cost": r.cost, "notes": r.notes,
            "event_date": r.event_date, "found_at": r.found_at, "source": r.source,
        }
        for r in resources
    ]
    return (
        _TEMPLATE
        .replace("__TODAY__", date.today().isoformat())
        .replace("__COUNT__", str(len(resources)))
        .replace("__MODE__", mode)
        .replace("__XHREF__", xhref)
        .replace("__XTEXT__", xtext)
        .replace("__NOSCRIPT__", _noscript(resources))
        .replace("__TYPE_ORDER__", json.dumps(_TYPE_ORDER))
        .replace("__TYPE_LABEL__", json.dumps(_TYPE_LABEL, ensure_ascii=False))
        .replace("__DATA__", json.dumps(payload, ensure_ascii=False))
    )


def write(resources: list[Resource], path: Path | str, mode: str = "live",
          xhref: str = "", xtext: str = "") -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render(resources, mode, xhref, xtext))
    return path
