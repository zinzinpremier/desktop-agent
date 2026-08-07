/*
    SPDX-FileCopyrightText: 2026 Joshua Roman
    SPDX-License-Identifier: GPL-2.0-or-later
*/

.pragma library

var name = "manage_goals";
var displayName = "Manage Goals";
var description = "Track long-running objectives the agent is working toward. Goals persist in ~/.local/share/plasmallm/goals/index.json and are surfaced in the system prompt so the agent pursues them proactively. Use action='list' | 'create' | 'update' | 'complete' | 'delete' | 'add_note'.";
var parameters = {
    type: "object",
    properties: {
        justification: { type: "string", description: "A brief 1 sentence justification for why you are running this command." },
        action: { type: "string", enum: ["list", "create", "update", "complete", "delete", "add_note"], description: "What to do" },
        id: { type: "string", description: "Goal id (for update/complete/delete/add_note)" },
        title: { type: "string", description: "Goal title (for create/update)" },
        description: { type: "string", description: "Goal description (for create/update)" },
        priority: { type: "int", description: "Priority 0-3 (0 = most important)" },
        note: { type: "string", description: "Note to append (for add_note)" },
        state: { type: "string", enum: ["open", "in_progress", "done", "failed", "blocked"], description: "New state (for update)" }
    },
    required: ["justification", "action"]
};
var sandboxed = false;
var sideEffect = true;

var ID_CHARS = "g_" + Math.random().toString(36).substring(2, 10);

// All mutations go through Python that takes the index path + operation args
// as a single JSON blob on stdin. This avoids shell injection on the args
// (title, note, description) and keeps each branch readable.
function execute(args, context) {
    var home = (context.config.userHome || "$HOME").replace(/'/g, "'\\''");
    var goalsDir = home + "/.local/share/plasmallm/goals";
    var indexFile = goalsDir + "/index.json";
    var action = args.action || "list";

    if (action === "list") {
        context.exec("mkdir -p '" + goalsDir + "' && cat '" + indexFile + "' 2>/dev/null || echo '{\"goals\":[]}'", name, args);
        return;
    }

    if (action === "create" && !args.title) { context.error(context.i18n("title required for create")); return; }
    if (action === "update" && !args.id) { context.error(context.i18n("id required for update")); return; }
    if ((action === "complete" || action === "delete") && !args.id) { context.error(context.i18n("id required")); return; }
    if (action === "add_note" && (!args.id || !args.note)) { context.error(context.i18n("id and note required")); return; }

    // Pack the operation as JSON and pipe through Python. The Python script
    // is generic across all operations.
    var op = { action: action };
    if (args.id) op.id = args.id;
    if (args.title) op.title = args.title;
    if (args.description) op.description = args.description;
    if (args.priority !== undefined) op.priority = args.priority;
    if (args.note) op.note = args.note;
    if (args.state) op.state = args.state;

    // Write the JSON to a temp file, then run Python on it. Avoids any
    // quoting concern on the op payload.
    var tmpJson = "/tmp/plasma-goal-op-" + Math.random().toString(36).substring(2, 10) + ".json";
    var writeJson = "mkdir -p '" + goalsDir + "' && printf '%s' '" +
                    JSON.stringify(op).replace(/'/g, "'\\''") + "' > '" + tmpJson + "'";

    var py =
        "import json, sys, datetime, os\n" +
        "p = '" + indexFile + "'\n" +
        "op = json.load(open('" + tmpJson + "'))\n" +
        "idx = {'goals': []}\n" +
        "if os.path.exists(p):\n" +
        "    try: idx = json.load(open(p))\n" +
        "    except: pass\n" +
        "now = datetime.datetime.now().isoformat()\n" +
        "if op['action'] == 'create':\n" +
        "    idx['goals'].append({\n" +
        "        'id': 'g_' + os.urandom(4).hex(),\n" +
        "        'title': op.get('title',''),\n" +
        "        'description': op.get('description',''),\n" +
        "        'state': 'open',\n" +
        "        'priority': op.get('priority', 2),\n" +
        "        'created': now, 'updated': now,\n" +
        "        'subtasks': [], 'notes': []\n" +
        "    })\n" +
        "elif op['action'] == 'update':\n" +
        "    for g in idx['goals']:\n" +
        "        if g['id'] == op['id']:\n" +
        "            if 'state' in op: g['state'] = op['state']\n" +
        "            if 'title' in op: g['title'] = op['title']\n" +
        "            if 'description' in op: g['description'] = op['description']\n" +
        "            g['updated'] = now\n" +
        "            break\n" +
        "elif op['action'] == 'complete':\n" +
        "    for g in idx['goals']:\n" +
        "        if g['id'] == op['id']:\n" +
        "            g['state'] = 'done'\n" +
        "            g['updated'] = now\n" +
        "            break\n" +
        "elif op['action'] == 'delete':\n" +
        "    idx['goals'] = [g for g in idx['goals'] if g['id'] != op['id']]\n" +
        "elif op['action'] == 'add_note':\n" +
        "    for g in idx['goals']:\n" +
        "        if g['id'] == op['id']:\n" +
        "            g['notes'].append(now + ': ' + op.get('note',''))\n" +
        "            g['updated'] = now\n" +
        "            break\n" +
        "json.dump(idx, open(p, 'w'), indent=2)\n" +
        "os.remove('" + tmpJson + "')\n";

    // Pass the script via heredoc-equivalent: write to a temp file, run with python3.
    // Avoids any quoting of multi-line code through bash.
    var tmpPy = "/tmp/plasma-goal-py-" + Math.random().toString(36).substring(2, 10) + ".py";
    var writePy = "printf '%s' '" + py.replace(/'/g, "'\\''").replace(/\n/g, "\\n") + "' > '" + tmpPy + "'";

    context.exec(writeJson + " && " + writePy + " && python3 '" + tmpPy + "' && rm -f '" + tmpPy + "'", name, args);
}