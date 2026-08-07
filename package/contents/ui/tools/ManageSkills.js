/*
    SPDX-FileCopyrightText: 2026 Joshua Roman
    SPDX-License-Identifier: GPL-2.0-or-later
*/

.pragma library

var name = "manage_skills";
var displayName = "Manage Skills";
var description = "List, create, show, or delete reusable skills (markdown prompt fragments with YAML frontmatter). Skills live in ~/.local/share/plasmallm/skills/ and are auto-injected into the system prompt when their name appears in the activeSkills config. Use action='list' | 'create' | 'show' | 'delete'.";
var parameters = {
    type: "object",
    properties: {
        justification: { type: "string", description: "A brief 1 sentence justification for why you are running this command." },
        action: { type: "string", enum: ["list", "create", "show", "delete"], description: "What to do" },
        name: { type: "string", description: "Skill name (used as filename without .md)" },
        content: { type: "string", description: "Full markdown content (with YAML frontmatter) for create" }
    },
    required: ["justification", "action"]
};
var sandboxed = false;
var sideEffect = true;

function execute(args, context) {
    var home = (context.config.userHome || "$HOME").replace(/'/g, "'\\''");
    var skillsDir = home + "/.local/share/plasmallm/skills";
    var action = args.action || "list";
    var cmd;

    if (action === "list") {
        cmd = "ls -1 '" + skillsDir + "'/*.md 2>/dev/null | xargs -I {} basename {} .md";
    } else if (action === "show") {
        if (!args.name) { context.error(context.i18n("name required for show")); return; }
        var safeName = args.name.replace(/[^A-Za-z0-9_-]/g, "");
        cmd = "cat '" + skillsDir + "/" + safeName + ".md' 2>/dev/null";
    } else if (action === "create") {
        if (!args.name || !args.content) {
            context.error(context.i18n("name and content required for create"));
            return;
        }
        var safeNameC = args.name.replace(/[^A-Za-z0-9_-]/g, "");
        // Write content via temp file to avoid quoting issues with arbitrary markdown
        var tmpFile = "/tmp/plasma-skill-" + Math.random().toString(36).substring(2, 10) + ".md";
        var writeCmd = "mkdir -p '" + skillsDir + "' && printf '%s' '" +
                        args.content.replace(/'/g, "'\\''") + "' > '" + tmpFile + "'";
        cmd = writeCmd + " && mv '" + tmpFile + "' '" + skillsDir + "/" + safeNameC + ".md'";
    } else if (action === "delete") {
        if (!args.name) { context.error(context.i18n("name required for delete")); return; }
        var safeNameD = args.name.replace(/[^A-Za-z0-9_-]/g, "");
        cmd = "rm -f '" + skillsDir + "/" + safeNameD + ".md'";
    } else {
        context.error(context.i18n("Unknown action: %1", action));
        return;
    }

    context.exec(cmd, name, args);
}