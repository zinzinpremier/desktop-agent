/*
    SPDX-FileCopyrightText: 2026 Joshua Roman
    SPDX-License-Identifier: GPL-2.0-or-later
*/

// Reflex layer — short-circuit common shell-like inputs without invoking the
// LLM. Saves latency and tokens for things the user types a hundred times a
// day: `ls`, `pwd`, `date`, simple file reads, etc.
//
// Returns null if the input doesn't match a reflex, otherwise returns
// { response: string, exec?: string, ephemeral?: boolean }.

.pragma library

// Each pattern: { trigger: RegExp, exec: string }
// When triggered, `exec` runs in the background and its output replaces
// the placeholder in the chat. The pattern matches the user's trimmed input.
var REFLEXES = [
    {
        name: "ls",
        pattern: /^\s*(ls|ll|la)\s*(\/\S*|~\S*|\.\S*)?\s*$/,
        build: function(m) {
            var dir = m[2] || ".";
            var cmd = "ls -lah --color=always " + dir + " 2>&1 | head -n 50";
            return { exec: cmd, ephemeral: false };
        }
    },
    {
        name: "pwd",
        pattern: /^\s*pwd\s*$/,
        build: function() {
            return { exec: "pwd", ephemeral: false };
        }
    },
    {
        name: "date",
        pattern: /^\s*(date|what'?s?\s+the\s+(date|time))\s*[\?\.]?\s*$/i,
        build: function() {
            return { exec: "date", ephemeral: false };
        }
    },
    {
        name: "uptime",
        pattern: /^\s*(uptime|how\s+long\s+has\s+(the\s+)?(system|computer|pc)\s+been\s+up)\s*[\?\.]?\s*$/i,
        build: function() {
            return { exec: "uptime", ephemeral: false };
        }
    },
    {
        name: "df",
        pattern: /^\s*(df|disk\s+space)\s*[\?\.]?\s*$/i,
        build: function() {
            return { exec: "df -h", ephemeral: false };
        }
    },
    {
        name: "whoami",
        pattern: /^\s*(whoami|who\s+am\s+i)\s*[\?\.]?\s*$/i,
        build: function() {
            return { exec: "whoami", ephemeral: false };
        }
    },
    {
        name: "ip",
        pattern: /^\s*(my\s+ip|what'?s?\s+my\s+ip|public\s+ip)\s*[\?\.]?\s*$/i,
        build: function() {
            return { exec: "curl -s https://ifconfig.me 2>/dev/null || ip addr show | grep inet", ephemeral: false };
        }
    },
    {
        name: "weather",
        pattern: /^\s*(weather|forecast|temperature\s+now)\s*[\?\.]?\s*$/i,
        build: function() {
            return { exec: "curl -s 'wttr.in?format=%C+%t+(feels+%f)\\nWind:+%w\\nHumidity:+%h' 2>/dev/null", ephemeral: false };
        }
    }
];

// In-memory cache of user-defined reflexes, populated by main.qml via
// loadUserReflexes(). Each entry: { name, pattern (string), exec (string),
// ephemeral: bool }. Patterns are interpreted as JS regexes (case-insensitive).
var userReflexes = [];

function loadUserReflexes(arr) {
    if (!Array.isArray(arr)) { userReflexes = []; return; }
    var clean = [];
    for (var i = 0; i < arr.length; i++) {
        var r = arr[i];
        if (!r || typeof r.pattern !== "string" || typeof r.exec !== "string") continue;
        if (r.pattern.length === 0 || r.pattern.length > 200) continue;
        try {
            var re = new RegExp(r.pattern, "i");
            clean.push({
                name: typeof r.name === "string" ? r.name : ("user_" + i),
                pattern: re,
                exec: r.exec,
                ephemeral: r.ephemeral === true
            });
        } catch (e) {
            // bad regex; skip silently
        }
    }
    userReflexes = clean;
}

function tryReflex(input) {
    if (!input) return null;
    var text = input.trim();
    if (text.length === 0 || text.length > 200) return null;
    // Don't trigger on multi-line input or complex questions
    if (text.indexOf("\n") !== -1) return null;
    if (text.indexOf("?") !== -1 && text.split(/\s+/).length > 4) return null;

    // User reflexes win over built-ins so a learned alias can override defaults.
    for (var u = 0; u < userReflexes.length; u++) {
        var ur = userReflexes[u];
        var mu = text.match(ur.pattern);
        if (mu) {
            return { name: ur.name, exec: ur.exec, ephemeral: ur.ephemeral };
        }
    }

    for (var i = 0; i < REFLEXES.length; i++) {
        var r = REFLEXES[i];
        var m = text.match(r.pattern);
        if (m) {
            var action = r.build(m);
            if (action) {
                action.name = r.name;
                return action;
            }
        }
    }
    return null;
}