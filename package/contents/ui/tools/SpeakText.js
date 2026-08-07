/*
    SPDX-FileCopyrightText: 2026 Joshua Roman
    SPDX-License-Identifier: GPL-2.0-or-later
*/

.pragma library

var name = "speak_text";
var displayName = "Speak Text";
var description = "Read a piece of text aloud using the local Piper TTS engine. Useful for when the user wants something read out, e.g. 'lis le contenu de ce fichier' or 'dis-moi le résumé'. Truncates to ttsMaxChars (default 1000) characters.";
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

    var homeDir = (context.config.userHome || "$HOME").replace(/'/g, "'\\''");
    var piperBin = homeDir + "/.local/share/plasmallm/bin/piper";
    var voiceName = (context.config.ttsDefaultVoice || "fr_FR-upmc-medium").replace(/'/g, "'\\''");
    var speed = parseFloat(context.config.ttsSpeed) || 1.0;
    var lengthScale = (1.0 / speed).toFixed(3);

    // Write the text to a temp file, then have the shell read it. This is the
    // only safe way to pass arbitrary user-supplied text to a shell command —
    // never inline untrusted text into a command string.
    var tmpTxt = "/tmp/plasma-tts-" + Math.random().toString(36).substring(2, 10) + ".txt";
    var escapedText = text.replace(/'/g, "'\\''");
    var writeCmd = "mkdir -p /tmp && printf '%s' '" + escapedText + "' > '" + tmpTxt + "'";

    // Build the synthesis+play command. Text is read from the temp file, not
    // interpolated, so it cannot break out of the shell. The variable list
    // contains only paths and the user-configured voice name.
    var cmd = "bash -c '"
            + "PIPER=\"" + piperBin + "\"; "
            + "VOICE_BASE=\"" + homeDir + "/.local/share/plasmallm/models/piper\"; "
            + "VOICE=\"$(find \"$VOICE_BASE\" -name \"" + voiceName + ".onnx\" 2>/dev/null | head -1)\"; "
            + "TXT=\"" + tmpTxt + "\"; "
            + "if [ ! -x \"$PIPER\" ]; then echo \"TTS_NOT_INSTALLED\" >&2; exit 1; fi; "
            + "if [ -z \"$VOICE\" ]; then echo \"VOICE_NOT_FOUND:" + voiceName + "\" >&2; exit 1; fi; "
            + "if [ ! -s \"$TXT\" ]; then echo \"EMPTY_TEXT\" >&2; exit 1; fi; "
            + "WAV=$(mktemp --suffix=.wav); "
            + "\"$PIPER\" --model \"$VOICE\" --length_scale " + lengthScale + " --output_file \"$WAV\" < \"$TXT\" 2>/dev/null; "
            + "if [ $? -ne 0 ] || [ ! -s \"$WAV\" ]; then echo \"PIPER_FAILED\" >&2; rm -f \"$WAV\"; exit 1; fi; "
            + "paplay \"$WAV\" 2>/dev/null || aplay -q \"$WAV\" 2>/dev/null || mpv --no-terminal --no-video \"$WAV\" 2>/dev/null || echo \"NO_AUDIO_PLAYER\" >&2; "
            + "rm -f \"$WAV\" \"$TXT\""
            + "'";

    context.exec(writeCmd + " && " + cmd, name, args);
}
