/*
    SPDX-FileCopyrightText: 2026 Joshua Roman
    SPDX-License-Identifier: GPL-2.0-or-later
*/

.pragma library

var name = "read_conversation";
var displayName = "Read SMS Conversation";
var description = "Read messages from an SMS conversation thread via KDE Connect. Get thread IDs from list_conversations.";
var parameters = {
    type: "object",
    properties: {
        justification: { type: "string", description: "A brief 1 sentence justification for why you are trying to run this command." },
        conversation_id: { type: "string", description: "Conversation/thread ID (from list_conversations)" },
        count: { type: "string", description: "Number of messages to read (default: 20)" }
    },
    required: ["justification", "conversation_id"]
};
var sandboxed = false;
var sideEffect = false;

function execute(args, context) {
    var cid = (args.conversation_id || "").replace(/'/g, "'\\''");
    var count = (args.count || "20").replace(/'/g, "'\\''");
    context.exec("bash ~/plasmallm-tools/read_conversation.sh '" + cid + "' '" + count + "'", name, args);
}
