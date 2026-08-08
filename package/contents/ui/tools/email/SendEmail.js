.pragma library

var name = "send_email";
var displayName = "Send Email";
var description = "Send an email via Gmail API. Supports attachments.";
var parameters = {
    type: "object",
    properties: {
        justification: { type: "string", description: "Why you need to send this email" },
        to: { type: "string", description: "Recipient email address" },
        subject: { type: "string", description: "Email subject line" },
        body: { type: "string", description: "Email body content" },
        attachments: { type: "string", description: "Comma-separated file paths for attachments (optional)" }
    },
    required: ["justification", "to", "subject", "body"]
};
var sandboxed = false;
var sideEffect = true;

function execute(args, context) {
    var scriptPath = context.config.packageRoot + "/contents/scripts/protocols/gmail_agent.py";
    var to = args.to || "";
    var subject = args.subject || "";
    var body = args.body || "";
    var attachments = args.attachments || "";
    
    // Escape single quotes in body
    var escapedBody = body.replace(/'/g, "'\\''");
    var escapedSubject = subject.replace(/'/g, "'\\''");
    
    var cmd = "python3 '" + scriptPath + "' send '" + to + "' '" + escapedSubject + "' '" + escapedBody + "'";
    
    if (attachments) {
        cmd += " '" + attachments + "'";
    }
    
    context.exec(cmd, name, args);
}
