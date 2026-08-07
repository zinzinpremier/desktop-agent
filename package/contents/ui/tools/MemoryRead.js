.pragma library

var name = "mcp_memory_read";
var displayName = "Memory Read";
var description = "Read information stored in persistent memory for a specific topic.";
var parameters = {
    type: "object",
    properties: {
        justification: { type: "string", description: "A brief 1 sentence justification for why you are trying to run this command." },
        topic: { type: "string", description: "The topic to read from memory" }
    },
    required: ["justification", "topic"]
};
var sandboxed = false;
var sideEffect = false;

function execute(args, context) {
    var topic = (args.topic || "").replace(/'/g, "'\\''");
    var cmd = "bash ~/plasmallm-tools/mcp_memory.sh read '" + topic + "'";
    context.exec(cmd, name, args);
}
