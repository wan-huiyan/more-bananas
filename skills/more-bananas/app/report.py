"""The memory report as a case: this 16 GB Mac is too small for a busy workday.

Six full-screen panels behind a pill tab bar (no long scroll), cute charts with buddy decor.
memlog.py collects the readings and calls render(v) with its variables; buddy.py then adds the
mascot, the buddy yard (at <!--YARD-->) and the sparkle effects.
"""
import datetime as dt
import html
import json
import os

from hotpanel import CAUSE_NAMES, _span as span, add_heat, heat_section, minute_causes


def gb(x):
    return f"{x:.1f}"


HEAD = ('<g class="hd"><circle r="1" fill="#ffd93b"/><circle r=".46" fill="#fff" stroke="#8b949f" stroke-width=".2"/>'
        '<circle r=".2" fill="#7a4b23"/></g>')


def mini(x, y, s, cls="", suit="#2f6fb5", flip=False, mood="calm"):
    """A small buddy as an SVG group, feet at (x, y), s = height in px."""
    k = s / 92
    mouth = {"over": "M23 50 Q30 45 37 50", "tight": "M24 48 L36 48"}.get(mood, "M23 46 Q30 52 37 46")
    f = f" translate(60 0) scale(-1 1)" if flip else ""
    return (f'<g class="{cls}" transform="translate({x - 30*k:.1f} {y - 90*k:.1f}) scale({k:.3f}){f}">'
            f'<rect x="19" y="76" width="8" height="10" rx="3" fill="{suit}"/><rect x="33" y="76" width="8" height="10" rx="3" fill="{suit}"/>'
            f'<ellipse cx="22" cy="87" rx="7" ry="3.5" fill="#333a45"/><ellipse cx="38" cy="87" rx="7" ry="3.5" fill="#333a45"/>'
            f'<rect x="6" y="6" width="48" height="76" rx="24" fill="#ffd93b"/><ellipse cx="17" cy="20" rx="5" ry="9" fill="#fff" opacity=".3"/>'
            f'<path d="M6 58h48v1a24 24 0 0 1-48 0z" fill="{suit}"/><rect x="18" y="56" width="24" height="14" rx="4" fill="{suit}"/>'
            f'<path d="M30 6q-3-6-8-7M30 6q2-7 6-8" stroke="#333a45" stroke-width="2" fill="none" stroke-linecap="round"/>'
            f'<rect x="6" y="27" width="48" height="5" fill="#333a45"/><circle cx="30" cy="30" r="10" fill="#fff" stroke="#9aa3ad" stroke-width="3"/>'
            f'<circle class="pp" cx="30" cy="31" r="4.5" fill="#7a4b23"/><path d="{mouth}" stroke="#5a2d0c" stroke-width="2.6" fill="none" stroke-linecap="round"/></g>')


