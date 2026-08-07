.pragma library

var name = "mcp_memory_search";
var displayName = "Memory Search";
var description = "Search for information in persistent memory using a keyword query.";
var parameters = {
    type: "object",
    properties: {
        justification: { type: "string", description: "A brief 1 sentence justification for why you are trying to run this command." },
        query: { type: "string", description: "The keyword or phrase to search for" }
    },
    required: ["justification", "query"]
};
var sandboxed = false;
var sideEffect = false;

function execute(args, context) {
    var query = (args.query || "").replace(/'/g, "'\\''");
    var cmd = "bash ~/plasmallm-tools/mcp_memory.sh search '" + query + "'";
    context.exec(cmd, name, args);
}
