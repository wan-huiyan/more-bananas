#!/usr/bin/env python3
"""Backfill: how many Claude Code sessions were running at once, per hour, from the session transcripts.

macOS keeps no memory history, so the Claude Code transcripts in ~/.claude/projects are the only record of the
workload from before the monitor was installed. A session counts as running from one message to the next when the gap is
under 30 minutes. Subagent transcripts are skipped: they run inside their parent session's process.
Writes ~/memlog/history_sessions.csv: hour,max_sessions_at_once,session_minutes
"""
import glob, os, re, datetime as dt, collections
TS = re.compile(rb'"timestamp":"(\d{4}-\d\d-\d\dT\d\d:\d\d)')
GAP = 30
minutes = collections.Counter()  # local minute -> sessions running
for f in glob.glob(os.path.expanduser("~/.claude/projects/*/*.jsonl")):
    seen = sorted({m.group(1) for m in TS.finditer(open(f, "rb").read())})
    ts = [dt.datetime.fromisoformat(s.decode()).replace(tzinfo=dt.timezone.utc).astimezone().replace(tzinfo=None) for s in seen]
    for a, b in zip(ts, ts[1:] + ts[-1:]):
        end = b if (b - a).total_seconds() <= GAP * 60 else a + dt.timedelta(minutes=1)
        t = a
        while t <= end:
            minutes[t] += 1; t += dt.timedelta(minutes=1)
hours = collections.defaultdict(lambda: [0, 0])
for t, n in minutes.items():
    h = hours[t.strftime("%Y-%m-%d %H:00")]; h[0] = max(h[0], n); h[1] += n
with open(os.path.expanduser("~/memlog/history_sessions.csv"), "w") as out:
    for h in sorted(hours): out.write(f"{h},{hours[h][0]},{hours[h][1]}\n")
print(len(hours), "hours;", "first", min(hours), "last", max(hours), "; max at once", max(v[0] for v in hours.values()))
