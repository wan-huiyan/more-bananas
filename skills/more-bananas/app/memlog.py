#!/usr/bin/env python3
"""more-bananas, a Mac memory monitor: run once a minute (by launchd). Each run appends one reading to ~/memlog/*.csv
and rebuilds ~/memlog/memory-report.html (linked from the Desktop).

Reads macOS memory figures (sysctl, vm_stat, ps); sends nothing anywhere. Settings: ~/memlog/config.json.
"""
import collections
import datetime as dt
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import time

HOME = os.path.expanduser("~/memlog")
LOG = os.path.join(HOME, "mem.csv")              # time, RAM used GB, swap GB, Claude GB, Chrome GB, Claude sessions
APPS = os.path.join(HOME, "apps.csv")            # time, app group, GB
LIVE = os.path.join(HOME, "live.csv")            # time, MB/min to disk, MB/min back, compressor GB, wired GB, compressed GB
OUT = os.path.join(HOME, "memory-report.html")   # background jobs may not write to ~/Desktop; a Desktop link points here
sys.path.insert(0, HOME)

try:
    cfg = json.load(open(os.path.join(HOME, "config.json")))
except Exception:
    cfg = {}


def sh(*a):
    return subprocess.check_output(a, text=True)


# ---------- take one reading ----------
TOTAL_GB = int(sh("sysctl", "-n", "hw.memsize")) / 2**30
swap = float(sh("sysctl", "-n", "vm.swapusage").split()[5].rstrip("M")) / 1024
free_pct = int(sh("sysctl", "-n", "kern.memorystatus_level"))
GROUPS = [  # first match wins; order matters
    ("Claude Code sessions", lambda c: "/claude-code/" in c or c.split()[0] == "claude" or c.split()[0].endswith("/claude")),
    ("Claude desktop app", lambda c: "/Claude.app/" in c),
    ("Browsers Claude drives", lambda c: False),  # set below: Chrome started by Playwright and other test tools
    ("Chrome (incl. Meet)", lambda c: "Google Chrome" in c),
    ("Slack", lambda c: "/Slack.app/" in c),
    ("Safari", lambda c: "Safari" in c or "WebKit" in c),
    ("Zoom / Teams", lambda c: "zoom.us" in c or "Microsoft Teams" in c),
    ("Tools Claude starts", lambda c: any(k in c for k in ("node", "npm", "npx", "python", "Python", "pytest", "uv", "playwright", "gcloud", "bq ", "git", "Chromium", "chrome-headless"))),
    ("Security software", lambda c: any(k in c for k in ("crowdstrike", "Netskope", "falcon", "SentinelOne", "Jamf"))),
    ("Google Drive", lambda c: "Google Drive" in c),
    ("macOS system", lambda c: c.startswith(("/System/", "/usr/", "/sbin/", "/Library/Apple"))),
]
claude = chrome = 0.0
terms, by_group, sessions = 0, {}, []
grp = {}  # pid -> app group, reused below to split the processor load by app
procs = {}
pcpu = {}  # pid -> % of one core, for the processor share of each Claude tool
for line in sh("ps", "-axo", "pid=,ppid=,rss=,%cpu=,command=").splitlines():
    parts = line.strip().split(None, 4)
    if len(parts) == 5:
        procs[parts[0]] = [parts[1], parts[2], parts[4]]
        pcpu[parts[0]] = float(parts[3]) if parts[3].replace(".", "", 1).isdigit() else 0.0
# Attribute a process only when its own executable or an observed ancestor identifies Codex.
# The desktop app is shared infrastructure; none of these processes represents a chat.
def codex_class(pid):
    seen = set()
    current = pid
    while current in procs and current not in seen:
        seen.add(current)
        command = procs[current][2]
        executable = command.split()[0] if command.split() else ""
        if ("/codex-cli/" in command and "/MacOS/codex" in command) or executable.endswith("/codex") or executable == "codex":
            return "Codex shared processes" if current == pid else "Tools started by Codex"
        if ("/ChatGPT.app/Contents/" in command or "/Codex.app/Contents/" in command
                or "/.codex/computer-use/" in command):
            return "Codex shared processes" if current == pid else "Tools started by Codex"
        current = procs[current][0]
    return None


