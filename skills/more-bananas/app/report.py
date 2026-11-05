"""The memory report as a case: this 16 GB Mac is too small for a busy workday.

Six full-screen panels behind a pill tab bar (no long scroll), cute charts with buddy decor.
memlog.py collects the readings and calls render(v) with its variables; buddy.py then adds the
mascot, the buddy yard (at <!--YARD-->) and the sparkle effects.
"""
import datetime as dt
import html
import json
import os


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
    cpu_now = v.get("cpu_pct")
    cpu_top = sorted(((x, g) for g, x in (v.get("cpu_by_group") or {}).items() if x >= 3), reverse=True)[:3]
    disk_now = "nothing is being pushed to disk" if calm else f"it is pushing {out_mb:.0f} MB a minute to disk"
    if cpu_now is not None and cpu_now >= 60:
        who = f" ({', '.join(f'{g} {x:.0f}%' for x, g in cpu_top)})" if cpu_top else ""
        status_line = (f"Right now the processors are {min(cpu_now, 100):.0f}% busy{who}, enough to run warm and loud. "
                       + ("Memory is fine: nothing is being pushed to disk." if calm else f"And {disk_now}."))
    elif calm:
        status_line = "Right now it is quiet: nothing is being pushed to disk" + (f", and the processors are {cpu_now:.0f}% busy." if cpu_now is not None else ".")
    else:
        status_line = f"Right now {disk_now}" + (f", and the processors are {cpu_now:.0f}% busy." if cpu_now is not None else ".")
    peak_when = dt.datetime.strptime(T[pk], "%Y-%m-%d %H:%M").strftime("%-d %b, %H:%M")
    swap_when = dt.datetime.strptime(LT[lpk], "%Y-%m-%d %H:%M").strftime("%-d %b, %H:%M")

    # ---------- panel 2: the busy-stretch chart ----------
    W, H, PAD = 1000, 300, 30
    top = max(max(need), TOTAL) * 1.18
    n = len(need)
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
        ticks += f'<text x="{X(i):.1f}" y="{H + 20}" class=tk text-anchor="middle">{e(T[i][11:] if T[i][:10] == T[0][:10] == T[-1][:10] else T[i][5:10].replace("-", "/") + " " + T[i][11:])}</text>'
    swap_by_t = {t: x for t, x in zip(LT, LO)}
    drops = []
    smax = max(max(LO), 50)
    for i, t in enumerate(T):
        x = swap_by_t.get(t, 0)
        if x >= 5:
            h = 10 + 50 * x / smax
            drops.append(f'<g class=dr style="--d:{(i % 7) * .3:.1f}s"><rect x="{X(i)-3:.1f}" y="0" width="6" height="{h:.1f}" rx="3"/>'
                         f'<circle cx="{X(i):.1f}" cy="{h + 4:.1f}" r="3.2"/><title>{e(t)}: {x:.0f} MB pushed to disk</title></g>')
    series = json.dumps({"t": T, "need": [round(x, 2) for x in need], "ram": [round(x, 2) for x in U],
                         "swap": [round(swap_by_t.get(t, 0)) for t in T]})

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
    meas = [d for d in days if d in dmem]
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

    last_t = max(tj) if tj else stamp_now
    last_dt = dt.datetime.strptime(last_t, "%Y-%m-%d %H:%M")
    views, take_k = [], None
    for vid, vname, hours in (("now", "Now", 0), ("d1", "24 hours", 24), ("d7", "7 days", 168), ("d30", "30 days", 720)):
        cut = (last_dt - dt.timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M")
        mins_ = [t_ for t_ in tj if (t_ == last_t if hours == 0 else t_ > cut)]
        ks, peak_k, per_min = {}, {}, {}
        for t_ in mins_:
            for (se, jb), g_ in tj[t_].items():
                k_ = kind(jb)
                ks.setdefault(k_, {}).setdefault((se, label(jb)), 0)
                ks[k_][(se, label(jb))] += g_ / len(mins_)  # average over the window's minutes (now: this minute)
                per_min[(t_, k_)] = per_min.get((t_, k_), 0) + g_
        for (t_, k_), g_ in per_min.items():
            peak_k[k_] = max(peak_k.get(k_, 0), g_)
        tot = {k_: sum(v.values()) for k_, v in ks.items()}
        if hours == 168 and peak_k:
            take_k = max(peak_k.items(), key=lambda kv: kv[1])
        if not tot:
            body = '<p class=note>Nothing from Claude in this window.</p>'
        else:
            sc = max(tot.values())
            desc = dict(KINDS)
            body = '<p class=uh><span>Group</span><span>' + ("memory now" if hours == 0 else "average &middot; busiest minute, GB") + '</span></p>'
            for j, (k_, x) in enumerate(sorted(tot.items(), key=lambda kv: -kv[1])):
                topj = sorted(ks[k_].items(), key=lambda kv: -kv[1])[:6]
                inner = "".join(f'<li><span><b>{e(jb)}</b> <i>{e(se)}</i></span><em>{g_:.1f} GB</em></li>' for (se, jb), g_ in topj)
                more = len(ks[k_]) - len(topj)
                val = f"{x:.1f} GB" if hours == 0 else f"{x:.1f} &middot; {peak_k.get(k_, 0):.1f}"
                body += (f'<details class=kind style="--i:{j}"><summary><div class="row jr"><span><b>{e(k_)}</b><br><i>{len(ks[k_])} job{"s" if len(ks[k_]) != 1 else ""}</i></span>'
                         f'<div class=track><b style="--w:{x/sc*100:.0f}%"></b></div><em>{val}</em></div></summary>'
                         f'<p class=kd>{e(desc[k_])}</p><ul class=jl>{inner}</ul>{f"<p class=kd>+{more} smaller</p>" if more > 0 else ""}</details>')
        views.append((vid, vname, hours, body))
    have_h = (last_dt - dt.datetime.strptime(tfirst, "%Y-%m-%d %H:%M")).total_seconds() / 3600 if tfirst else 0
    jobs_tabs = "".join(f'<button type=button class=jt data-v={vid} aria-pressed={"true" if j == 0 else "false"}>{vn}</button>' for j, (vid, vn, _, _) in enumerate(views))
    jobs_views = "".join(f'<div class=jv data-v={vid}{"" if j == 0 else " hidden"}>'
                         + ("" if h == 0 or have_h >= h else f'<p class=kd>Only {have_h:.0f} hours recorded so far, so this covers less than {vn}.</p>')
                         + f'<div class=list>{b_}</div></div>' for j, (vid, vn, h, b_) in enumerate(views))

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
    HRS = list(range(7, 24))  # working hours only: 00:00-06:59 left out
    wcell = {k: x for k, x in cell.items() if k[1] in HRS}
    lo_ = min(wcell.values()) if wcell else 0; hi_ = max(wcell.values()) if wcell else 1
    def shade(x):  # one hue, light to dark (dataviz: sequential = single hue)
        f = (x - lo_) / max(hi_ - lo_, .01)
        return f"color-mix(in oklab, #e5484d {15 + 85*f:.0f}%, #fff4cc)"
    hm = []
    names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for wd in range(7):
        hm.append(f'<text x="{LX-8}" y="{TY + wd*CH + CH*.62:.0f}" text-anchor=end class=tk>{names[wd]}</text>')
        for h in HRS:
            x_, y_ = LX + (h - HRS[0])*CW, TY + wd*CH
            if (wd, h) in cell:
                val = cell[(wd, h)]
                ring = f'<circle cx="{x_ + CW/2 - 1:.0f}" cy="{y_ + CH/2 - 1:.0f}" r="4" fill="#fff"/>' if val > TOTAL else ""
                hm.append(f'<g class=hc style="--i:{wd*24+h}"><rect x="{x_}" y="{y_}" width="{CW-2}" height="{CH-2}" rx="7" style="fill:{shade(val)}"/>{ring}'
                          f'<title>{names[wd]} {h:02d}:00–{h:02d}:59: highest need {val:.1f} GB{" (over " + str(int(TOTAL)) + " GB)" if val > TOTAL else ""}</title></g>')
            else:
                hm.append(f'<rect x="{x_}" y="{y_}" width="{CW-2}" height="{CH-2}" rx="7" class=empty><title>{names[wd]} {h:02d}:00: no reading yet</title></rect>')
    for h in range(HRS[0], 24, 2):
        hm.append(f'<text x="{LX + (h - HRS[0])*CW + CW/2 - 1:.0f}" y="{TY - 8}" text-anchor=middle class=tk>{h:02d}:00</text>')
    heat_svg = "".join(hm)
    heat_w, heat_h = LX + len(HRS)*CW + 4, TY + 7*CH + 6
    filled = sum(1 for (_, h) in cell if h in HRS)

    # ---------- Recommendation: how often each size would have been enough ----------
    BR = "Browsers Claude drives"
    apps_all = v["apps"]
    work = [(t, x) for t, x in all_need if 7 <= int(t[11:13]) < 24]
    split_t = min((t for t, d_ in apps_all.items() if BR in d_), default=None)
    work_nb = [(t, x - apps_all.get(t, {}).get(BR, 0)) for t, x in work if split_t and t >= split_t]
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
        nb = f'<i>without Claude&#x27;s test browsers: {fits(sz, work_nb):.0%}</i>' if work_nb else ""
        ladder += (f'<div class="row lad{" me" if sz == rec else ""}" data-sz="{sz}" style="--i:{LADDER.index(sz)}"><span><b>{sz} GB</b>{tag}<br>{nb}</span>'
                   f'<div class=track><b style="--w:{max(f_ * 100, 2):.0f}%"></b></div><em>{f_:.0%}</em></div>')
    cpu_rows = []
    cp_ = os.path.join(v["HOME"], "cpu.csv")
    if os.path.exists(cp_):
        cpu_rows = [l.strip().split(",") for l in open(cp_) if l.count(",") == 3]
    cpu_work = sorted(float(r[1]) for r in cpu_rows if 7 <= int(r[0][11:13]) < 24)
    cpu_p95 = cpu_work[int(.95 * (len(cpu_work) - 1))] if cpu_work else None
    cpu_txt = (f"processor: 95% of working minutes used under {cpu_p95:.0f}% of its {cpu_rows[-1][3]} cores, so memory is the limit, not the chip." if cpu_p95 is not None and cpu_p95 < 70 and len(cpu_work) >= 60 else
               f"processor: 95% of working minutes used under {cpu_p95:.0f}% of its {cpu_rows[-1][3]} cores." if cpu_p95 is not None and len(cpu_work) >= 60 else
               "processor: measured from today, too few readings to judge yet.")

    lesson = lesson_html(TOTAL=TOTAL, work=work, wdays=wdays, work_nb=work_nb, fits=fits, LADDER=LADDER, peak_ever=peak_ever,
                         peak_ever_when=peak_ever_when, target=target, rec=rec, budget=budget, fit16=fit16, disk_used=disk_used,
                         disk_txt=disk_txt, disk_rec=disk_rec, n_wd=n_wd, WD_GOAL=WD_GOAL)

    # ---------- Busy hours: the takeaway ----------
    over_cells = sorted(((x, k) for k, x in wcell.items() if x > TOTAL), reverse=True)
    names_ = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    hours_take = (f"The worst so far: {names_[over_cells[0][1][0]]} {over_cells[0][1][1]:02d}:00, {over_cells[0][0]:.1f} GB." if over_cells else "No working hour has gone over yet.")

    # ---------- What uses memory: app groups over a time window, Claude's work opened up ----------
    a_last = max(apps_all) if apps_all else ""
    def uses_view(hours):
        if not a_last:
            return '<p class=note>No readings yet.</p>', 0
        if hours == 0:
            mins = [a_last]
        else:
            cut = (dt.datetime.strptime(a_last, "%Y-%m-%d %H:%M") - dt.timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M")
            mins = [t for t in apps_all if t > cut]
        tot, top_ = {}, {}
        for t in mins:
            for g, x in apps_all[t].items():
                tot[g] = tot.get(g, 0) + x; top_[g] = max(top_.get(g, 0), x)
        avg = {g: x / len(mins) for g, x in tot.items()}
        tmins = [t for t in mins if t in tj]
        sc = max(avg.values()) if avg else 1
        desc = dict(KINDS)
        out = ""
        for j, (g, x) in enumerate(sorted(avg.items(), key=lambda kv: -kv[1])):
            if x < .05:
                continue
            val = f"{x:.1f} GB" if hours == 0 else f"{x:.1f} &middot; {top_[g]:.1f}"
            row = f'<div class="row ur" style="--i:{j}" title="{e(g)}"><span>{e(g)}</span><div class=track><b style="--w:{x/sc*100:.0f}%"></b></div><em>{val}</em></div>'
            sub = ""
            if g in ("Tools Claude starts", BR) and tmins:
                ks = {}
                for t in tmins:
                    for (se, jb), g_ in tj[t].items():
                        k_ = kind(jb)
                        if (k_ == KINDS[0][0]) != (g == BR):
                            continue
                        ks.setdefault(k_, {}); ks[k_][(se, label(jb))] = ks[k_].get((se, label(jb)), 0) + g_ / len(tmins)
                for k_, jobs_ in sorted(ks.items(), key=lambda kv: -sum(kv[1].values())):
                    topj = sorted(jobs_.items(), key=lambda kv: -kv[1])[:5]
                    sub += (f'<p class=kd><b>{e(k_)}</b> &middot; {sum(jobs_.values()):.1f} GB{"" if hours == 0 else " on average"}. {e(desc[k_])}</p><ul class=jl>'
                            + "".join(f'<li><span><b>{e(jb_)}</b> <i>{e(se)}</i></span><em>{g_:.1f} GB</em></li>' for (se, jb_), g_ in topj) + "</ul>")
            out += f'<details class=kind><summary>{row}</summary>{sub}</details>' if sub else row
        return out, len(mins)
    uviews = []
    for vid, vname, hours in (("now", "Now", 0), ("d1", "24 hours", 24), ("d7", "7 days", 168), ("d30", "30 days", 720)):
        body, nmin = uses_view(hours)
        short_ = "" if hours == 0 or nmin >= hours * 60 * .9 else f'<p class=kd>Only {nmin / 60:.0f} hours recorded in this window so far.</p>'
        head_ = '<p class=uh><span>App</span><span>' + ("memory now" if hours == 0 else "average &middot; busiest minute, GB") + '</span></p>'
        uviews.append((vid, vname, short_ + head_ + body))
    uses_tabs = "".join(f'<button type=button class=jt data-v={vid} aria-pressed={"true" if j == 0 else "false"}>{vn}</button>' for j, (vid, vn, _) in enumerate(uviews))
    uses_views = "".join(f'<div class=jv data-v={vid}{"" if j == 0 else " hidden"}><div class=list>{b_}</div></div>' for j, (vid, _, b_) in enumerate(uviews))
    d7_cut = (dt.datetime.strptime(a_last, "%Y-%m-%d %H:%M") - dt.timedelta(days=7)).strftime("%Y-%m-%d %H:%M") if a_last else ""
    br_peak = max((d_.get(BR, 0) for t, d_ in apps_all.items() if t > d7_cut), default=0)

    tabs = [("rec", "Recommendation"), ("today", "Today"), ("days", "Busy days"), ("hours", "Busy hours"), ("uses", "What uses memory"), ("claude", "What Claude runs"), ("how", "How this works")]
    tab_html = "".join(f'<button role=tab data-go="{k}" aria-controls="p-{k}">{t}</button>' for k, t in tabs)

    return add_lesson(f"""<!doctype html><html lang=en><head><meta charset=utf-8><script>try{{if(sessionStorage.getItem("mm-again"))document.documentElement.classList.add("again")}}catch(_){{}}
setTimeout(function(){{try{{sessionStorage.setItem("mm-again","1")}}catch(_){{}}location.reload()}},60000)</script>
<style>html{{background:#fff7d6}}</style>
<script>addEventListener("load",function(){{if(!document.documentElement.classList.contains("again"))return;
var f=function(){{document.getAnimations().forEach(function(a){{if(a.effect&&a.effect.getTiming().iterations!==Infinity)a.finish()}})}};f();setTimeout(f,50)}})</script>
<meta name=viewport content="width=device-width,initial-scale=1"><title>{"Too Small a Mac" if rec > TOTAL else "Mac Memory Check"}</title>
<link rel=icon type=image/png sizes=64x64 href="data:image/png;base64,{open(os.path.join(v['HOME'], 'icon', 'fav64.b64')).read()}"><link rel=apple-touch-icon href="data:image/png;base64,{open(os.path.join(v['HOME'], 'icon', 'fav64.b64')).read()}">
<link rel=icon href='data:image/svg+xml,{v["fav"]}'>
<link rel=preconnect href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Geist:wght@300;400;600;800&family=Geist+Mono:wght@400;600&display=swap" rel=stylesheet>
<style>
:root{{--bg:#fff8dc;--fg:#1d2a44;--mute:#5f6b80;--card:rgba(255,255,255,.8);--line:rgba(47,111,181,.16);--tone:{v["tone"]};--hot:#e5484d;--good:#2f9e5b;--ram:#2f6fb5;--banana:#ffd93b;--fillA:#ffe680;--fillB:#ffd23b}}
@media(prefers-color-scheme:dark){{:root:not([data-theme=light]){{--bg:#0e1a2f;--fg:#f4f1e6;--mute:#9aa6bb;--card:rgba(255,217,59,.06);--line:rgba(255,217,59,.15);--hot:#ff6b6f;--good:#4ade80;--ram:#7fb0ef;--fillA:rgba(255,217,59,.55);--fillB:rgba(255,217,59,.12)}}}}
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
header.t3 .tabs button{{padding:6px 8px;font-size:12.5px}} header.t4 .live{{display:none}}
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
.list{{margin-top:10px;display:grid;gap:7px}}
.jtabs{{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px}} .jt{{font:600 13px Geist,sans-serif;border:2px solid var(--line);background:transparent;border-radius:99px;padding:5px 14px;cursor:pointer;color:inherit}} .jt[aria-pressed=true]{{background:#1f2a44;color:#fff;border-color:#1f2a44}}
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
.specs{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}}
.specs .c{{padding:12px 16px}} .specs .c b{{display:block;font:700 24px/1.1 Fredoka,sans-serif}} .specs .c span{{font-size:13.5px;color:var(--mute)}}
.specs .c:first-child{{background:var(--fg);color:var(--bg);border-color:var(--fg)}} .specs .c:first-child b{{color:#ffd93b}} .specs .c:first-child span{{color:inherit;opacity:.8}}
footer{{display:flex;justify-content:space-between;align-items:center;gap:10px;padding:6px 20px 12px;max-width:1240px;width:100%;margin:0 auto;color:var(--mute);font-size:12px}}
.nav2{{display:flex;gap:6px}} .nav2 button{{all:unset;cursor:pointer;width:34px;height:34px;border-radius:50%;border:2px solid var(--line);display:grid;place-items:center;font:700 16px Fredoka,sans-serif;color:var(--fg)}}
.nav2 button:hover{{background:var(--banana);color:#1d2a44}}
details{{position:relative}} summary{{cursor:pointer;color:var(--fg)}}
details ul{{position:absolute;bottom:28px;left:0;width:min(560px,90vw);padding:14px 16px 14px 30px;border-radius:20px;background:var(--fg);color:var(--bg);display:grid;gap:6px;font-size:13px;z-index:9;box-shadow:0 12px 40px rgba(0,0,0,.25)}}
.climb{{display:none!important}}
/* motion: everything enters on panel change; reduced motion keeps it still */
@media(prefers-reduced-motion:no-preference){{
 .on .en{{animation:pop .7s cubic-bezier(.3,1.5,.5,1) both;animation-delay:calc(var(--n,0)*90ms)}}
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
<header><div class=brand><i></i>{"Too small a Mac" if rec > TOTAL else "Mac memory check"}</div><nav class=tabs role=tablist aria-label="Sections">{tab_html}<span class=ink></span><svg class=rider viewBox="0 0 60 92" aria-hidden=true>{mini(30, 90, 90)}</svg></nav><span class=live title="Memory written out to the disk in the last minute">{out_mb:.0f} MB/min<span class=lx> to disk</span></span></header>
<div class=stage>

<section class=panel id=p-rec role=tabpanel><div class=inner>
<section class=hero>
<p class="kick en">My work has needed up to {peak_ever:.1f} GB of memory. This Mac has {TOTAL:.0f}.</p>
<h1 class=en id=rec-h1>{f"Get <em>{rec} GB</em> of memory<br>and {disk_txt} of storage." if rec > TOTAL else f"This Mac&#x27;s <em>{TOTAL:.0f} GB</em> is enough<br>for now."}</h1>
{lesson}
</section>
<div class=two>
<div class="c en" style="--n:2"><small>Share of working minutes each size would have handled</small><div class="list ladder">{ladder}</div>
<p class=note id=rec-note style="margin-top:10px">{len(work):,} working minutes, 7am to midnight{f'; the small &ldquo;without&rdquo; figures take out the hidden test browsers Claude opens, and cover only minutes since {split_t}, when those were first measured apart' if work_nb else ''}.</p></div>
<div class="c en" id=rec-jars style="--n:3"><svg class=jars viewBox="0 -60 1000 440" role=img aria-label="A {TOTAL:.0f} GB jar holding the busiest minute's {peak_ever:.1f} GB, next to a {rec} GB jar holding it with room to spare">{jars}</svg></div>
</div>
<div class=specs>
<div class="c en" id=rec-mem style="--n:4"><b>{rec} GB</b><span>memory, or {budget} GB if budget is tight: enough today, little room to grow.</span></div>
<div class="c en" id=rec-disk style="--n:5"><b>{disk_txt}</b><span>storage: {disk_used:.0f} GB of this Mac&#x27;s {disk_total:.0f} GB is in use, plus half again for growth.</span></div>
<div class="c en" id=rec-days style="--n:6"><b>{n_wd} of {WD_GOAL}</b><span>working days measured so far. {e(cpu_txt[0].upper() + cpu_txt[1:])}</span></div>
</div>
</div></section>

<section class=panel id=p-today role=tabpanel><div class=inner>
<div class=en><p class=kick><i class=dot></i>{status_line}</p><h2 class=big>{"Today it needed <em>" + gb(peak) + " GB</em>" if peak > TOTAL else "Today it has <em>fitted</em> so far"}</h2></div>
<p class="lede en" style="--n:1">The red line is everything the Mac is holding. Above the dotted {TOTAL:.0f} GB line it no longer fits, so the striped part sits on the disk, and the drops underneath are the minutes it was busy moving memory out. Hover to read any minute.</p>
<div class=two>
<div class="c chartbox en" style="--n:2" id=chart>
<svg class=ts viewBox="0 -30 {W} {H + 120}" role=img aria-label="Memory needed per minute against the {TOTAL:.0f} GB the Mac has">
<clipPath id=above><rect x=0 y=-40 width={W} height={ram_y + 40:.1f} /></clipPath><clipPath id=below><rect x=0 y={ram_y:.1f} width={W} height={H} /></clipPath>
<polygon class=under points="{area}" clip-path="url(#below)"/>
<polygon class=over points="{area}" clip-path="url(#above)"/>
<line class=ceil x1=0 x2={W} y1={ram_y:.1f} y2={ram_y:.1f} />
<text x=8 y={ram_y + 20:.1f} class=tk>{TOTAL:.0f} GB: all the memory this Mac has</text>
<polyline class=ram pathLength=1 points="{upts}"/>
<polyline class=need pathLength=1 points="{pts}"/>
<g transform="translate({px:.1f} {py:.1f})"><line x1=0 y1=0 x2=0 y2=-46 stroke="var(--fg)" stroke-width=2 />
<path class=flagb d="M0 -46 h{-74 if flag_left else 74} v22 h{74 if flag_left else -74}z" fill="var(--hot)"/>
<text x="{-37 if flag_left else 37}" y=-30 text-anchor=middle fill="#fff" font-family="Fredoka,sans-serif" font-weight=700 font-size=14>{gb(peak)} GB</text>
<circle r=6 fill="var(--bg)" stroke="var(--hot)" stroke-width=3 /></g>
<line class=xh x1=0 x2=0 y1=0 y2={H} />
<g class=walker id=walker>{mini(0, 0, 40, mood=mood)}</g>
{ticks}
<g class=drops transform="translate(0 {H + 30})">{"".join(drops)}</g>
<text x=0 y={H + 104} class=tk>Drops: minutes it pushed memory to disk (worst: {LO[lpk]:.0f} MB at {e(swap_when)})</text>
<g class=peek>{mini(W - 34, H + 2, 46, flip=True, mood=mood)}</g>
</svg>
<div class=tip id=tip></div>
</div>
<div class="c en" style="--n:3"><small>What held the memory at today&#x27;s busiest minute, {e(peak_when)}</small><div class=list>{bars(peak_d, peak_t)}</div></div>
</div>
<div class="legend en" style="--n:4"><span><i style="background:var(--hot)"></i>memory needed (in RAM + parked on disk)</span><span><i style="background:var(--ram)"></i>in RAM</span><span><i style="background:repeating-linear-gradient(45deg,var(--hot) 0 2px,transparent 2px 5px)"></i>overflow onto disk</span><span>{swap_mins} minutes swapping, {heavy_mins} of them heavy</span></div>
</div></section>

<section class=panel id=p-days role=tabpanel><div class=inner>
<div class=en><p class=kick>Every day since {first.strftime("%-d %B")}</p><h2 class=big>Over {TOTAL:.0f} GB on <em>{over_days} of {len(meas)}</em> measured days</h2></div>
<p class="lede en" style="--n:1">Above the line: how many Claude Code sessions ran at once, one head each. {busy_days} days reached 10 or more. Below the line: how far that day's busiest minute went past {TOTAL:.0f} GB. Memory has only been measured since {since}.</p>
<div class="c en" style="--n:2"><svg class=hist style="max-height:44vh" viewBox="0 -24 {HW} {HH + OH + 76}" role=img aria-label="One timeline: Claude Code sessions open at once each day above, memory over this Mac's RAM below">
<text x=4 y=-12 class=tk>&#9650; Claude Code sessions at once (from my session logs)</text>
<line x1=0 x2={HW} y1={ten_y:.1f} y2={ten_y:.1f} stroke="var(--hot)" stroke-dasharray="2 7" stroke-width=2 stroke-linecap=round opacity=".7"/>
<text x=4 y={ten_y - 8:.1f} class=tk>10 at once</text>
{"".join(heads)}{hticks}
<line x1=0 x2={HW} y1={HH + 30:.1f} y2={HH + 30:.1f} stroke="var(--line)" stroke-width="2"/>
<g transform="translate(0 {HH + 34:.1f})">{"".join(obars)}</g>
<text x=4 y={HH + OH + 48:.1f} class=tk>&#9660; Memory over {TOTAL:.0f} GB at the busiest minute (measured from {since}; dots = not measured)</text></svg>
<ol class="top meas">{"".join(f'<li><b>+{max(dmem[d][0] - TOTAL, 0):.1f} GB</b><span>over {TOTAL:.0f} GB &middot; {day_sess.get(d, (0, ""))[0]} sessions<br><i>{dt.date.fromisoformat(d).strftime("%a %-d %b")} &middot; {heavy.get(d, 0)} min heavy swapping</i></span></li>' for d in sorted(meas, reverse=True))}</ol>
<p class=note>Measured since {since}: {over_days} of {len(meas)} days went over {TOTAL:.0f} GB{f", the worst by {dmem[worst_d][0] - TOTAL:.1f} GB on {dt.date.fromisoformat(worst_d).strftime('%a %-d %b')} with {heavy.get(worst_d, 0)} minutes of heavy swapping" if worst_d else ""}. Earlier days were not measured (faint dots); their session counts above are the only record.</p></div>
<div class=en style="--n:3"><p class=kick style="margin-bottom:8px">Busiest days</p><ol class=top>{top_html}</ol></div>
</div></section>

<section class=panel id=p-hours role=tabpanel><div class=inner>
<div class=en><p class=kick>Working hours, 7am to midnight</p><h2 class=big>{TOTAL:.0f} GB ran out in <em>{len(over_cells)} of {filled}</em> hours seen</h2></div>
<p class="lede en" style="--n:1">{hours_take} Each square is one hour of one weekday, darker for more memory needed; a white dot means it went over {TOTAL:.0f} GB. Blank squares have no readings yet.</p>
<div class="c en" style="--n:2"><svg class=heat viewBox="0 0 {heat_w} {heat_h}" role=img aria-label="Highest memory needed by weekday and hour">{heat_svg}</svg>
<div class=legend style="margin-top:12px"><span>lighter = less</span><span class=ramp></span><span>darker = more ({lo_:.0f} to {hi_:.0f} GB)</span><span><i style="background:#fff;border:2px solid var(--hot);width:10px;height:10px;border-radius:50%;vertical-align:-1px"></i>over {TOTAL:.0f} GB</span></div></div>
</div></section>

<section class=panel id=p-uses role=tabpanel><div class=inner>
<div class=en><p class=kick>Every app, and what Claude runs underneath, refreshed every minute</p><h2 class=big>What uses <em>memory</em></h2></div>
<div class=whogrid>
<div class=en style="--n:1"><!--YARD--></div>
<div class="c en jobs" style="--n:2"><div class=jtabs role=group aria-label="Time window">{uses_tabs}</div>{uses_views}
<p class=note style="margin-top:10px">Tap a Claude row to see its groups and the scripts in each, with the session folder that started them.{f" Could be saved without new hardware: the hidden test browsers peaked at {br_peak:.1f} GB this week." if br_peak >= 1 else ""}</p></div>
</div></div></section>

<section class=panel id=p-claude role=tabpanel><div class=inner>
<div class=en><p class=kick>The tools and hidden browsers Claude starts, by kind, refreshed every minute</p><h2 class=big>{(e(take_k[0]) + " peaked at <em>" + f"{take_k[1]:.1f}" + " GB</em> this week") if take_k else "What Claude <em>runs</em>"}</h2></div>
<div class="c en jobs" style="--n:2"><div class=jtabs role=group aria-label="Time window">{jobs_tabs}</div>{jobs_views}
<p class=note style="margin-top:10px">Tap a group to see its scripts and the Claude session folder that started each one. Tracked since {e(tfirst or "now")}.</p></div>
</div></section>

<section class=panel id=p-how role=tabpanel><div class=inner>
<div class=en><p class=kick>What is measured, and what is not</p><h2 class=big>How this <em>works</em></h2></div>
<div class="c en howc" style="--n:1"><ul>
<li><b>Every minute</b> a background job reads macOS figures (<code>vm_stat</code>, <code>sysctl</code>, <code>ps</code>) into <code>~/memlog/</code>{', copied to Google Drive every 15 minutes' if cfg.get('drive_backup') else ''}: memory in use, memory on disk, memory per app, the scripts Claude runs, and processor load. Nothing is sent anywhere else.</li>
<li><b>Memory needed</b> is memory in use plus memory parked on disk (swap). Swap can keep old data from hours earlier, so this can overstate the real need; the minutes the Mac was actively moving memory to disk are shown separately as the drops on the Today chart.</li>
<li><b>The recommendation</b> is the busiest minute ever measured plus a quarter, rounded up to a size Macs come in. The budget pick is the smallest size that would have covered 99% of working minutes. Storage is what is in use now plus half again.</li>
<li><b>Per-app memory</b> counts memory still in memory, not on disk. Memory two apps share can be counted twice. Meet is counted inside Chrome.</li>
<li>{f'<b>Before {e(split_t)}</b> Chrome and the hidden test browsers Claude opens were counted together; those readings say so. ' if any('not split' in g for d_ in apps_all.values() for g in d_) else ''}Claude&#x27;s scripts are tracked from {e(tfirst or "now")}, processor load from {e(cpu_rows[0][0] if cpu_rows else "now")}.</li>
<li><b>Session history</b> before {since} comes from Claude Code transcripts: a session counts as open while its messages are under 30 minutes apart. Codex and idle open sessions are not counted, so real numbers were probably higher.</li>
<li><b>Right now:</b> {gb(U[-1])} GB in memory, {gb(S[-1])} GB on disk, {v["comp_gb"]:.1f} GB of memory holding {v["squeezed_gb"]:.1f} GB compressed, {v["wired_gb"]:.1f} GB locked by the system, {terms} sessions open.</li>
</ul></div>
</div></section>
</div>

<footer><span>Updated {e(T[-1])} &middot; scroll, swipe or use the arrow keys</span><div class=nav2><button id=prev aria-label="Previous section">&lsaquo;</button><button id=next aria-label="Next section">&rsaquo;</button></div></footer>
</div>
<script>
(() => {{
  const ids = {json.dumps([k for k, _ in tabs])};
  const tabs = [...document.querySelectorAll(".tabs button")], ink = document.querySelector(".tabs .ink"), rider = document.querySelector(".tabs .rider");
  let cur = -1;
  const dotBox = document.createElement("nav"); dotBox.className = "dots"; dotBox.setAttribute("aria-label", "Sections");
  const dots = ids.map((id, j) => {{ const b = document.createElement("button"); b.setAttribute("aria-label", tabs[j].textContent); b.onclick = () => show(j, true); dotBox.appendChild(b); return b; }});
  document.body.appendChild(dotBox);
  const show = (i, push) => {{
    i = (i + ids.length) % ids.length; if (i === cur) return;
    document.querySelectorAll(".panel").forEach((p, j) => {{ p.classList.toggle("on", j === i); p.classList.toggle("above", j < i); }});
    tabs.forEach((t, j) => t.setAttribute("aria-selected", j === i));
    dots.forEach((d, j) => d.setAttribute("aria-current", j === i));
    const pn = document.querySelectorAll(".panel")[i]; pn.scrollTop = 0;
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
  document.querySelectorAll(".jt").forEach(b => b.addEventListener("click", () => {{
    const box = b.closest(".jobs"), key = "mm-win-" + b.closest(".panel").id;
    box.querySelectorAll(".jt").forEach(x => x.setAttribute("aria-pressed", x === b));
    box.querySelectorAll(".jv").forEach(v => v.hidden = v.dataset.v !== b.dataset.v);
    try {{ localStorage.setItem(key, b.dataset.v); }} catch (_) {{}}
  }}));
  document.querySelectorAll(".jobs").forEach(box => {{ try {{ const jv = localStorage.getItem("mm-win-" + box.closest(".panel").id);
    const jb = jv && box.querySelector('.jt[data-v="' + jv + '"]'); if (jb) jb.click(); }} catch (_) {{}} }});
  let start = location.hash.slice(1); try {{ start = start || localStorage.getItem("mm-tab"); }} catch (_) {{}}
  // Tighten the header one step at a time until every tab fits (t1: smaller tabs, t2: title and "to disk" go, t3: smaller again, t4: the disk chip goes).
  const hdr = document.querySelector("header"), bar = document.querySelector(".tabs");
  const fitTabs = () => {{ hdr.classList.remove("t1", "t2", "t3", "t4");
    for (const c of ["t1", "t2", "t3", "t4"]) {{ if (bar.scrollWidth <= bar.clientWidth + 1) break; hdr.classList.add(c); }} }};
  fitTabs();
  show(Math.max(0, ids.indexOf(start)), false);
  const refit = () => {{ fitTabs(); const c = cur; cur = -1; show(c, false); }};
  addEventListener("resize", refit); if (document.fonts) document.fonts.ready.then(refit);

  // Busy-day chart: a buddy walks along the red line; hovering moves it to the minute under the pointer.
  const D = {series}, n = D.t.length, W = {W}, H = {H}, PAD = {PAD}, top = {top:.3f};
  const X = i => i * W / Math.max(n - 1, 1), Y = v => PAD + (H - PAD) - v * (H - PAD) / top;
  const svg = document.querySelector(".ts"), walker = document.getElementById("walker"), xh = svg.querySelector(".xh"), tip = document.getElementById("tip"), box = document.getElementById("chart");
  const still = matchMedia("(prefers-reduced-motion: reduce)").matches;
  let hover = -1, step = 0;
  const put = (i) => {{
    walker.setAttribute("transform", `translate(${{X(i)}} ${{Y(D.need[i]) - 2}})`);
    xh.setAttribute("x1", X(i)); xh.setAttribute("x2", X(i));
  }};
  const tipAt = (i) => {{
    const r = svg.getBoundingClientRect(), b = box.getBoundingClientRect(), vb = svg.viewBox.baseVal;
    tip.style.left = (r.left - b.left + (X(i) - vb.x) * r.width / vb.width) + "px";
    tip.style.top = (r.top - b.top + (Y(D.need[i]) - vb.y - 40) * r.height / vb.height) + "px";
    tip.innerHTML = `<b>${{D.t[i].slice(5).replace("-", "/")}}</b><br><i style="background:var(--hot)"></i>needed ${{D.need[i].toFixed(1)}} GB<br><i style="background:var(--ram)"></i>in RAM ${{D.ram[i].toFixed(1)}} GB<br>${{D.swap[i] ? D.swap[i] + " MB pushed to disk" : "no swapping this minute"}}`;
  }};
  const pick = ev => {{
    const r = svg.getBoundingClientRect(), vb = svg.viewBox.baseVal;
    const x = (ev.clientX - r.left) * vb.width / r.width + vb.x;
    return Math.max(0, Math.min(n - 1, Math.round(x / W * (n - 1))));
  }};
  svg.addEventListener("pointermove", ev => {{ hover = pick(ev); svg.classList.add("hovering"); put(hover); tipAt(hover); }});
  svg.addEventListener("pointerleave", () => {{ hover = -1; svg.classList.remove("hovering"); }});
  svg.addEventListener("pointerdown", ev => {{ if (ev.pointerType !== "mouse") box.classList.add("touch"); }});
  put({pk});
  if (!still) setInterval(() => {{ if (hover < 0) {{ step = (step + Math.max(1, Math.round(n / 120))) % n; put(step); }} }}, 250);
}})();
let seen = false; try {{ seen = sessionStorage.getItem("mm-seen") === "1"; sessionStorage.setItem("mm-seen", "1"); }} catch (_) {{}}
</script></body></html>""")


# ---------- Recommendation: the buddy teaches how it got to the answer ----------
# Every number comes from the readings. Steps that do not apply to this Mac are left out.
def lesson_html(*, TOTAL, work, wdays, work_nb, fits, LADDER, peak_ever, peak_ever_when, target, rec, budget, fit16,
                disk_used, disk_txt, disk_rec, n_wd, WD_GOAL):
    def row(sz):
        return f".lad[data-sz='{sz}']" if sz in LADDER else ""
    me = int(round(TOTAL))
    nd = len(wdays)
    # (what the stick points at, what the bubble says, the scene the page acts out, that scene's numbers)
    steps = [("#rec-note", f"I watched <b>{len(work):,} working minutes</b>, 7am to midnight, over {nd} day{'s' if nd != 1 else ''}. "
                           "Here is how I got from those to my answer.", "minutes", {"n": len(work)})]
    spill = peak_ever > TOTAL
    steps.append(("#rec-jars", f"The busiest minute, {peak_ever_when}, needed <b>{peak_ever:.1f} GB</b>. "
                               + (f"This Mac has {TOTAL:.0f}, so {peak_ever - TOTAL:.1f} GB of it had to wait on the disk." if spill else
                                  f"This Mac has {TOTAL:.0f}, so even that minute fitted."),
                  "jar", {"jar": 0}))
    steps.append((row(me), f"{TOTAL:.0f} GB was enough in {'only ' if fit16 < .9 else ''}<b>{fit16:.0%} of those minutes</b>."
                           + (" The rest of the time, part of what you had open sat on the disk." if fit16 < 1 else ""),
                  "fit", {"sz": me, "pct": round(fit16 * 100)}))
    if work_nb:
        nb = fits(me, work_nb)
        if nb >= fit16 + .05:
            steps.append((row(me), f"Without the hidden test browsers Claude opens, {TOTAL:.0f} GB would have been enough "
                                   f"<b>{nb:.0%} of the time</b>. Closing those is free; more memory is not.",
                          "nobrowsers", {"sz": me, "pct": round(fit16 * 100), "nb": round(nb * 100)}))
    if rec > TOTAL and budget != rec and budget > TOTAL:
        steps.append((row(budget), f"<b>{budget} GB</b> would have covered 99% of minutes. That is the budget pick: "
                                   "enough for today, with little room to grow.",
                      "budget", {"sz": budget, "pct": round(fits(budget, work) * 100)}))
    jar_i, cap = (1, rec) if rec > TOTAL else (0, int(round(TOTAL)))
    steps.append(("#rec-jars, #rec-mem",
                  f"For my answer I take the busiest minute, {peak_ever:.1f} GB, and add a quarter for a heavier week: {target:.1f} GB. "
                  + (f"The next size Macs come in is <b>{rec} GB</b>." if rec > TOTAL else f"This Mac already has <b>{TOTAL:.0f} GB</b>."),
                  "measure", {"jar": jar_i, "cap": cap, "a": round(peak_ever, 1), "b": round(target, 1)}))
    steps.append(("#rec-disk", f"Storage: <b>{disk_used:.0f} GB</b> is in use now. Half again for growth makes "
                               f"{disk_used * 1.5:.0f} GB, so <b>{disk_txt}</b>.",
                  "disk", {"used": round(disk_used), "need": round(disk_used * 1.5), "cap": disk_rec, "label": disk_txt}))
    steps.append(("#rec-days", f"I have measured {n_wd} of {WD_GOAL} working days so far. A busier week could change this, "
                               "so keep me running.", "days", {"n": n_wd, "goal": WD_GOAL}))
    steps.append(("#rec-h1", f"So: <b>{rec} GB</b> of memory and <b>{disk_txt}</b> of storage." if rec > TOTAL else
                             f"So: this Mac&#x27;s <b>{TOTAL:.0f} GB</b> is enough for now. Look again after a busy week.",
                  "sum", {}))
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
.sc-ghost{position:absolute;top:-3px;bottom:-3px;border-radius:9px;border:2px dashed #c99700;background:repeating-linear-gradient(45deg,rgba(255,217,59,.6) 0 6px,transparent 6px 12px);
 transform-origin:left;animation:scgrow .9s cubic-bezier(.16,1,.3,1) both}
.sc-tag{position:absolute;bottom:calc(100% + 6px);white-space:nowrap;font:600 12.5px Geist,sans-serif;animation:scfade .35s .55s both}
.sc-disk .sc-tag{right:0;color:var(--hot)} .sc-ghost .sc-tag{left:0;color:#9a7400}
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
 .sc-disk,.sc-ghost,.sc-tag,.sc-line,.sc-call,.sc-gauge i,.sc-leg i,.sc-days i.y,.sc-meas .t3.on,.sc-slam{animation:none}}
@media(max-width:760px){.lesson{flex-direction:column;align-items:stretch;border-radius:22px;text-align:left}.lesson:before{display:none}.lesson .ctl{justify-content:center}}
"""

LESSON_JS = r"""<script>
(() => {
  const L = document.getElementById("lesson"); if (!L) return;
  const P = document.getElementById("p-rec"), steps = [...L.querySelectorAll("li")], n = steps.length;
  const calm = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const ld = L.querySelector(".ld"); ld.innerHTML = steps.map(() => "<i></i>").join(""); const dots = [...ld.children];
  const bt = L.querySelector(".lt"), today = new Date().toISOString().slice(0, 10);
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
    else if (localStorage.getItem("mm-lesson-day") === today) { i = n - 1; playing = false; }
  } catch (_) {}
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
  P.querySelectorAll(".lad").forEach(r => { const b = r.querySelector(".track b"); r.dataset.w = b.style.getPropertyValue("--w"); r.dataset.em = r.querySelector("em").textContent; });
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
    P.querySelectorAll(".lad").forEach(r => { const b = r.querySelector(".track b"); b.style.transition = ""; b.style.setProperty("--w", r.dataset.w); r.querySelector("em").textContent = r.dataset.em; });
    const note = document.getElementById("rec-note"); if (note && note.dataset.t) note.innerHTML = note.dataset.t;
  };
  const SC = {
    minutes(d) { const card = P.querySelector(".ladder").closest(".c"), note = document.getElementById("rec-note");
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
    nobrowsers(d) { const r = lad(d.sz); if (!r) return; dim("sc-on", "sc-rows"); lead(r.closest(".c"), r);
      const t = r.querySelector(".track");
      const gh = add(t, `<span class=sc-tag>with Claude's test browsers closed: ${d.nb}%</span>`, "sc-ghost"); gh.style.left = d.pct + "%"; gh.style.width = (d.nb - d.pct) + "%";
      if (d.nb < 100) later(() => add(t, "", "sc-disk").style.left = d.nb + "%", 900); },
    budget(d) { const r = lad(d.sz); if (!r) return; const lc = P.querySelector(".ladder"), tr = [...lc.querySelectorAll(".track")];
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
    disk(d) { const c = document.getElementById("rec-disk"); if (!c) return; dim("sc-on"); lead(c);
      const w = v => Math.min(v / d.cap * 100, 100).toFixed(1) + "%";
      add(c, `<div class=sc-gauge><i class=h style="width:${w(d.need)};animation-delay:.9s"></i><i class=u style="width:${w(d.used)}"></i></div>`
        + `<div class=sc-leg><i>in use ${d.used} GB</i><i class=e2 style="animation-delay:1.3s">+ half = ${d.need} GB</i><i class=end style="animation-delay:1.8s">fits in ${d.label}</i></div>`, "sc-call"); },
    days(d) { const c = document.getElementById("rec-days"); if (!c) return; dim("sc-on"); lead(c);
      add(c, `<div>${d.n} of ${d.goal} working days measured</div><div class=sc-days>`
        + Array.from({ length: d.goal }, (_, k) => k < d.n ? `<i class=y style="animation-delay:${.3 + k * .12}s"></i>` : "<i></i>").join("") + "</div>", "sc-call"); },
    sum() { const em = document.querySelector("#rec-h1 em"); if (em) { em.classList.remove("sc-slam"); void em.offsetWidth; later(() => em.classList.add("sc-slam"), 200); }
      ["rec-mem", "rec-disk"].forEach((id, k) => later(() => document.getElementById(id)?.classList.add("sc-pop"), 600 + k * 260)); },
  };
  const scene = () => { reset(); const st = steps[i], f = SC[st.dataset.scene]; if (!f || !P.classList.contains("on")) return;
    try { f(JSON.parse(st.dataset.d || "{}")); } catch (_) {} };
  // Never block use: a click anywhere outside the bubble (or, on a wide screen, a scroll) puts the page back as it was.
  // Not pointerdown: on a phone every scroll starts with one, and the reader has to scroll to reach steps 6 to 8.
  const back = e => { if (!e.target.closest("#lesson")) reset(); };
  P.addEventListener("click", back); P.addEventListener("wheel", e => wide() && back(e), { passive: true });
  let sceneT = null; const later0 = f => { clearTimeout(sceneT); sceneT = setTimeout(f, calm ? 0 : 120); };
  const go = (k, keepT) => {
    tgts(i).forEach(el => el.classList.remove("lit"));
    i = Math.max(0, Math.min(n - 1, k)); if (!keepT) t = 0;
    steps.forEach((s, j) => s.classList.toggle("on", j === i));
    dots.forEach((d, j) => { d.classList.toggle("on", j === i); d.classList.toggle("done", j < i); d.style.setProperty("--p", 0); });
    tgts(i).forEach(el => el.classList.add("lit"));
    show(); later0(scene);
    if (svg && !calm) { svg.classList.remove("nod"); void svg.getBoundingClientRect(); svg.classList.add("nod"); }
    aim(); label(); save();
  };
  const finish = () => { playing = false; try { localStorage.setItem("mm-lesson-day", today); } catch (_) {} label(); save(); };
  L.querySelector(".lp").onclick = () => { playing = false; go(i - 1); };
  L.querySelector(".ln").onclick = () => { playing = false; go(i + 1); };
  bt.onclick = () => { if (playing) { playing = false; label(); save(); } else { playing = true; if (i === n - 1) go(0); else { label(); save(); } } };
  go(i, true);
  setInterval(() => {
    const now = performance.now(), dt = now - last; last = now;
    aim();
    const on = P.classList.contains("on"); if (on && !wasOn) { setTimeout(show, 450); later0(scene); } if (!on && wasOn) reset(); wasOn = on;
    if (!playing || !P.classList.contains("on") || document.hidden) return;
    t += dt; const d = dur(i);
    if (dots[i]) dots[i].style.setProperty("--p", Math.min(t / d, 1).toFixed(3));
    if (t >= d) { if (i < n - 1) go(i + 1); else finish(); }
    else if (Math.floor(t / 1000) !== Math.floor((t - dt) / 1000)) save();
  }, 100);
})();
</script>"""


def add_lesson(page):
    return page.replace("</style>", LESSON_CSS + "</style>", 1).replace("</body>", LESSON_JS + "</body>", 1)
