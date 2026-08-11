/*
    SPDX-FileCopyrightText: 2026 Joshua Roman
    SPDX-License-Identifier: GPL-2.0-or-later
*/

import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami
import org.kde.plasma.components as PlasmaComponents
import org.kde.plasma.plasma5support as P5Support
import org.kde.plasma.plasmoid


BaseConfigPage {
    id: configPage

    property var availableFonts: Qt.fontFamilies()

    property bool hasMatplotlib: true

    onHasMatplotlibChanged: {
        if (!hasMatplotlib && cfg_latexRenderMode === 2) {
            cfg_latexRenderMode = 1;
            rootItem.triggerCapture();
        }
    }

    P5Support.DataSource {
        id: matplotlibChecker
        engine: "executable"
        connectedSources: ["python3 -c 'import matplotlib'"]
        onNewData: function(source, data) {
            if (data["exit code"] !== undefined) {
                hasMatplotlib = (data["exit code"] === 0);
                disconnectSource(source);
            }
        }
    }

    // Lists PipeWire capture sources for the ASR microphone picker.
    // pw-dump is locale-independent JSON (pactl output is localized).
    P5Support.DataSource {
        id: asrDeviceSource
        engine: "executable"
        connectedSources: []
        onNewData: function(source, data) {
            disconnectSource(source);
            var out = data["stdout"] || "";
            var list = [{ "display": i18n("System default"), "name": "" }];
            var lines = out.split("\n");
            for (var i = 0; i < lines.length; i++) {
                var parts = lines[i].split("\t");
                if (parts.length === 2 && parts[0].length > 0) {
                    list.push({ "display": parts[1], "name": parts[0] });
                }
            }
            asrDeviceCombo.devices = list;
            asrDeviceCombo.setCurrentFromConfig();
        }
    }

    // Lists installed Piper voices for the TTS voice picker
    P5Support.DataSource {
        id: ttsVoiceSource
        engine: "executable"
        connectedSources: []
        onNewData: function(source, data) {
            disconnectSource(source);
            var out = (data["stdout"] || "").trim();
            if (!out) return;
            ttsVoiceCombo.voices = out.split("\n");
            ttsVoiceCombo.setCurrentFromConfig();
        }
    }

    // Fire-and-forget voice preview playback
    P5Support.DataSource {
        id: ttsPreviewSource
        engine: "executable"
        connectedSources: []
        onNewData: function(source, data) { disconnectSource(source); }
    }

    // ASR Test result capture
    P5Support.DataSource {
        id: asrTestSource
        engine: "executable"
        connectedSources: []
        onNewData: function(source, data) {
            if (data["exit code"] === 0) {
                var output = data["stdout"] || "";
                if (output.trim()) {
                    testAsrResult.text = output.trim();
                }
            } else {
                testAsrResult.text = "Test failed with exit code: " + data["exit code"];
            }
            testAsrButton.enabled = true;
            disconnectSource(source);
        }
    }

    Kirigami.FormLayout {
        QQC2.CheckBox {
            Kirigami.FormData.label: i18n("Profile Header:")
            text: i18n("Show provider and model in profile header")
            checked: cfg_showProviderInTitle
            onCheckedChanged: {
                if (_initialized) {
                    cfg_showProviderInTitle = checked;
                    rootItem.triggerCapture();
                }
            }
        }

        Kirigami.Separator {
            Kirigami.FormData.isSection: true
            Layout.fillWidth: true
        }

        ColumnLayout {
            Kirigami.FormData.label: i18n("Chat Spacing: %1px", Math.round(chatSpacingSlider.value))
            Layout.fillWidth: true
            spacing: Kirigami.Units.smallSpacing

            QQC2.Slider {
                id: chatSpacingSlider
                Layout.fillWidth: true
                from: 0
                to: 24
                stepSize: 1
                value: cfg_chatSpacing
                onValueChanged: {
                    if (_initialized) {
                        cfg_chatSpacing = value;
                        rootItem.triggerCapture();
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                QQC2.Label {
                    text: i18n("Compact")
                    font: Kirigami.Theme.smallFont
                }
                Item { Layout.fillWidth: true }
                QQC2.Label {
                    text: i18n("Spacious")
                    font: Kirigami.Theme.smallFont
                }
            }
        }

        Kirigami.Separator {
            Kirigami.FormData.isSection: true
            Layout.fillWidth: true
        }

        Item {
            Kirigami.FormData.label: i18n("Chat Labels:")
            Layout.fillWidth: true
        }

        PlasmaComponents.TextField {
            id: userNameField
            Kirigami.FormData.label: i18n("User label:")
            Layout.fillWidth: true
            text: cfg_userName
            placeholderText: i18n("You")
            onTextChanged: {
                if (_initialized) {
                    cfg_userName = text;
                    rootItem.triggerCapture();
                }
            }
        }

        PlasmaComponents.TextField {
            id: assistantNameField
            Kirigami.FormData.label: i18n("Assistant label:")
            Layout.fillWidth: true
            text: cfg_assistantName
            placeholderText: i18n("Assistant")
            enabled: !cfg_showModelNameAsAssistant
            onTextChanged: {
                if (_initialized) {
                    cfg_assistantName = text;
                    rootItem.triggerCapture();
                }
            }
        }

        QQC2.CheckBox {
            id: showModelNameAsAssistantCheck
            text: i18n("Use model name as assistant label")
            checked: cfg_showModelNameAsAssistant
            onCheckedChanged: {
                if (_initialized) {
                    cfg_showModelNameAsAssistant = checked;
                    rootItem.triggerCapture();
                }
            }
        }

        Kirigami.Separator {
            Kirigami.FormData.isSection: true
            Layout.fillWidth: true
        }

        Item {
            Kirigami.FormData.label: i18n("Chat Colors:")
            Layout.fillWidth: true
        }

        RowLayout {
            Layout.fillWidth: true
            QQC2.CheckBox {
                text: i18n("Use custom user color")
                checked: cfg_useCustomUserColor
                onCheckedChanged: {
                    if (_initialized) {
                        cfg_useCustomUserColor = checked;
                        rootItem.triggerCapture();
                    }
                }
            }
            ColorButton {
                enabled: cfg_useCustomUserColor
                color: cfg_userColor
                onAccepted: color => {
                    if (_initialized) {
                        cfg_userColor = color;
                        rootItem.triggerCapture();
                    }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            QQC2.CheckBox {
                text: i18n("Use custom assistant color")
                checked: cfg_useCustomAssistantColor
                onCheckedChanged: {
                    if (_initialized) {
                        cfg_useCustomAssistantColor = checked;
                        rootItem.triggerCapture();
                    }
                }
            }
            ColorButton {
                enabled: cfg_useCustomAssistantColor
                color: cfg_assistantColor
                onAccepted: color => {
                    if (_initialized) {
                        cfg_assistantColor = color;
                        rootItem.triggerCapture();
                    }
                }
            }
        }

        Kirigami.Separator {
            Kirigami.FormData.isSection: true
            Layout.fillWidth: true
        }

        QQC2.CheckBox {
            Kirigami.FormData.label: i18n("UI Font:")
            text: i18n("Use custom UI font")
            checked: cfg_useCustomFont
            onCheckedChanged: {
                if (_initialized) {
                    cfg_useCustomFont = checked;
                    rootItem.triggerCapture();
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            visible: cfg_useCustomFont

            QQC2.ComboBox {
                Layout.fillWidth: true
                model: availableFonts
                currentIndex: availableFonts.indexOf(cfg_customFontFamily) >= 0 ? availableFonts.indexOf(cfg_customFontFamily) : availableFonts.indexOf(Kirigami.Theme.defaultFont.family)
                onActivated: function(index) {
                    if (_initialized) {
                        cfg_customFontFamily = availableFonts[index];
                        rootItem.triggerCapture();
                    }
                }
                Component.onCompleted: {
                    if (cfg_customFontFamily === "") {
                        cfg_customFontFamily = Kirigami.Theme.defaultFont.family
                    }
                }
            }

            QQC2.SpinBox {
                from: 6
                to: 72
                value: cfg_customFontSize
                onValueModified: {
                    if (_initialized) {
                        cfg_customFontSize = value;
                        rootItem.triggerCapture();
                    }
                }
            }
        }

        Kirigami.Separator {
            Kirigami.FormData.isSection: true
            Layout.fillWidth: true
        }

        QQC2.CheckBox {
            Kirigami.FormData.label: i18n("Code Font:")
            text: i18n("Use custom code font")
            checked: cfg_useCustomCodeFont
            onCheckedChanged: {
                if (_initialized) {
                    cfg_useCustomCodeFont = checked;
                    rootItem.triggerCapture();
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            visible: cfg_useCustomCodeFont

            QQC2.ComboBox {
                Layout.fillWidth: true
                model: availableFonts
                currentIndex: availableFonts.indexOf(cfg_customCodeFontFamily) >= 0 ? availableFonts.indexOf(cfg_customCodeFontFamily) : availableFonts.indexOf("monospace")
                onActivated: function(index) {
                    if (_initialized) {
                        cfg_customCodeFontFamily = availableFonts[index];
                        rootItem.triggerCapture();
                    }
                }
            }

            QQC2.SpinBox {
                from: 6
                to: 72
                value: cfg_customCodeFontSize
                onValueModified: {
                    if (_initialized) {
                        cfg_customCodeFontSize = value;
                        rootItem.triggerCapture();
                    }
                }
            }
        }

        Kirigami.Separator {
            Kirigami.FormData.isSection: true
            Layout.fillWidth: true
        }

        QQC2.CheckBox {
            Kirigami.FormData.label: i18n("Thoughts Font:")
            text: i18n("Use custom thoughts font")
            checked: cfg_useCustomThoughtsFont
            onCheckedChanged: {
                if (_initialized) {
                    cfg_useCustomThoughtsFont = checked;
                    rootItem.triggerCapture();
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            visible: cfg_useCustomThoughtsFont

            QQC2.ComboBox {
                Layout.fillWidth: true
                model: availableFonts
                currentIndex: availableFonts.indexOf(cfg_customThoughtsFontFamily) >= 0 ? availableFonts.indexOf(cfg_customThoughtsFontFamily) : availableFonts.indexOf(Kirigami.Theme.smallFont.family)
                onActivated: function(index) {
                    if (_initialized) {
                        cfg_customThoughtsFontFamily = availableFonts[index];
                        rootItem.triggerCapture();
                    }
                }
                Component.onCompleted: {
                    if (cfg_customThoughtsFontFamily === "") {
                        cfg_customThoughtsFontFamily = Kirigami.Theme.smallFont.family
                    }
                }
            }

            QQC2.SpinBox {
                from: 6
                to: 72
                value: cfg_customThoughtsFontSize
                onValueModified: {
                    if (_initialized) {
                        cfg_customThoughtsFontSize = value;
                        rootItem.triggerCapture();
                    }
                }
            }
        }

        Kirigami.Separator {
            Kirigami.FormData.isSection: true
            Layout.fillWidth: true
        }

        Item {
            Kirigami.FormData.label: i18n("LaTeX Rendering:")
            Layout.fillWidth: true
        }

        QQC2.ComboBox {
            id: latexRenderModeCombo
            Layout.fillWidth: true
            model: [
                i18n("Leave as TeX"),
                i18n("Replace with Unicode (Default)"),
                configPage.hasMatplotlib ? i18n("Mathtext") : i18n("Mathtext (python3-matplotlib missing)")
            ]
            currentIndex: cfg_latexRenderMode === -1 ? (configPage.hasMatplotlib ? 2 : 1) : cfg_latexRenderMode
            onActivated: function(index) {
                if (_initialized) {
                    cfg_latexRenderMode = index;
                    rootItem.triggerCapture();
                }
            }
            delegate: QQC2.ItemDelegate {
                width: latexRenderModeCombo.width
                text: modelData
                enabled: index !== 2 || configPage.hasMatplotlib
                highlighted: latexRenderModeCombo.highlightedIndex === index
            }
        }

        Kirigami.Separator {
            Kirigami.FormData.isSection: true
            Layout.fillWidth: true
        }

        Item {
            Kirigami.FormData.label: i18n("Header Icons:")
            Layout.fillWidth: true
        }

        QQC2.CheckBox {
            text: i18n("Profile Header")
            checked: cfg_showIconProfile
            onCheckedChanged: {
                if (_initialized) {
                    cfg_showIconProfile = checked;
                    rootItem.triggerCapture();
                }
            }
        }

        QQC2.CheckBox {
            text: i18n("Always show Tasks")
            checked: cfg_showIconTasks
            onCheckedChanged: {
                if (_initialized) {
                    cfg_showIconTasks = checked;
                    rootItem.triggerCapture();
                }
            }
        }

        QQC2.CheckBox {
            text: i18n("Always show Auto Toggle")
            checked: cfg_showIconAuto
            onCheckedChanged: {
                if (_initialized) {
                    cfg_showIconAuto = checked;
                    rootItem.triggerCapture();
                }
            }
        }

        QQC2.CheckBox {
            text: i18n("Show History")
            checked: cfg_showIconHistory
            onCheckedChanged: {
                if (_initialized) {
                    cfg_showIconHistory = checked;
                    rootItem.triggerCapture();
                }
            }
        }

        QQC2.CheckBox {
            text: i18n("Show Copy conversation")
            checked: cfg_showIconCopy
            onCheckedChanged: {
                if (_initialized) {
                    cfg_showIconCopy = checked;
                    rootItem.triggerCapture();
                }
            }
        }

        QQC2.CheckBox {
            text: i18n("Show Clear chat")
            checked: cfg_showIconClear
            onCheckedChanged: {
                if (_initialized) {
                    cfg_showIconClear = checked;
                    rootItem.triggerCapture();
                }
            }
        }

        QQC2.CheckBox {
            text: i18n("Show Settings")
            checked: cfg_showIconSettings
            onCheckedChanged: {
                if (_initialized) {
                    cfg_showIconSettings = checked;
                    rootItem.triggerCapture();
                }
            }
        }

        QQC2.CheckBox {
            text: i18n("Show Pin")
            checked: cfg_showIconPin
            onCheckedChanged: {
                if (_initialized) {
                    cfg_showIconPin = checked;
                    rootItem.triggerCapture();
                }
            }
        }
    Kirigami.Separator {
            Kirigami.FormData.isSection: true
            Layout.fillWidth: true
        }

        QQC2.Label {
            text: i18n("Text-to-Speech (Piper)")
            font.bold: true
            Kirigami.FormData.labelAlignment: Qt.AlignTop
        }

        QQC2.CheckBox {
            id: ttsEnabledCb
            text: i18n("Enable text-to-speech")
            checked: cfg_ttsEnabled
            onCheckedChanged: if (_initialized) cfg_ttsEnabled = checked
        }

        QQC2.CheckBox {
            text: i18n("Auto-read assistant responses")
            checked: cfg_ttsAutoRead
            enabled: cfg_ttsEnabled
            onCheckedChanged: if (_initialized) cfg_ttsAutoRead = checked
        }

        // Mode selection: Cloud (Cloudflare) vs Local (Piper)
        RowLayout {
            Kirigami.FormData.label: i18n("TTS Mode:")
            enabled: cfg_ttsEnabled
            spacing: Kirigami.Units.smallSpacing

            QQC2.RadioButton {
                id: ttsModeCloudRadio
                text: i18n("Cloud (Cloudflare API)")
                checked: !cfg_ttsUseLocal
                onCheckedChanged: {
                    if (_initialized && checked) {
                        cfg_ttsUseLocal = false;
                        rootItem.triggerCapture();
                    }
                }
            }

            QQC2.RadioButton {
                id: ttsModeLocalRadio
                text: i18n("Local (Piper)")
                checked: cfg_ttsUseLocal
                onCheckedChanged: {
                    if (_initialized && checked) {
                        cfg_ttsUseLocal = true;
                        rootItem.triggerCapture();
                    }
                }
            }
        }

        // Cloud TTS settings
        ColumnLayout {
            Layout.fillWidth: true
            visible: cfg_ttsEnabled && !cfg_ttsUseLocal
            spacing: Kirigami.Units.smallSpacing

            QQC2.Label {
                text: i18n("Using Cloudflare TTS API (aura-2 model)")
                font.pixelSize: Kirigami.Theme.smallFont.pixelSize
                opacity: 0.7
                wrapMode: Text.WordWrap
            }

            RowLayout {
                Kirigami.FormData.label: i18n("Voice:")
                QQC2.ComboBox {
                    id: ttsCloudVoiceCombo
                    Layout.fillWidth: true
                    model: [
                        "athena", "andromeda", "apollo", "arcas", "aries",
                        "asteria", "atlas", "celeste", "danu", "desmond",
                        "echo", "emma", "fable", "febe", "fenrir",
                        "gaia", "gemini", "hyperion", "jupiter", "kore",
                        "leda", "liora", "manta", "marcus", "melissa",
                        "mercury", "metis", "minerva", "mira", "nadia",
                        "orion", "percy", "pheme", "rhea", "saga",
                        "selene", "shango", "talon", "thalia", "typhon"
                    ]
                    currentIndex: model.indexOf(cfg_ttsCloudVoice) >= 0 ? model.indexOf(cfg_ttsCloudVoice) : 10
                    onActivated: function(idx) {
                        if (_initialized) cfg_ttsCloudVoice = model[idx];
                    }
                }
            }

            RowLayout {
                Kirigami.FormData.label: i18n("Langue:")
                QQC2.ComboBox {
                    id: ttsLangCombo
                    Layout.fillWidth: true
                    model: ["fr", "en", "de", "es", "it", "pt", "nl", "pl", "ru", "ja", "zh", "ko"]
                    currentIndex: model.indexOf(cfg_ttsLang) >= 0 ? model.indexOf(cfg_ttsLang) : 0
                    onActivated: function(idx) {
                        if (_initialized) cfg_ttsLang = model[idx];
                    }
                }
            }

            QQC2.Label {
                text: i18n("Voices powered by Deepgram Aura-2 via Cloudflare Workers AI")
                font.pixelSize: Kirigami.Theme.smallFont.pixelSize
                opacity: 0.6
            }

            RowLayout {
                Kirigami.FormData.label: i18n("Guig API Key:")
                QQC2.TextField {
                    id: guigApiKeyField
                    Layout.fillWidth: true
                    text: cfg_guigApiKey
                    echoMode: TextInput.Password
                    placeholderText: "911a8b9..."
                    onTextChanged: if (_initialized) cfg_guigApiKey = text
                }
                PlasmaComponents.ToolButton {
                    icon.name: guigApiKeyField.echoMode === TextInput.Password ? "view-visible" : "view-hidden"
                    onClicked: guigApiKeyField.echoMode = guigApiKeyField.echoMode === TextInput.Password ? TextInput.Normal : TextInput.Password
                }
            }

            RowLayout {
                Kirigami.FormData.label: i18n("Guig API URL:")
                QQC2.TextField {
                    Layout.fillWidth: true
                    text: cfg_guigApiUrl
                    placeholderText: "https://api.guig.dev/v1"
                    onTextChanged: if (_initialized) cfg_guigApiUrl = text
                }
            }
        }

        // Local TTS settings (existing Piper config)
        ColumnLayout {
            Layout.fillWidth: true
            visible: cfg_ttsEnabled && cfg_ttsUseLocal
            spacing: Kirigami.Units.smallSpacing

            QQC2.ComboBox {
                id: ttsVoiceCombo
                Layout.fillWidth: true
                property var voices: []
                model: voices
                Component.onCompleted: refreshVoices()
                function refreshVoices() {
                    ttsVoiceSource.connectSource("find $HOME/.local/share/plasmallm/models/piper -name '*.onnx' -printf '%f\\n' 2>/dev/null | sed 's/\\.onnx$//' | sort");
                }
                function setCurrentFromConfig() {
                    var idx = voices.indexOf(cfg_ttsDefaultVoice);
                    currentIndex = idx >= 0 ? idx : 0;
                }
                onActivated: function(idx) { if (_initialized) cfg_ttsDefaultVoice = voices[idx]; }
            }

            PlasmaComponents.ToolButton {
                icon.name: "audio-volume-high"
                Accessible.name: i18n("Preview voice")
                PlasmaComponents.ToolTip.text: Accessible.name
                PlasmaComponents.ToolTip.visible: hovered
                onClicked: {
                    var v = ttsVoiceCombo.voices[ttsVoiceCombo.currentIndex] || cfg_ttsDefaultVoice;
                    var cmd = "bash -c 'export LD_LIBRARY_PATH=\"$HOME/.local/share/plasmallm/lib:${LD_LIBRARY_PATH:-}\"; "
                        + "M=$(find \"$HOME/.local/share/plasmallm/models/piper\" -name \"" + v + ".onnx\" 2>/dev/null | head -1); "
                        + "[ -z \"$M\" ] && exit 1; "
                        + "echo \"Bonjour, voici un aperçu de ma voix.\" | \"$HOME/.local/share/plasmallm/bin/piper\" --model \"$M\" --output_file /tmp/tts-preview.wav 2>/dev/null && "
                        + "(paplay /tmp/tts-preview.wav 2>/dev/null || aplay -q /tmp/tts-preview.wav 2>/dev/null)'";
                    ttsPreviewSource.connectSource(cmd);
                }
            }
        }

        QQC2.Label {
            text: i18n("Browse available voices at rhasspy/piper-voices on HuggingFace. Install with scripts/install_tts.sh.")
            font.pixelSize: Kirigami.Theme.smallFont.pixelSize
            opacity: 0.7
            wrapMode: Text.WordWrap
            Layout.maximumWidth: Kirigami.Units.gridUnit * 30
        }

        RowLayout {
            Kirigami.FormData.label: i18n("Speed:")
            spacing: Kirigami.Units.smallSpacing
            enabled: cfg_ttsEnabled

            QQC2.Slider {
                id: ttsSpeedSlider
                from: 0.5
                to: 2.0
                stepSize: 0.1
                value: cfg_ttsSpeed
                Layout.preferredWidth: Kirigami.Units.gridUnit * 15
                onMoved: if (_initialized) cfg_ttsSpeed = value
            }
            QQC2.Label {
                text: ttsSpeedSlider.value.toFixed(1) + "x"
                Layout.minimumWidth: Kirigami.Units.gridUnit * 4
            }
        }

        QQC2.SpinBox {
            Kirigami.FormData.label: i18n("Max chars to read:")
            from: 50
            to: 10000
            value: cfg_ttsMaxChars
            enabled: cfg_ttsEnabled
            onValueModified: if (_initialized) cfg_ttsMaxChars = value
        }

        QQC2.Label {
            text: i18n("Run scripts/install_tts.sh to download Piper and the default FR + EN voices.")
            font.pixelSize: Kirigami.Theme.smallFont.pixelSize
            opacity: 0.7
            wrapMode: Text.WordWrap
            Layout.maximumWidth: Kirigami.Units.gridUnit * 30
        }

        Kirigami.Separator {
            Kirigami.FormData.isSection: true
            Layout.fillWidth: true
        }

        // Mode selection: Cloud (Cloudflare) vs Local (Whisper.cpp)
        RowLayout {
            Kirigami.FormData.label: i18n("ASR Mode:")
            enabled: cfg_asrEnabled
            spacing: Kirigami.Units.smallSpacing

            QQC2.RadioButton {
                id: asrModeCloudRadio
                text: i18n("Cloud (Cloudflare API)")
                checked: !cfg_asrUseLocal
                onCheckedChanged: {
                    if (_initialized && checked) {
                        cfg_asrUseLocal = false;
                        rootItem.triggerCapture();
                    }
                }
            }

            QQC2.RadioButton {
                id: asrModeLocalRadio
                text: i18n("Local (Whisper.cpp)")
                checked: cfg_asrUseLocal
                onCheckedChanged: {
                    if (_initialized && checked) {
                        cfg_asrUseLocal = true;
                        rootItem.triggerCapture();
                    }
                }
            }
        }

        // Cloud ASR settings
        ColumnLayout {
            Layout.fillWidth: true
            visible: cfg_asrEnabled && !cfg_asrUseLocal
            spacing: Kirigami.Units.smallSpacing

            QQC2.Label {
                text: i18n("Using Cloudflare ASR API (native or OpenAI-compatible endpoint)")
                font.pixelSize: Kirigami.Theme.smallFont.pixelSize
                opacity: 0.7
                wrapMode: Text.WordWrap
            }

            RowLayout {
                Kirigami.FormData.label: i18n("Language:")
                PlasmaComponents.TextField {
                    placeholderText: i18n("auto / fr / en / …")
                    text: cfg_asrLanguage
                    onTextChanged: if (_initialized) cfg_asrLanguage = text
                }
            }

            QQC2.Label {
                text: i18n("Endpoint: %1/audio/transcriptions").arg(cfg_guigApiUrl || "https://api.guig.dev/v1")
                font.pixelSize: Kirigami.Theme.smallFont.pixelSize
                opacity: 0.6
                wrapMode: Text.WrapAnywhere
            }

            // Test ASR Button
            RowLayout {
                Kirigami.FormData.label: i18n("Test ASR:")
                spacing: Kirigami.Units.smallSpacing

                QQC2.Button {
                    id: testAsrButton
                    text: i18n("Test with sample audio")
                    icon.name: "media-playback-start"
                    onClicked: {
                        testAsrResult.text = i18n("Testing...");
                        testAsrButton.enabled = false;
                        
                        var apiKey = cfg_guigApiKey || "911a8b92e3b66b8b36f15d9af5a7f49aba87025accdef28140148fb5f5f247d9";
                        var apiUrl = (cfg_guigApiUrl || "https://api.guig.dev/v1") + "/audio/transcriptions";
                        var lang = cfg_asrLanguage || "fr";
                        var scriptPath = Plasmoid.package.filePath + "/contents/scripts/test_asr_cloud.py";
                        var testAudio = Plasmoid.package.filePath + "/contents/test.mp3";
                        var cmd = "bash -c 'export PLASMALLM_ASR_API_KEY=\"" + apiKey + "\"; export PLASMALLM_ASR_API_URL=\"" + apiUrl + "\"; python3 \"" + scriptPath + "\" \"" + testAudio + "\" \"" + lang + "\"'";
                        asrTestSource.connectSource(cmd);
                    }
                }

                QQC2.Label {
                    text: i18n("(uses test.mp3 from package)")
                    font.pixelSize: Kirigami.Theme.smallFont.pixelSize
                    opacity: 0.6
                }
            }

            QQC2.TextArea {
                id: testAsrResult
                Layout.fillWidth: true
                readOnly: true
                placeholderText: i18n("Transcription result will appear here...")
                text: ""
                font.family: "monospace"
                font.pixelSize: Kirigami.Theme.smallFont.pixelSize
                background: Rectangle {
                    color: Kirigami.ColorUtils.tintWithAlpha(Kirigami.Theme.backgroundColor, Kirigami.Theme.textColor, 0.05)
                    radius: Kirigami.Units.smallSpacing
                }
            }
        }

        // Local ASR settings (existing Whisper.cpp config)
        ColumnLayout {
            Layout.fillWidth: true
            visible: cfg_asrEnabled && cfg_asrUseLocal
            spacing: Kirigami.Units.smallSpacing

        QQC2.Label {
            text: i18n("Speech-to-Text (whisper.cpp)")
            font.bold: true
            Kirigami.FormData.labelAlignment: Qt.AlignTop
        }

        RowLayout {
            Kirigami.FormData.label: i18n("Model:")
            QQC2.ComboBox {
                id: asrModelCombo
                model: ["tiny", "base", "small", "medium"]
                currentIndex: Math.max(0, model.indexOf(cfg_asrModel))
                onActivated: if (_initialized) cfg_asrModel = currentText
            }
            QQC2.Label {
                text: i18n("(tiny=75 MB, base=140 MB, small=460 MB, medium=1.5 GB)")
                opacity: 0.6
                font.pixelSize: Kirigami.Theme.smallFont.pixelSize
            }
        }

        // Local ASR settings continued (Microphone, Hotkey, Duration)
        RowLayout {
            Kirigami.FormData.label: i18n("Microphone:")
            visible: cfg_asrEnabled && cfg_asrUseLocal
            QQC2.ComboBox {
                id: asrDeviceCombo
                Layout.fillWidth: true
                property var devices: [{ "display": i18n("System default"), "name": "" }]
                model: devices
                textRole: "display"
                Component.onCompleted: refreshDevices()
                function refreshDevices() {
                    asrDeviceSource.connectSource("pw-dump 2>/dev/null | python3 -c \"import json,sys; d=json.load(sys.stdin); [print(o['info']['props'].get('node.name','')+'\\t'+o['info']['props'].get('node.description','')) for o in d if o.get('info',{}).get('props',{}).get('media.class')=='Audio/Source']\"");
                }
                function setCurrentFromConfig() {
                    for (var i = 0; i < devices.length; i++) {
                        if (devices[i].name === cfg_asrDevice) { currentIndex = i; return; }
                    }
                    currentIndex = 0;
                }
                onActivated: function(idx) { if (_initialized) cfg_asrDevice = devices[idx].name; }
            }
            PlasmaComponents.ToolButton {
                icon.name: "view-refresh"
                Accessible.name: i18n("Refresh device list")
                onClicked: asrDeviceCombo.refreshDevices()
            }
        }

        PlasmaComponents.TextField {
            Kirigami.FormData.label: i18n("Global hotkey:")
            placeholderText: i18n("Meta+Shift+Space")
            text: cfg_asrGlobalHotkey
            enabled: cfg_asrEnabled
            visible: cfg_asrEnabled && cfg_asrUseLocal
            onTextChanged: if (_initialized) cfg_asrGlobalHotkey = text
        }

        QQC2.SpinBox {
            Kirigami.FormData.label: i18n("Max recording (sec):")
            from: 5
            to: 600
            value: cfg_asrMaxDurationSec
            enabled: cfg_asrEnabled
            visible: cfg_asrEnabled && cfg_asrUseLocal
            onValueModified: if (_initialized) cfg_asrMaxDurationSec = value
        }

        QQC2.Label {
            text: cfg_asrUseLocal ? i18n("Run scripts/install_asr.sh to build whisper.cpp, download the base model, and install the systemd --user service. The global hotkey works from anywhere in Plasma.") : i18n("Cloudflare ASR API is ready to use. No local installation required. Just ensure DNS propagation is complete for api.guig.dev.")
            font.pixelSize: Kirigami.Theme.smallFont.pixelSize
            opacity: 0.7
            wrapMode: Text.WordWrap
            Layout.maximumWidth: Kirigami.Units.gridUnit * 30
        }
    }
}
}