def render(v):
    e = html.escape
    TOTAL = v["TOTAL_GB"]
    need, pk, T = v["need"], v["pk"], v["T"]
    U, S, N = v["U"], v["S"], v["N"]
    LO, LT, lpk = v["LO"], v["LT"], v["lpk"]
    out_mb = v["out_mb"]
    cfg = v["cfg"]
    HIST_FROM = cfg.get("history_from") or "0000"  # optional: ignore session history before this date
    day_sess = {d: x for d, x in v["day_sess"].items() if d >= HIST_FROM} or {v["T"][0][:10]: (v["terms"], v["T"][0][11:])}
    since = dt.datetime.strptime(v["first_reading"], "%Y-%m-%d %H:%M").strftime("%-d %b %Y")
    day_mem = v["day_mem"]
    now_d, by_group, peak_d = v["now_d"], v["by_group"], v["peak_d"]
    terms, mood = v["terms"], v["mood"]
    T_all, need_all, U_all, LO_all, LT_all = T, need, U, LO, LT   # every minute; the range views below cut their own
    # The Today tab draws today's minutes only (the last 24 hours early in the morning).
    today = T[-1][:10]
    ix = [i for i, t in enumerate(T) if t[:10] == today]
    if len(ix) < 60:
        ix = list(range(max(0, len(T) - 24 * 60), len(T)))
    T, need, U, S, N = [T[i] for i in ix], [need[i] for i in ix], [U[i] for i in ix], [S[i] for i in ix], [N[i] for i in ix]
    pk = max(range(len(need)), key=need.__getitem__)
    lv_ix = [i for i, t in enumerate(LT) if t >= T[0]] or [len(LT) - 1]
    LO, LT = [LO[i] for i in lv_ix], [LT[i] for i in lv_ix]
    lpk = max(range(len(LO)), key=LO.__getitem__)

    peak = need[pk]
    over_by = peak - TOTAL
    heavy_mins = sum(x >= 100 for x in LO)
    swap_mins = sum(x >= 5 for x in LO)
    written_gb = v["swapped_total_gb"]
    hist_max = max(n for n, _ in day_sess.values())
    busy_days = sum(1 for n_, _ in day_sess.values() if n_ >= 10)
    first = dt.date.fromisoformat(min(day_sess))
    # Recommendation from what was measured, not from a guess about how many sessions run:
    # the highest memory need ever recorded, plus 25% headroom, rounded up to a size Macs are sold in.
    import csv, shutil
    allrows = [r for r in csv.reader(open(v["LOG"])) if len(r) == 6]
    all_need = [(r[0], float(r[1]) + float(r[2])) for r in allrows]
    peak_ever_t, peak_ever = max(all_need, key=lambda x: x[1])
    days_measured = len({t[:10] for t, _ in all_need})
    HEADROOM = 1.25
    SIZES = [16, 24, 32, 36, 48, 64, 96, 128]
    target = peak_ever * HEADROOM
    rec = next((x for x in SIZES if x >= target), SIZES[-1])
    nxt = next((x for x in SIZES if x > rec), rec)
    disk = shutil.disk_usage("/")
    disk_used, disk_total = disk.used / 1e9, disk.total / 1e9
    disk_rec = next((x for x in (512, 1000, 2000, 4000) if x >= disk_used * 1.5), 4000)
    disk_txt = "1 TB" if disk_rec == 1000 else "2 TB" if disk_rec == 2000 else "4 TB" if disk_rec == 4000 else "512 GB"
    peak_ever_when = dt.datetime.strptime(peak_ever_t, "%Y-%m-%d %H:%M").strftime("%a %-d %b, %H:%M")
    # Weekday x hour heatmap of the highest memory need seen in that hour.
    cell = {}
    for t, x in all_need:
        d_ = dt.datetime.strptime(t, "%Y-%m-%d %H:%M"); k_ = (d_.weekday(), d_.hour)
        cell[k_] = max(cell.get(k_, 0), x)
    calm = out_mb < 5
    # The line says what the Mac is doing this minute: memory (pushing to disk) AND the processors, because a hot,
    # loud Mac with nothing going to disk is busy processors, and "quiet" alone would be wrong.
    # Processors are measured as work waiting: the 1-minute load average over the core count. Above 1, more work is
    # waiting than the cores can run. (% busy hides this on Apple chips, where half the cores are slower ones.)
    wait_now = v["load1"] / v["cores"] if v.get("load1") is not None and v.get("cores") else None
    cpu_top = sorted(((x, g) for g, x in (v.get("cpu_by_group") or {}).items() if x >= 3), reverse=True)[:3]
    disk_now = "nothing is being pushed to disk" if calm else f"it is pushing {out_mb:.0f} MB a minute to disk"
    if wait_now is not None and wait_now > 1:
        who = f"; busiest: {', '.join(f'{g} {x:.0f}%' for x, g in cpu_top)}" if cpu_top else ""
        status_line = (f"Right now the processors have {wait_now:.1f} times the work its {v['cores']} cores can run{who}, enough to run warm, loud and slow. "
                       + ("Memory is fine: nothing is being pushed to disk." if calm else f"And {disk_now}."))
    elif calm:
        status_line = "Right now it is quiet: nothing is being pushed to disk" + (", and the processors are keeping up." if wait_now is not None else ".")
    else:
        status_line = f"Right now {disk_now}" + (", and the processors are keeping up." if wait_now is not None else ".")
    # What held each minute up (memory, processors, both, or heat), shared by Recommendation, Today, Busy days and hours.
    cause, cpu_from = minute_causes(v["HOME"])
    def held(c_):
        return CAUSE_NAMES[c_]
    # Which held it up more over working hours since the processors were first measured. Every tab leads with it.
    HOURS_TXT = v.get("hours_txt", "every hour the Mac was on")
    WM = "working minutes" if v.get("hours") == "work" else "minutes"   # the readings arrive already cut to these hours
    wc = [c_ for t, c_ in cause.items() if cpu_from and t >= cpu_from]
    vn, vc = len(wc), {k_: wc.count(k_) for k_ in ("cpu", "both", "mem", "heat")}
    cpu_first = vn >= 60 and vc["cpu"] > vc["mem"]
    def rows_(name, ncol):
        p_ = os.path.join(v["HOME"], name)
        return [l.rstrip("\n").split(",") for l in open(p_) if l.count(",") == ncol - 1] if os.path.exists(p_) else []
    wait_by_t = {r[0]: float(r[2]) / float(r[3]) for r in rows_("cpu.csv", 4) if float(r[3]) > 0}   # work waiting, x its cores
    capps = {}                                   # minute -> {app group: % of all cores}
    for r in rows_("cpu_apps.csv", 3):
        capps.setdefault(r[0], {})[r[1]] = float(r[2])
    tjc = {}                                     # minute -> {(session folder, job): % of all cores}
    for r in rows_("tools_cpu.csv", 4):
        tjc.setdefault(r[0], {})[(r[1], r[2])] = float(r[3])
    peak_when = dt.datetime.strptime(T[pk], "%Y-%m-%d %H:%M").strftime("%-d %b, %H:%M")
    swap_when = dt.datetime.strptime(LT[lpk], "%Y-%m-%d %H:%M").strftime("%-d %b, %H:%M")

    CAUSE_KEY = "".join(f'<span><i class="cz {k_}"></i>{CAUSE_NAMES[k_]}</span>' for k_ in ("cpu", "both", "mem", "heat"))

    # ---------- panel 2: Today, or the last 3, 7 or 30 days. One view per range, switched by buttons ----------
    W, H, PAD = 1000, 300, 30
    RANGES = (1, 3, 7, 30)

    def mstamp(t):                                 # minutes since year 1, cheap enough for a month of stamps
        return dt.date(int(t[:4]), int(t[5:7]), int(t[8:10])).toordinal() * 1440 + int(t[11:13]) * 60 + int(t[14:16])

    def win(stamps, r):
        """Indices of the stamps in range r: today (the last 24 hours early in the morning), or the last r days."""
        if r == 1:
            ix_ = [i for i, t in enumerate(stamps) if t[:10] == stamps[-1][:10]]
            if len(ix_) >= 60:
                return ix_
        cut = mstamp(stamps[-1]) - 1440 * r
        return [i for i, t in enumerate(stamps) if mstamp(t) > cut]

    def bsize(nmin):                               # minutes per point, so a chart never draws more than ~1,100 points
        return next((b for b in (1, 2, 5, 10, 15, 30, 60, 120) if nmin / b <= 1100), 240)

    def groups(stamps, ix_, b):
        gs, k0 = [], None
        for i in ix_:
            k = i if b == 1 else mstamp(stamps[i]) // b
            if k != k0:
                gs.append([]); k0 = k
            gs[-1].append(i)
        return gs

    def ranges_on(stamps):
        """The ranges worth a button: each must reach further back than the one before it."""
        on, prev = [1], win(stamps, 1)[0]
        for r in RANGES[1:]:
            f_ = win(stamps, r)[0]
            if f_ < prev:
                on.append(r); prev = f_
        return on

    def rbar(on, stamps):
        nd_ = len({t[:10] for t in stamps})
        return ('<div class="rbar en" role=group aria-label="Time range">' + "".join(
            f'<button class="jt rg" data-r={r} aria-pressed={"true" if r == 1 else "false"}>{"Today" if r == 1 else f"{r} days"}</button>' if r in on else
            f'<button class="jt rg" data-r={r} disabled title="{nd_} day{"s" if nd_ != 1 else ""} measured so far">{r} days</button>' for r in RANGES) + '</div>')

    def tview(r, sfx):
        ix_ = win(T_all, r)
        b = 1 if r == 1 else bsize(mstamp(T_all[ix_[-1]]) - mstamp(T_all[ix_[0]]) + 1)
        gs = groups(T_all, ix_, b)
        T = [T_all[g[0]] for g in gs]
        need = [max(need_all[i] for i in g) for g in gs]
        U = [max(U_all[i] for i in g) for g in gs]
        raw = {T_all[i] for i in ix_}                  # a set: a reinstall can log a minute twice
        ml = T[0][:10] != T[-1][:10]
        def lab(t):
            return dt.datetime.strptime(t, "%Y-%m-%d %H:%M").strftime("%a %-d %b, %H:%M") if ml else t[11:]
        when = ((("today" if T[-1][:10] == dt.date.today().isoformat() else      # a weekend on the working-hours page
                  "on " + dt.datetime.strptime(T[-1][:10], "%Y-%m-%d").strftime("%A %-d %b")) if not ml else "in the last 24 hours")
                if r == 1 else f"in the last {r} days")
        n = len(need)
        pk = max(range(n), key=need.__getitem__)
        peak = need[pk]
        peak_t = T_all[max(ix_, key=lambda i: need_all[i])]   # the real busiest minute, not a bucket's start
        peak_when = dt.datetime.strptime(peak_t, "%Y-%m-%d %H:%M").strftime("%-d %b, %H:%M" if r == 1 else "%a %-d %b, %H:%M")
        swap_by_t = {t: x for t, x in zip(LT_all, LO_all) if t >= T_all[ix_[0]]}
        LO = list(swap_by_t.values()) or [0]
        lpk_t = max(swap_by_t, key=swap_by_t.get) if swap_by_t else T[-1]
        swap_when = dt.datetime.strptime(lpk_t, "%Y-%m-%d %H:%M").strftime("%-d %b, %H:%M")
        heavy_mins, swap_mins = sum(x >= 100 for x in LO), sum(x >= 5 for x in LO)
        gswap = [max((swap_by_t.get(T_all[i], 0) for i in g), default=0) for g in gs]
        top = max(max(need), TOTAL) * 1.18
        def X(i): return i * W / max(n - 1, 1)
        def Y(val): return PAD + (H - PAD) - val * (H - PAD) / top
        ram_y = Y(TOTAL)
        pts = " ".join(f"{X(i):.1f},{Y(x):.1f}" for i, x in enumerate(need))
        upts = " ".join(f"{X(i):.1f},{Y(x):.1f}" for i, x in enumerate(U))
        area = f"0,{H} {pts} {W},{H}"
        px, py = X(pk), Y(peak)
        flag_left = px > W * .72
        ticks = ""
        for i in range(0, n, max(n // 6, 1)):
            ticks += f'<text x="{X(i):.1f}" y="{H + 20}" class=tk text-anchor="middle">{e(T[i][11:] if not ml else T[i][5:10].replace("-", "/") + " " + T[i][11:])}</text>'
        drops = []
        smax = max(max(LO), 50)
        for i, t in enumerate(T):
            x = gswap[i]
            if x >= 5:
                h = 10 + 50 * x / smax
                drops.append(f'<g class=dr style="--d:{(i % 7) * .3:.1f}s"><rect x="{X(i)-3:.1f}" y="0" width="6" height="{h:.1f}" rx="3"/>'
                             f'<circle cx="{X(i):.1f}" cy="{h + 4:.1f}" r="3.2"/><title>{e(lab(t))}: {x:.0f} MB pushed to disk{f" (the most in {b} minutes)" if b > 1 else ""}</title></g>')
        CB, step_ = H + 118, W / max(n - 1, 1)
        band = []
        if b == 1:
            tc = [cause.get(t, "") for t in T]
            run_c, run_s = None, 0
            for i in range(n + 1):
                c_ = tc[i] if i < n else None
                if c_ != run_c:
                    if run_c:
                        x0 = max(X(run_s) - step_ / 2, 0)
                        band.append(f'<rect class="cz {run_c}" x="{x0:.1f}" y="{CB}" width="{min(X(i - 1) + step_ / 2, W) - x0:.1f}" height="16">'
                                    f'<title>{e(lab(T[run_s]))}{"–" + e(T[i - 1][11:]) if i - 1 > run_s else ""}: held up by {held(run_c)}</title></rect>')
                    run_c, run_s = c_, i
        else:                                          # one block per point, fainter when fewer of its minutes were held up
            tc = []
            for i, g in enumerate(gs):
                hc = [cause.get(T_all[j], "") for j in g]
                hc = [c_ for c_ in hc if c_]
                c_ = ("heat" if "heat" in hc else max(set(hc), key=hc.count)) if hc else ""
                tc.append(c_)
                if c_:
                    sh = len(hc) / len(g)
                    band.append(f'<rect class="cz {c_}" x="{max(X(i) - step_ / 2, 0):.1f}" y="{CB}" width="{step_:.2f}" height="16" style="opacity:{.25 + .75 * sh:.2f}">'
                                f'<title>{e(lab(T[i]))}, {b} minutes: held up {sh:.0%} of them, mostly by {held(c_)}</title></rect>')
        cpu_i = next((i for i, t in enumerate(T) if cpu_from and t >= cpu_from), None)
        band_note = ("processors not measured yet" if cpu_i is None else
                     f"processors measured from {lab(T[cpu_i])}" if cpu_i > 30 else "")
        # The processors chart: work waiting per minute (load average over cores); above 1x there is more work than cores.
        wv = [max((wait_by_t[T_all[i]] for i in g if T_all[i] in wait_by_t), default=None) for g in gs]
        has_w = any(x is not None for x in wv)
        CH_ = 190
        ctop = max(min(max([x for x in wv if x is not None], default=1) * 1.1, 4), 1.5)
        def CY(x): return 10 + CH_ - min(x, ctop) * CH_ / ctop
        cruns, cur_, last_ = [], [], -9
        for i, x in enumerate(wv):
            if x is None:
                continue
            if i - last_ > 3 and cur_:
                cruns.append(cur_); cur_ = []
            cur_.append((i, x)); last_ = i
        if cur_:
            cruns.append(cur_)
        cpoly = ""
        for run in cruns:
            pts_ = " ".join(f"{X(i):.1f},{CY(x):.1f}" for i, x in run)
            ar_ = f"{X(run[0][0]):.1f},{10 + CH_} {pts_} {X(run[-1][0]):.1f},{10 + CH_}"
            cpoly += (f'<polygon class=wa points="{ar_}"/><polygon class=wah points="{ar_}" clip-path="url(#wabove{sfx})"/>'
                      f'<polyline class=wl points="{pts_}"/><polyline class=wlh points="{pts_}" clip-path="url(#wabove{sfx})"/>')
        cores_n = int(v.get("cores") or 0)
        held_t = {t for t in raw if t[:10] == T[-1][:10]} if r == 1 else raw
        cpu_held = sum(1 for t in held_t if cause.get(t) in ("cpu", "both"))
        worst_w = max(((wait_by_t[t], t) for t in raw if t in wait_by_t), default=(None, None))
        csh = {}
        for t in raw:
            for g_, x in capps.get(t, {}).items():
                csh[g_] = csh.get(g_, 0) + x
        ctot = sum(csh.values())
        if ctot:
            csc = max(csh.values())
            cwho = "".join(f'<div class=row style="--i:{j}" title="{e(g_)}"><span>{e(g_)}</span><div class=track><b style="--w:{x / csc * 100:.0f}%"></b></div><em>{x / ctot * 100:.0f}%</em></div>'
                           for j, (g_, x) in enumerate(sorted(csh.items(), key=lambda kv: -kv[1])[:9]) if x / ctot >= .005)
            cwho += f'<p class=note style="margin-top:8px">Share of all the processor time used, from {e(lab(min(t for t in raw if t in capps)))}.</p>'
        else:
            cwho = '<p class=note>The per-app processor log starts with the next reading.</p>'
        capg = {}
        for i, g in enumerate(gs):
            acc, k_ = {}, 0
            for j in g:
                if T_all[j] in capps:
                    k_ += 1
                    for g_, x in capps[T_all[j]].items():
                        acc[g_] = acc.get(g_, 0) + x
            if k_:
                capg[str(i)] = sorted(((g_, round(x / k_, 1)) for g_, x in acc.items()), key=lambda kv: -kv[1])[:3]
        cdata = json.dumps({"t": T, "w": [None if x is None else round(x, 2) for x in wv], "apps": capg, "b": b, "ml": ml,
                            "top": ctop, "ch": CH_, "cores": cores_n}).replace("</", "<\\/")
        mdata = json.dumps({"t": T, "need": [round(x, 2) for x in need], "ram": [round(x, 2) for x in U], "b": b, "pk": pk, "top": round(top, 3),
                            "swap": [round(x) for x in gswap], "cause": tc, "cn": CAUSE_NAMES}).replace("</", "<\\/")
        peak_d = v["apps"].get(peak_t, {})
        since_ = mstamp(T_all[ix_[0]]) > mstamp(T_all[-1]) - 1440 * r + 30 and r > 1
        h2 = (f"Processors held it up <em class=nw>{span(cpu_held)}</em> {when}" if cpu_first and cpu_held else
              f"{when[0].upper() + when[1:]} it needed <em>{gb(peak)} GB</em>" if peak > TOTAL else
              f"{when[0].upper() + when[1:]} it has <em>fitted</em>{' so far' if when == 'today' else ''}")
        return f"""<div class=rv data-r={r}{"" if r == 1 else " hidden"}>
<div class=en><h2 class=big>{h2}</h2>{f'<p class=note style="margin:8px 0 14px">Measured since {e(lab(T_all[ix_[0]]))}; the monitor has not run longer than that yet.</p>' if since_ else ""}</div>
<p class="lede en" style="--n:1">{"Two things can hold it up, and the one that held it up more comes first. " if has_w else ""}{"The purple line is work waiting for the processors: above its dotted line there was more work than its " + str(cores_n) + " cores could run. " if has_w else ""}The red line is everything held in memory: above the dotted {TOTAL:.0f} GB line it no longer fits, so the striped part sits on the disk, and the drops are the minutes it was moving memory out. {f"Each point is the busiest minute of {b}. " if b > 1 else ""}Hover to read any {"minute" if b == 1 else "point"}.</p>
<div class="todays{" cpufirst" if cpu_first else ""}">
{f"""<div class="two tcpu">
<div class="c chartbox en cchart" style="--n:2">
<small>Processors: work waiting, as &times; its {cores_n} cores</small>
<svg class=ws viewBox="0 -14 {W} {CH_ + 52}" role=img aria-label="Work waiting for the processors per minute, against the {cores_n} cores this Mac has">
<clipPath id=wabove{sfx}><rect x=0 y=-20 width={W} height={CY(1) + 20:.1f} /></clipPath>
<rect class=czb x=0 y=10 width={W} height={CH_} rx=8 />{cpoly}
<line class=ceil x1=0 x2={W} y1={CY(1):.1f} y2={CY(1):.1f} /><text x={W} y=2 class=tk text-anchor=end>dotted line: 1&times;, more work than its {cores_n} cores can run</text>
{f'<text x="{X(cruns[0][0][0]) - 6:.1f}" y="{CH_ + 2}" class=tk text-anchor=end>measured from {e(lab(T[cruns[0][0][0]]))}</text>' if cruns and cruns[0][0][0] > 30 else ""}
{ticks.replace(f'y="{H + 20}"', f'y="{CH_ + 32}"')}
<line class=xh x1=0 x2=0 y1=10 y2={10 + CH_} /></svg>
<div class=tip></div>
<script type=application/json class=cdata>{cdata}</script>
</div>
<div class="c en" style="--n:3"><small>Who kept the processors busy {when}{f", worst at {e(lab(worst_w[1]))} ({worst_w[0]:.1f}&times;)" if worst_w[1] is not None else ""}</small><div class=list>{cwho}</div></div>
</div>""" if has_w else ""}
<div class="two tmem">
<div class="c chartbox en mchart" style="--n:2">
<svg class=ts viewBox="0 -30 {W} {H + 170}" role=img aria-label="Memory needed per minute against the {TOTAL:.0f} GB the Mac has">
<clipPath id=above{sfx}><rect x=0 y=-40 width={W} height={ram_y + 40:.1f} /></clipPath><clipPath id=below{sfx}><rect x=0 y={ram_y:.1f} width={W} height={H} /></clipPath>
<polygon class=under points="{area}" clip-path="url(#below{sfx})"/>
<polygon class=over points="{area}" clip-path="url(#above{sfx})"/>
<line class=ceil x1=0 x2={W} y1={ram_y:.1f} y2={ram_y:.1f} />
<text x=8 y={ram_y + 20:.1f} class=tk>{TOTAL:.0f} GB: all the memory this Mac has</text>
<polyline class=ram pathLength=1 points="{upts}"/>
<polyline class=need pathLength=1 points="{pts}"/>
<g transform="translate({px:.1f} {py:.1f})"><line x1=0 y1=0 x2=0 y2=-46 stroke="var(--fg)" stroke-width=2 />
<path class=flagb d="M0 -46 h{-74 if flag_left else 74} v22 h{74 if flag_left else -74}z" fill="var(--hot)"/>
<text x="{-37 if flag_left else 37}" y=-30 text-anchor=middle fill="#fff" font-family="Fredoka,sans-serif" font-weight=700 font-size=14>{gb(peak)} GB</text>
<circle r=6 fill="var(--bg)" stroke="var(--hot)" stroke-width=3 /></g>
<line class=xh x1=0 x2=0 y1=0 y2={H} />
<g class=walker>{mini(0, 0, 40, mood=mood)}</g>
{ticks}
<g class=drops transform="translate(0 {H + 30})">{"".join(drops)}</g>
<text x=0 y={H + 104} class=tk>Drops: {"minutes" if b == 1 else "stretches"} it pushed memory to disk (worst: {max(LO):.0f} MB at {e(swap_when)})</text>
<g class=peek>{mini(W - 34, H + 2, 46, flip=True, mood=mood)}</g>
<rect class=czb x=0 y={CB} width={W} height=16 rx=4 />{"".join(band)}
<text x=0 y={CB + 36} class=tk>What held it up, {"minute by minute (blank: nothing did)" if b == 1 else f"{b} minutes at a time (fainter: held up for fewer of them)"}{(" &middot; " + band_note) if band_note else ""}</text>
</svg>
<div class=tip></div>
<script type=application/json class=mdata>{mdata}</script>
</div>
<div class="c en" style="--n:3"><small>What held the memory at {"today&#x27;s busiest minute" if when == "today" else "the busiest minute " + when}, {e(peak_when)}</small><div class=list>{bars(peak_d, peak_t)}</div></div>
</div>
<div class="legend en" style="--n:4"><span><i style="background:var(--hot)"></i>memory needed (in RAM + parked on disk)</span><span><i style="background:var(--ram)"></i>in RAM</span><span><i style="background:repeating-linear-gradient(45deg,var(--hot) 0 2px,transparent 2px 5px)"></i>overflow onto disk</span><span>{swap_mins} minutes swapping, {heavy_mins} of them heavy</span></div>
<div class="legend en" style="--n:5">{CAUSE_KEY}</div>
</div></div>"""

    # ---------- panel 4: history as stacked buddy heads ----------
    days = [d for d in v["days"] if d >= min(day_sess)]
    HW = 1000
    cw = HW / len(days)
    r = cw * .42
    HH = r * 2.15 * hist_max + r * 2
    heads = []
    for i, d in enumerate(days):
        k_, at = day_sess.get(d, (0, ""))
        if not k_:
            continue
        cx = i * cw + cw / 2
        hot = k_ >= 10
        col = "".join(f'<use href="#head" transform="translate({cx:.1f} {HH - r - j * r * 2.15:.1f}) scale({r:.2f})"/>' for j in range(k_))
        heads.append(f'<g class="col{" hot" if hot else ""}" style="--i:{i}"><rect x="{i*cw:.1f}" y="0" width="{cw:.1f}" height="{HH}" fill="transparent"/>{col}'
                     f'<title>{dt.date.fromisoformat(d).strftime("%a %-d %b")}: {k_} sessions at once (around {at})</title></g>')
    # measured overflow per day: busiest minute over this Mac's RAM, and minutes of heavy swapping
    heavy = {}
    lp_ = os.path.join(v["HOME"], "live.csv")
    if os.path.exists(lp_):
        for l in open(lp_):
            f_ = l.strip().split(",")
            if len(f_) == 6 and float(f_[1]) >= 100:
                heavy[f_[0][:10]] = heavy.get(f_[0][:10], 0) + 1
    dmem = v["day_mem"]
    OH = HH * .55
    omax = max([dmem[d][0] - TOTAL for d in days if d in dmem] + [4])
    obars = []
    for i, d in enumerate(days):
        cx = i * cw + cw / 2
        if d in dmem:
            ov = max(dmem[d][0] - TOTAL, 0)
            h_ = max(OH * ov / omax, 3)
            obars.append(f'<g class=ob style="--i:{i}"><rect x="{cx - cw*.35:.1f}" y="0" width="{cw*.7:.1f}" height="{h_:.1f}" rx="{min(cw*.3, 6):.1f}" fill="var(--hot)"/>'
                         ''
                         f'<title>{dt.date.fromisoformat(d).strftime("%a %-d %b")}: busiest minute needed {dmem[d][0]:.1f} GB at {dmem[d][1]}, {ov:.1f} GB more than the {TOTAL:.0f} GB this Mac has; {heavy.get(d, 0)} minutes of heavy swapping</title></g>')
        else:
            obars.append(f'<circle cx="{cx:.1f}" cy="4" r="1.6" fill="var(--mute)" opacity=".35"><title>{d}: memory not measured (the monitor started {since})</title></circle>')
    dcause = {}
    for t, c_ in cause.items():
        if c_:
            dc_ = dcause.setdefault(t[:10], {}); dc_[c_] = dc_.get(c_, 0) + 1
    CY0, CHh = HH + 34, OH * .8           # the held-up row sits right under the line; memory over RAM comes below it
    M0 = CY0 + CHh + 34
    cmax = max([sum(dcause.get(d, {}).values()) for d in days] + [30])
    cbars = []
    for i, d in enumerate(days):
        dc_ = dcause.get(d, {})
        if not dc_:
            continue
        y_, cx = 0, i * cw + cw / 2
        segs = ""
        for k_ in ("cpu", "both", "mem", "heat"):
            if dc_.get(k_):
                h_ = max(CHh * dc_[k_] / cmax, 1.5)
                segs += f'<rect class="cz {k_}" x="{cx - cw*.35:.1f}" y="{y_:.1f}" width="{cw*.7:.1f}" height="{h_:.1f}"/>'
                y_ += h_
        unmeas = " (processors not measured yet that day)" if not cpu_from or d < cpu_from[:10] else ""
        cbars.append(f'<g class=ob style="--i:{i}">{segs}<title>{dt.date.fromisoformat(d).strftime("%a %-d %b")}: held up for '
                     + ", ".join(f"{dc_[k_]} min by {held(k_)}" for k_ in ("cpu", "both", "mem", "heat") if dc_.get(k_)) + f"{unmeas}</title></g>")
    meas = [d for d in days if d in dmem]
    dheld = {d: sum(dcause.get(d, {}).values()) for d in meas}
    held_days = [d for d in meas if dheld[d] >= 30]       # a day counts as held up after half an hour of it
    def dom_(d):
        dc_ = dcause.get(d, {})
        return max(dc_, key=dc_.get) if dc_ else ""
    over_days = sum(1 for d in meas if dmem[d][0] > TOTAL)
    worst_d = max(meas, key=lambda d: dmem[d][0]) if meas else None
    ten_y = HH - 10 * r * 2.15 + r
    hticks = "".join(f'<text x="{i*cw:.1f}" y="{HH + 20}" class=tk>{dt.date.fromisoformat(d).strftime("%-d %b")}</text>'
                     for i, d in enumerate(days) if d.endswith("-01") or d.endswith("-15"))
    top_days = sorted(day_sess.items(), key=lambda kv: -kv[1][0])[:5]
    top_html = "".join(f'<li><svg viewBox="0 0 30 46" aria-hidden=true>{mini(15, 45, 44, suit="#e5484d")}</svg><b>{k_}</b><span>sessions<br><i>{dt.date.fromisoformat(d).strftime("%a %-d %b")}</i><br><i class={"ovh" if d in v["day_mem"] else "ovn"}>{f"+{max(v['day_mem'][d][0] - TOTAL, 0):.1f} GB over {TOTAL:.0f}" if d in v["day_mem"] else "memory not measured"}</i></span></li>'
                       for d, (k_, _) in top_days)

    # ---------- who is holding memory ----------
    peak_t = T[pk]
    peak_d = v["apps"].get(peak_t, {})

    def bars(d, t=None):
        if not d:
            return f'<p class=note>Not recorded for this minute: the per-app log started on {since}.</p>'
        sc = max(d.values())
        out = ""
        for j, (g, x) in enumerate(sorted(d.items(), key=lambda kv: -kv[1])):
            if x < .05:
                continue
            row = f'<div class="row" style="--i:{j}" title="{e(g)}"><span>{e(g)}</span><div class=track><b style="--w:{x/sc*100:.0f}%"></b></div><em>{x:.1f} GB</em></div>'
            sub = breakdown(t, g) if t and g in ("Tools Claude starts", "Browsers Claude drives") else ""
            out += f'<details class=kind><summary>{row}</summary>{sub}</details>' if sub else row
        return out

    # ---------- what Claude is running: per job, per session ----------
    tj, tfirst = {}, None
    stamp_now = v.get("stamp", "")
    tp = os.path.join(v["HOME"], "tools.csv")
    if os.path.exists(tp):
        for l in open(tp):
            t_, se, jb, g_ = l.rstrip("\n").split(",")
            tfirst = tfirst or t_
            tj.setdefault(t_, {})[(se, jb)] = float(g_)
    KINDS = [  # (name, what it is); first match wins
        ("Test browsers", "Hidden Chrome windows a script opened to load and check a web page (Playwright)."),
        ("Claude plug-ins (MCP)", "Small helper servers that give Claude extra tools, such as driving a browser."),
        ("Page checks and tests", "Scripts that check a dashboard or run tests, before or after a change."),
        ("Google Cloud and GitHub", "Command-line tools talking to BigQuery, Google Cloud or GitHub."),
        ("Build and data scripts", "Python or Node scripts that build pages or pull data."),
        ("Claude's shell and housekeeping", "The shell Claude types commands into, plus backups and small helpers."),
    ]

    def tidy(jb):  # readable job names; also cleans rows logged before the names were fixed
        jb = jb.replace(" \u2192 its Chrome", "").replace(" → its Chrome", "")
        if jb.startswith("MCP server: "):
            n_ = jb[12:].strip("-").replace("cli-mcp", "Claude in Chrome").replace("playwright/mcp", "Playwright").replace("playwright-mcp", "Playwright")
            return "MCP: " + n_
        if jb.startswith("snapshot-zsh"):
            return "Claude's shell"
        return {"gcloud.py": "gcloud", "bq.py": "bq"}.get(jb, jb)

    def kind(raw):
        jb = tidy(raw)
        lo = jb.lower()
        if raw.startswith("Chrome opened by") or "its Chrome" in raw:
            return KINDS[0][0]
        if jb.startswith("MCP"):
            return KINDS[1][0]
        if any(k in lo for k in ("check", "test", "mustfail", "preflight", "pytest", "shot", "proto", "pw_run")):
            return KINDS[2][0]
        if lo.split()[0] in ("gcloud", "bq", "git", "gh"):
            return KINDS[3][0]
        if lo.endswith((".py", ".js", ".mjs", ".ts")):
            return KINDS[4][0]
        return KINDS[5][0]

    def label(raw):
        jb = tidy(raw)
        return ("Chrome for " + tidy(jb.replace("Chrome opened by ", ""))) if raw.startswith("Chrome opened by") or "its Chrome" in raw else jb

    def breakdown(t, g):  # one minute's Claude jobs inside an app group, by kind
        rows = {}
        for (se, jb), g_ in tj.get(t, {}).items():
            k_ = kind(jb)
            if (k_ == KINDS[0][0]) != (g == "Browsers Claude drives"):
                continue
            rows.setdefault(k_, []).append((g_, label(jb), se))
        if not rows:
            return ""
        h_ = ""
        for k_, items in sorted(rows.items(), key=lambda kv: -sum(x[0] for x in kv[1])):
            items.sort(reverse=True)
            h_ += f'<p class=kd><b>{e(k_)}</b> &middot; {sum(x[0] for x in items):.1f} GB</p><ul class=jl>' + "".join(
                f'<li><span><b>{e(jb)}</b> <i>{e(se)}</i></span><em>{g_:.1f} GB</em></li>' for g_, jb, se in items[:5]) + "</ul>"
        return h_

    def claude_views(src, cpu):
        fmt = (lambda x: f"{x:.0f}%") if cpu else (lambda x: f"{x:.1f} GB")
        last_t = max(src) if src else stamp_now
        last_dt = dt.datetime.strptime(last_t, "%Y-%m-%d %H:%M")
        views, take_k = [], None
        for vid, vname, hours in (("now", "Now", 0), ("d1", "24 hours", 24), ("d7", "7 days", 168), ("d30", "30 days", 720)):
            cut_ = (last_dt - dt.timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M")
            mins_ = [t_ for t_ in src if (t_ == last_t if hours == 0 else t_ > cut_)]
            ks, peak_k, per_min = {}, {}, {}
            for t_ in mins_:
                for (se, jb), g_ in src[t_].items():
                    k_ = kind(jb)
                    ks.setdefault(k_, {}).setdefault((se, label(jb)), 0)
                    ks[k_][(se, label(jb))] += g_ / len(mins_)  # average over the window's minutes (now: this minute)
                    per_min[(t_, k_)] = per_min.get((t_, k_), 0) + g_
            for (t_, k_), g_ in per_min.items():
                peak_k[k_] = max(peak_k.get(k_, 0), g_)
            tot = {k_: sum(v_.values()) for k_, v_ in ks.items()}
            if hours == 168 and peak_k:
                take_k = max(peak_k.items(), key=lambda kv: kv[1])
            if not tot:
                body = '<p class=note>' + ("Processor use per tool is recorded from the next reading on." if cpu and not src else "Nothing from Claude in this window.") + '</p>'
            else:
                sc = max(tot.values())
                desc = dict(KINDS)
                body = '<p class=uh><span>Group</span><span>' + (("share of all cores now" if cpu else "memory now") if hours == 0 else
                                                                  ("average &middot; busiest minute, % of all cores" if cpu else "average &middot; busiest minute, GB")) + '</span></p>'
                for j_, (k_, x) in enumerate(sorted(tot.items(), key=lambda kv: -kv[1])):
                    topj = sorted(ks[k_].items(), key=lambda kv: -kv[1])[:6]
                    inner = "".join(f'<li><span><b>{e(jb)}</b> <i>{e(se)}</i></span><em>{fmt(g_)}</em></li>' for (se, jb), g_ in topj)
                    more = len(ks[k_]) - len(topj)
                    val = fmt(x) if hours == 0 else (f"{x:.0f} &middot; {peak_k.get(k_, 0):.0f}" if cpu else f"{x:.1f} &middot; {peak_k.get(k_, 0):.1f}")
                    body += (f'<details class=kind style="--i:{j_}"><summary><div class="row jr"><span><b>{e(k_)}</b><br><i>{len(ks[k_])} job{"s" if len(ks[k_]) != 1 else ""}</i></span>'
                             f'<div class=track><b style="--w:{x/sc*100:.0f}%"></b></div><em>{val}</em></div></summary>'
                             f'<p class=kd>{e(desc[k_])}</p><ul class=jl>{inner}</ul>{f"<p class=kd>+{more} smaller</p>" if more > 0 else ""}</details>')
            views.append((vid, vname, hours, body))
        first_t = min(src) if src else None
        have_h = (last_dt - dt.datetime.strptime(first_t, "%Y-%m-%d %H:%M")).total_seconds() / 3600 if first_t else 0
        tabs_ = "".join(f'<button type=button class=jt data-v={vid} aria-pressed={"true" if j_ == 0 else "false"}>{vn}</button>' for j_, (vid, vn, _, _) in enumerate(views))
        views_ = "".join(f'<div class=jv data-v={vid}{"" if j_ == 0 else " hidden"}>'
                         + ("" if h == 0 or have_h >= h else f'<p class=kd>Only {have_h:.0f} hours recorded so far, so this covers less than {vn}.</p>')
                         + f'<div class=list>{b_}</div></div>' for j_, (vid, vn, h, b_) in enumerate(views))
        return tabs_, views_, take_k
    jobs_tabs, jobs_views, take_k = claude_views(tj, False)
    cjobs_tabs, cjobs_views, take_kc = claude_views(tjc, True)

    # ---------- panel 6: memory jars ----------
    def jar(cx, cap, fill_gb, label, sub, spill):
        jw, jh, base = 190, 230, 300
        level = min(fill_gb / cap, 1)
        fh = (jh - 20) * level
        inner = f'<clipPath id="jc{cap}"><rect x="{cx - jw/2 + 8}" y="{base - jh + 12}" width="{jw - 16}" height="{jh - 20}" rx="26"/></clipPath>'
        bananas = "".join(f'<use href="#nana" x="{cx - jw/2 + 22 + (k*37) % (jw - 50)}" y="{base - 26 - (k*29) % max(fh - 30, 1)}" width="34" height="34" transform="rotate({(k*47) % 60 - 30} {cx} {base})" opacity=".9"/>'
                          for k in range(int(fill_gb * 1.4)))
        spill_g = ""
        if spill:
            spill_g = "".join(f'<use class=spill href="#nana" x="{cx - 70 + k*24}" y="{base - jh - 30}" width="30" height="30" style="--k:{k}"/>' for k in range(6))
            spill_g += f'<text x="{cx}" y="{base - jh - 40}" text-anchor=middle class="jtag bad">{fill_gb - cap:.0f} GB spills onto the disk</text>'
        room = "" if spill else f'<text x="{cx}" y="{base - jh + 50}" text-anchor=middle class="jtag good">{cap - fill_gb:.0f} GB of room left</text>'
        sitter = "" if spill else mini(cx + 40, base - fh + 4, 54, cls="sit")
        return (f'<g class="jar{" full" if spill else ""}">{inner}'
                f'<rect x="{cx - jw/2}" y="{base - jh}" width="{jw}" height="{jh}" rx="34" class=glass />'
                f'<g clip-path="url(#jc{cap})"><rect class=fill x="{cx - jw/2}" y="{base - fh - 8}" width="{jw}" height="{fh + 8}" style="--fh:{fh:.0f}px"/>{bananas}</g>'
                f'<rect x="{cx - jw/2 - 8}" y="{base - jh - 12}" width="{jw + 16}" height="22" rx="10" class=lid />'
                f'{spill_g}{room}{sitter}'
                f'<text x="{cx}" y="{base + 34}" text-anchor=middle class=jlabel>{label}</text>'
                f'<text x="{cx}" y="{base + 56}" text-anchor=middle class=tk>{sub}</text></g>')
    jars = jar(260, TOTAL, peak_ever, f"This Mac: {TOTAL:.0f} GB", f"the busiest minute needed {peak_ever:.1f} GB", peak_ever > TOTAL) + \
           jar(740, rec, peak_ever, f"Recommended: {rec} GB", "the same busiest minute", False)

    # ---------- heatmap panel ----------
    CW, CH, LX, TY = 50, 34, 46, 24
    HRS = list(v.get("hrs", range(24)))       # this page's hours: working hours, or all 24
    WDS = list(v.get("wds", range(7)))        # and days: Monday to Friday, or all seven
    wcell = {k: x for k, x in cell.items() if k[1] in HRS}
    lo_ = min(wcell.values()) if wcell else 0; hi_ = max(wcell.values()) if wcell else 1
    def shade(x):  # one hue, light to dark (dataviz: sequential = single hue)
        f = (x - lo_) / max(hi_ - lo_, .01)
        return f"color-mix(in oklab, #e5484d {15 + 85*f:.0f}%, #fff4cc)"
    hm = []
    names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for row_, wd in enumerate(WDS):
        hm.append(f'<text x="{LX-8}" y="{TY + row_*CH + CH*.62:.0f}" text-anchor=end class=tk>{names[wd]}</text>')
        for h in HRS:
            x_, y_ = LX + (h - HRS[0])*CW, TY + row_*CH
            if (wd, h) in cell:
                val = cell[(wd, h)]
                ring = f'<circle cx="{x_ + CW/2 - 1:.0f}" cy="{y_ + CH/2 - 1:.0f}" r="4" fill="#fff"/>' if val > TOTAL else ""
                hm.append(f'<g class=hc style="--i:{wd*24+h}"><rect x="{x_}" y="{y_}" width="{CW-2}" height="{CH-2}" rx="7" style="fill:{shade(val)}"/>{ring}'
                          f'<title>{names[wd]} {h:02d}:00–{h:02d}:59: highest need {val:.1f} GB{" (over " + str(int(TOTAL)) + " GB)" if val > TOTAL else ""}</title></g>')
            else:
                hm.append(f'<rect x="{x_}" y="{y_}" width="{CW-2}" height="{CH-2}" rx="7" class=empty><title>{names[wd]} {h:02d}:00: no reading yet</title></rect>')
    for h in range(HRS[0], HRS[-1] + 1, 2):
        hm.append(f'<text x="{LX + (h - HRS[0])*CW + CW/2 - 1:.0f}" y="{TY - 8}" text-anchor=middle class=tk>{h:02d}:00</text>')
    ccell = {}
    for t, c_ in cause.items():
        d_ = dt.datetime.strptime(t, "%Y-%m-%d %H:%M"); cc = ccell.setdefault((d_.weekday(), d_.hour), {})
        cc["n"] = cc.get("n", 0) + 1
        if c_:
            cc[c_] = cc.get(c_, 0) + 1
    hc2 = []
    for row_, wd in enumerate(WDS):
        for h in HRS:
            cc = ccell.get((wd, h))
            if not cc:
                continue
            x_, y_ = LX + (h - HRS[0])*CW, TY + row_*CH
            hk = [k_ for k_ in ("cpu", "both", "mem", "heat") if cc.get(k_)]
            if not hk:
                hc2.append(f'<rect x="{x_}" y="{y_}" width="{CW-2}" height="{CH-2}" rx="7" class=cz0><title>{names[wd]} {h:02d}:00: nothing held it up ({cc["n"]} minutes)</title></rect>')
                continue
            dom = max(hk, key=cc.get); share = sum(cc[k_] for k_ in hk) / cc["n"]
            hc2.append(f'<rect x="{x_}" y="{y_}" width="{CW-2}" height="{CH-2}" rx="7" style="fill:color-mix(in oklab,var(--c-{dom}) {30 + 70*share:.0f}%,var(--bg))">'
                       f'<title>{names[wd]} {h:02d}:00: held up {share:.0%} of {cc["n"]} minutes, mostly by {held(dom)} ('
                       + ", ".join(f"{held(k_)} {cc[k_]}" for k_ in hk) + ')</title></rect>')
    heat_svg = "".join(hm) + f'<g class=hmc>{"".join(hc2)}</g>'
    seen_hours = sum(1 for (_, h) in cell if h in HRS)   # the same hours the memory view counts, so the switch keeps one total
    held_hours = sum(1 for k_, cc in ccell.items() if k_[1] in HRS and k_ in cell and sum(cc.get(x_, 0) for x_ in ("cpu", "both", "mem", "heat")) >= .1 * cc["n"])
    heat_w, heat_h = LX + len(HRS)*CW + 4, TY + len(WDS)*CH + 6
    filled = sum(1 for (_, h) in cell if h in HRS)

    # ---------- Recommendation: how often each size would have been enough ----------
    BR = "Browsers Claude drives"
    apps_all = v["apps"]
    work = list(all_need)
    split_t = min((t for t, d_ in apps_all.items() if BR in d_), default=None)
    def fits(sz, vals):
        return sum(x <= sz for _, x in vals) / max(len(vals), 1)
    LADDER = sorted({16, 24, 32, 36, 48, 64, int(round(TOTAL))})
    budget = next((x for x in LADDER if fits(x, work) >= .99), rec)
    fit16 = fits(TOTAL, work)
    wdays = sorted({t[:10] for t, _ in work})
    n_wd = sum(1 for d in wdays if dt.date.fromisoformat(d).weekday() < 5)
    WD_GOAL = 10
    ladder = ""
    for sz in LADDER:
        f_ = fits(sz, work)
        tag = " &middot; this Mac" if sz == TOTAL else " &middot; recommended" if sz == rec else " &middot; budget pick" if sz == budget else ""
        ladder += (f'<div class="row lad{" me" if sz == rec else ""}" data-sz="{sz}" style="--i:{LADDER.index(sz)}"><span><b>{sz} GB</b>{tag}</span>'
                   f'<div class=track><b style="--w:{max(f_ * 100, 2):.0f}%"></b></div><em>{f_:.0%}</em></div>')
    cpu_rows = []
    cp_ = os.path.join(v["HOME"], "cpu.csv")
    if os.path.exists(cp_):
        cpu_rows = list({r[0]: r for r in (l.strip().split(",") for l in open(cp_) if l.count(",") == 3)}.values())  # a reinstall can write a minute twice
    # Processors: in how many working minutes would a chip with this many cores have kept up (load average <= cores)?
    # Counts cores only. Newer chips' cores are faster than an older Mac's, so this overstates the need.
    cores = int(cpu_rows[-1][3]) if cpu_rows else 0
    loadw = [(r[0], float(r[2])) for r in cpu_rows]
    cpu_ok = len(loadw) >= 60
    CORE_LADDER = sorted({cores, 10, 12, 14, 16}) if cores else []
    def cfits(c):
        return sum(l_ <= c for _, l_ in loadw) / max(len(loadw), 1)
    CHIP_COVER = .9   # the pick keeps up in 9 working minutes of 10: waiting work slows things down, it does not stall them
    chip = next((c for c in CORE_LADDER if cfits(c) >= CHIP_COVER), None) if cpu_ok else cores
    chip_up = cpu_ok and (chip is None or chip > cores)
    chip_b = f"{chip} cores" if chip else f"{CORE_LADDER[-1]}+ cores"
    cpu_days = len({t[:10] for t, _ in loadw if dt.date.fromisoformat(t[:10]).weekday() < 5})
    wait_pct = 1 - cfits(cores) if cpu_ok else 0
    cl_rows = ""
    for k_, c in enumerate(CORE_LADDER):
        f_ = cfits(c)
        tag = " &middot; this Mac" if c == cores else " &middot; first pick" if c == chip else ""
        cl_rows += (f'<div class="row cad{" me" if c == chip and chip_up else ""}" data-c="{c}" style="--i:{k_}"><span><b>{c} cores</b>{tag}</span>'
                    f'<div class=track><b style="--w:{max(f_ * 100, 2):.0f}%"></b></div><em>{f_:.0%}</em></div>')
    # The verdict: working minutes since the processors were first measured, by what held them up.
    # The other measures over the same working minutes: did heat slow it, did graphics, disk or network go over their lines?
    wmin = {t for t, c_ in cause.items() if cpu_from and t >= cpu_from}
    oth = {"n": 0, "over": 0, "hot": 0, "slowed": 0}
    io_ = {r[0]: r for r in rows_("io.csv", 5)}
    for r in rows_("heat.csv", 6):
        if r[0] not in wmin:
            continue
        oth["n"] += 1
        num = lambda x: float(x) if x not in ("", "-1", "-1.0") else -1
        fan = num(r[2]) / num(r[3]) * 100 if num(r[2]) >= 0 and num(r[3]) > 0 else -1
        oth["hot"] += num(r[4]) >= 90 or fan >= 60
        oth["slowed"] += r[1] in ("fair", "serious", "critical")
        q = io_.get(r[0])
        oth["over"] += num(r[5]) >= 85 or (q is not None and (num(q[1]) + num(q[2]) >= 1000 or num(q[3]) + num(q[4]) >= 500))
    p_cpu, p_mem = ((vc["cpu"] + vc["both"]) / vn, (vc["mem"] + vc["both"]) / vn) if vn else (0, 0)
    if vn >= 60:
        seg = "".join(f'<i class="cz {k_}" style="width:{vc[k_] / vn * 100:.2f}%" title="{held(k_)}: {vc[k_]} minutes"></i>' for k_ in vc if vc[k_])
        key = "".join(f'<span><i class="cz {k_}"></i>{held(k_)} <b>{vc[k_]:,} min</b> ({vc[k_] / vn:.0%})</span>' for k_ in vc)
        big, small = ("processors", "memory") if cpu_first else ("memory", "processors")
        why_txt = (f"The {big} held it up more often than the {small}. "
                   + ("Processors count as holding it up when more work is waiting than its cores can run; memory when it pushes 100 MB a minute or more to disk. ")
                   + ("Heat counts only when macOS slows the chip down to cool it, which has not happened yet." if not vc["heat"] else "Heat counts when macOS slowed the chip down to cool it."))
        verdict = (f'<div class="c en verdict" id=rec-why style="--n:2"><small>What held it up, {vn:,} {WM} since '
                   f'{dt.datetime.strptime(cpu_from, "%Y-%m-%d %H:%M").strftime("%-d %b")}</small>'
                   f'<div class=vbar role=img aria-label="Processors {vc["cpu"]}, both {vc["both"]}, memory {vc["mem"]}, heat {vc["heat"]} of {vn} minutes">{seg}</div>'
                   f'<div class="legend vkey">{key}</div><p class=note>{why_txt}</p></div>')
    else:
        verdict = ""

    lesson = lesson_html(hours_txt=HOURS_TXT, wm=WM, TOTAL=TOTAL, work=work, wdays=wdays, fits=fits, LADDER=LADDER, peak_ever=peak_ever,
                         peak_ever_when=peak_ever_when, target=target, rec=rec, budget=budget, fit16=fit16, disk_used=disk_used,
                         disk_txt=disk_txt, disk_rec=disk_rec, n_wd=n_wd, WD_GOAL=WD_GOAL,
                         cpu=dict(ok=cpu_ok, cores=cores, chip=chip, chip_b=chip_b, up=chip_up, wait=wait_pct, days=cpu_days,
                                  rows=[[c, round(cfits(c) * 100)] for c in CORE_LADDER], first=cpu_first, vn=vn,
                                  p_cpu=p_cpu, p_mem=p_mem, others=oth))
    # The headline names the bigger cause first.
    if rec > TOTAL:
        h1_html = (f"Get a chip with <em>{chip_b}</em>,<br>{rec} GB of memory<br>and {disk_txt} of storage." if chip_up and cpu_first else
                   f"Get <em>{rec} GB</em> of memory,<br>a chip with {chip_b}<br>and {disk_txt} of storage." if chip_up else
                   f"Get <em>{rec} GB</em> of memory<br>and {disk_txt} of storage.")
    else:
        h1_html = (f"This Mac&#x27;s memory is enough;<br>the processors want <em>{chip_b}</em>." if chip_up else
                   f"This Mac&#x27;s <em>{TOTAL:.0f} GB</em> is enough<br>for now.")
    kick_html = (f"Work waited on the processors in {p_cpu:.0%} of {WM}, and on memory in {p_mem:.0%}." if cpu_first else
                 f"My work has needed up to {peak_ever:.1f} GB of memory. This Mac has {TOTAL:.0f}.")

    # ---------- Busy hours: the takeaway ----------
    over_cells = sorted(((x, k) for k, x in wcell.items() if x > TOTAL), reverse=True)
    names_ = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    hours_take = (f"The worst so far: {names_[over_cells[0][1][0]]} {over_cells[0][1][1]:02d}:00, {over_cells[0][0]:.1f} GB." if over_cells else "No working hour has gone over yet.")

    # ---------- What uses memory: app groups over a time window, Claude's work opened up ----------
    a_last = max(apps_all) if apps_all else ""
    def uses_view(hours, src, tsrc, cpu):
        fmt = (lambda x: f"{x:.0f}%") if cpu else (lambda x: f"{x:.1f} GB")
        last = max(src) if src else ""
        if not last:
            return '<p class=note>' + ("The per-app processor log starts with the next reading." if cpu else "No readings yet.") + '</p>', 0
        if hours == 0:
            mins = [last]
        else:
            cut_ = (dt.datetime.strptime(last, "%Y-%m-%d %H:%M") - dt.timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M")
            mins = [t for t in src if t > cut_]
        tot, top_ = {}, {}
        for t in mins:
            for g, x in src[t].items():
                tot[g] = tot.get(g, 0) + x; top_[g] = max(top_.get(g, 0), x)
        avg = {g: x / len(mins) for g, x in tot.items()}
        tmins = [t for t in mins if t in tsrc]
        sc = max(avg.values()) if avg else 1
        desc = dict(KINDS)
        out = ""
        for j, (g, x) in enumerate(sorted(avg.items(), key=lambda kv: -kv[1])):
            if x < (.5 if cpu else .05):
                continue
            val = fmt(x) if hours == 0 else (f"{x:.0f} &middot; {top_[g]:.0f}" if cpu else f"{x:.1f} &middot; {top_[g]:.1f}")
            row = f'<div class="row ur" style="--i:{j}" title="{e(g)}"><span>{e(g)}</span><div class=track><b style="--w:{x/sc*100:.0f}%"></b></div><em>{val}</em></div>'
            sub = ""
            if g in ("Tools Claude starts", BR) and tmins:
                ks = {}
                for t in tmins:
                    for (se, jb), g_ in tsrc[t].items():
                        k_ = kind(jb)
                        if (k_ == KINDS[0][0]) != (g == BR):
                            continue
                        ks.setdefault(k_, {}); ks[k_][(se, label(jb))] = ks[k_].get((se, label(jb)), 0) + g_ / len(tmins)
                for k_, jobs_ in sorted(ks.items(), key=lambda kv: -sum(kv[1].values())):
                    topj = sorted(jobs_.items(), key=lambda kv: -kv[1])[:5]
                    sub += (f'<p class=kd><b>{e(k_)}</b> &middot; {fmt(sum(jobs_.values()))}{"" if hours == 0 else " on average"}. {e(desc[k_])}</p><ul class=jl>'
                            + "".join(f'<li><span><b>{e(jb_)}</b> <i>{e(se)}</i></span><em>{fmt(g_)}</em></li>' for (se, jb_), g_ in topj) + "</ul>")
            out += f'<details class=kind><summary>{row}</summary>{sub}</details>' if sub else row
        return out, len(mins)
    def uses_block(src, tsrc, cpu):
        uviews = []
        for vid, vname, hours in (("now", "Now", 0), ("d1", "24 hours", 24), ("d7", "7 days", 168), ("d30", "30 days", 720)):
            body, nmin = uses_view(hours, src, tsrc, cpu)
            short_ = "" if hours == 0 or nmin >= hours * 60 * .9 else f'<p class=kd>Only {nmin / 60:.0f} hours recorded in this window so far.</p>'
            head_ = '<p class=uh><span>App</span><span>' + (("share of all cores now" if cpu else "memory now") if hours == 0 else
                                                           ("average &middot; busiest minute, % of all cores" if cpu else "average &middot; busiest minute, GB")) + '</span></p>'
            uviews.append((vid, vname, short_ + head_ + body))
        tabs_ = "".join(f'<button type=button class=jt data-v={vid} aria-pressed={"true" if j == 0 else "false"}>{vn}</button>' for j, (vid, vn, _) in enumerate(uviews))
        views_ = "".join(f'<div class=jv data-v={vid}{"" if j == 0 else " hidden"}><div class=list>{b_}</div></div>' for j, (vid, _, b_) in enumerate(uviews))
        return tabs_, views_
    uses_tabs, uses_views = uses_block(apps_all, tj, False)
    cuses_tabs, cuses_views = uses_block(capps, tjc, True)
    # The processors view comes first wherever the processors held the Mac up more.
    m_first = "cpu" if cpu_first and capps else "mem"
    m_first_c = "cpu" if m_first == "cpu" and len(tjc) >= 60 else "mem"
    v["yard_measure"] = m_first          # buddy.py sizes the yard's buddies by the same measure (memlog.py reads it back)
    def mtabs(panel, first):
        return ('<div class="jtabs mtabs" role=group aria-label="Measure">' + "".join(
            f'<button type=button class="jt mt" data-m={m} aria-pressed={"true" if m == first else "false"}>{n_}</button>'
            for m, n_ in (("cpu", "Processors"), ("mem", "Memory")) if m == "mem" or capps) + '</div>')
    d7_cut = (dt.datetime.strptime(a_last, "%Y-%m-%d %H:%M") - dt.timedelta(days=7)).strftime("%Y-%m-%d %H:%M") if a_last else ""
    br_peak = max((d_.get(BR, 0) for t, d_ in apps_all.items() if t > d7_cut), default=0)

    cores_n = int(v.get("cores") or 0)
    # Working hours or all hours: two pages built from the same readings, one switch at the bottom of every tab.
    from urllib.parse import quote
    is_work = v.get("hours") == "work"
    def hlink(lbl, on, ok, tip):
        if on:
            return f'<button class="jt hs" aria-pressed=true title="{e(tip)}">{lbl}</button>'
        if not ok:
            return f'<button class="jt hs" disabled title="No readings inside working hours yet">{lbl}</button>'
        return f'<a class="jt hs" aria-pressed=false title="{e(tip)}" href="file://{quote(v.get("other", ""))}">{lbl}</a>'
    wt_ = v.get("work_txt", "Monday to Friday, 9am to 7pm")
    hours_switch = (hlink("Working hours", is_work, v.get("other_ok", True), f"Count only {wt_}")
                    + hlink("All hours", not is_work, True, "Count every minute the Mac was on"))
    t_on = ranges_on(T_all)                           # Today, then 3, 7 and 30 days once there is that much to show
    heat_sec = heat_section(v["HOME"], T[-1][:10])   # the Hot & slow tab; empty (and no tab) before any reading
    tabs = [("rec", "Recommendation"), ("today", "Today")] + ([("heat", "Hot & slow")] if heat_sec else []) + [("days", "Busy days"), ("hours", "Busy hours"), ("uses", "What uses the Mac" if capps else "What uses memory"), ("claude", "What Claude runs"), ("how", "How this works")]
    tab_html = "".join(f'<button role=tab data-go="{k}" aria-controls="p-{k}">{t}</button>' for k, t in tabs)

    return add_today_cpu(add_heat(add_lesson(f"""<!doctype html><html lang=en><head><meta charset=utf-8><script>try{{if(sessionStorage.getItem("mm-again"))document.documentElement.classList.add("again")}}catch(_){{}}
(function(){{var act=Date.now(),due=Date.now()+60000;["pointerdown","pointermove","wheel","keydown","touchstart","scroll"].forEach(function(t){{addEventListener(t,function(){{act=Date.now()}},{{passive:true,capture:true}})}});
setInterval(function(){{if(Date.now()<due||(!document.hidden&&Date.now()-act<45000))return;try{{sessionStorage.setItem("mm-again","1");var p=document.querySelector(".panel.on");if(p)sessionStorage.setItem("mm-scroll",JSON.stringify({{id:p.id,top:p.scrollTop}}))}}catch(_){{}}location.reload()}},5000)}})()</script>
<style>html{{background:#fff7d6}}</style>
<script>addEventListener("load",function(){{if(!document.documentElement.classList.contains("again"))return;
var f=function(){{document.getAnimations().forEach(function(a){{if(a.effect&&a.effect.getTiming().iterations!==Infinity)a.finish()}})}};f();setTimeout(f,50)}})</script>
<meta name=viewport content="width=device-width,initial-scale=1"><title>{"Too Small a Mac" if rec > TOTAL else "Mac Memory Check"}</title>
<link rel=icon type=image/png sizes=64x64 href="data:image/png;base64,{open(os.path.join(v['HOME'], 'icon', 'fav64.b64')).read()}"><link rel=apple-touch-icon href="data:image/png;base64,{open(os.path.join(v['HOME'], 'icon', 'fav64.b64')).read()}">
<link rel=icon href='data:image/svg+xml,{v["fav"]}'>
<link rel=preconnect href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Geist:wght@300;400;600;800&family=Geist+Mono:wght@400;600&display=swap" rel=stylesheet>
<style>
:root{{--bg:#fff8dc;--fg:#1d2a44;--mute:#5f6b80;--card:rgba(255,255,255,.8);--line:rgba(47,111,181,.16);--tone:{v["tone"]};--hot:#e5484d;--good:#2f9e5b;--ram:#2f6fb5;--banana:#ffd93b;--fillA:#ffe680;--fillB:#ffd23b;--c-cpu:#6e56cf;--c-mem:#e5484d;--c-both:#9b2d7f;--c-heat:#d98b06}}
@media(prefers-color-scheme:dark){{:root:not([data-theme=light]){{--bg:#0e1a2f;--fg:#f4f1e6;--mute:#9aa6bb;--card:rgba(255,217,59,.06);--line:rgba(255,217,59,.15);--hot:#ff6b6f;--good:#4ade80;--ram:#7fb0ef;--fillA:rgba(255,217,59,.55);--fillB:rgba(255,217,59,.12);--c-cpu:#8a78ee;--c-mem:#f0545a;--c-both:#c0479f;--c-heat:#d99a1c}}}}
*{{box-sizing:border-box;margin:0}}
html,body{{height:100%}}
body{{background:var(--bg);color:var(--fg);font:16px/1.5 Geist,-apple-system,sans-serif;overflow:hidden}}
body:before{{content:"";position:fixed;inset:-20%;z-index:-2;filter:blur(30px)}}
.app{{height:100dvh;display:grid;grid-template-rows:auto 1fr auto;grid-template-columns:minmax(0,1fr);width:100%}}
/* motionsites-style pill bar: brand left, filter chips, live pill */
header{{display:flex;align-items:center;gap:14px;padding:14px 20px 8px;max-width:1400px;width:100%;margin:0 auto}}
.brand{{font:700 18px Fredoka,sans-serif;display:flex;align-items:center;gap:8px;white-space:nowrap}}
.brand i{{width:10px;height:10px;border-radius:50%;background:var(--tone)}}
.tabs{{min-width:0;position:relative;display:flex;gap:4px;padding:5px;border-radius:999px;border:2px solid var(--line);background:color-mix(in srgb,var(--bg) 70%,transparent);backdrop-filter:blur(14px);margin:0 auto;overflow-x:auto;scrollbar-width:none}}
.tabs button{{all:unset;position:relative;z-index:1;padding:7px 14px;border-radius:999px;font:600 14px Geist,sans-serif;color:var(--mute);white-space:nowrap;cursor:pointer;transition:color .3s}}
.tabs button[aria-selected=true]{{color:var(--bg)}}
.tabs button:focus-visible{{outline:2px solid var(--ram);outline-offset:2px}}
.tabs .ink{{position:absolute;z-index:0;top:5px;bottom:5px;border-radius:999px;background:var(--fg);transition:left .5s cubic-bezier(.3,1.3,.5,1),width .5s cubic-bezier(.3,1.3,.5,1)}}
.tabs .rider{{position:absolute;z-index:2;top:-20px;width:20px;transition:left .5s cubic-bezier(.3,1.3,.5,1)}}
.live{{padding:6px 12px;border-radius:999px;background:var(--fg);color:var(--bg);font:600 13px 'Geist Mono',monospace;white-space:nowrap}}
/* When the seven tabs do not fit, the header tightens in steps (set by fitTabs below) rather than cutting a tab off. */
header.t1{{gap:10px}} header.t1 .tabs button{{padding:7px 10px;font-size:13.5px}}
header.t2 .brand{{font-size:0;gap:0}} header.t2 .live .lx{{display:none}}
header.t3 .tabs button{{padding:6px 8px;font-size:12.5px}} header.t4 .live{{display:none}} header.t5 .tabs{{gap:2px}} header.t5 .tabs button{{padding:6px 6px;font-size:12px}}
.stage{{position:relative;overflow:hidden}} .inner>:first-child{{margin-top:auto}} .inner>:last-child{{margin-bottom:auto}}
.panel{{position:absolute;inset:0;overflow-y:auto;overscroll-behavior:contain;padding:var(--top,80px) 20px var(--bot,64px);opacity:0;visibility:hidden;transform:translateY(56px) scale(.985);filter:blur(4px);
 transition:opacity .7s cubic-bezier(.22,1,.36,1),transform .9s cubic-bezier(.22,1,.36,1),filter .7s,visibility 0s .9s}}
.panel.on{{opacity:1;visibility:visible;transform:none;filter:none;transition:opacity .7s cubic-bezier(.22,1,.36,1) .08s,transform .9s cubic-bezier(.22,1,.36,1),filter .7s,visibility 0s}}
.panel.above{{transform:translateY(-56px) scale(.985)}}
.dots{{position:fixed;right:14px;top:50%;transform:translateY(-50%);display:grid;gap:10px;z-index:6}}
.dots button{{all:unset;width:9px;height:9px;border-radius:9px;background:var(--line);cursor:pointer;transition:height .5s cubic-bezier(.22,1,.36,1),background .3s}}
.dots button[aria-current=true]{{height:28px;background:var(--fg)}}
@media(prefers-reduced-motion:reduce){{.panel,.panel.on{{transition:opacity .2s,visibility 0s;transform:none;filter:none}}}}
@media(max-width:860px){{.dots{{display:none}}}}
.inner{{max-width:1200px;min-height:100%;margin:0 auto;display:flex;flex-direction:column;justify-content:flex-start;gap:clamp(10px,1.8vh,18px)}}
.kick{{font:600 13px 'Geist Mono',monospace;color:var(--mute)}}
h2.big{{font:700 clamp(2rem,4.6vw,3.8rem)/1 Fredoka,sans-serif;text-transform:uppercase;letter-spacing:-.01em}}
h2.big em,.hero h1 em{{font-style:normal;background:linear-gradient(100deg,#ffb800,#e5484d);-webkit-background-clip:text;background-clip:text;color:transparent}}
.lede{{color:var(--mute);max-width:46rem}}
.c{{border:2px solid var(--line);border-radius:28px;background:var(--card);padding:18px 20px;position:relative}}
.c small{{display:block;color:var(--mute);font-size:13px}}
.note{{color:var(--mute);font-size:13px}}
.tk{{fill:var(--mute);font:12px 'Geist Mono',monospace}}
/* panel 1 */
.hero{{text-align:center}}
.hero h1{{font:700 clamp(2.2rem,5.4vw,4.4rem)/.98 Fredoka,sans-serif;text-transform:uppercase;max-width:62rem;margin:0 auto}}
.hero .lede{{margin:14px auto 0;font-size:clamp(1rem,1.6vw,1.15rem)}}
.proof{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}}
.proof .c b{{display:block;font:700 clamp(1.6rem,3vw,2.3rem)/1.1 Fredoka,sans-serif;color:var(--hot)}}
.proof .c span{{color:var(--mute);font-size:13px;line-height:1.4;display:block;margin-top:2px}}
.now{{display:flex;justify-content:center;align-items:center;gap:8px;color:var(--mute);font-size:14px}}
.now i{{width:9px;height:9px;border-radius:50%;background:var(--tone)}}
.buddy-wrap{{width:118px!important}} .buddy{{width:118px!important}} .bubble{{left:110px!important}}
/* panel 2 chart */
.chartbox{{position:relative}}
svg.ts{{width:100%;height:auto;display:block;overflow:visible;touch-action:pan-y}}
.ts .over{{fill:url(#hatch)}} .ts .under{{fill:url(#fa)}}
.ts .ceil{{stroke:var(--fg);stroke-width:2;stroke-dasharray:2 8;stroke-linecap:round;opacity:.7}}
.ts .need{{fill:none;stroke:var(--hot);stroke-width:3;stroke-linejoin:round;stroke-linecap:round}}
.ts .ram{{fill:none;stroke:var(--ram);stroke-width:2;stroke-linejoin:round}}
.ts .xh{{stroke:var(--fg);stroke-width:1;opacity:0}} .ts.hovering .xh{{opacity:.35}}
.drops rect,.drops circle{{fill:var(--hot);opacity:.85}}
.tip{{position:absolute;pointer-events:none;padding:8px 12px;border-radius:14px;background:var(--fg);color:var(--bg);font-size:13px;line-height:1.35;opacity:0;transform:translate(-50%,-110%);transition:opacity .15s;white-space:nowrap}}
.tip b{{font:600 15px Fredoka,sans-serif}} .tip i{{font-style:normal;display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:5px}}
.chartbox:hover .tip,.chartbox.touch .tip{{opacity:1}}
.legend{{display:flex;flex-wrap:wrap;gap:6px 18px;color:var(--mute);font-size:13px}} .legend i{{display:inline-block;width:14px;height:4px;border-radius:2px;margin-right:6px;vertical-align:3px}}
.two{{display:grid;grid-template-columns:2fr 1fr;gap:14px;align-items:start}}
/* what held it up: one colour per cause, the same on every tab */
.cz.cpu{{fill:var(--c-cpu);background:var(--c-cpu)}} .cz.mem{{fill:var(--c-mem);background:var(--c-mem)}} .cz.both{{fill:var(--c-both);background:var(--c-both)}} .cz.heat{{fill:var(--c-heat);background:var(--c-heat)}}
.czb{{fill:color-mix(in srgb,var(--ram) 6%,transparent)}} .cz0{{fill:color-mix(in srgb,var(--ram) 8%,transparent)}}
.legend i.cz{{width:12px;height:12px;border-radius:3px;vertical-align:-1px}} .tip i.cz{{border-radius:3px}}
.verdict{{margin:4px 0 14px}} .vbar{{display:flex;height:22px;border-radius:8px;overflow:hidden;background:color-mix(in srgb,var(--ram) 10%,transparent);margin:10px 0 8px;gap:2px}}
.vbar i{{display:block;height:100%}} .vkey b{{color:var(--fg)}}
.ladders{{display:flex;flex-direction:column;gap:18px}}
h2 .nw{{white-space:nowrap}}
.todays{{display:flex;flex-direction:column;gap:14px}} .todays.cpufirst .tcpu{{order:-1}}
.ws{{width:100%;height:auto;display:block;overflow:visible;margin-top:6px}}
.ws .wa{{fill:color-mix(in srgb,var(--c-cpu) 14%,transparent)}} .ws .wl{{fill:none;stroke:var(--c-cpu);stroke-width:2;stroke-linejoin:round}}
.ws .wah{{fill:color-mix(in srgb,var(--c-cpu) 40%,transparent)}} .ws .wlh{{fill:none;stroke:var(--c-cpu);stroke-width:3;stroke-linejoin:round}}
.ws .ceil{{stroke:var(--fg);stroke-width:2;stroke-dasharray:2 8;stroke-linecap:round;opacity:.7}}
.ws .xh{{stroke:var(--fg);stroke-width:1;opacity:0}} .ws.hovering .xh{{opacity:.35}} .ladders.cpufirst .lcpu{{order:-1}}
#p-hours .hmc,#p-hours .hleg-cause,#p-hours .hl-cause{{display:none}} #p-hours.bycause .hmc,#p-hours.bycause .hl-cause{{display:inline}} #p-hours.bycause .hleg-cause{{display:flex}} #p-hours.bycause .hleg-mem,#p-hours.bycause .hl-mem,#p-hours.bycause .hc circle{{display:none}}
.list{{margin-top:10px;display:grid;gap:7px}}
.jtabs{{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px}} .rbar{{display:flex;gap:6px;flex-wrap:wrap;margin:2px 0 18px}} .rg:disabled{{opacity:.4;cursor:default}} .jt{{font:600 13px Geist,sans-serif;border:2px solid var(--line);background:transparent;border-radius:99px;padding:5px 14px;cursor:pointer;color:inherit}} .jt[aria-pressed=true]{{background:var(--fg);color:var(--bg);border-color:var(--fg)}}
.jobs .jr{{grid-template-columns:minmax(0,17rem) 1fr 5.5rem}} .jobs .list{{max-height:52vh;overflow:auto;padding-right:4px}} details.kind summary{{list-style:none;cursor:pointer}} details.kind summary::-webkit-details-marker{{display:none}} details.kind summary .jr span b::before{{content:"\\25B8  ";color:var(--mute)}} details.kind[open] summary .jr span b::before{{content:"\\25BE  "}}
details.kind summary .row:not(.jr) span::before{{content:"\\25B8  ";color:var(--mute)}} details.kind[open] summary .row:not(.jr) span::before{{content:"\\25BE  "}}
.kd{{font-size:12.5px;color:var(--mute);margin:4px 0 6px 1.2rem}} details.kind .jl{{position:static;width:auto;background:none;color:inherit;box-shadow:none;border-radius:0;z-index:auto;list-style:none;margin:0 0 10px 1.2rem;padding:0;display:grid;gap:4px;font-size:12.5px}} .jl li{{display:flex;justify-content:space-between;gap:10px}} .jl i{{font-style:normal;color:var(--mute)}} .jl em{{font-style:normal;font-family:'Geist Mono',monospace;color:var(--mute);white-space:nowrap}}
.ladder .row{{grid-template-columns:minmax(0,15rem) 1fr 3rem}} .ladder .row span i{{font-style:normal;font-size:11.5px;color:var(--mute)}} .ladder .me span b{{color:var(--hot)}}
.ur{{grid-template-columns:minmax(0,12rem) 1fr 6.5rem}} .uh{{display:flex;justify-content:space-between;font-size:11.5px;color:var(--mute);margin:2px 0 4px}}
.howc ul{{display:grid;gap:10px;padding-left:18px;font-size:14.5px;max-width:70rem}} .howc code{{font-size:12.5px}} .kick .dot{{display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--tone);margin-right:8px;vertical-align:1px}}
#p-rec .hero{{display:grid;grid-template-columns:auto 1fr;column-gap:22px;align-items:center;text-align:left;padding-top:0}} #p-rec .hero>*{{grid-column:2}} #p-rec .hero .buddy-wrap{{grid-column:1;grid-row:1/span 3;transform:scale(.72);transform-origin:center}}
#p-rec .hero h1{{font-size:clamp(1.8rem,3.6vw,3.1rem);margin:0}} #p-rec .hero .lede{{margin:6px 0 0;max-width:52rem}}
#p-rec .two{{grid-template-columns:3fr 2fr}} #p-rec .hero .bubble,#p-rec .hero .says{{display:none}} #p-rec svg.jars{{max-height:34vh}}
@media (max-width:760px){{.ladder .row{{grid-template-columns:minmax(0,8.5rem) 1fr 2.8rem}} #p-rec .hero{{grid-template-columns:minmax(0,1fr);text-align:center}} #p-rec .hero>*,#p-rec .hero .buddy-wrap{{grid-column:1;grid-row:auto}} #p-rec .two{{grid-template-columns:minmax(0,1fr)}}}}
.jobgrid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;margin-top:16px}} .jr span{{line-height:1.2}} .jr span i{{font-style:normal;font-size:11.5px;color:var(--mute)}} .jr{{grid-template-columns:minmax(0,18rem) 1fr 3.8rem}}
@media (max-width:760px){{.jobgrid{{grid-template-columns:minmax(0,1fr)}}}}
.row{{display:grid;grid-template-columns:minmax(0,10.5rem) 1fr 3.8rem;align-items:center;gap:10px;font-size:13.5px}}
.row span{{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}} .row em{{font-style:normal;text-align:right;font-family:'Geist Mono',monospace;color:var(--mute);font-size:12.5px}}
.track{{height:12px;border-radius:9px;background:var(--line);overflow:visible;position:relative}}
.track b{{display:block;height:100%;border-radius:9px;background:linear-gradient(90deg,var(--banana),#f0a500);width:0;transition:width 1s cubic-bezier(.2,.8,.2,1) calc(var(--i)*60ms);position:relative}}
.track b:after{{content:"";position:absolute;right:-7px;top:-4px;width:20px;height:20px;border-radius:50%;background:#ffd93b url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='-1 -1 2 2'%3E%3Crect x='-1' y='-.12' width='2' height='.24' fill='%23333a45'/%3E%3Ccircle r='.5' fill='%23fff' stroke='%239aa3ad' stroke-width='.16'/%3E%3Ccircle r='.22' fill='%237a4b23'/%3E%3C/svg%3E") center/100% no-repeat;box-shadow:0 1px 0 rgba(0,0,0,.15)}}
.on .track b{{width:var(--w)}}
.heat{{width:100%;height:auto;display:block}} .heat .empty{{fill:none;stroke:var(--line);stroke-width:1.5;stroke-dasharray:3 3}}
.heat .hc:hover rect{{stroke:var(--fg);stroke-width:2}}
.ramp{{display:inline-block;width:120px;height:10px;border-radius:5px;background:linear-gradient(90deg,color-mix(in oklab,#e5484d 15%,#fff4cc),#e5484d)}}
@media(prefers-reduced-motion:no-preference){{.on .heat .hc{{animation:pop .5s cubic-bezier(.3,1.5,.5,1) both;animation-delay:calc(var(--i)*4ms)}}}}
/* panel 3 */
.whogrid{{display:grid;grid-template-columns:3fr 2fr;gap:14px;align-items:stretch}}
.yard-wrap{{margin:0!important}} .yard{{height:min(52vh,420px)!important}}
/* panel 4 history */
svg.hist{{width:100%;height:auto;display:block;overflow:visible}}
.hist .col use{{transform-box:view-box}}
.hist .col:hover{{filter:drop-shadow(0 0 4px rgba(229,72,77,.6))}}
.hist .hot .hd circle:first-child{{fill:#ff9d4d}}
ol.meas{{margin:6px 0 8px}} ol.meas li{{padding:8px 14px}} ol.meas b{{color:var(--hot);font:700 20px Fredoka,sans-serif}} ol.meas span{{font-size:12.5px;line-height:1.35}} ol.meas i{{font-style:normal;color:var(--mute)}}
ol.top .ovh{{color:var(--hot);font-style:normal;font-weight:700}} ol.top .ovn{{font-size:11px}}
ol.top{{list-style:none;padding:0;display:flex;gap:10px;flex-wrap:wrap}}
ol.top li{{display:flex;align-items:center;gap:8px;padding:8px 14px 8px 8px;border-radius:20px;border:2px solid var(--line);background:var(--card)}}
ol.top svg{{width:26px;height:40px}} ol.top b{{font:700 28px Fredoka,sans-serif;color:var(--hot)}} ol.top span{{font-size:12px;color:var(--mute);line-height:1.2}} ol.top i{{font-style:normal}}
/* panel 5 */
.quote{{font:500 clamp(1.2rem,2.6vw,1.9rem)/1.3 Fredoka,sans-serif;max-width:52rem;padding:22px 26px;border-left:6px solid var(--hot);background:var(--card);border-radius:0 28px 28px 0}}
.quote cite{{display:block;margin-top:8px;font:13px Geist,sans-serif;color:var(--mute);font-style:normal}}
.feel{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}}
.feel h3{{font:600 20px/1.2 Fredoka,sans-serif;margin:8px 0 4px}} .feel p{{color:var(--mute);font-size:14.5px}} .feel svg{{width:84px;height:84px}}
/* panel 6 jars */
svg.jars{{width:100%;max-height:28vh;display:block;overflow:visible}}
.glass{{fill:color-mix(in srgb,var(--card) 60%,transparent);stroke:var(--fg);stroke-width:3;opacity:.9}}
.lid{{fill:var(--ram)}} .fill{{fill:url(#jf);transform-origin:bottom;transform-box:fill-box}}
.jlabel{{font:700 22px Fredoka,sans-serif;fill:var(--fg)}} .jtag{{font:600 15px Fredoka,sans-serif}} .jtag.bad{{fill:var(--hot)}} .jtag.good{{fill:var(--good)}}
.specs{{display:grid;grid-template-columns:repeat(auto-fit,minmax(13rem,1fr));gap:12px}}
.specs .c{{padding:12px 16px}} .specs .c b{{display:block;font:700 24px/1.1 Fredoka,sans-serif}} .specs .c span{{font-size:13.5px;color:var(--mute)}}
.specs .c:first-child{{background:var(--fg);color:var(--bg);border-color:var(--fg)}} .specs .c:first-child b{{color:#ffd93b}} .specs .c:first-child span{{color:inherit;opacity:.8}}
footer{{display:flex;justify-content:space-between;align-items:center;gap:10px;padding:6px 20px 12px;max-width:1240px;width:100%;margin:0 auto;color:var(--mute);font-size:12px}}
footer .fl{{display:flex;align-items:center;gap:6px 14px;flex-wrap:wrap;min-width:0}} .hsw{{display:inline-flex;gap:4px;flex:none}} .hsw .jt{{font-size:12px;padding:4px 11px}} a.jt{{text-decoration:none;display:inline-block}} .hs:disabled{{opacity:.4;cursor:default}}
.nav2{{display:flex;gap:6px}} .nav2 button{{all:unset;cursor:pointer;width:34px;height:34px;border-radius:50%;border:2px solid var(--line);display:grid;place-items:center;font:700 16px Fredoka,sans-serif;color:var(--fg)}}
.nav2 button:hover{{background:var(--banana);color:#1d2a44}}
details{{position:relative}} summary{{cursor:pointer;color:var(--fg)}}
details ul{{position:absolute;bottom:28px;left:0;width:min(560px,90vw);padding:14px 16px 14px 30px;border-radius:20px;background:var(--fg);color:var(--bg);display:grid;gap:6px;font-size:13px;z-index:9;box-shadow:0 12px 40px rgba(0,0,0,.25)}}
.climb{{display:none!important}}
/* motion: everything enters on panel change; reduced motion keeps it still */
@media(prefers-reduced-motion:no-preference){{
 .on .en{{animation:pop .7s cubic-bezier(.3,1.5,.5,1) both;animation-delay:calc(var(--n,0)*90ms)}}
 .again .on .en,.again .on .ts .need,.again .on .ts .ram,.again .on .hist .col,.again .on .fill{{animation:none}}
 .on .ts .need,.on .ts .ram{{animation:draw 2.4s cubic-bezier(.6,0,.2,1) backwards}}
 .on .drops .dr{{animation:drip 2.6s ease-in var(--d) infinite}}
 .on .hist .col{{animation:stack .6s cubic-bezier(.3,1.6,.5,1) both;animation-delay:calc(var(--i)*12ms)}}
 .on .fill{{animation:fillup 1.6s cubic-bezier(.2,.8,.2,1) both}}
 .on .spill{{animation:spill 2.2s cubic-bezier(.3,0,.7,1) calc(var(--k)*.35s + 1.2s) infinite}}
 .peek .pp{{animation:look 5s ease-in-out infinite}}
 .walker{{transition:transform .25s linear}}
 .sit{{animation:sitbob 2.4s ease-in-out infinite}}
 .flagb{{animation:wave 1.6s ease-in-out infinite;transform-origin:0 100%;transform-box:fill-box}}
 .feel .c:hover svg{{animation:wobble .5s ease-in-out}}
 .spinner{{animation:spin 1.4s linear infinite;transform-origin:center;transform-box:fill-box}}
}}
@keyframes pop{{from{{opacity:0;transform:translateY(18px) scale(.96)}}}}
@keyframes draw{{from{{stroke-dasharray:1;stroke-dashoffset:1}}to{{stroke-dasharray:1;stroke-dashoffset:0}}}}
@keyframes drip{{0%{{transform:translateY(-8px);opacity:0}}20%{{opacity:1}}70%{{transform:none}}100%{{transform:none}}}}
@keyframes stack{{from{{transform:translateY(30px);opacity:0}}}}
@keyframes fillup{{from{{transform:scaleY(0)}}}}
@keyframes spill{{0%{{transform:translate(0,0) rotate(0);opacity:0}}10%{{opacity:1}}100%{{transform:translate(calc((var(--k) - 2.5)*22px),300px) rotate(260deg);opacity:0}}}}
@keyframes look{{0%,40%,100%{{transform:none}}55%,70%{{transform:translateX(-3px)}}80%,90%{{transform:translateX(3px)}}}}
@keyframes sitbob{{50%{{transform:translateY(-3px)}}}}
@keyframes wave{{50%{{transform:skewY(-8deg) scaleX(.92)}}}}
@keyframes wobble{{30%{{transform:rotate(-8deg)}}60%{{transform:rotate(6deg)}}}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}
@media(max-width:860px){{
 .bubble{{display:none}} header{{flex-wrap:wrap;justify-content:center}} .brand,.live{{display:none}} .tabs{{max-width:100%}}
 .proof,.specs{{grid-template-columns:repeat(2,1fr)}} .two,.whogrid,.feel{{grid-template-columns:1fr}}
 .panel .inner{{justify-content:flex-start}} .row{{grid-template-columns:minmax(0,8rem) 1fr 3.6rem}}
}}
</style></head><body>
<svg width=0 height=0 style="position:absolute" aria-hidden=true><defs>
<g id=head>{HEAD}</g>
<symbol id=nana viewBox="0 0 24 24"><path d="M4 15c4 4 12 4 16-6 1-2 0-4-1-4 0 6-6 11-14 8z" fill="#ffd93b" stroke="#c99700" stroke-width="1"/><path d="M19 5l1-2" stroke="#6b4b1b" stroke-width="2" stroke-linecap="round"/></symbol>
<linearGradient id=fa x1=0 y1=0 x2=0 y2=1><stop offset=0 stop-color="var(--fillA)"/><stop offset=1 stop-color="var(--fillB)" stop-opacity=".2"/></linearGradient>
<linearGradient id=jf x1=0 y1=0 x2=0 y2=1><stop offset=0 stop-color="#ffe680"/><stop offset=1 stop-color="#ffc21a"/></linearGradient>
<pattern id=hatch width=10 height=10 patternUnits=userSpaceOnUse patternTransform="rotate(45)"><rect width=10 height=10 fill="var(--hot)" opacity=".16"/><line x1=0 y1=0 x2=0 y2=10 stroke="var(--hot)" stroke-width=3 opacity=".5"/></pattern>
</defs></svg>
<div class=app>
<header><div class=brand><i></i>{"Too small a Mac" if rec > TOTAL or chip_up else "Mac memory check"}</div><nav class=tabs role=tablist aria-label="Sections">{tab_html}<span class=ink></span><svg class=rider viewBox="0 0 60 92" aria-hidden=true>{mini(30, 90, 90)}</svg></nav><span class=live title="Memory written out to the disk in the last minute">{out_mb:.0f} MB/min<span class=lx> to disk</span></span></header>
<div class=stage>

<section class=panel id=p-rec role=tabpanel><div class=inner>
<section class=hero>
<p class="kick en">{kick_html}</p>
<h1 class=en id=rec-h1>{h1_html}</h1>
{f'<p class="note en" style="margin:4px 0 0">The chip is a first guess from {cpu_days} working day{"s" if cpu_days != 1 else ""} of processor readings; memory and storage rest on {n_wd}.</p>' if chip_up else ""}
{lesson}
</section>
{verdict}
<div class=two>
<div class="c en ladders{" cpufirst" if cpu_first and cpu_ok else ""}" style="--n:2"><div class=lmem><small>Memory: share of {WM} each size would have handled</small><div class="list ladder meml">{ladder}</div>
<p class=note id=rec-note style="margin-top:10px">{len(work):,} minutes measured, {HOURS_TXT}.</p></div>
{f"""<div class=lcpu id=rec-cpu><small>Processors: share of {WM} a chip with this many cores would have kept up</small><div class="list ladder cpul">{cl_rows}</div>
<p class=note style="margin-top:10px">{len(loadw):,} {WM} on {cpu_days} working day{"s" if cpu_days != 1 else ""}, so this is a first guess. It counts cores only; newer chips&#x27; cores are faster than this Mac&#x27;s, so it overstates what you need.</p></div>""" if cpu_ok else ""}</div>
<div class="c en" id=rec-jars style="--n:3"><svg class=jars viewBox="0 -60 1000 440" role=img aria-label="A {TOTAL:.0f} GB jar holding the busiest minute's {peak_ever:.1f} GB, next to a {rec} GB jar holding it with room to spare">{jars}</svg></div>
</div>
<div class=specs>
{f'<div class="c en" id=rec-chip style="--n:5"><b>{chip_b}</b><span>processor, a first guess from {cpu_days} working day{"s" if cpu_days != 1 else ""}: more work was waiting than its {cores} cores could run in {wait_pct:.0%} of working minutes.</span></div>' if cpu_ok and cpu_first else ""}
<div class="c en" id=rec-mem style="--n:4"><b>{rec} GB</b><span>memory, or {budget} GB if budget is tight: enough today, little room to grow.</span></div>
{f'<div class="c en" id=rec-chip style="--n:5"><b>{chip_b}</b><span>processor, a first guess from {cpu_days} working day{"s" if cpu_days != 1 else ""}: more work was waiting than its {cores} cores could run in {wait_pct:.0%} of working minutes.</span></div>' if cpu_ok and not cpu_first else ""}
<div class="c en" id=rec-disk style="--n:5"><b>{disk_txt}</b><span>storage: {disk_used:.0f} GB of this Mac&#x27;s {disk_total:.0f} GB is in use, plus half again for growth.</span></div>
<div class="c en" id=rec-days style="--n:6"><b>{n_wd} of {WD_GOAL}</b><span>working days measured so far{f"; the processors on {cpu_days}" if cpu_rows else ""}.</span></div>
</div>
</div></section>

<section class="panel rpanel" id=p-today role=tabpanel><div class=inner>
<div class=en><p class=kick><i class=dot></i>{status_line}</p></div>
{rbar(t_on, T_all)}
{"".join(tview(r_, f"r{r_}") for r_ in t_on)}
</div></section>

{heat_sec}
<section class=panel id=p-days role=tabpanel><div class=inner>
<div class=en><p class=kick>Every day since {first.strftime("%-d %B")}</p><h2 class=big>{f"Held up on <em>{len(held_days)} of {len(meas)}</em> measured days" if cpu_from else f"Over {TOTAL:.0f} GB on <em>{over_days} of {len(meas)}</em> measured days"}</h2></div>
<p class="lede en" style="--n:1">Above the line: how many Claude Code sessions ran at once, one head each. {busy_days} days reached 10 or more. Below the line: how many minutes something held the Mac up, coloured by what held it up (a day counts as held up after half an hour), and under that, how far the busiest minute went past {TOTAL:.0f} GB. Memory has only been measured since {since}.</p>
<div class="c en" style="--n:2"><svg class=hist style="max-height:52vh" viewBox="0 -24 {HW} {M0 + OH + 40:.0f}" role=img aria-label="One timeline: Claude Code sessions open at once each day above, memory over this Mac's RAM below">
<text x=4 y=-12 class=tk>&#9650; Claude Code sessions at once (from my session logs)</text>
<line x1=0 x2={HW} y1={ten_y:.1f} y2={ten_y:.1f} stroke="var(--hot)" stroke-dasharray="2 7" stroke-width=2 stroke-linecap=round opacity=".7"/>
<text x=4 y={ten_y - 8:.1f} class=tk>10 at once</text>
{"".join(heads)}{hticks}
<line x1=0 x2={HW} y1={HH + 30:.1f} y2={HH + 30:.1f} stroke="var(--line)" stroke-width="2"/>
<g transform="translate(0 {CY0:.1f})">{"".join(cbars)}</g>
<text x=4 y={CY0 + CHh + 18:.1f} class=tk>&#9660; Minutes held up, coloured by what held it up{f" (processors measured from {dt.datetime.strptime(cpu_from, '%Y-%m-%d %H:%M').strftime('%-d %b')})" if cpu_from else ""}</text>
<g transform="translate(0 {M0:.1f})">{"".join(obars)}</g>
<text x=4 y={M0 + OH + 14:.1f} class=tk>&#9660; Memory over {TOTAL:.0f} GB at the busiest minute (measured from {since}; dots = not measured)</text></svg>
<div class=legend style="margin-top:8px">{CAUSE_KEY}</div>
<ol class="top meas">{"".join((f'<li><b>{span(dheld[d])}</b><span>held up, mostly {held(dom_(d))} &middot; {day_sess.get(d, (0, ""))[0]} sessions<br><i>{dt.date.fromisoformat(d).strftime("%a %-d %b")} &middot; +{max(dmem[d][0] - TOTAL, 0):.1f} GB over {TOTAL:.0f} GB{"" if cpu_from and d >= cpu_from[:10] else " &middot; processors not measured"}</i></span></li>' if dheld[d] else f'<li><b>+{max(dmem[d][0] - TOTAL, 0):.1f} GB</b><span>over {TOTAL:.0f} GB &middot; {day_sess.get(d, (0, ""))[0]} sessions<br><i>{dt.date.fromisoformat(d).strftime("%a %-d %b")} &middot; {heavy.get(d, 0)} min heavy swapping</i></span></li>') for d in sorted(meas, reverse=True))}</ol>
<p class=note>Measured since {since}: {over_days} of {len(meas)} days went over {TOTAL:.0f} GB{f", the worst by {dmem[worst_d][0] - TOTAL:.1f} GB on {dt.date.fromisoformat(worst_d).strftime('%a %-d %b')} with {heavy.get(worst_d, 0)} minutes of heavy swapping" if worst_d else ""}. Earlier days were not measured (faint dots); their session counts above are the only record.</p></div>
<div class=en style="--n:3"><p class=kick style="margin-bottom:8px">Busiest days</p><ol class=top>{top_html}</ol></div>
</div></section>

<section class="panel{" bycause" if cpu_first else ""}" id=p-hours role=tabpanel><div class=inner>
<div class=en><p class=kick>{HOURS_TXT[0].upper() + HOURS_TXT[1:]}</p><h2 class=big><span class=hl-mem>{TOTAL:.0f} GB ran out in <em>{len(over_cells)} of {filled}</em> hours seen</span><span class=hl-cause>Held up in <em>{held_hours} of {seen_hours}</em> hours seen</span></h2></div>
<p class="lede en" style="--n:1"><span class=hl-mem>{hours_take} Each square is one hour of one weekday, darker for more memory needed; a white dot means it went over {TOTAL:.0f} GB.</span><span class=hl-cause>Each square is one hour of one weekday, coloured by what held it up most in that hour; paler means fewer of its minutes were held up, and an hour counts as held up when a tenth of it was.</span> Blank squares have no readings yet.</p>
<div class="c en hmcard" style="--n:2"><div class=jtabs role=group aria-label="Colour the squares by"><button type=button class="jt hmt" data-hm=cause aria-pressed={"true" if cpu_first else "false"}>What held it up</button><button type=button class="jt hmt" data-hm=mem aria-pressed={"false" if cpu_first else "true"}>Memory needed</button></div>
<svg class=heat viewBox="0 0 {heat_w} {heat_h}" role=img aria-label="Highest memory needed by weekday and hour, or what held each hour up">{heat_svg}</svg>
<div class="legend hleg-cause" style="margin-top:12px">{CAUSE_KEY}<span>paler = held up for fewer of its minutes</span>{f"<span>processors measured from {dt.datetime.strptime(cpu_from, '%Y-%m-%d %H:%M').strftime('%-d %b')}; before that only memory could show</span>" if cpu_from else ""}</div>
<div class="legend hleg-mem" style="margin-top:12px"><span>lighter = less</span><span class=ramp></span><span>darker = more ({lo_:.0f} to {hi_:.0f} GB)</span><span><i style="background:#fff;border:2px solid var(--hot);width:10px;height:10px;border-radius:50%;vertical-align:-1px"></i>over {TOTAL:.0f} GB</span></div></div>
</div></section>

<section class=panel id=p-uses role=tabpanel><div class=inner>
<div class=en><p class=kick>Every app, and what Claude runs underneath, refreshed every minute</p><h2 class=big>What uses <em>{"the Mac" if capps else "memory"}</em></h2></div>
<div class=whogrid>
<div class=en style="--n:1"><!--YARD--></div>
<div class=en style="--n:2">{mtabs("uses", m_first)}
{f"""<div class="c jobs mbox" data-m=cpu{"" if m_first == "cpu" else " hidden"}><div class=jtabs role=group aria-label="Time window">{cuses_tabs}</div>{cuses_views}
<p class=note style="margin-top:10px">Each app&#x27;s share of all {cores_n} cores. Tap a Claude row to see its groups and scripts.</p></div>""" if capps else ""}
<div class="c jobs mbox" data-m=mem{"" if m_first == "mem" else " hidden"}><div class=jtabs role=group aria-label="Time window">{uses_tabs}</div>{uses_views}
<p class=note style="margin-top:10px">Tap a Claude row to see its groups and the scripts in each, with the session folder that started them.{f" The hidden test browsers peaked at {br_peak:.1f} GB this week." if br_peak >= 1 else ""}</p></div>
</div></div></div></section>

<section class=panel id=p-claude role=tabpanel><div class=inner>
<div class=en><p class=kick>The tools and hidden browsers Claude starts, by kind, refreshed every minute</p><h2 class=big>{(e(take_kc[0]) + " peaked at <em>" + f"{take_kc[1]:.0f}%" + "</em> of the processors this week") if m_first_c == "cpu" and take_kc else (e(take_k[0]) + " peaked at <em>" + f"{take_k[1]:.1f}" + " GB</em> this week") if take_k else "What Claude <em>runs</em>"}</h2></div>
<div class=en style="--n:2">{mtabs("claude", m_first_c)}
{f"""<div class="c jobs mbox" data-m=cpu{"" if m_first_c == "cpu" else " hidden"}><div class=jtabs role=group aria-label="Time window">{cjobs_tabs}</div>{cjobs_views}
<p class=note style="margin-top:10px">Share of all {cores_n} cores. Tap a group to see its scripts and the Claude session folder that started each one. Tracked since {e(min(tjc) if tjc else "the next reading")}.</p></div>""" if capps else ""}
<div class="c jobs mbox" data-m=mem{"" if m_first_c == "mem" else " hidden"}><div class=jtabs role=group aria-label="Time window">{jobs_tabs}</div>{jobs_views}
<p class=note style="margin-top:10px">Tap a group to see its scripts and the Claude session folder that started each one. Tracked since {e(tfirst or "now")}.</p></div></div>
</div></section>

<section class=panel id=p-how role=tabpanel><div class=inner>
<div class=en><p class=kick>What is measured, and what is not</p><h2 class=big>How this <em>works</em></h2></div>
<div class="c en howc" style="--n:1"><ul>
<li><b>Every minute</b> a background job reads macOS figures (<code>vm_stat</code>, <code>sysctl</code>, <code>ps</code>) into <code>~/memlog/</code>{', copied to Google Drive every 15 minutes' if cfg.get('drive_backup') else ''}: memory in use, memory on disk, memory and processor share per app, the scripts Claude runs with each one&#x27;s memory and processor share, and processor load. Nothing is sent anywhere else.</li>
<li><b>Memory needed</b> is memory in use plus memory parked on disk (swap). Swap can keep old data from hours earlier, so this can overstate the real need; the minutes the Mac was actively moving memory to disk are shown separately as the drops on the Today chart.</li>
<li><b>Working hours or all hours:</b> the switch at the bottom of every tab. Working hours ({e(v.get("work_txt", "Monday to Friday, 9am to 7pm"))}, set in config.json) is the default, and every tab, the recommendation included, then counts only minutes inside them. Time the Mac is off or asleep is never counted: nothing is measured then, and the first reading after a gap records no swap, disk or network rate rather than an average over the night.</li>
<li><b>The recommendation</b> is the busiest minute ever measured plus a quarter, rounded up to a size Macs come in. The budget pick is the smallest size that would have covered 99% of working minutes. Storage is what is in use now plus half again. The processor pick is the smallest core count that would have kept up in 9 working minutes of 10; it counts cores only, and newer chips&#x27; cores are faster than an older Mac&#x27;s, so it overstates the need.</li>
<li><b>Processors</b> are measured as work waiting: the 1-minute load average divided by the number of cores. Above 1&times;, more work is waiting than the cores can run, so things slow down. &ldquo;% busy&rdquo; is not used for this because on Apple chips half the cores are slower ones: the fast half can be full while the total reads 50 to 60%.</li>
<li><b>Every tab leads with what held the Mac up more</b> since the processors were first measured: Today opens on the processors chart or the memory chart, Busy days counts a day as held up after half an hour of it, Busy hours opens on &ldquo;What held it up&rdquo; (an hour counts when a tenth of it was), and What uses the Mac and What Claude runs open on processors or memory. Every one has a switch or a second chart for the other.</li>
<li><b>What held it up</b> labels each minute, the same way on every tab: <i>processors</i> when work is waiting, <i>memory</i> when it pushes 100 MB a minute or more to disk, <i>memory and processors</i> when both happen in the same minute, and <i>heat</i> when macOS&#x27;s own heat level is fair or worse, meaning it is slowing the chip down to cool it (heat wins over the others then, because it is what made the processors slower). A hot chip and a loud fan alone do not count: they make the Mac loud, not slow.</li>
<li><b>Hot &amp; slow</b> reads, each minute and without admin rights: the hottest processor temperature sensor and the fan speed (from a small Swift program, <code>heat</code>, built at install), macOS&#x27;s graphics load (<code>ioreg</code>), disk bytes read and written (<code>ioreg</code>), network bytes in and out (<code>netstat</code>) and each app&#x27;s share of the processors (<code>ps</code>). It also records macOS&#x27;s own heat level; when that goes above normal, macOS is slowing the Mac down to cool it, and the temperature tile says so. The dotted lines (90 &deg;C, fan at 60%, work waiting above 1&times; the cores, graphics 85% busy, 1 GB a minute of disk, 100 MB a minute pushed to disk, 500 MB a minute of network) are rules of thumb, not limits macOS enforces.</li>
<li><b>Per-app memory</b> counts memory still in memory, not on disk. Memory two apps share can be counted twice. Meet is counted inside Chrome.</li>
<li>{f'<b>Before {e(split_t)}</b> Chrome and the hidden test browsers Claude opens were counted together; those readings say so. ' if any('not split' in g for d_ in apps_all.values() for g in d_) else ''}Claude&#x27;s scripts are tracked from {e(tfirst or "now")}, processor load from {e(cpu_rows[0][0] if cpu_rows else "now")}.</li>
<li><b>Session history</b> before {since} comes from Claude Code transcripts: a session counts as open while its messages are under 30 minutes apart. Codex and idle open sessions are not counted, so real numbers were probably higher.</li>
<li><b>Right now:</b> {gb(U[-1])} GB in memory, {gb(S[-1])} GB on disk, {v["comp_gb"]:.1f} GB of memory holding {v["squeezed_gb"]:.1f} GB compressed, {v["wired_gb"]:.1f} GB locked by the system, {terms} sessions open.</li>
</ul></div>
</div></section>
</div>

<footer><div class=fl><span class=hsw role=group aria-label="Which hours to count">{hours_switch}</span><span>Updated {e(v.get("stamp") or T[-1])} &middot; scroll, swipe or use the arrow keys</span></div><div class=nav2><button id=prev aria-label="Previous section">&lsaquo;</button><button id=next aria-label="Next section">&rsaquo;</button></div></footer>
</div>
<script>
(() => {{
  const ids = {json.dumps([k for k, _ in tabs])};
  const tabs = [...document.querySelectorAll(".tabs button")], ink = document.querySelector(".tabs .ink"), rider = document.querySelector(".tabs .rider");
  let cur = -1;
  const dotBox = document.createElement("nav"); dotBox.className = "dots"; dotBox.setAttribute("aria-label", "Sections");
  const dots = ids.map((id, j) => {{ const b = document.createElement("button"); b.setAttribute("aria-label", tabs[j].textContent); b.onclick = () => show(j, true); dotBox.appendChild(b); return b; }});
  document.body.appendChild(dotBox);
  const show = (i, push, keep) => {{
    i = (i + ids.length) % ids.length; if (i === cur) return;
    if (push) document.documentElement.classList.remove("again");
    document.querySelectorAll(".panel").forEach((p, j) => {{ p.classList.toggle("on", j === i); p.classList.toggle("above", j < i); }});
    tabs.forEach((t, j) => t.setAttribute("aria-selected", j === i));
    dots.forEach((d, j) => d.setAttribute("aria-current", j === i));
    const pn = document.querySelectorAll(".panel")[i]; if (!keep) pn.scrollTop = 0;
    const t = tabs[i]; ink.style.left = t.offsetLeft + "px"; ink.style.width = t.offsetWidth + "px";
    rider.style.left = (t.offsetLeft + t.offsetWidth / 2 - 10) + "px";
    t.scrollIntoView({{block: "nearest", inline: "center"}});
    cur = i; try {{ localStorage.setItem("mm-tab", ids[i]); }} catch (_) {{}}
    if (push) history.replaceState(null, "", "#" + ids[i]);
  }};
  tabs.forEach((t, j) => t.addEventListener("click", () => show(j, true)));
  document.getElementById("prev").onclick = () => show(cur - 1, true);
  document.getElementById("next").onclick = () => show(cur + 1, true);
  // Scroll, swipe and keys move between screens. A screen that scrolls inside (on a phone) is scrolled first;
  // only at its top or bottom edge does the next screen come in. One move per gesture, no wrap-around.
  const go = d => {{ const j = cur + d; if (j >= 0 && j < ids.length) show(j, true); }};
  let lock = 0, acc = 0, accT = 0;
  const atEdge = (d) => {{ const p = document.querySelectorAll(".panel")[cur];
    return d > 0 ? p.scrollTop + p.clientHeight >= p.scrollHeight - 2 : p.scrollTop <= 0; }};
  addEventListener("wheel", e => {{
    if (e.ctrlKey || Math.abs(e.deltaY) < Math.abs(e.deltaX)) return;
    const d = Math.sign(e.deltaY), now = performance.now();
    if (!atEdge(d)) {{ acc = 0; return; }}
    e.preventDefault();
    if (now < lock) {{ lock = now + 260; return; }}  // swallow the tail of a trackpad fling
    if (now - accT > 300) acc = 0; accT = now; acc += e.deltaY;
    if (Math.abs(acc) > 70) {{ acc = 0; lock = now + 950; go(d); }}
  }}, {{ passive: false }});
  let ty = null;
  addEventListener("touchstart", e => {{ ty = e.touches[0].clientY; }}, {{ passive: true }});
  addEventListener("touchend", e => {{
    if (ty === null) return; const dy = ty - e.changedTouches[0].clientY; ty = null;
    if (Math.abs(dy) > 60 && atEdge(Math.sign(dy))) go(Math.sign(dy));
  }}, {{ passive: true }});
  addEventListener("keydown", e => {{
    if (["ArrowRight", "ArrowDown", "PageDown", " "].includes(e.key)) {{ e.preventDefault(); go(1); }}
    if (["ArrowLeft", "ArrowUp", "PageUp"].includes(e.key)) {{ e.preventDefault(); go(-1); }}
  }});
  document.querySelectorAll(".hmt").forEach(b => b.addEventListener("click", () => {{
    const card = b.closest(".panel"); card.classList.toggle("bycause", b.dataset.hm === "cause");
    card.querySelectorAll(".hmt").forEach(x => x.setAttribute("aria-pressed", x === b));
    try {{ localStorage.setItem("mm-hours-by", b.dataset.hm); }} catch (_) {{}}
  }}));
  try {{ const hb = localStorage.getItem("mm-hours-by"); if (hb) document.querySelector(`.hmt[data-hm="${{hb}}"]`)?.click(); }} catch (_) {{}}
  // Processors or memory, on What uses the Mac and What Claude runs; one choice for both tabs.
  const setM = m => document.querySelectorAll(".mtabs").forEach(g => {{ const p = g.closest(".panel"), b = g.querySelector(`.mt[data-m="${{m}}"]`); if (!b) return;
    g.querySelectorAll(".mt").forEach(x => x.setAttribute("aria-pressed", x === b)); p.querySelectorAll(".mbox").forEach(x => x.hidden = x.dataset.m !== m); }});
  document.querySelectorAll(".mt").forEach(b => b.addEventListener("click", () => {{ setM(b.dataset.m); try {{ localStorage.setItem("mm-measure", b.dataset.m); }} catch (_) {{}} }}));
  try {{ const mm = localStorage.getItem("mm-measure"); if (mm) setM(mm); }} catch (_) {{}}
  document.querySelectorAll(".jobs .jt").forEach(b => b.addEventListener("click", () => {{
    const box = b.closest(".jobs"), key = "mm-win-" + b.closest(".panel").id;
    box.querySelectorAll(".jt").forEach(x => x.setAttribute("aria-pressed", x === b));
    box.querySelectorAll(".jv").forEach(v => v.hidden = v.dataset.v !== b.dataset.v);
    try {{ localStorage.setItem(key, b.dataset.v); }} catch (_) {{}}
  }}));
  document.querySelectorAll(".jobs").forEach(box => {{ try {{ const jv = localStorage.getItem("mm-win-" + box.closest(".panel").id);
    const jb = jv && box.querySelector('.jt[data-v="' + jv + '"]'); if (jb) jb.click(); }} catch (_) {{}} }});
  document.querySelectorAll("a.hs").forEach(a => a.addEventListener("click", ev => {{
    ev.preventDefault(); const tab = document.querySelector(".tabs [aria-selected=true]"); location.href = a.href.split("#")[0] + (tab && tab.dataset.go ? "#" + tab.dataset.go : location.hash); }}));
  let start = location.hash.slice(1); try {{ start = start || localStorage.getItem("mm-tab"); }} catch (_) {{}}
  // Tighten the header one step at a time until every tab fits (t1: smaller tabs, t2: title and "to disk" go, t3: smaller again, t4: the disk chip goes, t5: tighter still).
  const hdr = document.querySelector("header"), bar = document.querySelector(".tabs");
  const fitTabs = () => {{ hdr.classList.remove("t1", "t2", "t3", "t4", "t5");
    for (const c of ["t1", "t2", "t3", "t4", "t5"]) {{ if (bar.scrollWidth <= bar.clientWidth + 1) break; hdr.classList.add(c); }} }};
  fitTabs();
  show(Math.max(0, ids.indexOf(start)), false);
  // After the minute reload, put the reader back where they were reading.
  try {{ const sc = JSON.parse(sessionStorage.getItem("mm-scroll") || "null"); sessionStorage.removeItem("mm-scroll");
    const pn = sc && document.getElementById(sc.id); if (pn && pn.classList.contains("on")) {{ pn.scrollTop = sc.top; requestAnimationFrame(() => pn.scrollTop = sc.top); }} }} catch (_) {{}}
  const refit = () => {{ fitTabs(); const c = cur; cur = -1; show(c, false, true); }};
  addEventListener("resize", refit); if (document.fonts) document.fonts.ready.then(refit);

  // Memory charts (one per time range): a buddy walks along the red line; hovering moves it to the point under the pointer.
  const still = matchMedia("(prefers-reduced-motion: reduce)").matches;
  document.querySelectorAll(".mchart").forEach(box => {{
    const D = JSON.parse(box.querySelector(".mdata").textContent), n = D.t.length, W = {W}, H = {H}, PAD = {PAD}, top = D.top;
    const X = i => i * W / Math.max(n - 1, 1), Y = v => PAD + (H - PAD) - v * (H - PAD) / top;
    const svg = box.querySelector(".ts"), walker = box.querySelector(".walker"), xh = svg.querySelector(".xh"), tip = box.querySelector(".tip");
    let hover = -1, step = 0;
    const put = (i) => {{
      walker.setAttribute("transform", `translate(${{X(i)}} ${{Y(D.need[i]) - 2}})`);
      xh.setAttribute("x1", X(i)); xh.setAttribute("x2", X(i));
    }};
    const tipAt = (i) => {{
      const r = svg.getBoundingClientRect(), b = box.getBoundingClientRect(), vb = svg.viewBox.baseVal;
      tip.style.left = (r.left - b.left + (X(i) - vb.x) * r.width / vb.width) + "px";
      tip.style.top = (r.top - b.top + (Y(D.need[i]) - vb.y - 40) * r.height / vb.height) + "px";
      const one = D.b === 1, span = one ? "this minute" : `these ${{D.b}} minutes`;
      tip.innerHTML = `<b>${{D.t[i].slice(5).replace("-", "/")}}${{one ? "" : ", busiest of " + D.b + " min"}}</b><br><i style="background:var(--hot)"></i>needed ${{D.need[i].toFixed(1)}} GB<br><i style="background:var(--ram)"></i>in RAM ${{D.ram[i].toFixed(1)}} GB<br>${{D.swap[i] ? D.swap[i] + " MB pushed to disk" + (one ? "" : " at most") : "no swapping " + span}}<br>${{D.cause[i] ? `<i class="cz ${{D.cause[i]}}"></i>held up by ${{D.cn[D.cause[i]]}}` : "nothing held it up"}}`;
    }};
    const pick = ev => {{
      const r = svg.getBoundingClientRect(), vb = svg.viewBox.baseVal;
      const x = (ev.clientX - r.left) * vb.width / r.width + vb.x;
      return Math.max(0, Math.min(n - 1, Math.round(x / W * (n - 1))));
    }};
    svg.addEventListener("pointermove", ev => {{ hover = pick(ev); svg.classList.add("hovering"); put(hover); tipAt(hover); }});
    svg.addEventListener("pointerleave", () => {{ hover = -1; svg.classList.remove("hovering"); }});
    svg.addEventListener("pointerdown", ev => {{ if (ev.pointerType !== "mouse") box.classList.add("touch"); }});
    put(D.pk);
    if (!still) setInterval(() => {{ if (hover < 0 && box.offsetParent) {{ step = (step + Math.max(1, Math.round(n / 120))) % n; put(step); }} }}, 250);
  }});
}})();
let seen = false; try {{ seen = sessionStorage.getItem("mm-seen") === "1"; sessionStorage.setItem("mm-seen", "1"); }} catch (_) {{}}
</script></body></html>""")))


TODAY_CPU_JS = """<script>
(() => {
  // The processors charts (one per time range): a crosshair and a tip with the work waiting and the busiest apps there.
  document.querySelectorAll(".cchart").forEach(box => {
    const C = JSON.parse(box.querySelector(".cdata").textContent), svg = box.querySelector("svg.ws"), tip = box.querySelector(".tip"), xh = svg.querySelector(".xh");
    const n = C.t.length, W = 1000;
    const at = ev => {
      const r = svg.getBoundingClientRect(), b = box.getBoundingClientRect(), vb = svg.viewBox.baseVal;
      const x = (ev.clientX - r.left) * vb.width / r.width + vb.x, i = Math.max(0, Math.min(n - 1, Math.round(x / W * (n - 1)))), vx = i * W / Math.max(n - 1, 1);
      xh.setAttribute("x1", vx); xh.setAttribute("x2", vx); svg.classList.add("hovering");
      const w = C.w[i], ap = C.apps[i];
      tip.innerHTML = `<b>${C.ml ? C.t[i].slice(5).replace("-", "/") : C.t[i].slice(11)}${C.b > 1 ? ", busiest of " + C.b + " min" : ""}</b><br>` + (w == null ? "processors not measured" : `${w.toFixed(1)}&times; its ${C.cores} cores, ${w > 1 ? "work waiting" : "keeping up"}`)
        + (ap ? `<br>${ap.map(([g, v]) => `${g} ${Math.round(v)}%`).join(", ")}` : "");
      const yv = w == null ? C.ch : 10 + C.ch - Math.min(w, C.top) * C.ch / C.top;
      tip.style.left = (r.left - b.left + (vx - vb.x) * r.width / vb.width) + "px";
      tip.style.top = (r.top - b.top + (yv - vb.y - 30) * r.height / vb.height) + "px";
    };
    svg.addEventListener("pointermove", at);
    svg.addEventListener("pointerdown", ev => { if (ev.pointerType !== "mouse") box.classList.add("touch"); at(ev); });
    svg.addEventListener("pointerleave", () => { svg.classList.remove("hovering"); box.classList.remove("touch"); });
  });
  // One time-range choice for Today and Hot & slow. A panel without that much history shows the longest it has.
  const apply = r => document.querySelectorAll(".rpanel").forEach(p => {
    const ok = [...p.querySelectorAll(".rg:not([disabled])")].map(b => +b.dataset.r), use = ok.filter(x => x <= r).pop() || ok[0];
    p.querySelectorAll(".rg").forEach(b => b.setAttribute("aria-pressed", +b.dataset.r === use));
    p.querySelectorAll(".rv").forEach(v => v.hidden = +v.dataset.r !== use);
  });
  document.querySelectorAll(".rg").forEach(b => b.addEventListener("click", () => {
    if (b.disabled) return; try { localStorage.setItem("mm-range", b.dataset.r); } catch (_) {} apply(+b.dataset.r); }));
  let r0 = 1; try { r0 = +(localStorage.getItem("mm-range") || 1); } catch (_) {}
  if (r0 !== 1) apply(r0);
})();
</script>"""


def add_today_cpu(page):
    return page.replace("</body>", TODAY_CPU_JS + "</body>", 1)


# ---------- Recommendation: the buddy teaches how it got to the answer ----------
# Every number comes from the readings. Steps that do not apply to this Mac are left out.
def lesson_html(*, hours_txt, wm, TOTAL, work, wdays, fits, LADDER, peak_ever, peak_ever_when, target, rec, budget, fit16,
                disk_used, disk_txt, disk_rec, n_wd, WD_GOAL, cpu):
    def row(sz):
        return f".lad[data-sz='{sz}']" if sz in LADDER else ""
    me = int(round(TOTAL))
    nd = len(wdays)
    # (what the stick points at, what the bubble says, the scene the page acts out, that scene's numbers)
    first = cpu.get("first") and cpu["ok"]
    why = []
    if cpu.get("vn", 0) >= 60:
        o = cpu["others"]
        heat_t = ("Heat made it loud but never made macOS slow it down. " if o["hot"] and not o["slowed"] else
                  f"macOS slowed the chip for heat in {o['slowed']} minutes. " if o["slowed"] else "")
        oth_t = (f"Graphics, disk and network were over their lines in {o['over']} of {o['n']:,} minutes. " if o["n"] else "")
        why = [("#rec-why", f"First, what held it up. In {cpu['vn']:,} {wm}, work waited on the processors <b>{cpu['p_cpu']:.0%}</b> "
                            f"of the time and on memory <b>{cpu['p_mem']:.0%}</b>. {heat_t}{oth_t}"
                            f"So I start with the {'processors' if first else 'memory'}.", "why", {})]
    mem = [("#rec-note", (f"Then memory. I watched <b>{len(work):,} minutes</b>, {hours_txt}, over {nd} day{'s' if nd != 1 else ''}." if first else
                          f"{'Memory: i' if why else 'I'} watched <b>{len(work):,} minutes</b>, {hours_txt}, over {nd} day{'s' if nd != 1 else ''}."
                          + ("" if why else " Here is how I got from those to my answer.")), "minutes", {"n": len(work)})]
    spill = peak_ever > TOTAL
    mem.append(("#rec-jars", f"The busiest minute, {peak_ever_when}, needed <b>{peak_ever:.1f} GB</b>. "
                             + (f"This Mac has {TOTAL:.0f}, so {peak_ever - TOTAL:.1f} GB of it had to wait on the disk." if spill else
                                f"This Mac has {TOTAL:.0f}, so even that minute fitted."),
                "jar", {"jar": 0}))
    mem.append((row(me), f"{TOTAL:.0f} GB was enough in {'only ' if fit16 < .9 else ''}<b>{fit16:.0%} of those minutes</b>."
                         + (" The rest of the time, part of what you had open sat on the disk." if fit16 < 1 else ""),
                "fit", {"sz": me, "pct": round(fit16 * 100)}))
    if rec > TOTAL and budget != rec and budget > TOTAL:
        mem.append((row(budget), f"<b>{budget} GB</b> would have covered 99% of minutes. That is the budget pick: "
                                 "enough for today, with little room to grow.",
                    "budget", {"sz": budget, "pct": round(fits(budget, work) * 100)}))
    jar_i, cap = (1, rec) if rec > TOTAL else (0, int(round(TOTAL)))
    mem.append(("#rec-jars, #rec-mem",
                f"For memory I take the busiest minute, {peak_ever:.1f} GB, and add a quarter for a heavier week: {target:.1f} GB. "
                + (f"The next size Macs come in is <b>{rec} GB</b>." if rec > TOTAL else f"This Mac already has <b>{TOTAL:.0f} GB</b>."),
                "measure", {"jar": jar_i, "cap": cap, "a": round(peak_ever, 1), "b": round(target, 1)}))
    proc = []
    if cpu["ok"]:
        cd = cpu["days"]
        proc.append(("#rec-cpu", f"{'The processors' if first else 'Then the processors'}. More work was waiting than this Mac&#x27;s {cpu['cores']} cores could run in "
                                 f"<b>{cpu['wait']:.0%} of {wm}</b>. "
                                 + (f"A chip with <b>{cpu['chip']} cores</b> would have kept up 9 minutes in 10. " if cpu["chip"] and cpu["up"] else
                                    f"Even {cpu['chip_b'][:-7]} cores would not have kept up 9 minutes in 10. " if cpu["up"] else
                                    "This chip kept up 9 minutes in 10, so it is enough. ")
                                 + f"That is from {cd} working day{'s' if cd != 1 else ''}, so it is a first guess.",
                     "cores", {"rows": cpu["rows"], "pick": cpu["chip"] if cpu["up"] else 0}))
    steps = why + (proc + mem if first else mem + proc)
    steps.append(("#rec-disk", f"Storage: <b>{disk_used:.0f} GB</b> is in use now. Half again for growth makes "
                               f"{disk_used * 1.5:.0f} GB, so <b>{disk_txt}</b>.",
                  "disk", {"used": round(disk_used), "need": round(disk_used * 1.5), "cap": disk_rec, "label": disk_txt}))
    steps.append(("#rec-days", f"I have measured {n_wd} of {WD_GOAL} working days so far. A busier week could change this, "
                               "so keep me running.", "days", {"n": n_wd, "goal": WD_GOAL}))
    mem_p = f"<b>{rec} GB</b> of memory" if rec > TOTAL else ""
    chip_p = f"a chip with <b>{cpu['chip_b']}</b>" if cpu["ok"] and cpu["up"] else ""
    parts = [x for x in ((chip_p, mem_p) if first else (mem_p, chip_p)) if x]
    order = ["rec-chip", "rec-mem", "rec-disk"] if first else ["rec-mem", "rec-chip", "rec-disk"]
    steps.append(("#rec-h1", ("So: " + ", ".join(parts) + f" and <b>{disk_txt}</b> of storage.") if mem_p else
                             (f"So: this Mac&#x27;s memory is enough, but it needs a chip with <b>{cpu['chip_b']}</b>." if chip_p else
                              f"So: this Mac&#x27;s <b>{TOTAL:.0f} GB</b> is enough for now. Look again after a busy week."),
                  "sum", {"order": order}))
    n = len(steps)
    items = "".join(f'<li data-t="{t}" data-scene="{sc}" data-d=\'{json.dumps(d)}\'{" class=on" if k == 0 else ""}>'
                    f'<span class=k>{k + 1} of {n}</span>{x}</li>' for k, (t, x, sc, d) in enumerate(steps))
    return (f'<div class="lesson en" id=lesson style="--n:1"><ol aria-label="How the buddy worked out the answer">{items}</ol>'
            '<div class=ctl><button type=button class=lp aria-label="Previous step">&lsaquo;</button><span class=ld aria-hidden=true></span>'
            '<button type=button class=lt aria-label="Pause the lesson"></button>'
            '<button type=button class=ln aria-label="Next step">&rsaquo;</button></div></div>')

LESSON_CSS = """
/* the lesson: one speech bubble, one step at a time; all steps share one grid cell so the bubble never changes height */
.lesson{position:relative;margin:10px 0 0;max-width:58rem;display:flex;gap:14px;align-items:center;padding:12px 14px 12px 18px;
 border:2px solid var(--line);border-radius:6px 22px 22px 22px;background:var(--card);box-shadow:0 6px 18px rgba(29,42,68,.07)}
.lesson:before{content:"";position:absolute;left:-12px;top:12px;border:10px solid transparent;border-right-color:var(--line);border-left:0}
.lesson ol{list-style:none;margin:0;padding:0;display:grid;flex:1;min-width:0}
.lesson li{grid-area:1/1;font-size:clamp(.98rem,1.45vw,1.08rem);line-height:1.45;color:var(--fg);opacity:0;visibility:hidden;
 transform:translateY(5px);transition:opacity .16s ease-out,transform .16s ease-out,visibility 0s .16s}
.lesson li.on{opacity:1;visibility:visible;transform:none;transition:opacity .24s ease-out .06s,transform .24s cubic-bezier(.2,.8,.2,1) .06s,visibility 0s}
.lesson li b{font-weight:700;background:linear-gradient(transparent 60%,var(--fillA) 0)}
.lesson .k{font:600 12px 'Geist Mono',monospace;color:var(--mute);margin-right:8px;white-space:nowrap}
.lesson .ctl{display:flex;align-items:center;gap:6px;flex:none}
.lesson button{width:30px;height:30px;border-radius:50%;border:2px solid var(--line);background:transparent;color:var(--fg);
 font:700 15px/1 Geist,sans-serif;display:grid;place-items:center;padding:0}
.lesson button:hover{border-color:var(--banana);background:var(--fillB)}
.lesson .ld{display:flex;gap:4px;align-items:center;margin:0 2px}
.lesson .ld i{width:7px;height:7px;border-radius:4px;background:var(--line);position:relative;overflow:hidden;transition:width .2s}
.lesson .ld i.done{background:color-mix(in oklab,var(--fg) 45%,transparent)}
.lesson .ld i.on{width:22px}
.lesson .ld i.on:after{content:"";position:absolute;inset:0;background:var(--fg);transform-origin:left;transform:scaleX(var(--p,0))}
.lesson-t{outline:3px solid transparent;outline-offset:5px;transition:outline-color .24s ease-out}
.lesson-t.lit{outline-color:var(--banana)}
#rec-h1.lesson-t{outline:0}
#p-rec .row.lad.lesson-t{border-radius:12px}
#p-rec .buddy svg{overflow:visible}
#p-rec .buddy-wrap .arm-r,#p-rec .buddy-wrap .arm-l{animation:none!important}
#p-rec .buddy-wrap[data-mood=over] .bob{animation:bob 2.6s ease-in-out infinite}
#p-rec .stick{transform-box:view-box;transform-origin:178px 100px;transition:transform .36s cubic-bezier(.2,.8,.2,1)}
#p-rec .buddy svg.nod{animation:nod .34s ease-out}
@keyframes nod{40%{transform:translateY(4px)}}
@media(prefers-reduced-motion:reduce){.lesson li,.lesson li.on,.lesson-t,#p-rec .stick,.lesson .ld i{transition:none}#p-rec .buddy svg.nod{animation:none}}

/* scenes: on each step the page's own pictures act it out. Everything else fades back; nothing changes size. */
#p-rec .hero>*,#p-rec .two>.c,#p-rec .specs>.c,#p-rec .ladder .row{transition:opacity .4s ease-out,transform .6s cubic-bezier(.2,.9,.25,1)}
#p-rec.sc-on .hero>:not(#lesson):not(.buddy-wrap),#p-rec.sc-on .two>.c:not(.sc-lead),#p-rec.sc-on .specs>.c:not(.sc-lead){opacity:.2}
#p-rec.sc-rows .ladder .row:not(.sc-lead){opacity:.3}
#p-rec.sc-soft .ladder .row:not(.sc-lead){opacity:.55}
#rec-jars.sc-fwd{position:relative;z-index:6;background:var(--bg);box-shadow:0 18px 50px rgba(29,42,68,.18)}
#rec-jars .jar{transition:opacity .4s}
#rec-jars .jar.sc-back{opacity:.25}
.sc-x{pointer-events:none}
.sc-disk{position:absolute;top:0;bottom:0;right:0;border-radius:0 9px 9px 0;background:repeating-linear-gradient(45deg,color-mix(in oklab,var(--hot) 55%,transparent) 0 6px,transparent 6px 12px);
 background-size:17px 17px;transform-origin:left;animation:scgrow .8s cubic-bezier(.16,1,.3,1) both,scslide 1.2s linear infinite}
.sc-tag{position:absolute;bottom:calc(100% + 6px);white-space:nowrap;font:600 12.5px Geist,sans-serif;animation:scfade .35s .55s both}
.sc-disk .sc-tag{right:0;color:var(--hot)}
.sc-line{position:absolute;width:0;border-left:2px dashed var(--fg);transform-origin:top;animation:scdrop .7s cubic-bezier(.16,1,.3,1) both}
.sc-line .sc-tag{left:6px;bottom:auto;top:-22px;color:var(--fg)}
.sc-meas line{stroke:var(--fg);stroke-width:3;stroke-dasharray:8 7;opacity:0;transition:opacity .3s,y1 .9s cubic-bezier(.16,1,.3,1),y2 .9s cubic-bezier(.16,1,.3,1)}
.sc-meas .m2{stroke:#e8590c}
.sc-meas text{font:600 21px Geist,sans-serif;fill:var(--fg);opacity:0;transition:opacity .35s}
.sc-meas .t2{fill:#e8590c} .sc-meas .t3{font:700 34px Fredoka,sans-serif}
.sc-meas .on{opacity:1}
.sc-meas .t3.on,.sc-slam{animation:scslam .3s cubic-bezier(.2,.8,.2,1) both;transform-box:fill-box;transform-origin:center}
#rec-jars.sc-fwd .jtag.good{opacity:0}
.sc-call{position:absolute;left:0;right:0;bottom:calc(100% + 12px);z-index:7;padding:12px 14px;border-radius:18px;background:var(--bg);border:2px solid var(--line);
 box-shadow:0 10px 30px rgba(29,42,68,.14);font:500 13px Geist,sans-serif;color:var(--mute);animation:scrise .45s cubic-bezier(.2,.9,.25,1) both}
.sc-gauge{position:relative;height:16px;border-radius:9px;background:var(--line);margin:8px 0 8px}
.sc-gauge i{position:absolute;left:0;top:0;bottom:0;border-radius:9px;transform-origin:left;animation:scgrow .9s cubic-bezier(.16,1,.3,1) both}
.sc-gauge .u{background:linear-gradient(90deg,var(--banana),#f0a500)}
.sc-gauge .h{background:repeating-linear-gradient(45deg,rgba(201,151,0,.55) 0 6px,transparent 6px 12px);border:2px dashed #c99700;top:-3px;bottom:-3px}
.sc-leg{display:flex;justify-content:space-between;gap:8px;font:600 12.5px Geist,sans-serif;color:var(--fg)}
.sc-leg i{font-style:normal;white-space:nowrap;animation:scfade .3s both} .sc-leg .e2{color:#9a7400} .sc-leg .end{margin-left:auto}
.sc-days{display:flex;gap:6px;margin-top:4px}
.sc-days i{flex:1;height:22px;border-radius:7px;border:2px dashed var(--line)}
.sc-days i.y{border:0;background:linear-gradient(180deg,var(--banana),#f0a500);animation:scpop .4s cubic-bezier(.3,1.6,.5,1) both}
.specs .c.sc-pop{transform:translateY(-6px);outline:3px solid var(--banana);outline-offset:4px}
@keyframes scgrow{from{transform:scaleX(0)}} @keyframes scslide{to{background-position:17px 0}} @keyframes scfade{from{opacity:0;transform:translateY(4px)}}
@keyframes scdrop{from{transform:scaleY(0)}} @keyframes scrise{from{opacity:0;transform:translateY(10px)}} @keyframes scpop{from{transform:scale(.3);opacity:0}}
@keyframes scslam{0%{transform:scale(1.55)}55%{transform:scale(.94)}100%{transform:scale(1)}}
@media(prefers-reduced-motion:reduce){#p-rec .hero>*,#p-rec .two>.c,#p-rec .specs>.c,#p-rec .ladder .row,.sc-meas line,.sc-meas text{transition:none}
 .sc-disk,.sc-tag,.sc-line,.sc-call,.sc-gauge i,.sc-leg i,.sc-days i.y,.sc-meas .t3.on,.sc-slam{animation:none}}
@media(max-width:760px){.lesson{flex-direction:column;align-items:stretch;border-radius:22px;text-align:left}.lesson:before{display:none}.lesson .ctl{justify-content:center}}
"""

LESSON_JS = r"""<script>
(() => {
  const L = document.getElementById("lesson"); if (!L) return;
  const P = document.getElementById("p-rec"), steps = [...L.querySelectorAll("li")], n = steps.length;
  const calm = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const ld = L.querySelector(".ld"); ld.innerHTML = steps.map(() => "<i></i>").join(""); const dots = [...ld.children];
  const bt = L.querySelector(".lt");
  const tgts = k => { const sel = steps[k].dataset.t; return sel ? [...document.querySelectorAll(sel)] : []; };
  steps.forEach((_, k) => tgts(k).forEach(el => el.classList.add("lesson-t")));
  // The pointer stick sits in the buddy's raised hand and turns toward whatever the bubble is about.
  const svg = document.querySelector("#p-rec .buddy svg"), bob = svg && svg.querySelector(".bob"), hand = svg && svg.querySelector(".arm-r circle");
  let stick = null;
  if (bob && hand) {
    stick = document.createElementNS("http://www.w3.org/2000/svg", "g"); stick.setAttribute("class", "stick");
    stick.innerHTML = '<rect x="174" y="97" width="100" height="6" rx="3" fill="#8b5a2b"/><rect x="264" y="95" width="16" height="10" rx="5" fill="#ffd93b" stroke="#c99700" stroke-width="1.5"/>';
    bob.insertBefore(stick, bob.firstChild);
  }
  let i = 0, playing = true, t = 0, last = performance.now(), ang = null, wasOn = false;
  // On a short screen the cards at the bottom sit below the fold: bring the one being explained into view.
  const show = () => { const el = tgts(i)[0]; if (!el || !P.classList.contains("on") || matchMedia("(max-width: 760px)").matches) return; const how = calm ? "auto" : "smooth";
    if (el.closest(".hero")) P.scrollTo({ top: 0, behavior: how }); else el.scrollIntoView({ block: "nearest", behavior: how }); };
  try {
    const s = JSON.parse(sessionStorage.getItem("mm-lesson") || "null");
    if (s && s.n === n) { i = Math.min(s.i, n - 1); playing = s.playing; t = s.t || 0; }
  } catch (_) {}
  // The page reloads itself every minute for the newest reading. A pause, or a lesson that has finished, must survive that
  // reload even when the browser drops session storage or the number of steps changes, so the hold is kept on its own.
  const HOLD = "mm-lesson-hold", holdFor = 2 * 3600e3;
  const held = () => { try { if (sessionStorage.getItem(HOLD)) return sessionStorage.getItem(HOLD);
    const h = JSON.parse(localStorage.getItem(HOLD) || "null"); return h && Date.now() - h.at < holdFor ? h.why : null; } catch (_) { return null; } };
  const hold = why => { try { if (why) { sessionStorage.setItem(HOLD, why); localStorage.setItem(HOLD, JSON.stringify({ why, at: Date.now() })); }
    else { sessionStorage.removeItem(HOLD); localStorage.removeItem(HOLD); } } catch (_) {} };
  const h0 = held();
  if (h0) { playing = false; if (h0 === "done") { i = n - 1; t = 0; } }
  const dur = k => Math.max(4500, Math.min(9500, 2400 + steps[k].textContent.length * 42));
  const save = () => { try { sessionStorage.setItem("mm-lesson", JSON.stringify({ n, i, playing, t })); } catch (_) {} };
  const label = () => {
    const end = !playing && i === n - 1;
    bt.innerHTML = '<svg viewBox="0 0 12 12" width="12" height="12" aria-hidden="true">' + (playing ? '<rect x="2" y="1.5" width="2.8" height="9" rx="1" fill="currentColor"/><rect x="7.2" y="1.5" width="2.8" height="9" rx="1" fill="currentColor"/>'
      : end ? '<path d="M9.6 4.2A4.2 4.2 0 1 0 10.2 7" stroke="currentColor" stroke-width="1.8" fill="none" stroke-linecap="round"/><path d="M10.4 1.4v3.4H7" stroke="currentColor" stroke-width="1.8" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
      : '<path d="M3.2 1.6l7 4.4-7 4.4z" fill="currentColor"/>') + '</svg>';
    bt.setAttribute("aria-label", playing ? "Pause the lesson" : end ? "Replay the lesson" : "Play the lesson");
  };
  const aim = () => {
    if (!stick) return; const el = tgts(i)[0]; if (!el) return;
    const r = el.getBoundingClientRect(); if (!r.width) return;
    const p = svg.createSVGPoint(); p.x = 178; p.y = 100; const h = p.matrixTransform(bob.getScreenCTM());
    let a = Math.atan2(r.top + r.height / 2 - h.y, Math.max(r.left + Math.min(r.width / 2, 160), r.left + 10) - h.x) * 180 / Math.PI;
    a = Math.max(22, Math.min(105, a));  // never across the headline
    if (ang === null || Math.abs(a - ang) > .5) { ang = a; stick.style.transform = `rotate(${a.toFixed(1)}deg)`; }
  };

  // Scenes: the page's own charts act out each step. Numbers come from the step's data-d, written by report.py.
  const NS = "http://www.w3.org/2000/svg", wide = () => !matchMedia("(max-width: 760px)").matches;
  const jarsCard = document.getElementById("rec-jars"), jarSvg = jarsCard && jarsCard.querySelector("svg");
  const lad = sz => P.querySelector(`.lad[data-sz='${sz}']`);
  P.querySelectorAll(".lad,.cad").forEach(r => { const b = r.querySelector(".track b"); r.dataset.w = b.style.getPropertyValue("--w"); r.dataset.em = r.querySelector("em").textContent; });
  P.querySelectorAll("#rec-why .vbar i").forEach(b => b.dataset.w = b.style.width);
  let ST = [];
  const later = (f, ms) => ST.push(setTimeout(f, calm ? 0 : ms));
  const count = (el, from, to, ms, fmt) => { if (calm) { el.textContent = fmt(to); return; } const t0 = performance.now();
    const f = () => { const q = Math.min((performance.now() - t0) / ms, 1); el.textContent = fmt(q >= 1 ? to : from + (to - from) * (1 - Math.pow(2, -10 * q))); if (q < 1 && ST.length) requestAnimationFrame(f); }; f(); };
  const pct = v => Math.round(v) + "%";
  const fill = (r, to, delay) => { const b = r.querySelector(".track b"), em = r.querySelector("em");
    b.style.transition = "none"; b.style.setProperty("--w", "2%"); em.textContent = "0%"; void b.offsetWidth;
    later(() => { b.style.transition = "width 1.1s cubic-bezier(.16,1,.3,1)"; b.style.setProperty("--w", to + "%"); count(em, 0, to, 1100, pct); }, delay); };
  // On a phone the step's target is often below the fold, so fading the rest would only dim what is on screen.
  const dim = (...c) => wide() && P.classList.add(...c);
  const lead = (...els) => els.forEach(e => e && e.classList.add("sc-lead"));
  const replay = g => g && g.getAnimations({ subtree: true }).forEach(a => { a.cancel(); a.play(); });
  // Bring the jars card forward into the space under the speech bubble, as large as fits there (never over the bubble).
  const forward = () => { if (!jarsCard || !wide()) return; const r = jarsCard.getBoundingClientRect(), top = L.getBoundingClientRect().bottom + 14,
      room = Math.min(innerHeight, P.getBoundingClientRect().bottom) - top - 14, s = Math.max(1, Math.min(1.28, room / r.height, innerWidth * .8 / r.width));
    jarsCard.classList.add("sc-fwd"); jarsCard.style.transform = `translate(${innerWidth / 2 - (r.left + r.width / 2)}px,${top + Math.max(room, r.height * s) / 2 - (r.top + r.height / 2)}px) scale(${s})`; };
  const add = (parent, html, cls) => { const d = document.createElement("div"); d.className = "sc-x " + cls; d.innerHTML = html; parent.appendChild(d); return d; };
  const reset = () => {
    ST.forEach(clearTimeout); ST = [];
    P.classList.remove("sc-on", "sc-rows", "sc-soft");
    P.querySelectorAll(".sc-lead,.sc-pop,.sc-back,.sc-slam").forEach(e => e.classList.remove("sc-lead", "sc-pop", "sc-back", "sc-slam"));
    P.querySelectorAll(".sc-x").forEach(e => e.remove()); jarSvg && jarSvg.querySelector(".sc-meas")?.remove();
    if (jarsCard) { jarsCard.style.transform = ""; jarsCard.classList.remove("sc-fwd"); }
    P.querySelectorAll(".lad,.cad").forEach(r => { const b = r.querySelector(".track b"); b.style.transition = ""; b.style.setProperty("--w", r.dataset.w); r.querySelector("em").textContent = r.dataset.em; });
    const note = document.getElementById("rec-note"); if (note && note.dataset.t) note.innerHTML = note.dataset.t;
    P.querySelectorAll("#rec-why .vbar i").forEach(b => { b.style.transition = ""; b.style.width = b.dataset.w; });
  };
  const SC = {
    minutes(d) { const card = P.querySelector(".ladder.meml").closest(".c"), note = document.getElementById("rec-note");
      dim("sc-on"); lead(card);
      P.querySelectorAll(".lad").forEach((r, k) => fill(r, parseInt(r.dataset.em), 120 + k * 90));
      note.dataset.t = note.innerHTML; const n = d.n.toLocaleString("en-GB");
      note.innerHTML = note.innerHTML.replace(n, `<b class=sc-n>${n}</b>`); const el = note.querySelector(".sc-n");
      if (el) count(el, 0, d.n, 1400, v => Math.round(v).toLocaleString("en-GB")); },
    jar(d) { const g = jarSvg && jarSvg.querySelectorAll(".jar"); if (!g) return;
      dim("sc-on"); lead(jarsCard); forward();
      g.forEach((x, k) => x.classList.toggle("sc-back", k !== d.jar));
      later(() => replay(g[d.jar]), 450); later(() => g[d.jar].querySelector(".jtag")?.classList.add("sc-slam"), 1700); },
    fit(d) { const r = lad(d.sz); if (!r) return; dim("sc-on", "sc-rows"); lead(r.closest(".c"), r);
      fill(r, d.pct, 300);
      if (d.pct < 100) later(() => add(r.querySelector(".track"), `<span class=sc-tag>${100 - d.pct}% of minutes: some of it on the disk</span>`, "sc-disk").style.left = d.pct + "%", 1500); },
    budget(d) { const r = lad(d.sz); if (!r) return; const lc = P.querySelector(".ladder.meml"), tr = [...lc.querySelectorAll(".track")];
      dim("sc-on", "sc-soft"); lead(r.closest(".c"), r);
      const a = tr[0].getBoundingClientRect(), z = tr[tr.length - 1].getBoundingClientRect(), o = lc.getBoundingClientRect(); lc.style.position = "relative";
      const ln = add(lc, "<span class=sc-tag>99% of minutes</span>", "sc-line");
      Object.assign(ln.style, { left: (a.left - o.left + a.width * .99) + "px", top: (a.top - o.top - 6) + "px", height: (z.bottom - a.top + 12) + "px" });
      fill(r, d.pct, 700); },
    measure(d) { const g = jarSvg && jarSvg.querySelectorAll(".jar"); if (!g) return;
      dim("sc-on"); lead(jarsCard, document.getElementById("rec-mem")); forward();
      g.forEach((x, k) => x.classList.toggle("sc-back", k !== d.jar));
      const cx = d.jar ? 740 : 260, y = v => 300 - 210 * v / d.cap, X0 = cx - 95, X1 = cx + 95;
      const m = document.createElementNS(NS, "g"); m.setAttribute("class", "sc-meas"); jarSvg.appendChild(m);
      m.innerHTML = `<line class=m1 x1="${X0 - 6}" x2="${X1 + 10}" y1="${y(d.a)}" y2="${y(d.a)}"/><text class=t1 x="${X1 + 18}" y="${y(d.a) + 7}">busiest ${d.a} GB</text>`
        + `<line class=m2 x1="${X0 - 6}" x2="${X1 + 10}" y1="${y(d.a)}" y2="${y(d.a)}"/><text class=t2 x="${X1 + 18}" y="${y(d.b) + 7}">+ ¼ = ${d.b} GB</text>`
        + `<text class=t3 x="${cx}" y="64" text-anchor=middle>${d.cap} GB</text>`;
      later(() => replay(g[d.jar]), 450);
      later(() => { m.querySelector(".m1").classList.add("on"); m.querySelector(".t1").classList.add("on"); }, 1400);
      later(() => { const l = m.querySelector(".m2"); l.classList.add("on"); l.setAttribute("y1", y(d.b)); l.setAttribute("y2", y(d.b)); m.querySelector(".t2").classList.add("on"); }, 2600);
      later(() => m.querySelector(".t3").classList.add("on"), 3900); },
    cores(d) { const box = document.getElementById("rec-cpu"); if (!box) return; const pick = d.pick && P.querySelector(`.cad[data-c='${d.pick}']`);
      dim("sc-on", "sc-rows"); lead(box.closest(".c"), ...(pick ? [pick] : [...box.querySelectorAll(".cad")]));
      d.rows.forEach(([c, p], k) => { const r = P.querySelector(`.cad[data-c='${c}']`); if (r) fill(r, p, 200 + k * 160); });
      if (pick) later(() => document.getElementById("rec-chip")?.classList.add("sc-pop"), 1400); },
    disk(d) { const c = document.getElementById("rec-disk"); if (!c) return; dim("sc-on"); lead(c);
      const w = v => Math.min(v / d.cap * 100, 100).toFixed(1) + "%";
      add(c, `<div class=sc-gauge><i class=h style="width:${w(d.need)};animation-delay:.9s"></i><i class=u style="width:${w(d.used)}"></i></div>`
        + `<div class=sc-leg><i>in use ${d.used} GB</i><i class=e2 style="animation-delay:1.3s">+ half = ${d.need} GB</i><i class=end style="animation-delay:1.8s">fits in ${d.label}</i></div>`, "sc-call"); },
    days(d) { const c = document.getElementById("rec-days"); if (!c) return; dim("sc-on"); lead(c);
      add(c, `<div>${d.n} of ${d.goal} working days measured</div><div class=sc-days>`
        + Array.from({ length: d.goal }, (_, k) => k < d.n ? `<i class=y style="animation-delay:${.3 + k * .12}s"></i>` : "<i></i>").join("") + "</div>", "sc-call"); },
    why() { const c = document.getElementById("rec-why"); if (!c) return; dim("sc-on"); lead(c);
      c.querySelectorAll(".vbar i").forEach((b, k) => { b.style.transition = "none"; b.style.width = "0%"; void b.offsetWidth;
        later(() => { b.style.transition = "width 1.1s cubic-bezier(.16,1,.3,1)"; b.style.width = b.dataset.w; }, 250 + k * 600); }); },
    sum(d) { const em = document.querySelector("#rec-h1 em"); if (em) { em.classList.remove("sc-slam"); void em.offsetWidth; later(() => em.classList.add("sc-slam"), 200); }
      (d.order || ["rec-mem", "rec-chip", "rec-disk"]).forEach((id, k) => later(() => document.getElementById(id)?.classList.add("sc-pop"), 600 + k * 260)); },
  };
  const scene = () => { reset(); const st = steps[i], f = SC[st.dataset.scene]; if (!f || !P.classList.contains("on")) return;
    try { f(JSON.parse(st.dataset.d || "{}")); } catch (_) {} };
  // Never block use: a click anywhere outside the bubble (or, on a wide screen, a scroll) puts the page back as it was.
  // Not pointerdown: on a phone every scroll starts with one, and the reader has to scroll to reach steps 6 to 8.
  // A click, scroll or swipe outside the bubble means the reader wants the page: stop the lesson and put the page back.
  const back = e => { if (e.target.closest && e.target.closest("#lesson")) return; reset();
    if (playing) { playing = false; hold("paused"); label(); save(); } };
  P.addEventListener("click", back); P.addEventListener("wheel", back, { passive: true }); P.addEventListener("touchmove", back, { passive: true });
  let sceneT = null; const later0 = f => { clearTimeout(sceneT); sceneT = setTimeout(f, calm ? 0 : 120); };
  const go = (k, keepT, user) => {
    tgts(i).forEach(el => el.classList.remove("lit"));
    i = Math.max(0, Math.min(n - 1, k)); if (!keepT) t = 0;
    steps.forEach((s, j) => s.classList.toggle("on", j === i));
    dots.forEach((d, j) => { d.classList.toggle("on", j === i); d.classList.toggle("done", j < i); d.style.setProperty("--p", 0); });
    tgts(i).forEach(el => el.classList.add("lit"));
    if (user) show();                  // only the reader's own step, replay or play scrolls the page
    if (user || playing) later0(scene); // a paused or finished lesson leaves the page as it is
    if (svg && !calm) { svg.classList.remove("nod"); void svg.getBoundingClientRect(); svg.classList.add("nod"); }
    aim(); label(); save();
  };
  L.querySelector(".lp").onclick = () => { playing = false; hold("paused"); go(i - 1, false, true); };
  L.querySelector(".ln").onclick = () => { playing = false; hold("paused"); go(i + 1, false, true); };
  bt.onclick = () => { if (playing) { playing = false; hold("paused"); label(); save(); }
    else { playing = true; hold(null); if (i === n - 1) go(0, false, true); else { label(); save(); } } };
  go(i, true);
  setInterval(() => {
    const now = performance.now(), dt = now - last; last = now;
    aim();
    const on = P.classList.contains("on"); if (on && !wasOn && playing) later0(scene); if (!on && wasOn) reset(); wasOn = on;
    if (!playing || !P.classList.contains("on") || document.hidden) return;
    t += dt; const d = dur(i);
    if (dots[i]) dots[i].style.setProperty("--p", Math.min(t / d, 1).toFixed(3));
    if (t >= d) { if (i < n - 1) go(i + 1); else { playing = false; hold("done"); label(); save(); } }   // plays once, then rests on the summary
    else if (Math.floor(t / 1000) !== Math.floor((t - dt) / 1000)) save();
  }, 100);
})();
</script>"""


def add_lesson(page):
    return page.replace("</style>", LESSON_CSS + "</style>", 1).replace("</body>", LESSON_JS + "</body>", 1)
