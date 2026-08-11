/*
    SPDX-FileCopyrightText: 2026 Joshua Roman
    SPDX-License-Identifier: GPL-2.0-or-later
*/

.pragma library

var name = "speak_text";
var displayName = "Speak Text";
var description = "Read a piece of text aloud using Cloudflare TTS API (Aura-2, default) or local Piper TTS engine. Useful for when the user wants something read out, e.g. 'lis le contenu de ce fichier' or 'speak this message'.";
var parameters = {
    type: "object",
    properties: {
        justification: { type: "string", description: "A brief 1 sentence justification for why you are running this command." },
        text: { type: "string", description: "The text to speak aloud" }
    },
    required: ["justification", "text"]
};
var sandboxed = false;
var sideEffect = true;
var outputScheme = "console style";

function execute(args, context) {
    if (!context.config.ttsEnabled) {
        context.error(context.i18n("TTS is disabled. Enable it in Configure Desktop Agent → Appearance → Text-to-Speech."));
        return;
    }

    var text = (args.text || "").substring(0, context.config.ttsMaxChars || 1000);
    if (text.length === 0) {
        context.error(context.i18n("Empty text."));
        return;
    }

    // Check if using cloud mode (default) or local mode
    var useLocal = context.config.ttsUseLocal || false;
    
    if (!useLocal) {
        // Cloud mode: Use Guig AI / Cloudflare TTS API via tts_helper.py
        var homeDir = (context.config.userHome || "$HOME").replace(/'/g, "'\\''");
        // Always run from the plasmoid's own scripts directory — no copy needed
        var ttsScript = context.config.packageFilePath + "/contents/scripts/tts_helper.py";
        var escapedText = text.replace(/'/g, "'\\''");
        
        // Auto-select voice based on language for optimal quality
        var lang = context.config.ttsLang || "fr";
        var cloudVoice = context.config.ttsCloudVoice;
        
        // If no specific voice is set, auto-select based on language
        if (!cloudVoice || cloudVoice === "athena") {
            if (lang.startsWith("fr")) {
                cloudVoice = "apollo";       // French male voice (clear, natural)
            } else if (lang.startsWith("es")) {
                cloudVoice = "artemis";      // Spanish female voice
            } else if (lang.startsWith("de")) {
                cloudVoice = "hebe";         // German female voice
            } else if (lang.startsWith("it")) {
                cloudVoice = "medusa";       // Italian female voice
            } else if (lang.startsWith("pt")) {
                cloudVoice = "iris";         // Portuguese BR female voice
            } else if (lang.startsWith("ja")) {
                cloudVoice = "maia";         // Japanese female voice
            } else {
                cloudVoice = "athena";       // Default English US female voice
            }
        }
        
        // Optimized speed for faster response
        var speed = parseFloat(context.config.ttsSpeed) || 1.1;
        var model = context.config.ttsModel || "aura-2";
        var apiKey = context.config.guigApiKey || "911a8b92e3b66b8b36f15d9af5a7f49aba87025accdef28140148fb5f5f247d9";
        var apiBase = context.config.guigApiUrl || "https://api.guig.dev/v1";
        var apiUrl = apiBase + "/audio/speech";
        
        // Write the text to a temp file for safe shell handling
        var tmpTxt = "/tmp/plasma-tts-" + Math.random().toString(36).substring(2, 10) + ".txt";
        var writeCmd = "mkdir -p /tmp && printf '%s' '" + escapedText + "' > '" + tmpTxt + "'";
        
        // Build command with environment variables passed directly - no binary copy needed
        var cmd = "bash -c '";
        cmd += "export PLASMALLM_TTS_API_KEY=\"" + apiKey.replace(/"/g, '\\"') + "\"; ";
        cmd += "export PLASMALLM_TTS_API_URL=\"" + apiUrl + "\"; ";
        cmd += "export PLASMALLM_TTS_MODE=\"cloud\"; ";
        cmd += "export PLASMALLM_TTS_VOICE=\"" + cloudVoice + "\"; ";
        cmd += "export PLASMALLM_TTS_LANG=\"" + lang + "\"; ";
        cmd += "export PLASMALLM_TTS_MODEL=\"" + model + "\"; ";
        cmd += "export PLASMALLM_TTS_SPEED=\"" + speed + "\"; ";
        cmd += "python3 \"" + ttsScript + "\" \"$(cat \"" + tmpTxt + "\")\"'; ";
        cmd += "rm -f '" + tmpTxt + "'";
        
        context.exec(writeCmd + " && " + cmd, name, args);
    } else {
        // Local mode: Use Piper TTS — tts_helper.py in the plasmoid scripts dir
        var homeDir = (context.config.userHome || "$HOME").replace(/'/g, "'\\''");
        var ttsScript = context.config.packageFilePath + "/contents/scripts/tts_helper.py";
        var voiceName = (context.config.ttsDefaultVoice || "fr_FR-siwis-medium").replace(/'/g, "'\\''");
        var speed = parseFloat(context.config.ttsSpeed) || 1.0;
        var plasmallmHome = homeDir + "/.local/share/plasmallm";

        var tmpTxt = "/tmp/plasma-tts-" + Math.random().toString(36).substring(2, 10) + ".txt";
        var escapedText = text.replace(/'/g, "'\\''");
        var writeCmd = "mkdir -p /tmp && printf '%s' '" + escapedText + "' > '" + tmpTxt + "'";

        var cmd = "bash -c '";
        cmd += "export LD_LIBRARY_PATH=\"" + plasmallmHome + "/lib:${LD_LIBRARY_PATH:-}\"; ";
        cmd += "export PLASMALLM_TTS_MODE=\"local\"; ";
        cmd += "export PLASMALLM_TTS_VOICE=\"" + voiceName + "\"; ";
        cmd += "export PLASMALLM_TTS_SPEED=\"" + speed + "\"; ";
        cmd += "python3 \"" + ttsScript + "\" \"$(cat \"" + tmpTxt + "\")\"'";
        cmd += "; rm -f '" + tmpTxt + "'";

        context.exec(writeCmd + " && " + cmd, name, args);
    }
}