AUTOMATION = ("--disable-field-trial-config", "--remote-debugging", "--headless", "--enable-automation")


def chrome_root(pid):  # the top Chrome process this one belongs to
    while procs.get(procs[pid][0], ("", "", ""))[2].find("Google Chrome") >= 0:
        pid = procs[pid][0]
    return procs[pid][2]


for pid, (_ppid, rss, cmd) in procs.items():
    gb = int(rss) / 2**20
    g = codex_class(pid) or next((name for name, test in GROUPS if test(cmd)), "Other apps")
    if g == "Chrome (incl. Meet)" and any(k in chrome_root(pid) for k in AUTOMATION):
        g = "Browsers Claude drives"
    grp[pid] = g
    by_group[g] = by_group.get(g, 0) + gb
    if g == "Chrome (incl. Meet)":
        chrome += gb
    elif g in ("Claude Code sessions", "Tools Claude starts", "Browsers Claude drives"):
        claude += gb
    if g == "Claude Code sessions" and "Helper" not in cmd and ("/MacOS/claude " in cmd or cmd.split()[0] == "claude" or cmd.split()[0].endswith("/claude")):
        terms += 1
        sessions.append((pid, gb))

# What each Claude tool or Claude-driven browser is, and which session started it.
TOOLS = os.path.join(HOME, "tools.csv")          # time, session folder, job, GB
TOOLCPU = os.path.join(HOME, "tools_cpu.csv")    # time, session folder, job, % of all cores
sess_pids = {p_ for p_, _ in sessions}


def job_name(pid):  # the script or tool behind a process, looking up through its parents
    for _ in range(12):
        if pid not in procs or pid in sess_pids:
            break
        cmd = procs[pid][2]
        words = cmd.split()
        mcp = next((w for w in words if "mcp" in w.lower() and "/MacOS/" not in w), None)
        if mcp:
            mcp = mcp.split("@latest")[0]
            return "MCP server: " + (os.path.basename(mcp) if mcp.startswith("/") else mcp.lstrip("@"))
        script = next((w for w in words[1:] if w.endswith((".py", ".js", ".mjs", ".ts", ".sh"))
                       and not any(k in w for k in ("/site-packages/", "node_modules", "/.cache/"))), None)
        if script:
            return os.path.basename(script)
        first = os.path.basename(words[0])
        if first in ("gcloud", "bq", "git", "gh", "pytest", "uv", "npm", "npx"):
            return first + (" " + words[1] if len(words) > 1 and not words[1].startswith("-") else "")
        pid = procs[pid][0]
    return "other tool"


def owner(pid):  # the Claude Code session above this process, if any
    for _ in range(40):
        if pid in sess_pids:
            return pid
        if pid not in procs:
            return None
        pid = procs[pid][0]


jobs, jobs_cpu = {}, {}
for pid, (_ppid, rss, cmd) in procs.items():
    if codex_class(pid):
        continue  # Codex resources have their own groups, not Claude tool rows.
    g = next((name for name, test in GROUPS if test(cmd)), "")
    if g == "Chrome (incl. Meet)" and any(k in chrome_root(pid) for k in AUTOMATION):
        root = pid
        while "Google Chrome" in procs.get(procs[root][0], ("", "", ""))[2]:
            root = procs[root][0]
        name = "Chrome opened by " + job_name(procs[root][0])
    elif g == "Tools Claude starts":
        name = job_name(pid)
    else:
        continue
    key = (owner(pid), name)
    jobs[key] = jobs.get(key, 0) + int(rss) / 2**20
    jobs_cpu[key] = jobs_cpu.get(key, 0) + pcpu.get(pid, 0)

# Which folder each Claude Code session works in, so its buddy can be named.
folders = {}
if sessions:
    try:
        pid = None
        for l in sh("lsof", "-a", "-d", "cwd", "-Fpn", "-p", ",".join(p for p, _ in sessions)).splitlines():
            if l[:1] == "p":
                pid = l[1:]
            elif l[:1] == "n" and pid:
                folders[pid] = l[1:]
    except subprocess.CalledProcessError:
        pass


