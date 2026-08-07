/*
    SPDX-FileCopyrightText: 2026 Joshua Roman
    SPDX-License-Identifier: GPL-2.0-or-later
*/

// Skills system: markdown files with YAML frontmatter that teach the LLM new
// behaviors on the fly. Loaded from $XDG_DATA_HOME/plasmallm/skills/.
//
// File format:
//
//     ---
//     name: "Daily standup"
//     description: "When the user asks for today's status, run a battery /
//                   disk / network / calendar / git-status sweep and report."
//     trigger: "/standup|status du jour|morning"
//     auto_invoke: false
//     requires_tools: ["run_command"]
//     ---
//
//     Body is a markdown prompt fragment injected into the system prompt
//     when the skill is active.

.pragma library

function skillsDir(userHome) {
    return (userHome || "$HOME") + "/.local/share/plasmallm/skills";
}

// Parse a single .md file. Returns { name, description, trigger, autoInvoke,
// requiresTools, body } or null if no frontmatter is found.
function parseSkillFile(content) {
    var fmMatch = content.match(/^---\s*\n([\s\S]*?)\n---\s*\n([\s\S]*)$/);
    if (!fmMatch) return null;

    var yaml = fmMatch[1];
    var body = fmMatch[2];

    var meta = {};
    yaml.split("\n").forEach(function(line) {
        var m = line.match(/^([a-zA-Z_][a-zA-Z0-9_]*):\s*(.*)$/);
        if (!m) return;
        var key = m[1];
        var val = m[2].replace(/^["']|["']$/g, "").trim();
        if (val.startsWith("[") && val.endsWith("]")) {
            meta[key] = val.slice(1, -1).split(",").map(function(s) {
                return s.trim().replace(/^["']|["']$/g, "");
            }).filter(Boolean);
        } else if (val === "true" || val === "false") {
            meta[key] = (val === "true");
        } else {
            meta[key] = val;
        }
    });

    return {
        name: meta.name || "",
        description: meta.description || "",
        trigger: meta.trigger || "",
        autoInvoke: meta.auto_invoke === true,
        requiresTools: meta.requires_tools || [],
        body: body.trim()
    };
}

// Build the shell command to read all skill files. Caller parses the output
// (each file's body is delimited by the file's basename header in the output).
function buildLoadCommand(userHome) {
    var dir = skillsDir(userHome);
    // For each *.md, emit "===FILE=name===" then cat. Caller splits by marker.
    return "for f in '" + dir + "'/*.md; do " +
           "  [ -e \"$f\" ] || continue; " +
           "  echo \"===FILE===$(basename \"$f\" .md)===\"; " +
           "  cat \"$f\"; " +
           "  echo; " +
           "done 2>/dev/null";
}

// Parse the multiline output of buildLoadCommand into { skillName: {meta, body} }.
function parseLoadOutput(stdout) {
    var out = {};
    var lines = stdout.split("\n");
    var currentName = null;
    var currentBody = [];
    var marker = /^===FILE===(.+)===$/;
    for (var i = 0; i < lines.length; i++) {
        var m = lines[i].match(marker);
        if (m) {
            if (currentName !== null) {
                out[currentName] = parseSkillFile(currentBody.join("\n"));
            }
            currentName = m[1];
            currentBody = [];
        } else if (currentName !== null) {
            currentBody.push(lines[i]);
        }
    }
    if (currentName !== null) {
        out[currentName] = parseSkillFile(currentBody.join("\n"));
    }
    return out;
}

function shouldAutoInvoke(skill, userMessage) {
    if (!skill || !skill.autoInvoke) return false;
    if (!skill.trigger || !userMessage) return false;
    var patterns = skill.trigger.split("|");
    var lower = userMessage.toLowerCase();
    for (var i = 0; i < patterns.length; i++) {
        var p = patterns[i].trim().toLowerCase();
        if (p && lower.indexOf(p) !== -1) return true;
    }
    return false;
}
