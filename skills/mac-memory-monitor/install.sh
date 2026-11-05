#!/bin/bash
# Mac Memory Monitor installer. Re-running it upgrades the code and keeps your readings and settings.
#   ./install.sh [--dock] [--drive-backup] [--history-from YYYY-MM-DD]
set -euo pipefail
[ "$(uname)" = Darwin ] || { echo "macOS only."; exit 1; }
SRC="$(cd "$(dirname "$0")" && pwd)/app"
DATA="$HOME/memlog"
LABEL="com.memlog.monitor"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
PY="$(command -v python3 || true)"
[ -n "$PY" ] || { echo "python3 not found. Install the Xcode command line tools: xcode-select --install"; exit 1; }
DOCK=0; DRIVE=""; HIST=""
while [ $# -gt 0 ]; do case "$1" in
  --dock) DOCK=1;; --drive-backup) DRIVE=1;; --history-from) HIST="$2"; shift;;
  *) echo "unknown option $1"; exit 1;; esac; shift; done

mkdir -p "$DATA/icon" "$HOME/Library/LaunchAgents"
cp "$SRC"/memlog.py "$SRC"/report.py "$SRC"/buddy.py "$SRC"/backfill_sessions.py "$DATA/"
cp "$SRC"/icon/* "$DATA/icon/"
# Settings: keep existing ones, apply any flags given now.
"$PY" - "$DATA/config.json" "$DRIVE" "$HIST" <<'PYEOF'
import json, os, sys
p, drive, hist = sys.argv[1:]
c = json.load(open(p)) if os.path.exists(p) else {"drive_backup": False, "history_from": ""}
if drive: c["drive_backup"] = True
if hist: c["history_from"] = hist
json.dump(c, open(p, "w"), indent=2)
print("settings:", c)
PYEOF

cat > "$PLIST" <<PL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>Label</key><string>$LABEL</string>
<key>ProgramArguments</key><array><string>$PY</string><string>$DATA/memlog.py</string></array>
<key>StartInterval</key><integer>60</integer>
<key>RunAtLoad</key><true/>
<key>StandardErrorPath</key><string>$DATA/error.log</string>
</dict></plist>
PL
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
ln -sf "$DATA/memory-report.html" "$HOME/Desktop/memory-report.html"

if [ "$DOCK" = 1 ]; then
  APP="$HOME/Applications/Memory Monitor.app"; mkdir -p "$HOME/Applications"; rm -rf "$APP"
  osacompile -o "$APP" -e 'do shell script "open " & quoted form of (POSIX path of (path to home folder) & "memlog/memory-report.html")'
  cp "$DATA/icon/buddy.icns" "$APP/Contents/Resources/applet.icns"
  rm -f "$APP/Contents/Resources/Assets.car"; /usr/libexec/PlistBuddy -c "Delete :CFBundleIconName" "$APP/Contents/Info.plist" 2>/dev/null || true
  codesign --force -s - "$APP" >/dev/null 2>&1 || true
  if ! defaults read com.apple.dock persistent-apps | grep -q "Memory%20Monitor.app"; then
    defaults export com.apple.dock "$DATA/dock-backup.plist"
    defaults write com.apple.dock persistent-apps -array-add "<dict><key>tile-data</key><dict><key>file-data</key><dict><key>_CFURLString</key><string>file://$HOME/Applications/Memory%20Monitor.app/</string><key>_CFURLStringType</key><integer>15</integer></dict></dict></dict>"
    killall Dock
  fi
fi

echo "Waiting for the first reading..."
for i in $(seq 1 30); do [ "$DATA/memory-report.html" -nt "$PLIST" ] && break; sleep 1; done
if [ "$DATA/memory-report.html" -nt "$PLIST" ]; then echo "Done. Opening ~/Desktop/memory-report.html"; open "$DATA/memory-report.html"
else echo "No page yet. Check $DATA/error.log"; exit 1; fi