def short(path):
    if "/.claude/worktrees/" in path:
        return path.split("/.claude/worktrees/")[1]
    return os.path.basename(path.rstrip("/")) or path


stamp = time.strftime("%Y-%m-%d %H:%M")
used = TOTAL_GB * (100 - free_pct) / 100
with open(APPS, "a") as f:
    for g, gb in by_group.items():
        f.write(f"{stamp},{g},{gb:.3f}\n")
with open(TOOLS, "a") as f:
    for (o, name), gb_ in jobs.items():
        if gb_ >= 0.02:
            f.write(f"{stamp},{short(folders.get(o, '')) if o else 'no Claude session'},{name.replace(',', ' ')},{gb_:.3f}\n")
ncores = os.cpu_count() or 1
with open(TOOLCPU, "a") as f:
    for (o, name), pc in jobs_cpu.items():
        if pc / ncores >= 0.2:
            f.write(f"{stamp},{short(folders.get(o, '')) if o else 'no Claude session'},{name.replace(',', ' ')},{pc / ncores:.1f}\n")
with open(LOG, "a") as f:
    f.write(f"{stamp},{used:.2f},{swap:.2f},{claude:.2f},{chrome:.2f},{terms}\n")

# Processor load: share of all cores busy right now, and the 1-minute load average.
CPU = os.path.join(HOME, "cpu.csv")              # time, % of all cores busy, 1-minute load average, cores
cores = int(sh("sysctl", "-n", "hw.ncpu"))
# Each app group's share of all cores, so the page can say which apps are keeping the processors busy right now.
cpu_by_group = {}
for line in sh("ps", "-axo", "pid=,%cpu=").splitlines():
    p_ = line.split()
    if len(p_) == 2:
        g_ = grp.get(p_[0], "Other apps"); cpu_by_group[g_] = cpu_by_group.get(g_, 0) + float(p_[1]) / cores
cpu_pct = sum(cpu_by_group.values())
load1 = float(sh("sysctl", "-n", "vm.loadavg").split()[1])
with open(CPU, "a") as f:
    f.write(f"{stamp},{min(cpu_pct, 100):.1f},{load1:.2f},{cores}\n")

# Live swapping: how much macOS wrote to / read from disk since the last run.
vm = sh("vm_stat")
page = int(re.search(r"page size of (\d+)", vm).group(1))
cnt = {k: int(v) for k, v in re.findall(r'^"?([A-Za-z ]+?)"?:\s+(\d+)\.', vm, re.M)}
state_p = os.path.join(HOME, "last.json")
try:
    prev = json.load(open(state_p))
except Exception:
    prev = None
mins = max((time.time() - prev["t"]) / 60, 1) if prev else 1
# After a sleep or a shutdown the counters cover the time the Mac was off too. That is not work, so the first reading
# after a gap of more than 5 minutes records no swap, disk or network rate rather than an average over the night.
if mins > 5:
    prev = None


def rate(k):  # MB per minute; 0 on the first run, or after a restart resets the counters
    return max(cnt[k] - prev[k], 0) * page / 2**20 / mins if prev and cnt[k] >= prev[k] else 0.0


out_mb, in_mb = rate("Swapouts"), rate("Swapins")
comp_gb = cnt["Pages occupied by compressor"] * page / 2**30
squeezed_gb = cnt["Pages stored in compressor"] * page / 2**30
wired_gb = cnt["Pages wired down"] * page / 2**30
# ---------- heat, and the other things that make a Mac hot, loud or slow (all readable without admin rights) ----------
HEAT = os.path.join(HOME, "heat.csv")        # time, thermal state, fan rpm, fan max rpm, hottest chip sensor C, graphics % busy
IO = os.path.join(HOME, "io.csv")            # time, disk read, disk write, network in, network out (MB per minute)
APPCPU = os.path.join(HOME, "cpu_apps.csv")  # time, app group, % of all cores it kept busy


def try_sh(*a):  # like sh(), but a missing tool or a slow answer gives "" instead of stopping the reading
    try:
        return subprocess.run(a, capture_output=True, text=True, timeout=10).stdout
    except Exception:
        return ""


