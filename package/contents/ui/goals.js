/*
    SPDX-FileCopyrightText: 2026 Joshua Roman
    SPDX-License-Identifier: GPL-2.0-or-later
*/

// Goals system: long-running objectives the agent is working toward.
//
// A goal has:
//   - id, title, description (what we're trying to achieve)
//   - state: "open" | "in_progress" | "done" | "failed" | "blocked"
//   - priority: 0..3 (lower = more important)
//   - created, updated (ISO timestamps)
//   - subtasks: [{title, done}]
//   - notes: array of strings (observations, partial progress)
//
// Goals are persisted as a JSON index at
// $XDG_DATA_HOME/plasmallm/goals/index.json.

.pragma library

function goalsDir(userHome) {
    return (userHome || "$HOME") + "/.local/share/plasmallm/goals";
}

function indexPath(userHome) {
    return goalsDir(userHome) + "/index.json";
}

// Build the shell command to read the index. Falls back to an empty index
// when the file doesn't exist.
function buildReadCommand(userHome) {
    var p = indexPath(userHome);
    return "mkdir -p '" + goalsDir(userHome) + "' && cat '" + p + "' 2>/dev/null || echo '{\"goals\":[]}'";
}

// Parse the index JSON. Returns { goals: [...] } or an empty default.
function parseIndex(stdout) {
    try {
        var data = JSON.parse(stdout);
        if (data && Array.isArray(data.goals)) return data;
    } catch (e) { /* fall through */ }
    return { goals: [] };
}

function newGoal(title, description, priority) {
    var now = new Date().toISOString();
    return {
        id: "g_" + Math.random().toString(36).substring(2, 10),
        title: title,
        description: description || "",
        state: "open",
        priority: priority !== undefined ? priority : 2,
        created: now,
        updated: now,
        subtasks: [],
        notes: []
    };
}
