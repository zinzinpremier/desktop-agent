.pragma library

var name = "send_sms";
var displayName = "Send SMS";
var description = "Send an SMS message via KDE Connect. Use --thread thread_id to reply to a conversation.";
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
    var dest = (args.dest || "").replace(/'/g, "'\\''");
    var msg = (args.message || "").replace(/'/g, "'\\''");
    var cmd = "bash ~/plasmallm-tools/send_sms.sh '" + dest + "' '" + msg + "'";
    context.exec(cmd, name, args);
}