heat_state, fan_rpm, fan_max, chip_c = "", -1, -1, -1.0
heat_bin = os.path.join(HOME, "heat")        # built from heat.swift by install.sh; absent if swiftc was not available
if os.access(heat_bin, os.X_OK):
    hp_ = try_sh(heat_bin).strip().split(",")
    if len(hp_) == 4:
        heat_state, fan_rpm, fan_max, chip_c = hp_[0], int(hp_[1]), int(hp_[2]), float(hp_[3])
gm_ = re.search(r'"Device Utilization %"=(\d+)', try_sh("ioreg", "-r", "-d", "1", "-c", "IOAccelerator"))
gpu_pct = float(gm_.group(1)) if gm_ else -1.0
st_ = try_sh("ioreg", "-c", "IOBlockStorageDriver", "-r", "-k", "Statistics", "-d", "1")
io_now = {"disk_r": sum(int(x) for x in re.findall(r'"Bytes \(Read\)"=(\d+)', st_)),
          "disk_w": sum(int(x) for x in re.findall(r'"Bytes \(Write\)"=(\d+)', st_)), "net_i": 0, "net_o": 0}
for l_ in try_sh("netstat", "-ib").splitlines()[1:]:   # one <Link> row per interface; byte columns counted from the end
    f_ = l_.split()
    if len(f_) >= 10 and f_[2].startswith("<Link") and not f_[0].startswith("lo"):
        io_now["net_i"] += int(f_[-5]); io_now["net_o"] += int(f_[-2])


def brate(k):  # MB per minute from a byte counter; 0 on the first run or after a restart resets it
    return max(io_now[k] - prev[k], 0) / 2**20 / mins if prev and k in prev and io_now[k] >= prev[k] else 0.0


io_rates = [brate(k) for k in ("disk_r", "disk_w", "net_i", "net_o")]
with open(HEAT, "a") as f:
    f.write(f"{stamp},{heat_state},{fan_rpm},{fan_max},{chip_c:.1f},{gpu_pct:.0f}\n")
with open(IO, "a") as f:
    f.write(stamp + "," + ",".join(f"{x:.1f}" if prev else "" for x in io_rates) + "\n")
with open(APPCPU, "a") as f:
    for g_, x_ in sorted(cpu_by_group.items(), key=lambda kv: -kv[1]):
        if x_ >= 0.5:
            f.write(f"{stamp},{g_},{x_:.1f}\n")
json.dump({"t": time.time(), "Swapouts": cnt["Swapouts"], "Swapins": cnt["Swapins"], **io_now}, open(state_p, "w"))
with open(LIVE, "a") as f:
    f.write(f"{stamp},{out_mb:.1f},{in_mb:.1f},{comp_gb:.2f},{wired_gb:.2f},{squeezed_gb:.2f}\n")

