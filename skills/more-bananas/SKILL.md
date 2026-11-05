---
name: more-bananas
description: Install a cute, always-on memory monitor on a Mac that records RAM and swap every minute and builds a self-updating page arguing whether the laptop is big enough, with a measured RAM recommendation. Use when someone says their Mac is slow or runs out of memory, wants to know how much RAM they need, wants evidence for a laptop upgrade, or asks to install, update, configure or remove "more-bananas", the "memory monitor" or the "Too Small a Mac" page. macOS only.
---

# more-bananas 🍌 (Mac memory monitor)

A background job reads macOS memory figures once a minute and rebuilds a local page,
`~/Desktop/memory-report.html`, with animated buddy mascots. The page makes one case, from
measurements: does this Mac have enough memory for the owner's real workload, and if not, how much is needed.

Nothing is sent anywhere. Everything lives in `~/memlog/` (readings as CSV, the page, settings).

## What the page shows (seven screens, answer first; scroll or swipe between them)

1. **Recommendation**: the RAM and storage to buy. RAM = highest memory need ever recorded × 1.25, rounded up
   to a size Macs are sold in (16/24/32/36/48/64/96/128 GB); a budget pick = smallest size that covered 99%
   of working minutes (7am to midnight). Shows the share of working minutes each size would have handled,
   with and without the hidden test browsers Claude opens, how many working days are measured (goal 10),
   and processor load. Storage = current disk use × 1.5.
2. **Today**: today's minute-by-minute memory need against the RAM line, the minutes it was actively
   swapping, and what held memory at today's busiest minute.
3. **Busy days**: one timeline since the history start: Claude Code sessions open at once above the line
   (from `~/.claude/projects` transcripts), memory over the RAM size below it, per measured day.
4. **Busy hours**: weekday by working-hour heatmap of the highest memory needed.
5. **What uses memory**: a walking buddy per app and per Claude session, plus every app group's memory
   now / 24 h / 7 days / 30 days (average and busiest minute); Claude's tools and test browsers expand into
   groups and scripts.
6. **What Claude runs**: Claude's tools and hidden test browsers by kind (test browsers, page checks, cloud tools,
   plug-ins, build scripts, shell), now / 24 h / 7 days / 30 days, each opening into its scripts and session.
7. **How this works**: what is measured, how the recommendation is worked out, and the caveats.

## Install

Run from this skill's folder:

```bash
./install.sh --dock
```

Options (all optional, can be re-run any time; re-running upgrades the code and keeps readings and settings):

| Flag | Effect |
|---|---|
| `--dock` | Adds a "Memory Monitor" app with a buddy icon to the Dock and `~/Applications` |
| `--drive-backup` | Copies readings and the page to `My Drive/Memory Monitor` every 15 minutes (needs Google Drive for desktop) |
| `--history-from YYYY-MM-DD` | Ignore Claude Code session history before this date (e.g. when earlier sessions were not recorded) |

Settings live in `~/memlog/config.json` and can be edited by hand.

When helping someone install: run `./install.sh --dock`, confirm the page opened, and tell them where things
live: the buddy in their Dock (`~/Applications/Memory Monitor.app`) opens the page; the page itself is
`~/memlog/memory-report.html` with a Desktop shortcut; readings and settings are in `~/memlog/`. Also tell them
the first useful answer needs at least one normal busy working day of readings; the recommendation firms up
as days accumulate.

## Remove

```bash
./uninstall.sh          # stops it, keeps the readings in ~/memlog
./uninstall.sh --purge  # also deletes the readings
```

## How to read it honestly (tell the user this)

- "Memory needed" = RAM in use + swap. Swap can include stale data parked earlier, so the peak and the
  recommendation lean high. The red "minutes swapping" bars (memory actively being written to disk) are the
  fairer test of a real slowdown.
- Per-app figures count memory still in RAM only, and Meet/Zoom in a browser count as the browser.
- The recommendation is only as good as the days recorded: a quiet week understates it.
- History before install comes from Claude Code transcripts only; Codex, and sessions idle for 30+ minutes,
  are not counted.

## Files

- `app/memlog.py`: takes a reading, appends to `~/memlog/{mem,apps,live,tools,cpu}.csv`, rebuilds the page.
- `app/report.py`: the page (seven screens, charts, recommendation).
- `app/buddy.py`: the mascot, the buddy yard and the sparkle effects.
- `app/backfill_sessions.py`: rebuilds session history from `~/.claude/projects/*/*.jsonl` (hourly).
- `app/icon/`: Dock icon, tab icon.
- Runs under launchd as `com.memlog.monitor`, errors go to `~/memlog/error.log`.
