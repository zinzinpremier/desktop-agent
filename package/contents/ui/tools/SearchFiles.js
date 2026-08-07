/*
    SPDX-FileCopyrightText: 2026 Joshua Roman
    SPDX-License-Identifier: GPL-2.0-or-later
*/

.pragma library

var name = "search_files";
var displayName = "Search Files";
var description = "Search for a pattern within files in a directory (recursive). Heavy, binary, and VCS directories are skipped. Output is truncated to 300 matches / 64 KiB. Max 204800 bytes per file.";
var longDescription = "Search for a pattern within files in a directory (recursive). Heavy, binary, and VCS directories are skipped. Output is truncated to 300 matches / 64 KiB. Max 204800 bytes per file.";
var parameters = {
    type: "object",
    properties: {
        justification: { type: "string", description: "A brief 1 sentence justification for why you are trying to run this command." },
        path: { type: "string", description: "Absolute path to the directory to search in" },
        pattern: { type: "string", description: "The regex pattern to search for" }
    },
    required: ["justification", "path", "pattern"]
};
var sandboxed = true;
var sideEffect = false;
var outputScheme = "console style";

// Safety constants
var SEARCH_TIMEOUT_SECONDS = 30;
var MAX_MATCHES_PER_FILE = 50;
var MAX_TOTAL_MATCHES = 300;
var MAX_OUTPUT_BYTES = 65536;

// Directories that should never be searched (heavy I/O, binary, or irrelevant)
var EXCLUDED_DIRS = [
    ".git", ".svn", ".hg",
    "node_modules", "__pycache__", ".cache", ".npm", ".yarn",
    ".local/share/Trash", ".local/share/baloo",
    ".gradle", ".m2", ".cargo", ".rustup",
    "venv", ".venv", "env",
    ".docker", ".containerd",
    "snap"
];

// File extensions to skip (binary / compiled / media)
var EXCLUDED_EXTENSIONS = [
    ".mo", ".pyc", ".pyo", ".class", ".o", ".so", ".a", ".dylib",
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".ico", ".svg",
    ".mp3", ".mp4", ".mkv", ".avi", ".mov", ".wav", ".flac", ".ogg",
    ".zip", ".tar", ".gz", ".bz2", ".xz", ".7z", ".rar",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".sqlite", ".db", ".woff", ".woff2", ".ttf", ".otf", ".eot",
    ".plasmoid", ".jar", ".war"
];

function execute(args, context) {
    var path = args.path.replace(/'/g, "'\\''");
    var pattern = args.pattern.replace(/'/g, "'\\''");

    // Build exclusion flags for grep
    var excludeFlags = " --binary-files=without-match";

    // Exclude heavy directories
    for (var i = 0; i < EXCLUDED_DIRS.length; i++) {
        excludeFlags += " --exclude-dir='" + EXCLUDED_DIRS[i].replace(/'/g, "'\\''") + "'";
    }

    // Exclude binary/media file types
    for (var j = 0; j < EXCLUDED_EXTENSIONS.length; j++) {
        excludeFlags += " --exclude='*" + EXCLUDED_EXTENSIONS[j] + "'";
    }

    // Build the command with all safety guards.
    // `set -o pipefail` makes the pipeline exit with the timeout (124) exit code
    // when grep hits the timeout, so the warning below actually fires.
    var cmd =
        "set -o pipefail; " +
        "timeout " + SEARCH_TIMEOUT_SECONDS + " " +
        "grep -rn" +
        excludeFlags +
        " --max-count=" + MAX_MATCHES_PER_FILE +
        " -- '" + pattern + "' '" + path + "' " +
        "2>/dev/null | head -n " + MAX_TOTAL_MATCHES + " | head -c " + MAX_OUTPUT_BYTES +
        "; if [ $? -eq 124 ]; then echo '[search_files: timed out after " + SEARCH_TIMEOUT_SECONDS + "s - try a more specific path or pattern]'; fi";

    context.exec(cmd, name, args);
}
