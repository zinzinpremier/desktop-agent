/*
    SPDX-FileCopyrightText: 2026 Joshua Roman
    SPDX-License-Identifier: GPL-2.0-or-later
*/

import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami
import org.kde.plasma.plasma5support as P5Support


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

        QQC2.TextField {
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

        QQC2.TextField {
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

        QQC2.TextField {
            id: ttsVoiceField
            Kirigami.FormData.label: i18n("Default voice:")
            placeholderText: i18n("e.g. fr_FR-upmc-medium")
            text: cfg_ttsDefaultVoice
            enabled: cfg_ttsEnabled
            onTextChanged: if (_initialized) cfg_ttsDefaultVoice = text
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

        QQC2.Label {
            text: i18n("Speech-to-Text (whisper.cpp)")
            font.bold: true
            Kirigami.FormData.labelAlignment: Qt.AlignTop
        }

        QQC2.CheckBox {
            text: i18n("Enable speech-to-text")
            checked: cfg_asrEnabled
            onCheckedChanged: if (_initialized) cfg_asrEnabled = checked
        }

        RowLayout {
            Kirigami.FormData.label: i18n("Model:")
            enabled: cfg_asrEnabled
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

        QQC2.TextField {
            Kirigami.FormData.label: i18n("Language:")
            placeholderText: i18n("auto / fr / en / …")
            text: cfg_asrLanguage
            enabled: cfg_asrEnabled
            onTextChanged: if (_initialized) cfg_asrLanguage = text
        }

        QQC2.TextField {
            Kirigami.FormData.label: i18n("Global hotkey:")
            placeholderText: i18n("Meta+Shift+Space")
            text: cfg_asrGlobalHotkey
            enabled: cfg_asrEnabled
            onTextChanged: if (_initialized) cfg_asrGlobalHotkey = text
        }

        QQC2.SpinBox {
            Kirigami.FormData.label: i18n("Max recording (sec):")
            from: 5
            to: 600
            value: cfg_asrMaxDurationSec
            enabled: cfg_asrEnabled
            onValueModified: if (_initialized) cfg_asrMaxDurationSec = value
        }

        QQC2.Label {
            text: i18n("Run scripts/install_asr.sh to build whisper.cpp, download the base model, and install the systemd --user service. The global hotkey works from anywhere in Plasma.")
            font.pixelSize: Kirigami.Theme.smallFont.pixelSize
            opacity: 0.7
            wrapMode: Text.WordWrap
            Layout.maximumWidth: Kirigami.Units.gridUnit * 30
        }
    }
}
