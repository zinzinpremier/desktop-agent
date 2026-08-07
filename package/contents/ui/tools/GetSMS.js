.pragma library

var name = "get_recent_sms";
var displayName = "Get SMS";
var description = "Display the N most recent received/sent SMS via KDE Connect.";
var parameters = {
    type: "object",
    properties: {
        justification: { type: "string", description: "A brief 1 sentence justification for why you are trying to run this command." },
        count: { type: "string", description: "Number of SMS to retrieve (default: 10)" }
    },
    required: ["justification"]
};
var sandboxed = false;
var sideEffect = false;

function execute(args, context) {
    var count = (args.count || "10").replace(/'/g, "'\\''");
    var cmd = "bash ~/plasmallm-tools/get_recent_sms.sh '" + count + "'";
    context.exec(cmd, name, args);
}
