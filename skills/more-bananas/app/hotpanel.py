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
    {"k": "cpu", "name": "Processors", "unit": "work waiting, as × its cores", "lo": 0, "hi": None, "line": 1,
     "line_txt": "1×: more work than its cores can run", "words": ("keeping up", "busy", "work waiting"), "mid": .6},
    {"k": "gpu", "name": "Graphics", "unit": "% busy", "lo": 0, "hi": 100, "line": 85, "line_txt": "85%: flat out",
     "words": ("fine", "busy", "flat out"), "mid": 60},
    {"k": "disk", "name": "Disk reads and writes", "unit": "MB a minute", "lo": 0, "hi": None, "line": 1000,
     "line_txt": "1 GB a minute: heavy", "words": ("fine", "busy", "heavy"), "mid": 300},
    {"k": "swap", "name": "Memory pushed to disk", "unit": "MB a minute", "lo": 0, "hi": None, "line": 100,
     "line_txt": "100 MB a minute: swapping hard", "words": ("calm", "a little", "swapping hard"), "mid": 5},
]
HOT_TEMP, LOUD_FAN = 90, 60   # a minute counts as "ran hot" when the chip reached 90 °C or the fan passed 60%
SWAP_HARD = 100               # MB a minute pushed to disk: memory is holding the Mac up
SLOWING = ("fair", "serious", "critical")   # macOS's own heat levels at which it holds the chip back to cool it
# What held a minute up, in the order the page draws them. The colours live in report.py's CSS (--c-cpu and so on).
CAUSE_NAMES = {"cpu": "processors", "mem": "memory", "both": "memory and processors", "heat": "heat"}


def _rows(path, ncol):
    try:
        with open(path) as source:
            return [l.rstrip("\n").split(",") for l in source if l.count(",") == ncol - 1]
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


def minute_causes(home):
    """What held each minute up, for every minute with a memory or processor reading.

    Returns ({minute: cause}, first minute the processors were measured or None). cause is one of
    "" (nothing did), "mem" (pushing SWAP_HARD MB a minute or more to disk), "cpu" (more work waiting than the
    cores can run: 1-minute load average above the core count), "both", or "heat" (macOS at a heat level where it
    slows the chip down; it wins over the others because it is what makes the processors slower).
    Before the processors were measured, a minute can only be "mem" or "".
    """
    swap = {r[0]: _num(r[1]) for r in _rows(os.path.join(home, "live.csv"), 6)}
    wait = {}
    for r in _rows(os.path.join(home, "cpu.csv"), 4):
        l_, c_ = _num(r[2]), _num(r[3])
        if l_ is not None and c_:
            wait[r[0]] = l_ / c_
    state = {r[0]: r[1] for r in _rows(os.path.join(home, "heat.csv"), 6) if r[1]}
    out = {}
    for t in set(swap) | set(wait):
        if swap.get(t) is None:
            continue  # Missing swap data is not a zero-pressure minute.
        m, p = (swap.get(t) or 0) >= SWAP_HARD, (wait.get(t) or 0) > 1
        out[t] = "heat" if state.get(t) in SLOWING else "both" if m and p else "mem" if m else "cpu" if p else ""
    return out, (min(wait) if wait else None)


