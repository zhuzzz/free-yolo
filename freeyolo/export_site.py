"""Render the catalog to a single self-contained static HTML page.

Design: a transit **departure board** — free AI opportunities are departures,
deadlines are boarding times, the top AI labs are operators. The generation date
is the giant amber board readout; time-sensitive items get a split-flap board
that flaps in on load. Everything else is structured underneath as operator-
badged tickets. Data is embedded as JSON, filtered client-side. Single file,
no server; host on GitHub Pages free.
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
<title>Free AI · Departure Board</title>
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
  .brandline { display:flex; align-items:center; gap:12px; }
  .brandline::after { content:""; flex:1; height:1px;
    background:repeating-linear-gradient(90deg,var(--line) 0 6px,transparent 6px 12px); }
  h1 { font-weight:700; font-size:clamp(26px,4.4vw,46px); line-height:1.02; letter-spacing:-.02em;
    margin:18px 0 4px; max-width:16ch; }
  h1 .em { color:var(--amber); }
  .lede { color:var(--dim); max-width:54ch; margin:0 0 30px; }

  /* readout strip — the generation date is the loudest cell */
  .readout { display:grid; grid-template-columns:auto auto auto; gap:14px; align-items:end; }
  .cell .k { font-family:var(--mono); font-size:11px; letter-spacing:.28em; text-transform:uppercase; color:var(--dim); }
  .cell .v { font-family:var(--mono); font-weight:700; line-height:1; }
  .cell.date .v { font-size:clamp(38px,8.5vw,76px); color:var(--amber);
    text-shadow:0 0 26px rgba(255,182,39,.35); }
  .cell.small .v { font-size:clamp(20px,3vw,30px); color:var(--ink); padding-bottom:6px; }
  .flap { display:inline-block; transform-origin:50% 100%; }

  /* ---------- Operators (brand chips) ---------- */
  .operators { padding:26px 0 4px; }
  .ops { display:flex; flex-wrap:wrap; gap:8px; margin-top:12px; }
  .op { cursor:pointer; font-family:var(--mono); font-size:13px; font-weight:600; color:var(--ink);
    background:var(--panel); border:1px solid var(--line); border-radius:6px; padding:7px 12px;
    display:inline-flex; align-items:center; gap:8px; transition:.14s; }
  .op .dot { width:9px; height:9px; border-radius:2px; background:var(--c); box-shadow:0 0 10px var(--c); }
  .op .n { color:var(--dim); font-weight:500; }
  .op:hover { border-color:var(--c); transform:translateY(-1px); }
  .op.active { background:var(--c); color:#0a0a0a; border-color:var(--c); }
  .op.active .n { color:rgba(0,0,0,.65); }
  .op.active .dot { background:#0a0a0a; box-shadow:none; }

  /* ---------- Search ---------- */
  .toolbar { padding:22px 0 6px; }
  #q { width:100%; max-width:520px; font-family:var(--mono); font-size:14px; color:var(--ink);
    background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:11px 14px; }
  #q::placeholder { color:var(--dim); }

  /* ---------- Sticky board nav ---------- */
  nav.jump { position:sticky; top:0; z-index:20; margin-top:18px; padding:9px 0;
    background:rgba(9,11,16,.86); backdrop-filter:blur(10px);
    border-top:1px solid var(--line); border-bottom:1px solid var(--line); }
  nav.jump .row { display:flex; flex-wrap:wrap; gap:6px; }
  nav.jump a { font-family:var(--mono); font-size:12.5px; text-decoration:none; color:var(--dim);
    border:1px solid transparent; border-radius:6px; padding:4px 10px; white-space:nowrap; }
  nav.jump a:hover { color:var(--ink); border-color:var(--line); }
  nav.jump a.board { color:var(--amber); }
  nav.jump a .nb { opacity:.6; margin-left:5px; }

  section.sec { padding-top:40px; scroll-margin-top:60px; }
  .sechead { display:flex; align-items:baseline; gap:12px; }
  .sechead .ix { font-family:var(--mono); font-size:12px; color:var(--mint); letter-spacing:.2em; }
  .sechead h2 { font-size:21px; font-weight:600; margin:0; letter-spacing:-.01em; }
  .sechead .ct { font-family:var(--mono); font-size:12px; color:var(--dim); }
  .sechead::after { content:""; flex:1; height:1px; background:var(--line); align-self:center; }

  /* ---------- Departure board (signature) ---------- */
  .board { margin-top:16px; border:1px solid var(--line); border-radius:10px; overflow:hidden;
    background:linear-gradient(180deg,var(--panel2),var(--panel)); }
  .board .head, .brow { display:grid; grid-template-columns:88px 1fr 150px 96px; gap:14px; align-items:center;
    padding:11px 16px; }
  .board .head { font-family:var(--mono); font-size:10.5px; letter-spacing:.22em; text-transform:uppercase;
    color:var(--dim); border-bottom:1px solid var(--line); background:rgba(0,0,0,.25); }
  .brow { border-bottom:1px solid var(--line); text-decoration:none; transition:background .14s;
    transform-origin:50% 0; }
  .brow:last-child { border-bottom:0; }
  .brow:hover { background:rgba(255,182,39,.06); }
  .brow .flt { font-family:var(--mono); font-size:13px; color:var(--mint); font-weight:600; }
  .brow .dest { font-weight:600; font-size:15.5px; }
  .brow .dest .opx { font-family:var(--mono); font-size:11px; padding:1px 7px; border-radius:5px;
    margin-left:9px; vertical-align:2px; }
  .brow .dep { font-family:var(--mono); font-size:13px; color:var(--ink); }
  .brow .cd { font-family:var(--mono); font-size:12px; font-weight:700; text-align:center;
    color:#0a0a0a; background:var(--amber); border-radius:5px; padding:5px 0; }
  .brow .cd.soon { background:#ff6b5e; color:#fff; }

  /* ---------- Tickets (card grid) ---------- */
  .grid { display:grid; gap:13px; margin-top:16px; grid-template-columns:repeat(auto-fill,minmax(300px,1fr)); }
  .grid.feat { grid-template-columns:repeat(auto-fill,minmax(260px,1fr)); }
  .card { position:relative; background:var(--panel); border:1px solid var(--line); border-radius:10px;
    padding:15px 16px; transition:transform .14s, border-color .14s, box-shadow .14s; overflow:hidden; }
  .card:hover { transform:translateY(-3px); border-color:var(--mint); box-shadow:0 14px 34px rgba(0,0,0,.4); }
  .card.feat { background:linear-gradient(165deg, color-mix(in srgb,var(--c) 16%, var(--panel)), var(--panel)); }
  .card.feat::before { content:""; position:absolute; inset:0 auto 0 0; width:3px; background:var(--c); }
  .opx { display:inline-block; font-family:var(--mono); font-size:10.5px; font-weight:700; letter-spacing:.06em;
    padding:2px 8px; border-radius:5px; margin-bottom:9px; }
  .card a.t { font-weight:600; font-size:15.5px; text-decoration:none; letter-spacing:-.01em; }
  .card:hover a.t { color:var(--mint); }
  .card .meta { font-family:var(--mono); font-size:11.5px; color:var(--dim); margin-top:6px; letter-spacing:.02em; }
  .card .meta .dep { color:var(--amber); }
  .card .desc { font-size:13.5px; color:#c6cdda; margin-top:8px; }
  .card .tags { margin-top:10px; display:flex; gap:6px; flex-wrap:wrap; }
  .card .tag { font-family:var(--mono); font-size:11px; color:var(--dim); border:1px solid var(--line);
    border-radius:5px; padding:1px 7px; }
  .empty { color:var(--dim); font-family:var(--mono); text-align:center; padding:48px; }
  footer { border-top:1px solid var(--line); margin-top:48px; padding:26px 0; color:var(--dim);
    font-family:var(--mono); font-size:12px; }

  /* ---------- Live departure ticker ---------- */
  .ticker { display:flex; align-items:center; border-bottom:1px solid var(--line);
    background:linear-gradient(180deg,#0c0f16,#0a0c11); font-family:var(--mono); font-size:12.5px;
    height:38px; overflow:hidden; }
  .ticker .clock { flex:none; padding:0 16px; height:100%; display:flex; align-items:center; gap:9px;
    color:var(--amber); border-right:1px solid var(--line); letter-spacing:.08em; font-weight:600; }
  .ticker .clock::before { content:""; width:8px; height:8px; border-radius:50%; background:#ff5a4d;
    box-shadow:0 0 10px #ff5a4d; animation:blink 1.4s steps(2,jump-none) infinite; }
  @keyframes blink { 50%{opacity:.25} }
  .ticker .tk { flex:1; overflow:hidden; white-space:nowrap; -webkit-mask-image:linear-gradient(90deg,transparent,#000 4%,#000 96%,transparent); }
  .tkin { display:inline-block; white-space:nowrap; animation:scroll 48s linear infinite; }
  .tkin .ti { color:var(--dim); margin:0 4px; }
  .tkin .ti em { color:var(--amber); font-style:normal; }
  .tkin i { color:var(--mint); margin:0 15px; font-style:normal; opacity:.55; }
  @keyframes scroll { from{transform:translateX(0)} to{transform:translateX(-50%)} }
  .ticker:hover .tkin { animation-play-state:paused; }

  /* ---------- Scroll reveal ---------- */
  .sec.reveal { opacity:0; transform:translateY(22px); transition:opacity .55s ease, transform .55s ease; }
  .sec.reveal.in { opacity:1; transform:none; }

  /* ---------- Countdown solari flip + card shine ---------- */
  @keyframes flipcd { 0%,100%{transform:rotateX(0)} 50%{transform:rotateX(90deg)} }
  .card::after { content:""; position:absolute; top:0; left:-65%; width:48%; height:100%;
    background:linear-gradient(100deg,transparent,rgba(255,255,255,.08),transparent);
    transform:skewX(-16deg); pointer-events:none; }
  .card:hover::after { animation:shine .7s ease; }
  @keyframes shine { to{left:135%} }

  @media (max-width:680px){
    .readout { grid-template-columns:1fr 1fr; }
    .cell.date { grid-column:1 / -1; }
    .board .head { display:none; }
    .brow { grid-template-columns:1fr 78px; gap:8px 12px; }
    .brow .flt { grid-column:1; } .brow .cd { grid-column:2; grid-row:1 / 3; align-self:center; }
    .brow .dest { grid-column:1; } .brow .dep { grid-column:1; }
  }
  @media (prefers-reduced-motion:reduce){
    .flap,.brow,.tkin,.ticker .clock::before,.card:hover::after{animation:none!important}
    .sec.reveal{opacity:1;transform:none}
  }
  :focus-visible { outline:2px solid var(--mint); outline-offset:2px; }
</style>
</head>
<body>
<div class="ticker">
  <div class="clock" id="clk">--:--:--</div>
  <div class="tk"><div class="tkin" id="tkin"></div></div>
</div>
<header><div class="wrap">
  <div class="brandline"><span class="eyebrow">Free AI · Departure Board</span></div>
  <h1>Catch free AI <span class="em">before it leaves the gate.</span></h1>
  <p class="lede">A living board of free ways to learn, use and understand AI — with the
    time-sensitive ones boarding first, so you never find out after it's gone.</p>
  <div class="readout">
    <div class="cell date"><div class="k">Board updated</div><div class="v" id="datev"></div></div>
    <div class="cell small"><div class="k">On board</div><div class="v">__COUNT__</div></div>
    <div class="cell small"><div class="k">Boarding soon</div><div class="v" id="soonv">—</div></div>
  </div>
</div></header>

<div class="operators"><div class="wrap">
  <span class="eyebrow">Operators · top AI labs</span>
  <div class="ops" id="ops"></div>
</div></div>

<div class="toolbar"><div class="wrap">
  <input id="q" placeholder="search the board…">
</div></div>

<nav class="jump"><div class="wrap"><div class="row" id="nav"></div></div></nav>

<main class="wrap" id="list"></main>
<div class="empty wrap" id="empty" style="display:none">No departures match. Clear the filter to see the full board.</div>
<footer><div class="wrap">free-yolo · open data · the board refreshes daily, scouts the web weekly.</div></footer>

<script>
const DATA = __DATA__;
const TODAY = "__TODAY__";
const TYPE_ORDER = __TYPE_ORDER__;
const TYPE_LABEL = __TYPE_LABEL__;

const BRANDS = [
  {key:'anthropic',      label:'Anthropic',      code:'ANT', color:'#d97757', match:['anthropic'],               top:true},
  {key:'deeplearningai', label:'DeepLearning.AI', code:'DLA', color:'#f43f5e', match:['deeplearning'],            top:true},
  {key:'huggingface',    label:'Hugging Face',   code:'HUG', color:'#ffd21e', match:['hugging face','huggingface'], top:true},
  {key:'openai',         label:'OpenAI',         code:'OAI', color:'#10a37f', match:['openai'],                  top:true},
  {key:'google',         label:'Google',         code:'GOO', color:'#4285f4', match:['google','deepmind','kaggle'], top:true},
  {key:'microsoft',      label:'Microsoft',      code:'MSF', color:'#3bb1ff', match:['microsoft'],               top:true},
  {key:'meta',           label:'Meta',           code:'MET', color:'#0866ff', match:['meta'],                    top:true},
  {key:'nvidia',         label:'NVIDIA',         code:'NVD', color:'#76b900', match:['nvidia'],                  top:true},
  {key:'stanford',       label:'Stanford',       code:'STA', color:'#b1322f', match:['stanford'],                top:false},
  {key:'mit',            label:'MIT',            code:'MIT', color:'#c2415a', match:['mit'],                     top:false},
  {key:'fastai',         label:'fast.ai',        code:'FST', color:'#9a6bff', match:['fast.ai'],                 top:false},
];
function brandFor(p){ p=(p||'').toLowerCase(); return BRANDS.find(b=>b.match.some(m=>p.includes(m)))||null; }
const esc = s => (s||'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const onDark = hex => { const n=parseInt(hex.slice(1),16),l=(0.299*(n>>16)+0.587*((n>>8)&255)+0.114*(n&255)); return l>150?'#0a0a0a':'#fff'; };
function days(d){ return Math.round((new Date(d)-new Date(TODAY))/86400000); }

// ---- giant date as split-flap characters ----
(function(){
  const host=document.getElementById('datev');
  TODAY.split('').forEach((ch,i)=>{
    const s=document.createElement('span'); s.className='flap'; s.textContent=ch;
    s.style.animation='flap .5s cubic-bezier(.2,.8,.2,1) both'; s.style.animationDelay=(i*55)+'ms';
    host.appendChild(s);
  });
})();
const _kf=document.createElement('style');
_kf.textContent='@keyframes flap{from{transform:rotateX(-90deg);opacity:0}to{transform:rotateX(0);opacity:1}}';
document.head.appendChild(_kf);

function opTag(br,cls){ if(!br) return '';
  return `<span class="${cls}" style="background:${br.color};color:${onDark(br.color)}">${br.label}</span>`; }

// ---- departure board rows (signature) ----
function boardRow(r,i){
  const br=brandFor(r.provider), n=days(r.event_date);
  const cd = n<=0?'NOW':('T-'+n+'d');
  const blob=(r.title+' '+r.provider+' '+r.description+' '+(r.topics||[]).join(' ')).toLowerCase();
  const flt=(br?br.code:'OPN')+'·'+String(100+i*37%900).padStart(3,'0');
  return `<a class="brow card" href="${esc(r.url)}" target="_blank" rel="noopener"
     data-s="${esc(blob)}" data-brand="${br?br.key:''}" style="animation:flap .5s cubic-bezier(.2,.8,.2,1) both;animation-delay:${120+i*70}ms">
    <span class="flt">${flt}</span>
    <span class="dest">${esc(r.title)}${opTag(br,'opx')}</span>
    <span class="dep">${r.event_date}</span>
    <span class="cd ${n<=10?'soon':''}">${cd}</span>
  </a>`;
}

function ticket(r,feat){
  const br=brandFor(r.provider);
  const blob=(r.title+' '+r.provider+' '+r.description+' '+(r.topics||[]).join(' ')).toLowerCase();
  const dep=r.event_date?` · <span class="dep">DEP ${r.event_date} · T-${Math.max(0,days(r.event_date))}d</span>`:'';
  const meta=[(!br&&r.provider)?esc(r.provider.toUpperCase()):'', r.type.toUpperCase()].filter(Boolean).join(' · ')+dep;
  const tags=(r.topics||[]).map(t=>`<span class="tag">${esc(t)}</span>`).join('');
  const style=(feat&&br)?` style="--c:${br.color}"`:'';
  return `<div class="card ${feat?'feat':''}"${style} data-s="${esc(blob)}" data-brand="${br?br.key:''}">
    ${opTag(br,'opx')}
    <a class="t" href="${esc(r.url)}" target="_blank" rel="noopener">${esc(r.title)}</a>
    <div class="meta">${meta}</div>
    ${(!feat&&r.description)?`<div class="desc">${esc(r.description)}</div>`:''}
    ${tags?`<div class="tags">${tags}</div>`:''}
  </div>`;
}

// ---- assemble sections ----
const FEATURED_ORDER=['google','openai','anthropic','huggingface','microsoft','meta','deeplearningai','nvidia'];
const RANK={tool:0,course:1,tutorial:2,video:3,book:4};
const featured=[];
for(const k of FEATURED_ORDER){
  const it=DATA.filter(r=>{const b=brandFor(r.provider);return b&&b.key===k&&r.source==='seed'&&r.type!=='event';})
    .sort((a,b)=>(RANK[a.type]??9)-(RANK[b.type]??9));
  featured.push(...it.slice(0,2));
}
const soon=DATA.filter(r=>r.event_date).sort((a,b)=>a.event_date.localeCompare(b.event_date));
document.getElementById('soonv').textContent=soon.length||'0';

const sections=[];
if(soon.length)     sections.push({id:'board',key:'BRD',label:'Boarding soon',items:soon,kind:'board'});
if(featured.length) sections.push({id:'featured',key:'FEA',label:'From the top AI labs',items:featured,kind:'feat'});
TYPE_ORDER.forEach(t=>{
  const it=DATA.filter(r=>r.type===t).sort((a,b)=>a.title.localeCompare(b.title));
  if(it.length) sections.push({id:'type-'+t,key:t.slice(0,3).toUpperCase(),label:TYPE_LABEL[t],items:it,kind:'grid'});
});

function sectionHTML(s,n){
  const head=`<div class="sechead"><span class="ix">${String(n+1).padStart(2,'0')}</span>
    <h2>${esc(s.label)}</h2><span class="ct">${s.items.length}</span></div>`;
  if(s.kind==='board'){
    return `<section class="sec reveal" id="${s.id}">${head}
      <div class="board"><div class="head"><span>Flight</span><span>Destination</span><span>Departs</span><span>Countdown</span></div>
      ${s.items.map((r,i)=>boardRow(r,i)).join('')}</div></section>`;
  }
  return `<section class="sec" id="${s.id}">${head}
    <div class="grid ${s.kind==='feat'?'feat':''}">${s.items.map(r=>ticket(r,s.kind==='feat')).join('')}</div></section>`;
}

document.getElementById('list').innerHTML=sections.map(sectionHTML).join('');
document.getElementById('nav').innerHTML=sections.map(s=>
  `<a href="#${s.id}" data-sec="${s.id}" class="${s.kind==='board'?'board':''}">${esc(s.label)}<span class="nb">${s.items.length}</span></a>`
).join('');

// ---- operators ----
const present=BRANDS.filter(b=>b.top).map(b=>({...b,count:DATA.filter(r=>brandFor(r.provider)?.key===b.key).length})).filter(b=>b.count>0);
document.getElementById('ops').innerHTML=present.map(b=>
  `<button class="op" data-b="${b.key}" style="--c:${b.color}"><span class="dot"></span>${esc(b.label)}<span class="n">${b.count}</span></button>`
).join('');

// ---- filtering ----
let activeBrand='';
const q=document.getElementById('q'), empty=document.getElementById('empty');
function applyFilter(){
  const term=q.value.toLowerCase(); let total=0;
  document.querySelectorAll('.sec').forEach(sec=>{
    let vis=0;
    sec.querySelectorAll('.card').forEach(c=>{
      const m=(!term||c.dataset.s.includes(term))&&(!activeBrand||c.dataset.brand===activeBrand);
      c.style.display=m?'':'none'; if(m)vis++;
    });
    total+=vis; sec.style.display=vis?'':'none';
    const ct=sec.querySelector('.ct'); if(ct)ct.textContent=vis;
    const nav=document.querySelector(`nav a[data-sec="${sec.id}"]`);
    if(nav){nav.style.display=vis?'':'none'; const nb=nav.querySelector('.nb'); if(nb)nb.textContent=vis;}
  });
  empty.style.display=total?'none':'';
}
q.addEventListener('input',applyFilter);
document.getElementById('ops').addEventListener('click',e=>{
  const b=e.target.closest('.op'); if(!b)return;
  activeBrand=activeBrand===b.dataset.b?'':b.dataset.b;
  document.querySelectorAll('.op').forEach(o=>o.classList.toggle('active',o.dataset.b===activeBrand));
  applyFilter();
});

// ---- dynamics ----
const reduce=matchMedia('(prefers-reduced-motion:reduce)').matches;

// live mission clock
const clk=document.getElementById('clk');
(function tick(){ clk.textContent=new Date().toTimeString().slice(0,8); setTimeout(tick,1000); })();

// scrolling departure ticker (content duplicated for a seamless loop)
const tkin=document.getElementById('tkin');
if(soon.length){
  const seg=soon.slice(0,14).map(r=>{ const n=Math.max(0,days(r.event_date)); const br=brandFor(r.provider);
    return `<span class="ti"><b style="color:${br?br.color:'#5fe3c0'}">${esc(br?br.label:'OPEN')}</b> ${esc(r.title)} <em>T-${n}d</em></span>`;
  }).join('<i>✈</i>');
  tkin.innerHTML='<span class="ti" style="color:var(--amber)">▲ NOW BOARDING</span><i>✈</i>'+seg+'<i>✈</i>'
    +'<span class="ti" style="color:var(--amber)">▲ NOW BOARDING</span><i>✈</i>'+seg+'<i>✈</i>';
}else{ document.querySelector('.ticker .tk').innerHTML='<span class="tkin" style="color:var(--dim);padding-left:14px">No departures scheduled — check back after the next scout run.</span>'; }

// scroll-reveal sections
if(!reduce){
  const io=new IntersectionObserver(es=>es.forEach(e=>{ if(e.isIntersecting){ e.target.classList.add('in'); io.unobserve(e.target); } }),{threshold:.06,rootMargin:'0px 0px -8% 0px'});
  document.querySelectorAll('.sec.reveal').forEach(s=>io.observe(s));
}else{ document.querySelectorAll('.sec.reveal').forEach(s=>s.classList.add('in')); }

// periodic solari flip on the most-urgent countdown to draw the eye
const lead=document.querySelector('#board .cd');
if(lead && !reduce){
  const orig=lead.textContent; let flipped=false;
  setInterval(()=>{ if(getComputedStyle(lead.closest('.brow')).display==='none') return;
    lead.style.animation='flipcd .55s ease';
    setTimeout(()=>{ flipped=!flipped; lead.textContent=flipped?'BOARD':orig; },270);
    setTimeout(()=>{ lead.style.animation=''; },580);
  },3800);
}
</script>
</body>
</html>
"""


def render(resources: list[Resource]) -> str:
    active = [r for r in resources if r.status == "active"]
    payload = [
        {
            "title": r.title, "url": r.url, "description": r.description,
            "type": r.type, "topics": r.topics, "provider": r.provider,
            "event_date": r.event_date, "found_at": r.found_at, "source": r.source,
        }
        for r in active
    ]
    return (
        _TEMPLATE
        .replace("__TODAY__", date.today().isoformat())
        .replace("__COUNT__", str(len(active)))
        .replace("__TYPE_ORDER__", json.dumps(_TYPE_ORDER))
        .replace("__TYPE_LABEL__", json.dumps(_TYPE_LABEL, ensure_ascii=False))
        .replace("__DATA__", json.dumps(payload, ensure_ascii=False))
    )


def write(resources: list[Resource], path: Path | str) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render(resources))
    return path
