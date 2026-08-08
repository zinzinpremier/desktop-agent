.pragma library

var name = "send_sms";
var displayName = "Send SMS";
var description = "Send an SMS message via KDE Connect D-Bus API. Use --thread thread_id to reply to a conversation.";
var parameters = {
    type: "object",
    properties: {
        justification: { type: "string", description: "A brief 1 sentence justification for why you are trying to run this command." },
        dest: { type: "string", description: "Phone number or --thread thread_id" },
        message: { type: "string", description: "The message text to send" }
    },
    required: ["justification", "dest", "message"]
};
var sandboxed = false;
var sideEffect = true;

function execute(args, context) {
    var dest = (args.dest || "");
    var msg = (args.message || "");
    var scriptPath = context.config.packageRoot + "/contents/scripts/sms/kdeconnect_sms.py";
    var cmd = "python3 '" + scriptPath + "' send '" + dest + "' '" + msg.replace(/'/g, "'\\''") + "'";
    context.exec(cmd, name, args);
}