def heat_section(home, today):
    """The panel's HTML for the day `today` ("YYYY-MM-DD"), or the last 24 hours early in the morning."""
    by = {s["k"]: {} for s in STRIPS}                     # measure -> {minute stamp: value}; a later row wins
    for r in _rows(os.path.join(home, "cpu.csv"), 4):      # work waiting: 1-minute load average over the core count
        l_, c_ = _num(r[2]), _num(r[3])
        by["cpu"][r[0]] = l_ / c_ if l_ is not None and c_ else None
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
        by["disk"][r[0]] = a + b if a is not None and b is not None else None
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
    end = dt.datetime.strptime(stamps[-1], "%Y-%m-%d %H:%M")
    RANK = {"": 0, "nominal": 0, "fair": 1, "serious": 2, "critical": 3}

    def window(r):
        """The stamps in range r: today (the last 24 hours early in the morning), or the last r days."""
        if r == 1:
            day = [t for t in stamps if t[:10] == today]
            if len(day) >= 60:
                return day
        cut = (end - dt.timedelta(days=r)).strftime("%Y-%m-%d %H:%M")   # stamps sort as text, so compare them as text
        return [t for t in stamps if t > cut]

    on, prev = [1], window(1)[0]                           # a range gets a button only if it reaches further back
    for r in (3, 7, 30):
        f_ = window(r)[0]
        if f_ < prev:
            on.append(r); prev = f_
    nd = len({t[:10] for t in stamps})
    rbar = ('<div class="rbar en" role=group aria-label="Time range">' + "".join(
        f'<button class="jt rg" data-r={r} aria-pressed={"true" if r == 1 else "false"}>{"Today" if r == 1 else f"{r} days"}</button>' if r in on else
        f'<button class="jt rg" data-r={r} disabled title="{nd} day{"s" if nd != 1 else ""} measured so far">{r} days</button>' for r in (1, 3, 7, 30)) + '</div>')

    def view(r):
        # Only minutes with a reading: while the Mac is off or asleep nothing is measured, so that time is left out
        # rather than drawn as an empty stretch.
        rawmin = window(r)
        nm = len(rawmin)
        raw = {s["k"]: [by[s["k"]].get(t) for t in rawmin] for s in STRIPS}
        b = 1 if r == 1 else next((b for b in (1, 2, 5, 10, 15, 30, 60, 120) if nm / b <= 1100), 240)
        minute = rawmin[::b]                               # each point is the busiest minute of its b minutes
        n = len(minute)
        series = {k: [max((x for x in xs[i:i + b] if x is not None), default=None) for i in range(0, nm, b)] for k, xs in raw.items()}
        st = [max((state.get(t, "") for t in rawmin[i:i + b]), key=RANK.get) for i in range(0, nm, b)]
        ml = minute[0][:10] != minute[-1][:10]
        lab = (lambda t: dt.datetime.strptime(t, "%Y-%m-%d %H:%M").strftime("%a %-d %b, %H:%M")) if ml else (lambda t: t[11:])
        for s in STRIPS:
            seen = [x for x in series[s["k"]] if x is not None]
            s["top"] = s["hi"] if s["hi"] is not None else max(max(seen, default=0) * 1.1, s["line"] * 1.3)
            if s["k"] == "cpu":                                # a Chrome launch can spike it to 20x; past 4x is just "a lot"
                s["top"] = min(s["top"], 4)

        def draw(W, SH, GAP, TOP, tag, wide):
            X = (lambda i: i * W / (n - 1)) if n > 1 else (lambda i: W / 2)
            svg, clips = [], []
            for j, s in enumerate(STRIPS):
                k, vals, lo, hi = s["k"], series[s["k"]], s["lo"], s["top"]
                y0 = TOP + j * (SH + GAP)                      # top of this strip; its label sits in the gap above
                Y = (lambda v, y0=y0, lo=lo, hi=hi: y0 + SH - (min(max(v, lo), hi) - lo) * SH / (hi - lo))
                ly = Y(s["line"])
                runs, cur, last = [], [], -9                   # runs of readings; a gap of more than 3 points breaks the line
                for i, x in enumerate(vals):
                    if x is None:
                        continue
                    if i - last > 3 and cur:
                        runs.append(cur); cur = []
                    cur.append((i, x)); last = i
                if cur:
                    runs.append(cur)
                cid = f"hz{tag}{r}-{k}"                        # one clip per strip, per layout, per range: ids must be unique
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
                elif runs[0][0][0] > 30 and X(runs[0][0][0]) > (260 if wide else 130):   # started later than the window, with room for the label
                    g.append(f'<text class=hnone x={X(runs[0][0][0]) - 6:.1f} y={y0 + SH - 8} text-anchor=end>{"measured " if wide else ""}from {e(lab(minute[runs[0][0][0]]))}</text>')
                line_txt = "dotted line: " + s["line_txt"] if wide else s["line_txt"].split(":")[0]
                g.append(f'<line class=hthr x1=0 x2={W} y1={ly:.1f} y2={ly:.1f} /><text class=htk x={W - 2} y={y0 - 10} text-anchor=end>{e(line_txt)}</text></g>')
                svg += g
            H = TOP + len(STRIPS) * (SH + GAP) - GAP
            every = max(n // (6 if wide else 3), 1)
            ticks = "".join(f'<text class=htk x="{X(i):.1f}" y="{H + 20}" text-anchor="{"start" if i == 0 else "end" if i == n - 1 else "middle"}">{minute[i][11:] if not ml else minute[i][5:10].replace("-", "/") + " " + minute[i][11:]}</text>'
                            for i in sorted({0, n - 1, *range(0, n, every)}) if i == n - 1 or n - 1 - i > n / (14 if wide else 6))
            return (f'<svg class="hstrips {"hwide" if wide else "hnarrow"}" data-w={W} viewBox="0 0 {W} {H + 30}" role=img '
                    f'aria-label="Chip temperature, fan speed, processor and graphics load, disk traffic and memory pushed to disk, minute by minute">'
                    f'{"".join(clips)}{"".join(svg)}{ticks}<line class=hxh x1=0 x2=0 y1=0 y2={H} /></svg>')

        strips = draw(1000, 44, 30, 22, "w", True) + draw(420, 54, 34, 22, "n", False)

        # ---- headline: how long it ran hot, counted on minutes, never on points ----
        hot = [i for i in range(nm) if (raw["temp"][i] or 0) >= HOT_TEMP or (raw["fan"][i] or 0) >= LOUD_FAN]
        flat = [i for i in range(nm) if (raw["cpu"][i] or 0) > 1]
        has_heat = any(x is not None for x in raw["temp"] + raw["fan"])
        one_day = rawmin[0][:10] == rawmin[-1][:10]
        when = (("Today" if rawmin[-1][:10] == dt.date.today().isoformat() else
                 "On " + dt.datetime.strptime(rawmin[-1][:10], "%Y-%m-%d").strftime("%A %-d %b")) if one_day else
                "In the last 24 hours") if r == 1 else f"In the last {r} days"
        if has_heat and hot:
            head = f"{when} it ran <em>hot</em> for {_span(len(hot))}"
        elif has_heat:
            head = f"{when} it has stayed <em>cool</em>"
        else:
            head = f"{when} the processors had <em>work waiting</em> for {_span(len(flat))}" if flat else f"{when} the processors had <em>room</em>"
        first_i = next((i for i in range(nm) if raw["temp"][i] is not None), None)

        # ---- who kept the processors busy: during the hot minutes if there are enough, otherwise the whole range ----
        pick = [rawmin[i] for i in hot] if len(hot) >= 10 else rawmin
        share = {}
        for t in pick:
            for g_, x in apps.get(t, {}).items():
                share[g_] = share.get(g_, 0) + x
        tot = sum(share.values())
        who_title = ("Who kept the processors busy while it ran hot" if len(hot) >= 10 else "Who kept the processors busy " + when[0].lower() + when[1:])
        if tot:
            sc = max(share.values())
            rows = "".join(f'<div class=row style="--i:{j}" title="{e(g_)}"><span>{e(g_)}</span><div class=track><b style="--w:{x / sc * 100:.0f}%"></b></div><em>{x / tot * 100:.0f}%</em></div>'
                           for j, (g_, x) in enumerate(sorted(share.items(), key=lambda kv: -kv[1])[:9]) if x / tot >= .005)
            who = f'<div class=list>{rows}</div><p class=note>Share of all the processor time used, from {e(lab(min(t for t in pick if t in apps)))}.</p>'
        else:
            who = '<p class=note>The per-app processor log starts with the next reading.</p>'
        papps = {}
        for i in range(0, nm, b):
            acc, k_ = {}, 0
            for t in rawmin[i:i + b]:
                if t in apps:
                    k_ += 1
                    for g_, x in apps[t].items():
                        acc[g_] = acc.get(g_, 0) + x
            if k_:
                papps[str(i // b)] = sorted(((g_, round(x / k_, 1)) for g_, x in acc.items()), key=lambda kv: -kv[1])[:3]
        data = {"t": minute, "s": {k: [None if x is None else round(x, 1) for x in v] for k, v in series.items()},
                "state": st, "apps": papps, "n": n, "b": b, "ml": ml,
                "names": {s["k"]: "Processors: work waiting" if s["k"] == "cpu" else s["name"] for s in STRIPS}, "units": {s["k"]: s["unit"] for s in STRIPS}}
        note = (f'<p class="note en" style="--n:5">Temperature, fan, graphics and disk are measured from {e(lab(rawmin[first_i]))}{" today" if when == "Today" else ""}; processors and memory from earlier.</p>'
                if first_i is not None and first_i > 30 else "")
        return raw, rawmin, f"""<div class=rv data-r={r}{"" if r == 1 else " hidden"}>
<div class=en><h2 class=big>{head}</h2></div>
<p class="lede en" style="--n:1">Each strip is one thing, {"minute by minute" if b == 1 else f"each point the busiest minute of {b}"}. Above the dotted line it starts to make the Mac hot, loud or slow, and that part turns red. Hover any strip to read every measure {"at that minute" if b == 1 else "there"} and which apps were keeping the processors busy.</p>
__TILES__
<div class=two>
<div class="c chartbox en hchart" style="--n:3">
{strips}
<div class="tip htip"></div>
<script type=application/json class=hdata>{json.dumps(data).replace("</", "<\\/")}</script>
</div>
<div class="c en" style="--n:4"><small>{e(who_title)}</small>{who}</div>
</div>
{note}
</div>"""

    views = [view(r) for r in on]
    raw, rawmin, _ = views[0]

    # ---- right now: the last reading of each measure ----
    def now(k):
        for x in reversed(raw[k]):
            if x is not None:
                return x
        return None

    def word(s, x):
        return s["words"][2] if x >= s["line"] else s["words"][1] if x >= s["mid"] else s["words"][0]

    def fmt(s, x):
        return f'{x:.0f}<small>°C</small>' if s["k"] == "temp" else f'{x:.1f}<small>×</small>' if s["k"] == "cpu" else f'{x:.0f}<small>%</small>' if s["unit"].startswith("%") else f'{x:,.0f}<small> MB/min</small>'

    state_now = next((state[t] for t in reversed(rawmin) if t in state), "")
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
    tiles_html = f'<div class="htiles en" style="--n:2">{"".join(tiles)}</div>'
    return f"""
<section class="panel rpanel" id=p-heat role=tabpanel><div class=inner>
<div class=en><p class=kick><i class=dot></i>Everything that makes a Mac hot, loud or slow, measured every minute.</p></div>
{rbar}
{"".join(h.replace("__TILES__", tiles_html) for _, _, h in views)}
</div></section>
"""


HEAT_CSS = """
/* Hot & slow tab */
.htiles{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:10px}
.ht{padding:10px 14px!important;border-radius:20px!important;display:flex;flex-direction:column;gap:2px;min-width:0}
.ht .htn{font-size:12.5px;line-height:1.3;color:var(--mute)}
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
.htip{transform:translate(-50%,8px);white-space:normal;width:max-content;max-width:360px}
.htip .r{display:flex;justify-content:space-between;gap:14px} .htip .r span,.htip .r b{white-space:nowrap}
.htip .r em{font:600 10.5px Geist,sans-serif;font-style:normal;text-transform:uppercase;letter-spacing:.04em;margin-left:6px;padding:1px 5px;border-radius:6px;background:var(--hot);color:#fff} .htip .ap{margin-top:5px;opacity:.85;font-size:12px}
@media(max-width:1250px){.htiles{grid-template-columns:repeat(4,minmax(0,1fr))}}
@media(max-width:560px){.htiles{grid-template-columns:repeat(3,minmax(0,1fr));gap:6px} .ht{padding:8px 9px!important;border-radius:16px!important} .ht .htn,.ht .hw{font-size:11px} .ht b{font-size:19px} .ht b small{font-size:10.5px;margin-left:1px}}
@media (min-width:861px) and (min-height:600px){
 .htiles{grid-template-columns:repeat(6,minmax(0,1fr))!important;gap:8px;margin-bottom:8px} .ht{padding:6px 10px!important;border-radius:14px!important;flex-direction:row;flex-wrap:wrap;align-items:baseline;gap:0 8px}
 .ht .htn{width:100%;font-size:11.5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis} .ht b{font-size:19px} .ht .hw{font-size:11.5px}
 #p-heat .hstrips.hwide{height:calc(100dvh - 430px);width:auto;max-width:100%;margin:0 auto}
 #p-heat .two>.c:last-child .list{max-height:calc(100dvh - 380px);overflow:auto}
}
"""

HEAT_JS = """<script>
(() => {
  // Hot & slow strips: one crosshair across every strip; the tip lists each measure at that minute and the busiest apps.
  document.querySelectorAll(".hchart").forEach(box => {
  const D = JSON.parse(box.querySelector(".hdata").textContent), tip = box.querySelector(".htip");
  const lines = {temp: 90, fan: 60, cpu: 1, gpu: 85, disk: 1000, swap: 100, net: 500};
  const fmt = (k, v) => v == null ? "–" : k === "temp" ? Math.round(v) + " °C" : k === "cpu" ? v.toFixed(1) + "× its cores" : D.units[k].startsWith("%") ? Math.round(v) + "%" : Math.round(v).toLocaleString() + " MB/min";
  const at = (svg, ev) => {
    const r = svg.getBoundingClientRect(), b = box.getBoundingClientRect(), Wd = +svg.dataset.w, xh = svg.querySelector(".hxh");
    const x = Math.min(Math.max((ev.clientX - r.left) / r.width, 0), 1), i = Math.round(x * (D.n - 1)), vx = i * Wd / Math.max(D.n - 1, 1);
    xh.setAttribute("x1", vx); xh.setAttribute("x2", vx); svg.classList.add("hovering");
    const over = k => D.s[k][i] != null && (k === "cpu" ? D.s[k][i] > 1 : D.s[k][i] >= lines[k]);
    const rows = Object.keys(D.names).map(k => `<div class="r${over(k) ? " hot" : ""}"><span>${D.names[k]}</span><b>${fmt(k, D.s[k][i])}${over(k) ? " <em>over the line</em>" : ""}</b></div>`).join("")
      + (D.state[i] && D.state[i] !== "nominal" ? `<div class="r hot"><span>macOS heat level</span><b>${D.state[i]} <em>slowing it down</em></b></div>` : "");
    const ap = D.apps[i] ? `<div class=ap>Busiest: ${D.apps[i].map(([g, v]) => `${g} ${Math.round(v)}%`).join(", ")}</div>` : "";
    tip.innerHTML = `<div style="font:600 14px Fredoka,sans-serif;margin-bottom:4px">${D.ml ? D.t[i].slice(5).replace("-", "/") : D.t[i].slice(11)}${D.b > 1 ? ", busiest of " + D.b + " min" : ""}</div>${rows}${ap}`;
    const left = r.left - b.left + vx * r.width / Wd, w = tip.offsetWidth;
    tip.style.left = Math.min(Math.max(left, w / 2 + 6), b.width - w / 2 - 6) + "px";
    tip.style.top = Math.min(ev.clientY - b.top + 14, b.height - tip.offsetHeight - 8) + "px";
  };
  box.querySelectorAll("svg.hstrips").forEach(svg => {
    svg.addEventListener("pointermove", ev => at(svg, ev));
    svg.addEventListener("pointerdown", ev => { box.classList.add("touch"); at(svg, ev); });
    svg.addEventListener("pointerleave", () => { svg.classList.remove("hovering"); box.classList.remove("touch"); });
  });
  });
})();
</script>"""


def add_heat(page):
    return page.replace("</style>", HEAT_CSS + "</style>", 1).replace("</body>", HEAT_JS + "</body>", 1)
