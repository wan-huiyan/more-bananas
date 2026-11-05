<p align="center">
  <img src="docs/buddy.svg" width="140" alt="The banana buddy mascot"/>
</p>

<h1 align="center">mac-memory-monitor 🍌</h1>
<p align="center"><em>Is your Mac too small for your work? Measure it, minute by minute, then buy the right amount of RAM.</em></p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/github/license/wan-huiyan/mac-memory-monitor" alt="license"/></a>
  <a href="https://github.com/wan-huiyan/mac-memory-monitor/commits"><img src="https://img.shields.io/github/last-commit/wan-huiyan/mac-memory-monitor" alt="last commit"/></a>
  <img src="https://img.shields.io/badge/macOS-only-lightgrey" alt="macOS only"/>
  <img src="https://img.shields.io/badge/python-3.9%2B-blue" alt="python 3.9+"/>
  <a href="https://claude.com/claude-code"><img src="https://img.shields.io/badge/Claude_Code-skill-orange" alt="Claude Code skill"/></a>
</p>

> **A tiny background job records what your Mac is really holding every minute (every app, every Claude Code session, and the hidden browsers and scripts those sessions start) and turns it into a cute, self-updating page that tells you how much memory your next laptop needs.**

<p align="center">
  <img src="docs/screens/rec.png" width="860" alt="The Recommendation tab: get 48 GB of memory and 1 TB of storage, with the share of working minutes each RAM size would have handled"/>
  <br/><sub>The first tab is the answer. Here a 16 GB Mac handled only 26% of working minutes; 32 GB would have covered 99%, and 48 GB covers the busiest minute with a quarter to spare. Real readings from one work laptop, project names replaced.</sub>
</p>

## Why it exists

"Get more RAM" is usually a guess: someone counts browser tabs, or the number of AI coding sessions they *think* they run, and picks a size. Then the laptop stalls on the one afternoon it matters, mid client call.

This measures instead. It reads macOS's own memory figures once a minute, keeps them on your Mac, and answers three questions on one page: **how much memory does my work actually need, when does it run out, and what is using it?** If you run Claude Code, it also shows the cost you can't see: each session can start Playwright test browsers, plug-in servers and scripts, and those add up.

## What you get

| | Feature | The specifics |
|---|---|---|
| 🎯 | **A measured recommendation** | Busiest minute ever recorded × 1.25, rounded up to a size Macs are sold in. Plus a budget pick (smallest size that covered 99% of working minutes) and storage (current use × 1.5). Updates itself every minute. |
| 📊 | **"Would it have fitted?" ladder** | For 16 / 24 / 32 / 36 / 48 / 64 GB: the share of your working minutes (7am to midnight) each size would have handled, with and without Claude's hidden test browsers. |
| 📈 | **Today, minute by minute** | Memory needed against your RAM line, the striped overflow onto disk, and the minutes the Mac was actively moving memory to disk. Hover any minute. |
| 📅 | **Busy days and busy hours** | One timeline since the history start: Claude Code sessions open at once above the line, memory over your RAM below it. Plus a weekday × hour heatmap. |
| 🧸 | **Who is using it** | One walking banana buddy per app and per Claude Code session, sized by memory. Every app's memory now / 24 h / 7 days / 30 days. |
| 🤖 | **What Claude runs** | Claude's tools grouped into plain kinds (test browsers, page checks, cloud tools, plug-ins, build scripts, shell), each opening into its scripts and the session folder that started them. |
| 🪶 | **Light** | One run takes about 0.35 s a minute and stores about 1 MB of readings a day. Nothing is sent anywhere. |
| 🛟 | **Survives a dead laptop** | Optional copy of readings and page to Google Drive every 15 minutes. |

<details>
<summary><b>📸 See every tab</b></summary>

