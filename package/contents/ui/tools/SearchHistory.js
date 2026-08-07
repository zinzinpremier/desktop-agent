/*
    SPDX-FileCopyrightText: 2026 Joshua Roman
    SPDX-License-Identifier: GPL-2.0-or-later
*/

.pragma library

var name = "search_history";
var displayName = "Search Past Chats";
var description = "Search your saved chat history for past discussions. Returns the best-matching user messages across all chats so the agent can recall context.";
var parameters = {
    type: "object",
    properties: {
        justification: { type: "string", description: "A brief 1 sentence justification for why you are running this command." },
        query: { type: "string", description: "Keyword or phrase to search for" },
        limit: { type: "int", description: "Max chats to inspect (default 5)" }
    },
    required: ["justification", "query"]
};
var sandboxed = true;
var sideEffect = false;

function execute(args, context) {
    var home = (context.config.userHome || "$HOME").replace(/'/g, "'\\''");
    var chatsDir = home + "/.local/share/plasmallm/chats";
    var query = (args.query || "").replace(/'/g, "'\\''");
    var limit = args.limit || 5;

    var cmd =
        "grep -r -l --include='*.jsonl' -F '" + query + "' '" + chatsDir + "' 2>/dev/null | " +
        "head -n " + limit + " | while read f; do " +
        "  echo \"=== $f ===\"; " +
        "  grep -m 2 -F '" + query + "' \"$f\" | head -c 800; " +
        "  echo; " +
        "done";
    context.exec(cmd, name, args);
}
