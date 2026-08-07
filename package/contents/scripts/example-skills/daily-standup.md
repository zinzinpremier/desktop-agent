---
name: "Daily standup"
description: "Run a battery, disk, memory, and package-update sweep then summarize the system's status."
trigger: "/standup|status du jour|daily status"
auto_invoke: true
requires_tools: ["run_command"]
---

When the user triggers this skill, run these commands and present a 3-5 line summary:

```bash
uptime -p
df -h /
free -h
ls -la ~/.local/share/plasmallm/screenshots | tail -3   # recent screenshots
```

Group findings into a short Markdown report:

1. **Uptime & load** — how long the system has been up
2. **Disk & memory** — usage percentages, anything red
3. **Recent activity** — number of chat screenshots taken this week (file count)

Keep it terse: the user wants the highlights, not a wall of numbers.
