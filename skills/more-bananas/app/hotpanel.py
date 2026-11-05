"""The "Hot & slow" tab: everything that makes a Mac hot, loud or slow, minute by minute today.

memlog.py writes the readings (heat.csv, io.csv, cpu.csv, cpu_apps.csv, live.csv); report.py calls heat_section()
for the panel's HTML and add_heat() to put this tab's CSS and JS into the page.
"""
import datetime as dt
import html
import json
import os

e = html.escape

# One strip per measure. lo/hi: the strip's scale (hi None = fit to the day's readings, at least 1.3 x the line).
# line: the level where it starts to make the Mac hot, loud or slow; anything above it is drawn red.
# words: what the tile says below, at and above the halfway mark and the line.
STRIPS = [
    {"k": "temp", "name": "Chip temperature", "unit": "°C", "lo": 30, "hi": 110, "line": 90, "line_txt": "90 °C: hot",
     "words": ("cool", "warm", "hot"), "mid": 70},
    {"k": "fan", "name": "Fan", "unit": "% of full speed", "lo": 0, "hi": 100, "line": 60, "line_txt": "60%: loud",
     "words": ("quiet", "audible", "loud"), "mid": 35},
    {"k": "cpu", "name": "Processors", "unit": "% busy", "lo": 0, "hi": 100, "line": 85, "line_txt": "85%: flat out",
     "words": ("fine", "busy", "flat out"), "mid": 60},
    {"k": "gpu", "name": "Graphics", "unit": "% busy", "lo": 0, "hi": 100, "line": 85, "line_txt": "85%: flat out",
     "words": ("fine", "busy", "flat out"), "mid": 60},
    {"k": "disk", "name": "Disk reads and writes", "unit": "MB a minute", "lo": 0, "hi": None, "line": 1000,
     "line_txt": "1 GB a minute: heavy", "words": ("fine", "busy", "heavy"), "mid": 300},
    {"k": "swap", "name": "Memory pushed to disk", "unit": "MB a minute", "lo": 0, "hi": None, "line": 100,
     "line_txt": "100 MB a minute: swapping hard", "words": ("calm", "a little", "swapping hard"), "mid": 5},
]
HOT_TEMP, LOUD_FAN = 90, 60   # a minute counts as "ran hot" when the chip reached 90 °C or the fan passed 60%


def _rows(path, ncol):
    try:
        return [l.rstrip("\n").split(",") for l in open(path) if l.count(",") == ncol - 1]
    except OSError:
        return []


def _num(x):
    try:
        v = float(x)
        return v if v >= 0 else None
    except ValueError:
        return None


def _span(minutes):
    h, m = divmod(int(minutes), 60)
    return f"{h} h {m} min" if h else f"{m} min"


