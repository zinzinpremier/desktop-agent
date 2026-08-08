.pragma library

var name = "read_email";
var displayName = "Read Email";
var description = "Read Gmail messages. Supports list, read, and search operations.";
var parameters = {
    type: "object",
    properties: {
        justification: { type: "string", description: "Why you need to read emails" },
        action: { type: "string", description: "Action: 'list', 'read', or 'search'" },
        messageId: { type: "string", description: "Email message ID (for 'read' action)" },
        query: { type: "string", description: "Search query (Gmail syntax) for 'list' or 'search'" },
        maxResults: { type: "string", description: "Max results to return (default: 10)" }
    },
    required: ["justification", "action"]
};
var sandboxed = false;
var sideEffect = false;

function execute(args, context) {
    var action = args.action || "list";
    var scriptPath = context.config.packageRoot + "/contents/scripts/protocols/gmail_agent.py";
    var cmd = "";
    
    if (action === "list" || action === "search") {
        var query = args.query || "";
        var maxResults = args.maxResults || "10";
        cmd = "python3 '" + scriptPath + "' list '" + query + "' '" + maxResults + "'";
    } else if (action === "read") {
        if (!args.messageId) {
            context.error("messageId required for 'read' action");
            return;
        }
        cmd = "python3 '" + scriptPath + "' read '" + args.messageId + "'";
    } else {
        context.error("Unknown action: " + action);
        return;
    }
    
    context.exec(cmd, name, args);
}
