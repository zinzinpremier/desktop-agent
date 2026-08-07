/*
    SPDX-FileCopyrightText: 2026 Joshua Roman
    SPDX-License-Identifier: GPL-2.0-or-later
*/

.pragma library

var name = "list_conversations";
var displayName = "List SMS Conversations";
var description = "List all SMS conversations (threads) via KDE Connect. Pair with read_conversation to read a thread, and contact_lookup to resolve names.";
var parameters = {
    type: "object",
    properties: {
        justification: { type: "string", description: "A brief 1 sentence justification for why you are trying to run this command." }
    },
    required: ["justification"]
};
var sandboxed = false;
var sideEffect = false;

function execute(args, context) {
    context.exec("bash ~/plasmallm-tools/list_conversations.sh", name, args);
}