def heat_section(home, today):
    """The panel's HTML for the day `today` ("YYYY-MM-DD"), or the last 24 hours early in the morning."""
    by = {s["k"]: {} for s in STRIPS}                     # measure -> {minute stamp: value}; a later row wins
    for r in _rows(os.path.join(home, "cpu.csv"), 4):
        by["cpu"][r[0]] = _num(r[1])
    state = {}                                            # macOS's own heat level: nominal / fair / serious / critical
    for r in _rows(os.path.join(home, "heat.csv"), 6):
        by["temp"][r[0]] = _num(r[4])
        if r[1]:
            state[r[0]] = r[1]
        rpm, top = _num(r[2]), _num(r[3])
        by["fan"][r[0]] = min(rpm / top * 100, 100) if rpm is not None and top else None
        by["gpu"][r[0]] = _num(r[5])
    for r in _rows(os.path.join(home, "io.csv"), 5):
        a, b = _num(r[1]), _num(r[2])
        by["disk"][r[0]] = (a or 0) + (b or 0) if a is not None or b is not None else None
    for r in _rows(os.path.join(home, "live.csv"), 6):
        by["swap"][r[0]] = _num(r[1])
    apps = {}
    for r in _rows(os.path.join(home, "cpu_apps.csv"), 3):
        x = _num(r[2])
        if x is not None:
            apps.setdefault(r[0], {})[r[1]] = x

    stamps = sorted(set().union(*[set(d) for d in by.values()]))
    if not stamps:
        return ""
    day = [t for t in stamps if t[:10] == today]
    if len(day) < 60:                                      # early morning: show the last 24 hours instead
        end = dt.datetime.strptime(stamps[-1], "%Y-%m-%d %H:%M")
        day = [t for t in stamps if dt.datetime.strptime(t, "%Y-%m-%d %H:%M") > end - dt.timedelta(hours=24)]
    t0 = dt.datetime.strptime(day[0], "%Y-%m-%d %H:%M")
    n = int((dt.datetime.strptime(day[-1], "%Y-%m-%d %H:%M") - t0).total_seconds() // 60) + 1
    minute = [(t0 + dt.timedelta(minutes=i)).strftime("%Y-%m-%d %H:%M") for i in range(n)]
    series = {s["k"]: [by[s["k"]].get(t) for t in minute] for s in STRIPS}

    # ---- the strips: one SVG, shared time axis. Drawn twice: wide for laptops, narrow (short labels) for phones ----
    for s in STRIPS:
        seen = [x for x in series[s["k"]] if x is not None]
        s["top"] = s["hi"] if s["hi"] is not None else max(max(seen, default=0) * 1.1, s["line"] * 1.3)

    def draw(W, SH, GAP, TOP, tag, wide):
        X = (lambda i: i * W / (n - 1)) if n > 1 else (lambda i: W / 2)
        svg, clips = [], []
        for j, s in enumerate(STRIPS):
            k, vals, lo, hi = s["k"], series[s["k"]], s["lo"], s["top"]
            y0 = TOP + j * (SH + GAP)                      # top of this strip; its label sits in the gap above
            Y = (lambda v, y0=y0, lo=lo, hi=hi: y0 + SH - (min(max(v, lo), hi) - lo) * SH / (hi - lo))
            ly = Y(s["line"])
            runs, cur, last = [], [], -9                   # runs of readings; a gap of more than 3 minutes breaks the line
            for i, x in enumerate(vals):
                if x is None:
                    continue
                if i - last > 3 and cur:
                    runs.append(cur); cur = []
                cur.append((i, x)); last = i
            if cur:
                runs.append(cur)
            cid = f"hz{tag}-{k}"
            clips.append(f'<clipPath id={cid}><rect x=-5 y={y0 - 8} width={W + 10} height={ly - y0 + 8:.1f} /></clipPath>')
            unit = f' <tspan class=hu>{e(s["unit"])}</tspan>' if wide else ""
            g = [f'<g class=hs data-k={k}>', f'<text class=hl x=0 y={y0 - 10}><tspan class=hn>{e(s["name"])}</tspan>{unit}</text>',
                 f'<rect class=hb x=0 y={y0} width={W} height={SH} rx=8 />']
            for run in runs:
                pts = " ".join(f"{X(i):.1f},{Y(x):.1f}" for i, x in run)
                area = f"{X(run[0][0]):.1f},{y0 + SH} {pts} {X(run[-1][0]):.1f},{y0 + SH}"
                g += [f'<polygon class=ha points="{area}"/>', f'<polyline class=hline points="{pts}"/>',
                      f'<polygon class=hhot points="{area}" clip-path="url(#{cid})"/>',
                      f'<polyline class=hlhot points="{pts}" clip-path="url(#{cid})"/>']
            if not runs:
                g.append(f'<text class=hnone x={W / 2} y={y0 + SH / 2 + 5} text-anchor=middle>{"No readings yet: this Mac has not reported it." if wide else "no readings yet"}</text>')
            elif runs[0][0][0] > 30:                       # the measure started later than the window
                g.append(f'<text class=hnone x={X(runs[0][0][0]) - 6:.1f} y={y0 + SH - 8} text-anchor=end>{"measured " if wide else ""}from {minute[runs[0][0][0]][11:]}</text>')
            line_txt = "dotted line: " + s["line_txt"] if wide else s["line_txt"].split(":")[0]
            g.append(f'<line class=hthr x1=0 x2={W} y1={ly:.1f} y2={ly:.1f} /><text class=htk x={W - 2} y={y0 - 10} text-anchor=end>{e(line_txt)}</text></g>')
            svg += g
        H = TOP + len(STRIPS) * (SH + GAP) - GAP
        every = max(n // (6 if wide else 3), 1)
        ticks = "".join(f'<text class=htk x="{X(i):.1f}" y="{H + 20}" text-anchor="{"start" if i == 0 else "end" if i == n - 1 else "middle"}">{minute[i][11:] if minute[0][:10] == minute[-1][:10] else minute[i][5:10].replace("-", "/") + " " + minute[i][11:]}</text>'
                        for i in sorted({0, n - 1, *range(0, n, every)}) if i == n - 1 or n - 1 - i > n / (14 if wide else 6))
        return (f'<svg class="hstrips {"hwide" if wide else "hnarrow"}" data-w={W} viewBox="0 0 {W} {H + 30}" role=img '
                f'aria-label="Chip temperature, fan speed, processor and graphics load, disk traffic and memory pushed to disk, minute by minute">'
                f'{"".join(clips)}{"".join(svg)}{ticks}<line class=hxh x1=0 x2=0 y1=0 y2={H} /></svg>')

    strips = draw(1000, 62, 40, 26, "w", True) + draw(420, 54, 34, 22, "n", False)

    # ---- right now: the last reading of each measure ----
    def now(k):
        for x in reversed(series[k]):
            if x is not None:
                return x
        return None

    def word(s, x):
        return s["words"][2] if x >= s["line"] else s["words"][1] if x >= s["mid"] else s["words"][0]

    def fmt(s, x):
        return f'{x:.0f}<small>°C</small>' if s["k"] == "temp" else f'{x:.0f}<small>%</small>' if s["unit"].startswith("%") else f'{x:,.0f}<small> MB/min</small>'

    state_now = next((state[t] for t in reversed(minute) if t in state), "")
    tiles = []
    for s in STRIPS:
        x = now(s["k"])
        if x is None:
            tiles.append(f'<div class="ht c"><span class=htn>{e(s["name"])}</span><b>–</b><span class="hw">not reported</span></div>')
            continue
        lvl = 2 if x >= s["line"] else 1 if x >= s["mid"] else 0
        w = word(s, x)
        if s["k"] == "temp" and state_now in ("serious", "critical"):   # macOS itself is slowing the Mac to cool it
            lvl, w = 2, f"{w}; macOS is slowing it down"
        elif s["k"] == "temp" and state_now == "fair":
            lvl, w = max(lvl, 1), f"{w}; macOS is starting to hold back"
        tiles.append(f'<div class="ht c" data-lvl={lvl}><span class=htn>{e(s["name"])}</span><b>{fmt(s, x)}</b>'
                     f'<span class=hw><i></i>{e(w)}</span></div>')

    # ---- headline: how long it ran hot today ----
    hot = [i for i in range(n) if (series["temp"][i] or 0) >= HOT_TEMP or (series["fan"][i] or 0) >= LOUD_FAN]
    flat = [i for i in range(n) if (series["cpu"][i] or 0) >= 85]
    has_heat = any(x is not None for x in series["temp"] + series["fan"])
    when = "Today" if minute[0][:10] == minute[-1][:10] else "In the last 24 hours"
    if has_heat and hot:
        head = f"{when} it ran <em>hot</em> for {_span(len(hot))}"
    elif has_heat:
        head = f"{when} it has stayed <em>cool</em>"
    else:
        head = f"{when} the processors were <em>flat out</em> for {_span(len(flat))}" if flat else f"{when} the processors had <em>room</em>"
    first_heat = next((minute[i][11:] for i in range(n) if series["temp"][i] is not None), None)

    # ---- who kept the processors busy: during the hot minutes if there are enough, otherwise all day ----
    pick = [minute[i] for i in hot] if len(hot) >= 10 else minute
    share = {}
    for t in pick:
        for g_, x in apps.get(t, {}).items():
            share[g_] = share.get(g_, 0) + x
    tot = sum(share.values())
    who_title = ("Who kept the processors busy while it ran hot" if len(hot) >= 10 else "Who kept the processors busy " + when.lower())
    if tot:
        sc = max(share.values())
        rows = "".join(f'<div class=row style="--i:{j}" title="{e(g_)}"><span>{e(g_)}</span><div class=track><b style="--w:{x / sc * 100:.0f}%"></b></div><em>{x / tot * 100:.0f}%</em></div>'
                       for j, (g_, x) in enumerate(sorted(share.items(), key=lambda kv: -kv[1])[:9]) if x / tot >= .005)
        who = f'<div class=list>{rows}</div><p class=note>Share of all the processor time used, from {e(min(t for t in pick if t in apps)[11:])}.</p>'
    else:
        who = '<p class=note>The per-app processor log starts with the next reading.</p>'

    data = {"t": minute, "s": {k: [None if x is None else round(x, 1) for x in v] for k, v in series.items()},
            "state": [state.get(t, "") for t in minute],
            "apps": {str(i): sorted(apps[t].items(), key=lambda kv: -kv[1])[:3] for i, t in enumerate(minute) if t in apps},
            "n": n,
            "names": {s["k"]: s["name"] for s in STRIPS}, "units": {s["k"]: s["unit"] for s in STRIPS}}
    return f"""
<section class=panel id=p-heat role=tabpanel><div class=inner>
<div class=en><p class=kick><i class=dot></i>Everything that makes a Mac hot, loud or slow, measured every minute.</p><h2 class=big>{head}</h2></div>
<p class="lede en" style="--n:1">Each strip is one thing, minute by minute. Above the dotted line it starts to make the Mac hot, loud or slow, and that part turns red. Hover any strip to read every measure at that minute and which apps were keeping the processors busy.</p>
<div class="htiles en" style="--n:2">{"".join(tiles)}</div>
<div class=two>
<div class="c chartbox en" style="--n:3" id=hchart>
{strips}
<div class=tip id=htip></div>
</div>
<div class="c en" style="--n:4"><small>{e(who_title)}</small>{who}</div>
</div>
{f'<p class="note en" style="--n:5">Temperature, fan and graphics are measured from {e(first_heat)}{" today" if when == "Today" else ""}; processors and memory from earlier.</p>' if first_heat and series["temp"].index(next(x for x in series["temp"] if x is not None)) > 30 else ""}
<script type=application/json id=hdata>{json.dumps(data).replace("</", "<\\/")}</script>
</div></section>
"""


HEAT_CSS = """
/* Hot & slow tab */
.htiles{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:10px}
.ht{padding:10px 14px!important;border-radius:20px!important;display:flex;flex-direction:column;gap:2px;min-width:0}
.ht .htn{font-size:12.5px;color:var(--mute);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.ht b{font:700 26px/1.1 Fredoka,sans-serif;color:var(--fg);white-space:nowrap} .ht b small{display:inline;margin-left:3px;font:600 13px Geist,sans-serif;color:var(--mute)}
.ht .hw{font-size:12.5px;color:var(--fg);display:flex;align-items:center;gap:6px}
.ht .hw i{width:8px;height:8px;border-radius:50%;background:var(--good)}
.ht[data-lvl="1"] .hw i{background:#f59e0b} .ht[data-lvl="2"] .hw i{background:var(--hot)}
.ht[data-lvl="2"]{border-color:color-mix(in srgb,var(--hot) 45%,transparent)}
.hstrips{width:100%;height:auto;display:block;overflow:visible}
.hstrips.hnarrow{display:none} @media(max-width:700px){.hstrips.hwide{display:none} .hstrips.hnarrow{display:block}}
.hstrips .hl{font:600 14px Geist,sans-serif;fill:var(--fg)} .hstrips .hu{font-weight:400;fill:var(--mute)}
.hstrips .hb{fill:color-mix(in srgb,var(--ram) 5%,transparent)}
.hstrips .ha{fill:color-mix(in srgb,var(--ram) 16%,transparent)}
.hstrips .hline{fill:none;stroke:var(--ram);stroke-width:2;stroke-linejoin:round}
.hstrips .hhot{fill:color-mix(in srgb,var(--hot) 22%,transparent)}
.hstrips .hlhot{fill:none;stroke:var(--hot);stroke-width:2.2;stroke-linejoin:round}
.hstrips .hthr{stroke:var(--fg);stroke-width:1.5;stroke-dasharray:2 7;stroke-linecap:round;opacity:.6}
.hstrips .htk,.hstrips .hnone{font:500 12px 'Geist Mono',monospace;fill:var(--mute)}
.hstrips .hxh{stroke:var(--fg);stroke-width:1;opacity:0} .hstrips.hovering .hxh{opacity:.35}
#htip{transform:translate(-50%,8px);white-space:normal;width:max-content;max-width:360px}
#htip .r{display:flex;justify-content:space-between;gap:14px} #htip .r span,#htip .r b{white-space:nowrap}
#htip .r em{font:600 10.5px Geist,sans-serif;font-style:normal;text-transform:uppercase;letter-spacing:.04em;margin-left:6px;padding:1px 5px;border-radius:6px;background:var(--hot);color:#fff} #htip .ap{margin-top:5px;opacity:.85;font-size:12px}
@media(max-width:1100px){.htiles{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media(max-width:560px){.htiles{grid-template-columns:repeat(2,minmax(0,1fr))}}
"""

HEAT_JS = """<script>
(() => {
  // Hot & slow strips: one crosshair across every strip; the tip lists each measure at that minute and the busiest apps.
  const box = document.getElementById("hchart"), dEl = document.getElementById("hdata");
  if (!box || !dEl) return;
  const D = JSON.parse(dEl.textContent), tip = document.getElementById("htip");
  const lines = {temp: 90, fan: 60, cpu: 85, gpu: 85, disk: 1000, swap: 100};
  const fmt = (k, v) => v == null ? "–" : k === "temp" ? Math.round(v) + " °C" : D.units[k].startsWith("%") ? Math.round(v) + "%" : Math.round(v).toLocaleString() + " MB/min";
  const at = (svg, ev) => {
    const r = svg.getBoundingClientRect(), b = box.getBoundingClientRect(), Wd = +svg.dataset.w, xh = svg.querySelector(".hxh");
    const x = Math.min(Math.max((ev.clientX - r.left) / r.width, 0), 1), i = Math.round(x * (D.n - 1)), vx = i * Wd / Math.max(D.n - 1, 1);
    xh.setAttribute("x1", vx); xh.setAttribute("x2", vx); svg.classList.add("hovering");
    const over = k => D.s[k][i] != null && D.s[k][i] >= lines[k];
    const rows = Object.keys(D.names).map(k => `<div class="r${over(k) ? " hot" : ""}"><span>${D.names[k]}</span><b>${fmt(k, D.s[k][i])}${over(k) ? " <em>over the line</em>" : ""}</b></div>`).join("")
      + (D.state[i] && D.state[i] !== "nominal" ? `<div class="r hot"><span>macOS heat level</span><b>${D.state[i]} <em>slowing it down</em></b></div>` : "");
    const ap = D.apps[i] ? `<div class=ap>Busiest: ${D.apps[i].map(([g, v]) => `${g} ${Math.round(v)}%`).join(", ")}</div>` : "";
    tip.innerHTML = `<div style="font:600 14px Fredoka,sans-serif;margin-bottom:4px">${D.t[i].slice(11)}</div>${rows}${ap}`;
    const left = r.left - b.left + vx * r.width / Wd, w = tip.offsetWidth;
    tip.style.left = Math.min(Math.max(left, w / 2 + 6), b.width - w / 2 - 6) + "px";
    tip.style.top = Math.min(ev.clientY - b.top + 14, b.height - tip.offsetHeight - 8) + "px";
  };
  box.querySelectorAll("svg.hstrips").forEach(svg => {
    svg.addEventListener("pointermove", ev => at(svg, ev));
    svg.addEventListener("pointerdown", ev => { box.classList.add("touch"); at(svg, ev); });
    svg.addEventListener("pointerleave", () => { svg.classList.remove("hovering"); box.classList.remove("touch"); });
  });
})();
</script>"""


def add_heat(page):
    return page.replace("</style>", HEAT_CSS + "</style>", 1).replace("</body>", HEAT_JS + "</body>", 1)