| Today | Busy days |
|---|---|
| <img src="docs/screens/today.png" width="420"/> | <img src="docs/screens/days.png" width="420"/> |
| **Busy hours** | **What uses memory** |
| <img src="docs/screens/hours.png" width="420"/> | <img src="docs/screens/uses.png" width="420"/> |
| **What Claude runs** | **How this works** |
| <img src="docs/screens/claude.png" width="420"/> | <img src="docs/screens/how.png" width="420"/> |

</details>

## Quick start

**Without Claude Code** (any Mac with Python 3, which comes with the Xcode command line tools):

```bash
git clone https://github.com/wan-huiyan/mac-memory-monitor
cd mac-memory-monitor/skills/mac-memory-monitor
./install.sh --dock
```

The page opens in your browser and a **Memory Monitor** buddy appears in your Dock. That's it: leave it running through a normal busy week.

**With Claude Code**, install it as a plugin and ask Claude to set it up:

```bash
claude plugin marketplace add wan-huiyan/mac-memory-monitor
claude plugin install mac-memory-monitor@wan-huiyan-mac-memory-monitor
```

Then say: *"install the memory monitor"*.

<details>
<summary>Options and removal</summary>

```bash
./install.sh --dock                       # add a Memory Monitor app to the Dock
./install.sh --drive-backup               # copy readings to My Drive/Memory Monitor every 15 min
./install.sh --history-from 2026-10-01    # ignore Claude Code session history before a date
./uninstall.sh                            # stop it, keep the readings in ~/memlog
./uninstall.sh --purge                    # stop it and delete the readings
```

Re-running `install.sh` upgrades the code and keeps your readings and settings. Settings live in `~/memlog/config.json`.

</details>

## Using it

- **Open it:** click the Dock buddy, or open `~/Desktop/memory-report.html`. It refreshes itself every minute.
- **Move around:** the tab bar, the scroll wheel, a swipe, or the arrow keys. One tab per screen, no long scroll.
- **Ask Claude:** *"how much RAM should my next Mac have?"*, *"why is my Mac slow this afternoon?"*, *"what is Claude running that uses so much memory?"* Claude reads the same files in `~/memlog/`.

## Limitations (read these before you buy anything)

- **It needs a busy week.** The answer is only as good as the days recorded; a quiet week understates it. The page shows how many working days it has (goal: 10).
- **It leans high.** "Memory needed" is RAM in use plus swap, and swap can hold stale data from hours earlier. The minutes the Mac was *actively* writing to disk are shown separately as the fairer slowdown signal.
- **Per-app figures are approximate.** They count memory still in RAM (not on disk), memory two apps share can be counted twice, and Meet or Zoom in a browser count as the browser.
- **History before install is partial.** Days before the monitor started come from Claude Code transcripts only; Codex and sessions idle for 30+ minutes are not counted.
- **Processor load is recorded but light-touch:** share of all cores busy per minute. It tells you whether memory or the chip is the limit, not which chip to buy.
- **macOS only.** It reads `vm_stat`, `sysctl` and `ps`, and runs under launchd.

## How it works

`launchd` runs `memlog.py` once a minute. It reads macOS's memory figures, groups processes into apps (and Claude Code's child processes into the session that started them), appends a row to a few CSV files in `~/memlog/`, and rebuilds one self-contained HTML page. No server, no network, no dependencies beyond the Python that ships with the Xcode command line tools.

```
skills/mac-memory-monitor/
├── SKILL.md            what Claude reads when you ask it to install or explain the monitor
├── install.sh          sets up ~/memlog, the launchd job, the Desktop link and the Dock app
├── uninstall.sh
└── app/
    ├── memlog.py       takes a reading, writes the CSVs, rebuilds the page
    ├── report.py       the page: tabs, charts, recommendation
    ├── buddy.py        the mascot, the buddy yard, the sparkles
    └── backfill_sessions.py   session history from ~/.claude/projects transcripts
```

## License

MIT. The banana buddy is an original drawing made for this project.
