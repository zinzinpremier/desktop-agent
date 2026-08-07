/*
    SPDX-FileCopyrightText: 2026 Joshua Roman
    SPDX-License-Identifier: GPL-2.0-or-later
*/

.pragma library

var name = "send_sms_by_name";
var displayName = "Send SMS by Name";
var description = "Send an SMS to a contact by (partial) name — resolves the number via KDE Connect contacts. Combo: contact_lookup to verify, then send.";
var parameters = {
    type: "object",
    properties: {
        justification: { type: "string", description: "A brief 1 sentence justification for why you are trying to run this command." },
        contact: { type: "string", description: "Contact name (partial match ok)" },
        message: { type: "string", description: "SMS text to send" }
    },
    required: ["justification", "contact", "message"]
};
var sandboxed = false;
var sideEffect = true;

function execute(args, context) {
    var contact = (args.contact || "").replace(/'/g, "'\\''");
    var msg = (args.message || "").replace(/'/g, "'\\''");
    context.exec("bash ~/plasmallm-tools/send_to.sh '" + contact + "' '" + msg + "'", name, args);
}
