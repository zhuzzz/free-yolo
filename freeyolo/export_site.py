"""Render the catalog to a single self-contained static HTML page.

Layout: a prominent generation-date stamp, a sticky category jump-nav, a
"closing soon" band for time-sensitive items, then one section per resource
type (cards in a grid) — no flat dump of everything. Data is embedded as JSON
and filtered client-side. No build step, no server. Host on GitHub Pages free.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from .models import Resource

# Section order + display labels (emoji first token is reused in the jump-nav).
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
  :root { --bg:#0d1117; --card:#161b22; --line:#30363d; --fg:#e6edf3;
          --muted:#8b949e; --accent:#58a6ff; --warn:#f0883e; }
  * { box-sizing:border-box; }
  html { scroll-behavior:smooth; }
  body { margin:0; font:15px/1.55 -apple-system,Segoe UI,Roboto,sans-serif;
         background:var(--bg); color:var(--fg); }

  /* ---- Hero: the generation date is the loudest element on the page ---- */
  header { text-align:center; padding:44px 20px 14px; max-width:1040px; margin:0 auto; }
  header h1 { margin:0 0 18px; font-size:23px; font-weight:600; letter-spacing:.3px; }
  .stamp { display:inline-block; border:2px solid var(--accent); border-radius:16px;
           padding:16px 34px; background:rgba(88,166,255,.10); }
  .stamp .lbl { font-size:12px; letter-spacing:2px; text-transform:uppercase; color:var(--accent); }
  .stamp .date { display:block; font-size:34px; font-weight:800; color:#fff; line-height:1.1; margin-top:2px; }
  .stamp .sub { display:block; font-size:13px; color:var(--muted); margin-top:6px; }

  .search { max-width:1040px; margin:18px auto 0; padding:0 20px; text-align:center; }
  .search input { width:min(440px,100%); background:var(--card); color:var(--fg);
    border:1px solid var(--line); border-radius:10px; padding:10px 14px; font-size:15px; }

  /* ---- Sticky category jump-nav ---- */
  nav.jump { position:sticky; top:0; z-index:10; margin-top:16px;
    background:rgba(13,17,23,.94); backdrop-filter:blur(8px);
    border-top:1px solid var(--line); border-bottom:1px solid var(--line);
    display:flex; flex-wrap:wrap; justify-content:center; gap:6px; padding:10px 14px; }
  nav.jump a { text-decoration:none; color:var(--fg); background:var(--card);
    border:1px solid var(--line); border-radius:20px; padding:5px 12px; font-size:14px;
    white-space:nowrap; }
  nav.jump a:hover { border-color:var(--accent); }
  nav.jump a .nb { color:var(--muted); font-size:12px; margin-left:5px; }
  nav.jump a.soon { border-color:var(--warn); }

  main { max-width:1040px; margin:0 auto; padding:8px 20px 64px; }
  section.sec { scroll-margin-top:64px; padding-top:26px; }
  section.sec h2 { font-size:19px; border-bottom:1px solid var(--line); padding-bottom:8px; }
  section.sec h2 .badge { font-size:13px; color:var(--muted); font-weight:400; }
  .grid { display:grid; gap:12px; grid-template-columns:repeat(auto-fill,minmax(290px,1fr)); }

  .card { background:var(--card); border:1px solid var(--line); border-radius:10px; padding:13px 15px; }
  .card.dated { border-left:3px solid var(--warn); }
  .card a.t { color:var(--accent); font-weight:600; text-decoration:none; font-size:15px; }
  .card a.t:hover { text-decoration:underline; }
  .card .meta { color:var(--muted); font-size:12.5px; margin:4px 0; }
  .card .date { color:var(--warn); font-weight:600; }
  .card .desc { font-size:13.5px; margin:6px 0 0; }
  .card .tags { margin-top:8px; display:flex; gap:6px; flex-wrap:wrap; }
  .card .tag { background:#21262d; color:var(--muted); border-radius:12px; padding:2px 9px; font-size:11.5px; }
  .empty { color:var(--muted); text-align:center; padding:40px; }
  footer { text-align:center; color:var(--muted); font-size:12px; padding:26px; }
</style>
</head>
<body>
<header>
  <h1>🦾 Free AI Resources — learn, use & understand AI</h1>
  <div class="stamp">
    <span class="lbl">Updated</span>
    <span class="date">__TODAY__</span>
    <span class="sub">__COUNT__ free resources · time-sensitive ones flagged so you don't miss them</span>
  </div>
</header>
<div class="search"><input id="q" placeholder="Search across every category…"></div>
<nav class="jump" id="nav"></nav>
<main id="list"></main>
<div class="empty" id="empty" style="display:none">No resources match your search.</div>
<footer>Generated by free-yolo · data is open, contributions welcome.</footer>
<script>
const DATA = __DATA__;
const TODAY = "__TODAY__";
const TYPE_ORDER = __TYPE_ORDER__;
const TYPE_LABEL = __TYPE_LABEL__;

const esc = s => (s||'').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

function daysLabel(d) {
  const n = Math.round((new Date(d) - new Date(TODAY)) / 86400000);
  if (isNaN(n)) return '';
  if (n <= 0) return ' · today';
  return ' · in ' + n + 'd';
}

function cardHTML(r) {
  const blob = (r.title+' '+r.provider+' '+r.description+' '+(r.topics||[]).join(' ')).toLowerCase();
  const date = r.event_date ? `<span class="date">📅 ${r.event_date}${daysLabel(r.event_date)}</span>` : '';
  const meta = [r.provider ? esc(r.provider) : '', r.type, date].filter(Boolean).join(' · ');
  const tags = (r.topics||[]).map(t => `<span class="tag">${esc(t)}</span>`).join('');
  return `<div class="card ${r.event_date ? 'dated':''}" data-s="${esc(blob)}">
    <a class="t" href="${esc(r.url)}" target="_blank" rel="noopener">${esc(r.title)}</a>
    <div class="meta">${meta}</div>
    ${r.description ? `<div class="desc">${esc(r.description)}</div>` : ''}
    ${tags ? `<div class="tags">${tags}</div>` : ''}
  </div>`;
}

function sectionHTML(id, label, items) {
  return `<section class="sec" id="${id}">
    <h2>${label} <span class="badge">(${items.length})</span></h2>
    <div class="grid">${items.map(cardHTML).join('')}</div>
  </section>`;
}

// Build the "closing soon" band + one section per type, plus the jump-nav.
const sections = [];
const soon = DATA.filter(r => r.event_date).sort((a,b) => a.event_date.localeCompare(b.event_date));
if (soon.length) sections.push({id:'soon', emoji:'⏰', label:'⏰ Closing soon', items:soon, soon:true});
for (const t of TYPE_ORDER) {
  const items = DATA.filter(r => r.type === t).sort((a,b) => a.title.localeCompare(b.title));
  if (items.length) sections.push({id:'type-'+t, emoji:TYPE_LABEL[t].split(' ')[0], label:TYPE_LABEL[t], items});
}

document.getElementById('list').innerHTML =
  sections.map(s => sectionHTML(s.id, s.label, s.items)).join('');
document.getElementById('nav').innerHTML = sections.map(s =>
  `<a href="#${s.id}" data-sec="${s.id}" class="${s.soon?'soon':''}" title="${esc(s.label)}">${s.emoji}<span class="nb">${s.items.length}</span></a>`
).join('');

// Live search: hide non-matching cards, recompute counts, hide empty sections/nav links.
const q = document.getElementById('q'), empty = document.getElementById('empty');
q.addEventListener('input', () => {
  const term = q.value.toLowerCase();
  let totalVisible = 0;
  for (const sec of document.querySelectorAll('.sec')) {
    let vis = 0;
    for (const card of sec.querySelectorAll('.card')) {
      const m = !term || card.dataset.s.includes(term);
      card.style.display = m ? '' : 'none';
      if (m) vis++;
    }
    totalVisible += vis;
    sec.style.display = vis ? '' : 'none';
    sec.querySelector('.badge').textContent = '(' + vis + ')';
    const nav = document.querySelector(`nav a[data-sec="${sec.id}"]`);
    if (nav) { nav.style.display = vis ? '' : 'none'; nav.querySelector('.nb').textContent = vis; }
  }
  empty.style.display = totalVisible ? 'none' : '';
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
            "event_date": r.event_date, "found_at": r.found_at,
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
