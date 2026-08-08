.pragma library

var name = "get_recent_sms";
var displayName = "Get SMS";
var description = "Display the N most recent received/sent SMS via KDE Connect D-Bus API.";
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
    var count = (args.count || "10");
    var scriptPath = context.config.packageRoot + "/contents/scripts/sms/kdeconnect_sms.py";
    var cmd = "python3 '" + scriptPath + "' received '" + count + "'";
    context.exec(cmd, name, args);
}
