/*
    SPDX-FileCopyrightText: 2026 Joshua Roman
    SPDX-License-Identifier: GPL-2.0-or-later
*/

.pragma library

// In-memory cache of the consolidated memory index. Populated by main.qml when
// memory_consolidate runs, or by reading ~/.local/share/plasmallm/memory/index.json
// at startup. The actual heavy lifting (scanning every chat) happens inside the
// tool — here we just provide a small keyword-scoring helper for digesting.

var STOP = {
    "the":1, "and":1, "that":1, "this":1, "with":1, "from":1, "they":1, "have":1,
    "been":1, "will":1, "what":1, "when":1, "where":1, "your":1, "their":1, "them":1,
    "pour":1, "avec":1, "sans":1, "vous":1, "nous":1, "mais":1, "donc":1, "elle":1,
    "elles":1, "tout":1, "tous":1, "tres":1, "plus":1, "moins":1, "encore":1,
    "alors":1, "comme":1, "because":1, "would":1, "could":1, "should":1, "about":1,
    "into":1, "over":1, "there":1, "these":1, "those":1
};

var TOKEN_RE = /[A-Za-zÀ-ÿ]{4,}/g;

function tokens(text) {
    var out = [];
    if (!text) return out;
    var t;
    while ((t = TOKEN_RE.exec(text)) !== null) {
        var lower = t[0].toLowerCase();
        if (!STOP[lower]) out.push(lower);
    }
    return out;
}

function snippetScore(snippet, queryTokens) {
    if (!snippet || !snippet.keywords) return 0;
    var kws = snippet.keywords;
    var score = 0;
    for (var i = 0; i < queryTokens.length; i++) {
        if (kws.indexOf(queryTokens[i]) !== -1) score++;
    }
    return score;
}

// Build a digest fragment for the system prompt from a list of snippets and a
// current user query. Returns a plain-text block suitable for inclusion in the
// system prompt, or "" if nothing relevant was found.
function buildDigest(snippets, query, limit) {
    if (!Array.isArray(snippets) || snippets.length === 0) return "";
    if (!query) return "";
    if (!limit) limit = 5;
    var qt = tokens(query);
    if (qt.length === 0) return "";
    var scored = [];
    for (var i = 0; i < snippets.length; i++) {
        var s = snippets[i];
        var sc = snippetScore(s, qt);
        if (sc > 0) scored.push({ score: sc, snippet: s });
    }
    if (scored.length === 0) return "";
    scored.sort(function(a, b) { return b.score - a.score; });
    var lines = ["Relevant snippets from past conversations:"];
    for (var k = 0; k < Math.min(limit, scored.length); k++) {
        var it = scored[k];
        var s = it.snippet;
        lines.push("- (" + s.role + " · " + s.file + ":" + s.line + ", " + it.score + " hits)");
        lines.push("  " + (s.snippet || "").replace(/\n/g, " "));
    }
    return lines.join("\n");
}