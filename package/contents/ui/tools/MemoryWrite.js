.pragma library

var name = "mcp_memory_write";
var displayName = "Memory Write";
var description = "Store information in persistent memory using topic||info format. Use || to separate the topic from the info.";
var parameters = {
    type: "object",
    properties: {
        justification: { type: "string", description: "A brief 1 sentence justification for why you are trying to run this command." },
        topic: { type: "string", description: "The topic name" },
        info: { type: "string", description: "The information to store" }
    },
    required: ["justification", "topic", "info"]
};
var sandboxed = false;
var sideEffect = true;

function execute(args, context) {
    var topic = (args.topic || "").replace(/'/g, "'\\''");
    var info = (args.info || "").replace(/'/g, "'\\''");
    var cmd = "bash ~/plasmallm-tools/mcp_memory.sh write '" + topic + "||" + info + "'";
    context.exec(cmd, name, args);
}
