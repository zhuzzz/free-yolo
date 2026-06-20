"""Render the catalog to a single self-contained static HTML page.

Layout: a bold generation-date hero, a row of brand-colored filter chips for the
top AI labs, a "From the top AI labs" featured band, a sticky category jump-nav,
a "closing soon" band, then one section per resource type. Every card carries a
brand badge when it comes from a recognized lab. Data is embedded as JSON and
filtered client-side. No build step, no server. Host on GitHub Pages free.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from .models import Resource

_TYPE_ORDER = [
    "event", "course", "tutorial", "video", "book",
    "tool", "dataset", "paper", "community", "newsletter", "article", "other",
]
_TYPE_LABEL = {
    "event": "🗓️ Events & live cohorts",
    "course": "🎓 Courses",
    "tutorial": "📝 Tutorials & guides",
    "video": "🎬 Videos & lectures",
    "book": "📚 Books",
    "tool": "🛠️ Tools & playgrounds",
    "dataset": "🗂️ Datasets",
    "paper": "📄 Papers",
    "community": "💬 Communities",
    "newsletter": "📰 Newsletters",
    "article": "🧵 Articles",
    "other": "🔗 Other",
}

_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Free AI Resources</title>
<style>
  :root { --bg:#0a0e14; --card:#161b22; --line:#2a313c; --fg:#e6edf3;
          --muted:#9aa4b2; --accent:#7c9cff; --warn:#f0883e; }
  * { box-sizing:border-box; }
  html { scroll-behavior:smooth; }
  body { margin:0; font:15px/1.55 -apple-system,Segoe UI,Roboto,sans-serif; color:var(--fg);
    background:
      radial-gradient(1100px 500px at 50% -8%, rgba(124,156,255,.18), transparent 60%),
      radial-gradient(900px 500px at 100% 0%, rgba(240,136,62,.10), transparent 55%),
      var(--bg); background-attachment:fixed; }

  /* ---- Hero ---- */
  header { text-align:center; padding:52px 20px 16px; max-width:1100px; margin:0 auto; }
  header h1 { margin:0 0 22px; font-size:clamp(22px,4vw,30px); font-weight:800; letter-spacing:.2px;
    background:linear-gradient(90deg,#fff,#9fb4ff); -webkit-background-clip:text; background-clip:text;
    -webkit-text-fill-color:transparent; }
  .stamp { display:inline-block; border:1px solid rgba(124,156,255,.5); border-radius:18px;
    padding:18px 40px; background:linear-gradient(180deg,rgba(124,156,255,.16),rgba(124,156,255,.05));
    box-shadow:0 8px 40px rgba(124,156,255,.15); }
  .stamp .lbl { font-size:12px; letter-spacing:3px; text-transform:uppercase; color:var(--accent); }
  .stamp .date { display:block; font-size:clamp(34px,7vw,46px); font-weight:900; color:#fff; line-height:1.05; margin-top:4px; }
  .stamp .sub { display:block; font-size:13px; color:var(--muted); margin-top:8px; }

  /* ---- Top-lab brand chips ---- */
  .labs { max-width:1100px; margin:26px auto 0; padding:0 20px; text-align:center; }
  .labs .t { font-size:12px; letter-spacing:2px; text-transform:uppercase; color:var(--muted); margin-bottom:10px; }
  .chips { display:flex; flex-wrap:wrap; gap:9px; justify-content:center; }
  .chip { cursor:pointer; border:1.5px solid var(--c); color:#fff; background:transparent;
    border-radius:22px; padding:7px 15px; font-size:14px; font-weight:600; display:inline-flex;
    align-items:center; gap:7px; transition:.15s; }
  .chip::before { content:""; width:9px; height:9px; border-radius:50%; background:var(--c); }
  .chip:hover { background:color-mix(in srgb, var(--c) 18%, transparent); }
  .chip.active { background:var(--c); color:#fff; }
  .chip.active::before { background:#fff; }
  .chip span { color:var(--muted); font-weight:500; font-size:12px; }
  .chip.active span { color:rgba(255,255,255,.85); }

  .search { max-width:1100px; margin:20px auto 0; padding:0 20px; text-align:center; }
  .search input { width:min(460px,100%); background:var(--card); color:var(--fg);
    border:1px solid var(--line); border-radius:12px; padding:11px 16px; font-size:15px; }

  /* ---- Sticky jump-nav ---- */
  nav.jump { position:sticky; top:0; z-index:10; margin-top:18px;
    background:rgba(10,14,20,.85); backdrop-filter:blur(10px);
    border-top:1px solid var(--line); border-bottom:1px solid var(--line);
    display:flex; flex-wrap:wrap; justify-content:center; gap:6px; padding:10px 14px; }
  nav.jump a { text-decoration:none; color:var(--fg); background:var(--card);
    border:1px solid var(--line); border-radius:20px; padding:5px 12px; font-size:14px; white-space:nowrap; }
  nav.jump a:hover { border-color:var(--accent); }
  nav.jump a .nb { color:var(--muted); font-size:12px; margin-left:5px; }
  nav.jump a.soon { border-color:var(--warn); }
  nav.jump a.featured { border-color:#e3b341; }

  main { max-width:1100px; margin:0 auto; padding:8px 20px 70px; }
  section.sec { scroll-margin-top:66px; padding-top:30px; }
  section.sec h2 { font-size:20px; border-bottom:1px solid var(--line); padding-bottom:9px; }
  section.sec h2 .badge { font-size:13px; color:var(--muted); font-weight:400; }
  .grid { display:grid; gap:13px; grid-template-columns:repeat(auto-fill,minmax(290px,1fr)); }
  .grid.feat { grid-template-columns:repeat(auto-fill,minmax(250px,1fr)); }

  .card { background:var(--card); border:1px solid var(--line); border-radius:12px; padding:14px 16px;
    transition:transform .12s, border-color .12s, box-shadow .12s; }
  .card:hover { transform:translateY(-3px); border-color:var(--accent); box-shadow:0 10px 30px rgba(0,0,0,.35); }
  .card.dated { border-left:3px solid var(--warn); }
  .fcard { background:linear-gradient(180deg, color-mix(in srgb,var(--c) 14%, var(--card)), var(--card));
    border:1px solid color-mix(in srgb,var(--c) 45%, var(--line)); border-top:3px solid var(--c); }
  .bb { display:inline-block; font-size:11px; font-weight:700; padding:2px 9px; border-radius:7px; margin-bottom:7px; }
  .card a.t { color:var(--fg); font-weight:700; text-decoration:none; font-size:15px; }
  .card a.t:hover { color:var(--accent); }
  .card .meta { color:var(--muted); font-size:12.5px; margin:5px 0 0; }
  .card .date { color:var(--warn); font-weight:600; }
  .card .desc { font-size:13.5px; margin:7px 0 0; color:#c9d3e0; }
  .card .tags { margin-top:9px; display:flex; gap:6px; flex-wrap:wrap; }
  .card .tag { background:#21262d; color:var(--muted); border-radius:12px; padding:2px 9px; font-size:11.5px; }
  .empty { color:var(--muted); text-align:center; padding:44px; }
  footer { text-align:center; color:var(--muted); font-size:12px; padding:28px; }
</style>
</head>
<body>
<header>
  <h1>🦾 Free AI Resources — learn, use &amp; understand AI</h1>
  <div class="stamp">
    <span class="lbl">Updated</span>
    <span class="date">__TODAY__</span>
    <span class="sub">__COUNT__ free resources · curated from the top AI labs &amp; the open web</span>
  </div>
</header>

<div class="labs">
  <div class="t">Top AI labs</div>
  <div class="chips" id="chips"></div>
</div>
<div class="search"><input id="q" placeholder="Search across every category…"></div>
<nav class="jump" id="nav"></nav>
<main id="list"></main>
<div class="empty" id="empty" style="display:none">No resources match.</div>
<footer>Generated by free-yolo · data is open, contributions welcome.</footer>

<script>
const DATA = __DATA__;
const TODAY = "__TODAY__";
const TYPE_ORDER = __TYPE_ORDER__;
const TYPE_LABEL = __TYPE_LABEL__;

// Brand registry. Order matters: co-branded providers resolve to the first match
// (e.g. "DeepLearning.AI + OpenAI" → DeepLearning.AI, the host).
const BRANDS = [
  {key:'anthropic',      label:'Anthropic',       color:'#d97757', fg:'#fff', match:['anthropic'],               top:true},
  {key:'deeplearningai', label:'DeepLearning.AI',  color:'#e11d48', fg:'#fff', match:['deeplearning'],            top:true},
  {key:'huggingface',    label:'Hugging Face',     color:'#ffd21e', fg:'#1a1a1a', match:['hugging face','huggingface'], top:true},
  {key:'openai',         label:'OpenAI',           color:'#10a37f', fg:'#fff', match:['openai'],                  top:true},
  {key:'google',         label:'Google',           color:'#4285f4', fg:'#fff', match:['google','deepmind','kaggle'], top:true},
  {key:'microsoft',      label:'Microsoft',        color:'#00a4ef', fg:'#fff', match:['microsoft'],               top:true},
  {key:'meta',           label:'Meta',             color:'#0866ff', fg:'#fff', match:['meta'],                    top:true},
  {key:'nvidia',         label:'NVIDIA',           color:'#76b900', fg:'#1a1a1a', match:['nvidia'],               top:true},
  {key:'stanford',       label:'Stanford',         color:'#8c1515', fg:'#fff', match:['stanford'],                top:false},
  {key:'mit',            label:'MIT',              color:'#a31f34', fg:'#fff', match:['mit'],                     top:false},
  {key:'fastai',         label:'fast.ai',          color:'#8a3ffc', fg:'#fff', match:['fast.ai'],                 top:false},
];
function brandFor(provider) {
  const p = (provider||'').toLowerCase();
  return BRANDS.find(b => b.match.some(m => p.includes(m))) || null;
}

const esc = s => (s||'').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
function daysLabel(d) {
  const n = Math.round((new Date(d) - new Date(TODAY)) / 86400000);
  if (isNaN(n)) return '';
  return n <= 0 ? ' · today' : ' · in ' + n + 'd';
}

function cardHTML(r, feat) {
  const br = brandFor(r.provider);
  const blob = (r.title+' '+r.provider+' '+r.description+' '+(r.topics||[]).join(' ')).toLowerCase();
  const date = r.event_date ? `<span class="date">📅 ${r.event_date}${daysLabel(r.event_date)}</span>` : '';
  const badge = br ? `<span class="bb" style="background:${br.color};color:${br.fg}">${esc(br.label)}</span>` : '';
  const meta = [(!br && r.provider) ? esc(r.provider) : '', r.type, date].filter(Boolean).join(' · ');
  const cls = (feat ? 'fcard card' : 'card') + (r.event_date ? ' dated' : '');
  const style = (feat && br) ? ` style="--c:${br.color}"` : '';
  const tags = (r.topics||[]).map(t => `<span class="tag">${esc(t)}</span>`).join('');
  return `<div class="${cls}"${style} data-s="${esc(blob)}" data-brand="${br?br.key:''}">
    ${badge}
    <a class="t" href="${esc(r.url)}" target="_blank" rel="noopener">${esc(r.title)}</a>
    <div class="meta">${meta}</div>
    ${(!feat && r.description) ? `<div class="desc">${esc(r.description)}</div>` : ''}
    ${tags ? `<div class="tags">${tags}</div>` : ''}
  </div>`;
}

function sectionHTML(s) {
  return `<section class="sec" id="${s.id}">
    <h2>${s.label} <span class="badge">(${s.items.length})</span></h2>
    <div class="grid ${s.feat?'feat':''}">${s.items.map(r => cardHTML(r, s.feat)).join('')}</div>
  </section>`;
}

// ---- Featured band: a couple of flagship picks per top lab (curated seeds) ----
const FEATURED_ORDER = ['google','openai','anthropic','huggingface','microsoft','meta','deeplearningai','nvidia'];
const RANK = {tool:0, course:1, tutorial:2, video:3, book:4};
const featured = [];
for (const k of FEATURED_ORDER) {
  const items = DATA.filter(r => { const b = brandFor(r.provider); return b && b.key === k && r.source === 'seed' && r.type !== 'event'; })
    .sort((a,b) => (RANK[a.type]??9) - (RANK[b.type]??9));
  featured.push(...items.slice(0, 2));
}

const sections = [];
if (featured.length) sections.push({id:'featured', emoji:'⭐', label:'⭐ From the top AI labs', items:featured, feat:true, cls:'featured'});
const soon = DATA.filter(r => r.event_date).sort((a,b) => a.event_date.localeCompare(b.event_date));
if (soon.length) sections.push({id:'soon', emoji:'⏰', label:'⏰ Closing soon', items:soon, cls:'soon'});
for (const t of TYPE_ORDER) {
  const items = DATA.filter(r => r.type === t).sort((a,b) => a.title.localeCompare(b.title));
  if (items.length) sections.push({id:'type-'+t, emoji:TYPE_LABEL[t].split(' ')[0], label:TYPE_LABEL[t], items});
}

document.getElementById('list').innerHTML = sections.map(sectionHTML).join('');
document.getElementById('nav').innerHTML = sections.map(s =>
  `<a href="#${s.id}" data-sec="${s.id}" class="${s.cls||''}" title="${esc(s.label)}">${s.emoji}<span class="nb">${s.items.length}</span></a>`
).join('');

// ---- Top-lab filter chips ----
const present = BRANDS.filter(b => b.top).map(b => ({...b, count: DATA.filter(r => brandFor(r.provider)?.key === b.key).length}))
  .filter(b => b.count > 0);
document.getElementById('chips').innerHTML = present.map(b =>
  `<button class="chip" data-b="${b.key}" style="--c:${b.color}">${esc(b.label)}<span>${b.count}</span></button>`
).join('');

let activeBrand = '';
const q = document.getElementById('q'), empty = document.getElementById('empty');

function applyFilter() {
  const term = q.value.toLowerCase();
  let total = 0;
  for (const sec of document.querySelectorAll('.sec')) {
    let vis = 0;
    for (const card of sec.querySelectorAll('.card')) {
      const m = (!term || card.dataset.s.includes(term)) && (!activeBrand || card.dataset.brand === activeBrand);
      card.style.display = m ? '' : 'none';
      if (m) vis++;
    }
    total += vis;
    sec.style.display = vis ? '' : 'none';
    const b = sec.querySelector('.badge'); if (b) b.textContent = '(' + vis + ')';
    const nav = document.querySelector(`nav a[data-sec="${sec.id}"]`);
    if (nav) { nav.style.display = vis ? '' : 'none'; const nb = nav.querySelector('.nb'); if (nb) nb.textContent = vis; }
  }
  empty.style.display = total ? 'none' : '';
}

q.addEventListener('input', applyFilter);
document.getElementById('chips').addEventListener('click', e => {
  const btn = e.target.closest('.chip'); if (!btn) return;
  const key = btn.dataset.b;
  activeBrand = activeBrand === key ? '' : key;
  for (const c of document.querySelectorAll('.chip')) c.classList.toggle('active', c.dataset.b === activeBrand);
  applyFilter();
});
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
