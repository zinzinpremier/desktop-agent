/*
    SPDX-FileCopyrightText: 2026 Joshua Roman
    SPDX-License-Identifier: GPL-2.0-or-later
*/

.pragma library

var name = "reflex_learn";
var displayName = "Reflex Learn";
var description = "Persist a learned reflex (pattern + shell command) so future matching user inputs short-circuit the LLM and run the command directly. Stored in ~/.local/share/plasmallm/reflexes.json. Use action='list' | 'add' | 'remove' | 'test'.";
var parameters = {
    type: "object",
    properties: {
        justification: { type: "string", description: "A brief 1 sentence justification for why you are running this command." },
        action: { type: "string", enum: ["list", "add", "remove", "test"], description: "What to do" },
        name: { type: "string", description: "Reflex name (e.g. 'myip')" },
        pattern: { type: "string", description: "JS regex source matching the user input (no slashes; case-insensitive)" },
        exec: { type: "string", description: "Shell command to run when the pattern matches" },
        ephemeral: { type: "Bool", description: "Mark the result as ephemeral (not saved into chat history)" },
        testInput: { type: "string", description: "Sample input to test the pattern against (for action='test')" }
    },
    required: ["justification", "action"]
};
var sandboxed = false;
var sideEffect = true;

function execute(args, context) {
    var home = (context.config.userHome || "$HOME").replace(/'/g, "'\\''");
    var reflexesFile = home + "/.local/share/plasmallm/reflexes.json";
    var action = args.action || "list";

    if (action === "list") {
        context.exec("mkdir -p '" + home + "/.local/share/plasmallm' && cat '" + reflexesFile + "' 2>/dev/null || echo '{\"reflexes\":[]}'", name, args);
        return;
    }

    if (action === "add") {
        if (!args.name || !args.pattern || !args.exec) {
            context.error(context.i18n("name, pattern, and exec required for add"));
            return;
        }
        // Validate regex client-side via a quick python test.
        var safeName = args.name.replace(/[^A-Za-z0-9_-]/g, "");
        var safePattern = args.pattern.replace(/'/g, "'\\''");
        var safeExec = args.exec.replace(/'/g, "'\\''");
        var safeEphemeral = args.ephemeral === true ? "True" : "False";
        var tmpJson = "/tmp/plasma-reflex-add-" + Math.random().toString(36).substring(2, 10) + ".json";
        var tmpPy = "/tmp/plasma-reflex-py-" + Math.random().toString(36).substring(2, 10) + ".py";

        var op = { name: safeName, pattern: args.pattern, exec: args.exec, ephemeral: args.ephemeral === true };
        var writeJson = "mkdir -p '" + home + "/.local/share/plasmallm' && printf '%s' '" +
                        JSON.stringify(op).replace(/'/g, "'\\''") + "' > '" + tmpJson + "'";

        var py =
            "import json, sys, os, re\n" +
            "p = '" + reflexesFile + "'\n" +
            "op = json.load(open('" + tmpJson + "'))\n" +
            "try:\n" +
            "    re.compile(op['pattern'], re.IGNORECASE)\n" +
            "except re.error as e:\n" +
            "    print('ERROR invalid regex: ' + str(e))\n" +
            "    sys.exit(2)\n" +
            "idx = {'reflexes': []}\n" +
            "if os.path.exists(p):\n" +
            "    try: idx = json.load(open(p))\n" +
            "    except: pass\n" +
            "if not isinstance(idx.get('reflexes'), list): idx['reflexes'] = []\n" +
            "kept = [r for r in idx['reflexes'] if r.get('name') != op['name']]\n" +
            "kept.append(op)\n" +
            "idx['reflexes'] = kept\n" +
            "json.dump(idx, open(p, 'w'), indent=2)\n" +
            "os.remove('" + tmpJson + "')\n" +
            "print('OK saved reflex ' + op['name'])\n";

        var writePy = "printf '%s' '" + py.replace(/'/g, "'\\''").replace(/\n/g, "\\n") + "' > '" + tmpPy + "'";
        context.exec(writeJson + " && " + writePy + " && python3 '" + tmpPy + "' && rm -f '" + tmpPy + "'", name, args);
        return;
    }

    if (action === "remove") {
        if (!args.name) { context.error(context.i18n("name required for remove")); return; }
        var safeNameR = args.name.replace(/[^A-Za-z0-9_-]/g, "");
        var tmpR = "/tmp/plasma-reflex-rm-" + Math.random().toString(36).substring(2, 10) + ".json";
        var tmpPyR = "/tmp/plasma-reflex-py-" + Math.random().toString(36).substring(2, 10) + ".py";
        var writeR = "mkdir -p '" + home + "/.local/share/plasmallm' && printf '%s' '{\"name\":\"" + safeNameR + "\"}' > '" + tmpR + "'";
        var pyR =
            "import json, os\n" +
            "p = '" + reflexesFile + "'\n" +
            "op = json.load(open('" + tmpR + "'))\n" +
            "if os.path.exists(p):\n" +
            "    idx = json.load(open(p))\n" +
            "    before = len(idx.get('reflexes', []))\n" +
            "    idx['reflexes'] = [r for r in idx.get('reflexes', []) if r.get('name') != op['name']]\n" +
            "    after = len(idx['reflexes'])\n" +
            "    json.dump(idx, open(p, 'w'), indent=2)\n" +
            "    print('removed ' + str(before - after))\n" +
            "os.remove('" + tmpR + "')\n";
        var writePyR = "printf '%s' '" + pyR.replace(/'/g, "'\\''").replace(/\n/g, "\\n") + "' > '" + tmpPyR + "'";
        context.exec(writeR + " && " + writePyR + " && python3 '" + tmpPyR + "' && rm -f '" + tmpPyR + "'", name, args);
        return;
    }

    if (action === "test") {
        if (!args.pattern || !args.testInput) {
            context.error(context.i18n("pattern and testInput required for test"));
            return;
        }
        var safePatternT = args.pattern.replace(/'/g, "'\\''");
        var safeTest = args.testInput.replace(/'/g, "'\\''");
        var cmd = "python3 -c \"import re,sys; p='" + safePatternT + "'; t='" + safeTest + "'; m=re.search(p,t,re.IGNORECASE); print('MATCH' if m else 'NO_MATCH')\"";
        context.exec(cmd, name, args);
        return;
    }

    context.error(context.i18n("Unknown action: %1", action));
}