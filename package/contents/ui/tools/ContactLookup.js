/*
    SPDX-FileCopyrightText: 2026 Joshua Roman
    SPDX-License-Identifier: GPL-2.0-or-later
*/

.pragma library

var name = "contact_lookup";
var displayName = "Contact Lookup";
var description = "Find a contact's phone number by (partial) name, or identify who a phone number belongs to, via KDE Connect synced contacts.";
var parameters = {
    type: "object",
    properties: {
        justification: { type: "string", description: "A brief 1 sentence justification for why you are trying to run this command." },
        query: { type: "string", description: "Contact name (partial match ok) or phone number to identify" }
    },
    required: ["justification", "query"]
};
var sandboxed = false;
var sideEffect = false;

function execute(args, context) {
    var q = (args.query || "").replace(/'/g, "'\\''");
    context.exec("bash ~/plasmallm-tools/identify_contact.sh '" + q + "'", name, args);
}