# ---------- what the page needs ----------
def page_data(home):
    """Everything the page reads from the per-minute logs in `home`. None if it holds less than an hour of readings."""
    log, live, apps_p = os.path.join(home, "mem.csv"), os.path.join(home, "live.csv"), os.path.join(home, "apps.csv")
    allrows = [l.strip().split(",") for l in open(log) if l.count(",") == 5] if os.path.exists(log) else []
    if len(allrows) < 60:
        return None
    first_reading = allrows[0][0]
    rows = allrows[-60 * 24 * 31:]  # last 31 days: the Today tab can show up to 30
    T = [r[0] for r in rows]
    U, S = [float(r[1]) for r in rows], [float(r[2]) for r in rows]
    N = [int(r[5]) for r in rows]
    need = [U[i] + S[i] for i in range(len(rows))]
    pk = max(range(len(rows)), key=lambda i: need[i])
    lv = [l.strip().split(",") for l in open(live) if l.count(",") == 5][-60 * 24 * 31:] if os.path.exists(live) else []
    lv = lv or [[T[-1], "0", "0", "0", "0", "0"]]
    LO, LT = [float(r[1]) for r in lv], [r[0] for r in lv]
    lpk = max(range(len(lv)), key=lambda i: LO[i])
    apps = {}
    for l in open(apps_p) if os.path.exists(apps_p) else ():
        if l.count(",") >= 2:
            t, g, gb = l.rstrip("\n").rsplit(",", 2)
            apps.setdefault(t, {})[g] = float(gb)
    peak_d = apps.get(T[pk], {})
    # History: most Claude Code sessions open at once per day (from the session transcripts, rebuilt hourly),
    # and the measured peak per day.
    day_sess = collections.defaultdict(lambda: (0, ""))
    hs = os.path.join(home, "history_sessions.csv")
    if os.path.exists(hs):
        for l in open(hs):
            h, n, _ = l.strip().split(",")
            if int(n) > day_sess[h[:10]][0]:
                day_sess[h[:10]] = (int(n), h[11:])
    day_sess = dict(day_sess)
    day_mem = {}
    for r in allrows:
        v_ = float(r[1]) + float(r[2])
        if v_ > day_mem.get(r[0][:10], (0, ""))[0]:
            day_mem[r[0][:10]] = (v_, r[0][11:])
    first = min([*day_sess, *day_mem])
    d0 = dt.date.fromisoformat(first)
    days = [(d0 + dt.timedelta(n)).isoformat() for n in range((dt.date.today() - d0).days + 1)]
    return dict(LOG=log, allrows=allrows, first_reading=first_reading, rows=rows, T=T, U=U, S=S, N=N, need=need, pk=pk,
                lv=lv, LO=LO, LT=LT, lpk=lpk, apps=apps, peak_d=peak_d, day_sess=day_sess, day_mem=day_mem, first=first, days=days)


hs = os.path.join(HOME, "history_sessions.csv")
if not os.path.exists(hs) or time.strftime("%M") == "00":
    subprocess.run([sys.executable, os.path.join(HOME, "backfill_sessions.py")], capture_output=True)
globals().update(page_data(HOME))
mood, word, tone = (("calm", "calm", "#34d399") if out_mb < 5 else
                    ("tight", "swapping a little", "#fbbf24") if out_mb < 100 else
                    ("over", "swapping hard", "#fb7185"))
if mood == "calm" and load1 > cores:  # memory is calm but the processors have more work than cores: amber, not green
    tone = "#fbbf24"
mouth = {"calm": "M12 21 Q16 25 20 21", "tight": "M12 22 L20 22", "over": "M12 23 Q16 19 20 23"}[mood]
fav = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect x="2" y="2" width="28" height="28" rx="9" fill="{tone.replace("#", "%23")}"/>'
       f'<circle cx="12" cy="14" r="2" fill="%23fff"/><circle cx="20" cy="14" r="2" fill="%23fff"/>'
       f'<path d="{mouth}" stroke="%23fff" stroke-width="1.8" fill="none" stroke-linecap="round"/></svg>')
now_d = apps.get(stamp, by_group)
sess = sorted(sessions, key=lambda x: -x[1])

# Working hours: by default the page counts only the minutes inside them (Monday to Friday, 9am to 7pm; config.json
# can change both). The readings are filtered into their own folder and the same page is built from it, so every
# tab, the recommendation included, sees only working minutes. The all-hours page is built beside it.
WORK_H = cfg.get("work_hours", [9, 19])
WORK_D = set(cfg.get("work_days", [0, 1, 2, 3, 4]))     # Monday is 0
_wd = {}
def at_work(t):
    d = t[:10]
    if d not in _wd:
        try:
            _wd[d] = dt.date.fromisoformat(d).weekday() in WORK_D
        except ValueError:
            _wd[d] = False
    return _wd[d] and len(t) >= 13 and t[11:13].isdigit() and WORK_H[0] <= int(t[11:13]) < WORK_H[1]
WDIR = os.path.join(HOME, ".workhours")
os.makedirs(WDIR, exist_ok=True)
for name in ("mem.csv", "apps.csv", "live.csv", "cpu.csv", "cpu_apps.csv", "tools_cpu.csv", "heat.csv", "io.csv", "tools.csv", "history_sessions.csv"):
    src = os.path.join(HOME, name)
    if os.path.exists(src):
        with open(src) as fi, open(os.path.join(WDIR, name + ".tmp"), "w") as fo:
            fo.writelines(l for l in fi if at_work(l[:16]))
        os.replace(os.path.join(WDIR, name + ".tmp"), os.path.join(WDIR, name))
