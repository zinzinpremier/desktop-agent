.pragma library

var name = "app_control";
var displayName = "App Control";
var description = "Check if an application is active and focus its window.";
var parameters = {
    type: "object",
    properties: {
        justification: { type: "string", description: "A brief 1 sentence justification for why you are trying to run this command." },
        app_name: { type: "string", description: "The application name to focus" }
    },
    required: ["justification", "app_name"]
};
var sandboxed = false;
var sideEffect = true;

function execute(args, context) {
    var name = (args.app_name || "").replace(/'/g, "'\\''");
    var cmd = "bash ~/plasmallm-tools/app_control.sh '" + name + "'";
    context.exec(cmd, name, args);
}
