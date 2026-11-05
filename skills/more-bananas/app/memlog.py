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
AUTOMATION = ("--disable-field-trial-config", "--remote-debugging", "--headless", "--enable-automation")


def chrome_root(pid):  # the top Chrome process this one belongs to
    while procs.get(procs[pid][0], ("", "", ""))[2].find("Google Chrome") >= 0:
        pid = procs[pid][0]
    return procs[pid][2]


for pid, (_ppid, rss, cmd) in procs.items():
    gb = int(rss) / 2**20
    g = next((name for name, test in GROUPS if test(cmd)), "Other apps")
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
    f.write(stamp + "," + ",".join(f"{x:.1f}" for x in io_rates) + "\n")
with open(APPCPU, "a") as f:
    for g_, x_ in sorted(cpu_by_group.items(), key=lambda kv: -kv[1]):
        if x_ >= 0.5:
            f.write(f"{stamp},{g_},{x_:.1f}\n")
json.dump({"t": time.time(), "Swapouts": cnt["Swapouts"], "Swapins": cnt["Swapins"], **io_now}, open(state_p, "w"))
with open(LIVE, "a") as f:
    f.write(f"{stamp},{out_mb:.1f},{in_mb:.1f},{comp_gb:.2f},{wired_gb:.2f},{squeezed_gb:.2f}\n")

# ---------- what the page needs ----------
allrows = [l.strip().split(",") for l in open(LOG) if l.count(",") == 5]
first_reading = allrows[0][0]
rows = allrows[-60 * 24 * 7:]  # last 7 days
T = [r[0] for r in rows]
U, S = [float(r[1]) for r in rows], [float(r[2]) for r in rows]
N = [int(r[5]) for r in rows]
need = [U[i] + S[i] for i in range(len(rows))]
pk = max(range(len(rows)), key=lambda i: need[i])
lv = [l.strip().split(",") for l in open(LIVE) if l.count(",") == 5][-60 * 24 * 7:]
LO, LT = [float(r[1]) for r in lv], [r[0] for r in lv]
lpk = max(range(len(lv)), key=lambda i: LO[i])
mood, word, tone = (("calm", "calm", "#34d399") if out_mb < 5 else
                    ("tight", "swapping a little", "#fbbf24") if out_mb < 100 else
                    ("over", "swapping hard", "#fb7185"))
if mood == "calm" and load1 > cores:  # memory is calm but the processors have more work than cores: amber, not green
    tone = "#fbbf24"
mouth = {"calm": "M12 21 Q16 25 20 21", "tight": "M12 22 L20 22", "over": "M12 23 Q16 19 20 23"}[mood]
fav = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect x="2" y="2" width="28" height="28" rx="9" fill="{tone.replace("#", "%23")}"/>'
       f'<circle cx="12" cy="14" r="2" fill="%23fff"/><circle cx="20" cy="14" r="2" fill="%23fff"/>'
       f'<path d="{mouth}" stroke="%23fff" stroke-width="1.8" fill="none" stroke-linecap="round"/></svg>')

apps = {}
for l in open(APPS):
    if l.count(",") >= 2:
        t, g, gb = l.rstrip("\n").rsplit(",", 2)
        apps.setdefault(t, {})[g] = float(gb)
now_d = apps.get(stamp, by_group)
peak_d = apps.get(T[pk], {})
sess = sorted(sessions, key=lambda x: -x[1])

# History: most Claude Code sessions open at once per day (from the session transcripts, rebuilt hourly),
# and the measured peak per day.
hs = os.path.join(HOME, "history_sessions.csv")
if not os.path.exists(hs) or time.strftime("%M") == "00":
    subprocess.run([sys.executable, os.path.join(HOME, "backfill_sessions.py")], capture_output=True)
day_sess = collections.defaultdict(lambda: (0, ""))
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
swapped_total_gb = cnt["Swapouts"] * page / 2**30
_boot = int(re.search(r"sec = (\d+)", sh("sysctl", "-n", "kern.boottime")).group(1))
_h = (time.time() - _boot) / 3600
uptime_txt = f"{_h / 24:.1f} days since the last restart" if _h >= 48 else f"{_h:.0f} hours since the last restart"

from report import render  # noqa: E402
from buddy import theme    # noqa: E402

ctx = locals()                     # at module level this is the module's own namespace; render() reads it and sets yard_measure
html_page = render(ctx)
# One buddy per app group and per Claude Code session, with its memory and its share of all the processors.
crowd = [{"name": g, "gb": round(gb, 2), "cpu": round(cpu_by_group.get(g, 0), 1), "kind": "app"} for g, gb in sorted(now_d.items(), key=lambda kv: -kv[1])
         if g != "Claude Code sessions" and (gb >= 0.1 or cpu_by_group.get(g, 0) >= 1)]
crowd += [{"name": short(folders.get(p_, "unknown folder")), "gb": round(gb, 2), "cpu": round(pcpu.get(p_, 0) / ncores, 1), "kind": "claude"} for p_, gb in sess]
html_page = theme(html_page, mood, crowd, ctx.get("yard_measure", "mem"))
open(OUT + ".tmp", "w").write(html_page)
os.replace(OUT + ".tmp", OUT)

# Optional: copy readings and page to Google Drive every 15 minutes, in case this Mac will not start.
if cfg.get("drive_backup"):
    drives = glob.glob(os.path.expanduser("~/Library/CloudStorage/GoogleDrive-*/My Drive"))
    if drives and (int(time.strftime("%M")) % 15 == 0 or not os.path.isdir(os.path.join(drives[0], "Memory Monitor"))):
        dest = os.path.join(drives[0], "Memory Monitor")
        os.makedirs(dest, exist_ok=True)
        for name in ("mem.csv", "apps.csv", "live.csv", "cpu.csv", "cpu_apps.csv", "tools_cpu.csv", "heat.csv", "io.csv", "tools.csv", "history_sessions.csv", "memory-report.html", "config.json"):
            if os.path.exists(os.path.join(HOME, name)):
                shutil.copy2(os.path.join(HOME, name), dest)