if not os.path.exists(os.path.join(WDIR, "icon")) and os.path.isdir(os.path.join(HOME, "icon")):
    os.symlink(os.path.join(HOME, "icon"), os.path.join(WDIR, "icon"))
_h0, _h1 = WORK_H
def _hr(h):
    return "noon" if h == 12 else "midnight" if h in (0, 24) else f"{h % 12}{'am' if h < 12 else 'pm'}"
_dn = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
_ds = sorted(WORK_D)
work_txt = (f"{_dn[_ds[0]]} to {_dn[_ds[-1]]}" if _ds == list(range(_ds[0], _ds[-1] + 1)) else ", ".join(_dn[d] for d in _ds)) + f", {_hr(_h0)} to {_hr(_h1)}"
swapped_total_gb = cnt["Swapouts"] * page / 2**30
_boot = int(re.search(r"sec = (\d+)", sh("sysctl", "-n", "kern.boottime")).group(1))
_h = (time.time() - _boot) / 3600
uptime_txt = f"{_h / 24:.1f} days since the last restart" if _h >= 48 else f"{_h:.0f} hours since the last restart"

from report import render  # noqa: E402
from buddy import theme    # noqa: E402

# One buddy per app group and per Claude Code session, with its memory and its share of all the processors.
crowd = [{"name": g, "gb": round(gb, 2), "cpu": round(cpu_by_group.get(g, 0), 1), "kind": "app"} for g, gb in sorted(now_d.items(), key=lambda kv: -kv[1])
         if g != "Claude Code sessions" and (gb >= 0.1 or cpu_by_group.get(g, 0) >= 1)]
crowd += [{"name": short(folders.get(p_, "unknown folder")), "gb": round(gb, 2), "cpu": round(pcpu.get(p_, 0) / ncores, 1), "kind": "claude"} for p_, gb in sess]
OUT_ALL = os.path.join(HOME, "memory-report-all.html")
wdata = page_data(WDIR)
ctx = dict(locals())               # the module's namespace; render() reads it and sets yard_measure
ctx.update(hours="all", hours_txt="every hour the Mac was on", other_ok=wdata is not None,
           here=OUT_ALL, other=OUT, hrs=list(range(24)), wds=list(range(7)))
pages = [(OUT_ALL, ctx)]
if wdata:                          # the default page: working hours only
    wctx = dict(ctx, **wdata)
    wctx.update(HOME=WDIR, hours="work", hours_txt=work_txt, here=OUT, other=OUT_ALL,
                hrs=list(range(_h0, _h1)), wds=_ds, days=[d for d in wdata["days"] if dt.date.fromisoformat(d).weekday() in WORK_D])
    pages.insert(0, (OUT, wctx))
else:                              # no working-hours readings yet: the all-hours page is also the default
    pages.append((OUT, dict(ctx, here=OUT, other=OUT)))
for out_, c_ in pages:
    html_page = theme(render(c_), mood, crowd, c_.get("yard_measure", "mem"))
    open(out_ + ".tmp", "w").write(html_page)
    os.replace(out_ + ".tmp", out_)

# Optional: copy readings and page to Google Drive every 15 minutes, in case this Mac will not start.
if cfg.get("drive_backup"):
    drives = glob.glob(os.path.expanduser("~/Library/CloudStorage/GoogleDrive-*/My Drive"))
    if drives and (int(time.strftime("%M")) % 15 == 0 or not os.path.isdir(os.path.join(drives[0], "Memory Monitor"))):
        dest = os.path.join(drives[0], "Memory Monitor")
        os.makedirs(dest, exist_ok=True)
        for name in ("mem.csv", "apps.csv", "live.csv", "cpu.csv", "cpu_apps.csv", "tools_cpu.csv", "heat.csv", "io.csv", "tools.csv", "history_sessions.csv", "memory-report.html", "memory-report-all.html", "config.json"):
            if os.path.exists(os.path.join(HOME, name)):
                shutil.copy2(os.path.join(HOME, name), dest)
