/*
    SPDX-FileCopyrightText: 2026 Joshua Roman
    SPDX-License-Identifier: GPL-2.0-or-later
*/

.pragma library

var name = "memory_recall";
var displayName = "Memory Recall";
var description = "Search the consolidated memory index (~/.local/share/plasmallm/memory/index.json) for snippets whose keywords overlap the supplied query, and print the top matches. Run memory_consolidate first if the index is empty.";
var parameters = {
    type: "object",
    properties: {
        justification: { type: "string", description: "A brief 1 sentence justification for why you are running this command." },
        query: { type: "string", description: "Search terms — usually a summary of the user's current question" },
        limit: { type: "int", description: "Maximum number of snippets to return (default 5)" }
    },
    required: ["justification", "query"]
};
var sandboxed = false;
var sideEffect = false;

function execute(args, context) {
    var home = (context.config.userHome || "$HOME").replace(/'/g, "'\\''");
    var indexFile = home + "/.local/share/plasmallm/memory/index.json";
    var query = (args.query || "").slice(0, 400);
    var limit = args.limit || 5;
    if (typeof limit !== "number" || limit < 1) limit = 5;
    if (limit > 30) limit = 30;

    var tmpArgs = "/tmp/plasma-recall-args-" + Math.random().toString(36).substring(2, 10) + ".json";
    var tmpPy = "/tmp/plasma-recall-py-" + Math.random().toString(36).substring(2, 10) + ".py";
    var op = { indexFile: indexFile, query: query, limit: limit };
    var writeArgs = "printf '%s' '" + JSON.stringify(op).replace(/'/g, "'\\''") + "' > '" + tmpArgs + "'";

    var py =
        "import json, os, re, sys\n" +
        "op = json.load(open('" + tmpArgs + "'))\n" +
        "idx_path = op['indexFile']\n" +
        "if not os.path.exists(idx_path):\n" +
        "    print('NO_INDEX: run memory_consolidate first')\n" +
        "    sys.exit(0)\n" +
        "kw_re = re.compile(r'[A-Za-zÀ-ÿ]{4,}')\n" +
        "q_tokens = set(t.lower() for t in kw_re.findall(op['query']))\n" +
        "data = json.load(open(idx_path))\n" +
        "snippets = data.get('snippets', [])\n" +
        "scored = []\n" +
        "for s in snippets:\n" +
        "    kws = set(s.get('keywords', []))\n" +
        "    if not kws: continue\n" +
        "    overlap = len(q_tokens & kws)\n" +
        "    if overlap == 0: continue\n" +
        "    scored.append((overlap, s))\n" +
        "scored.sort(key=lambda x: -x[0])\n" +
        "for score, s in scored[:op['limit']]:\n" +
        "    print('[' + str(score) + '] ' + s.get('file','') + ':' + str(s.get('line',0)) + ' (' + s.get('role','') + ')')\n" +
        "    print('  keywords: ' + ', '.join(s.get('keywords', [])))\n" +
        "    print('  ' + s.get('snippet',''))\n" +
        "print('---')\n" +
        "print('matches: ' + str(len(scored)) + ', indexed: ' + str(len(snippets)))\n" +
        "os.remove('" + tmpArgs + "')\n";

    var writePy = "printf '%s' '" + py.replace(/'/g, "'\\''").replace(/\n/g, "\\n") + "' > '" + tmpPy + "'";
    context.exec(writeArgs + " && " + writePy + " && python3 '" + tmpPy + "' && rm -f '" + tmpPy + "'", name, args);
}