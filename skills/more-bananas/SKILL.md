---
name: more-bananas
description: Install a cute, always-on memory monitor on a Mac that records RAM and swap every minute and builds a self-updating page arguing whether the laptop is big enough, with a measured RAM recommendation. Use when someone says their Mac is slow or runs out of memory, wants to know how much RAM they need, wants evidence for a laptop upgrade, or asks to install, update, configure or remove "more-bananas", the "memory monitor" or the "Too Small a Mac" page. macOS only.
---

# more-bananas 🍌 (Mac memory monitor)

A background job reads macOS memory figures once a minute and rebuilds a local page,
`~/Desktop/memory-report.html`, with animated buddy mascots. The page makes one case, from
measurements: does this Mac have enough memory for the owner's real workload, and if not, how much is needed.

Nothing is sent anywhere. Everything lives in `~/memlog/` (readings as CSV, the page, settings).

## What the page shows (eight screens, answer first; scroll or swipe between them)

1. **Recommendation**: the RAM and storage to buy. RAM = highest memory need ever recorded × 1.25, rounded up
   to a size Macs are sold in (16/24/32/36/48/64/96/128 GB); a budget pick = smallest size that covered 99%
   of working minutes (Monday to Friday, 9am to 7pm by default; see Working hours below). Shows the share of working minutes each size would have handled,
   and how many working days are measured (goal 10).
   Processors: a first-guess chip = fewest cores (8 to 16) that would have kept up in 9 working minutes of 10,
   where "kept up" means the 1-minute load average was at or below the core count. Storage = current disk use × 1.5.
   A "what held it up" bar on top splits working minutes into processors, memory, both and heat; the bigger
   cause's ladder comes first. The same per-minute labels colour Today, Busy days and Busy hours.
   The buddy explains the answer step by step in a speech bubble while the page's own charts act out each
   step. It opens with what held the Mac up (processors, memory, heat, graphics, disk, network), then walks
   the bigger cause first: bars regrow, the spill turns into red stripes, the jar is measured. It plays once,
   then rests on the summary; a pause holds through the page's once-a-minute reload; pause, step and replay
   buttons; a click, scroll or swipe outside the bubble stops it and puts the page back, and it only
   scrolls the page when you press its own buttons. The page refreshes itself once a minute, but waits while you
   are using it and keeps your place, without replaying the entrance animation.
2. **Today**: one chart: memory need against the RAM line, with work waiting for the processors drawn on it
   so the same dotted line means "full" for both (1&times; the cores), the minutes it was actively swapping, and
   what held it up minute by minute; beside it what held memory at the busiest minute, and below it who kept
   the processors busy. Buttons switch to the last 3, 7 or 30
   days; longer ranges plot the busiest minute of each 5 to 60, while the headline still counts real minutes.
3. **Hot & slow**: everything that makes the Mac hot, loud or slow, minute by minute, today or the last 3, 7 or 30 days
   (the same switch as Today): chip
   temperature, fan speed, processors, graphics, disk traffic, memory pushed to disk and network traffic, each with a
   dotted "too much" line and red above it; tiles for right now, and which apps kept the processors busy
   while it ran hot. Temperature and fan come from `heat`, a small Swift program install.sh builds.
4. **Busy days**: one timeline since the history start: Claude Code sessions open at once above the line
   (from `~/.claude/projects` transcripts); below it minutes held up per day by cause (a day counts as held up
   after half an hour), then memory over the RAM size, per measured day.
5. **Busy hours**: weekday by working-hour heatmap, opening on what held each hour up (switch to memory needed).
6. **What uses the Mac**: a walking buddy per app and per Claude session (sized by processor share or memory,
   following the same switch), plus every app group's processor share and memory
   now / 24 h / 7 days / 30 days (average and busiest minute); Claude's tools and test browsers expand into
   groups and scripts.
7. **What Claude runs**: Claude's tools and hidden test browsers by kind (test browsers, page checks, cloud tools,
   plug-ins, build scripts, shell), now / 24 h / 7 days / 30 days, each opening into its scripts and session,
   by processor share (`tools_cpu.csv`) or memory. Tabs 6 and 7 open on whichever held the Mac up more.
8. **How this works**: what is measured, how the recommendation is worked out, and the caveats.

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

**Working hours.** By default every tab counts only working hours: `"work_hours": [9, 19]` and
`"work_days": [0, 1, 2, 3, 4]` (Monday is 0) in config.json. A switch at the bottom of every tab opens the
all-hours page (`~/memlog/memory-report-all.html`), built beside it from the same readings. Time the Mac is off or
asleep is never counted: nothing is measured then, and the first reading after a gap of more than 5 minutes records
no swap, disk or network rate instead of an average over the gap.

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
- `app/report.py`: the page (eight screens, charts, recommendation).
- `app/hotpanel.py`: the Hot & slow screen. `app/heat.swift`: chip temperature, fan speed and macOS's heat level, built into `~/memlog/heat` at install.
- `app/buddy.py`: the mascot, the buddy yard and the sparkle effects.
- `app/backfill_sessions.py`: rebuilds session history from `~/.claude/projects/*/*.jsonl` (hourly).
- `app/icon/`: Dock icon, tab icon.
- Runs under launchd as `com.memlog.monitor`, errors go to `~/memlog/error.log`.
