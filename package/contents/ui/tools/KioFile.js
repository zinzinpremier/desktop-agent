/*
    SPDX-FileCopyrightText: 2026 Joshua Roman
    SPDX-License-Identifier: GPL-2.0-or-later
*/

.pragma library

var name = "kio_file";
var displayName = "KIO File Operations";
var description = "File operations over KDE KIO: works on local files AND remote URLs (sftp://, smb://, webdav://, trash:/…). " +
    "Actions: ls (list URL), cat (read file), copy, move, mkdir, remove. " +
    "TIP: to safely delete to the Trash instead of destroying, use action=move with destination 'trash:/'. " +
    "Examples: ls trash:/ | cat sftp://host/path/file.txt | copy file:///a smb://nas/b";
var parameters = {
    type: "object",
    properties: {
        justification: { type: "string", description: "A brief 1 sentence justification for why you are trying to run this command." },
        action: { type: "string", description: "One of: ls, cat, copy, move, mkdir, remove" },
        source: { type: "string", description: "Source URL or path (e.g. trash:/, file:///home/user/x, sftp://host/file)" },
        destination: { type: "string", description: "Destination URL (required for copy/move; use 'trash:/' to send to Trash)" }
    },
    required: ["justification", "action", "source"]
};
var sandboxed = false;
var sideEffect = true;

function execute(args, context) {
    var action = (args.action || "").toLowerCase();
    var valid = ["ls", "cat", "copy", "move", "mkdir", "remove"];
    if (valid.indexOf(action) === -1) {
        context.error("kio_file: invalid action '" + action + "'. Valid: " + valid.join(", "));
        return;
    }
    var src = (args.source || "").replace(/'/g, "'\\''");
    var dst = (args.destination || "").replace(/'/g, "'\\''");
    if (!src) {
        context.error("kio_file: source is required");
        return;
    }
    if ((action === "copy" || action === "move") && !dst) {
        context.error("kio_file: destination is required for copy/move");
        return;
    }

    var cmd = "kioclient5 --noninteractive " + action + " '" + src + "'";
    if (dst) cmd += " '" + dst + "'";
    context.exec(cmd, name, args);
}
