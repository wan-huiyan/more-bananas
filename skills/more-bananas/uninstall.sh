#!/bin/bash
# Stops the monitor and removes its launcher. Keeps ~/memlog (your readings) unless you pass --purge.
LABEL="com.memlog.monitor"
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null
rm -f "$HOME/Library/LaunchAgents/$LABEL.plist" "$HOME/Desktop/memory-report.html"
rm -rf "$HOME/Applications/Memory Monitor.app"
echo "If a Memory Monitor icon is still in your Dock, drag it off."
[ "${1:-}" = "--purge" ] && rm -rf "$HOME/memlog" && echo "Readings deleted."
echo "Memory Monitor stopped."
