/*
    SPDX-FileCopyrightText: 2026 Joshua Roman
    SPDX-License-Identifier: GPL-2.0-or-later
*/

import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami
import org.kde.plasma.components as PlasmaComponents

Kirigami.OverlaySheet {
    id: statsSheet
    title: i18n("System Status")

    property var watcherObservations: []
    property var activeGoals: []
    property var availableSkills: []
    property var activeSkillNames: []
    property int activeSkillsCount: 0
    property int chatCount: 0
    property int toolCallsThisSession: 0

    signal toggleSkillRequested(string name, bool active)

    contentItem: ColumnLayout {
        spacing: Kirigami.Units.largeSpacing

        Section {
            title: i18n("Live observations")
            emptyText: i18n("No concerns right now.")
            model: statsSheet.watcherObservations
            emptyVisible: statsSheet.watcherObservations.length === 0
            rowHeight: Kirigami.Units.gridUnit * 1.2
            rowDelegate: observationDelegate
        }

        Kirigami.Separator { Layout.fillWidth: true }

        Section {
            title: i18n("Skills")
            emptyText: i18n("No skills installed. Add .md files in ~/.local/share/plasmallm/skills/ to enable them.")
            model: statsSheet.availableSkills
            emptyVisible: statsSheet.availableSkills.length === 0
            rowHeight: Kirigami.Units.gridUnit * 1.8
            rowDelegate: skillDelegate
        }

        Kirigami.Separator { Layout.fillWidth: true }

        Section {
            title: i18n("Active goals")
            emptyText: i18n("No active goals. Use the manage_goals tool to set one.")
            model: statsSheet.activeGoals
            emptyVisible: statsSheet.activeGoals.length === 0
            rowHeight: Kirigami.Units.gridUnit * 1.6
            rowDelegate: goalDelegate
        }

        Kirigami.Separator { Layout.fillWidth: true }

        RowLayout {
            Layout.fillWidth: true
            spacing: Kirigami.Units.largeSpacing

            Counter { label: i18n("Saved chats"); value: statsSheet.chatCount }
            Counter { label: i18n("Tool calls this session"); value: statsSheet.toolCallsThisSession }
            Counter { label: i18n("Active skills"); value: statsSheet.activeSkillsCount }
            Item { Layout.fillWidth: true }
        }
    }

    // Reusable section: title + (list OR empty label)
    component Section: ColumnLayout {
        property string title: ""
        property string emptyText: ""
        property bool emptyVisible: false
        property var model: []
        property real rowHeight: Kirigami.Units.gridUnit * 1.4
        property Component rowDelegate: null

        Layout.fillWidth: true
        spacing: Kirigami.Units.smallSpacing

        QQC2.Label {
            text: title
            font.bold: true
            opacity: 0.85
        }

        ListView {
            Layout.fillWidth: true
            Layout.preferredHeight: Math.min(model.length * rowHeight, Kirigami.Units.gridUnit * 8)
            clip: true
            spacing: 2
            model: parent.model
            delegate: parent.rowDelegate
        }

        QQC2.Label {
            visible: emptyVisible
            text: emptyText
            opacity: 0.5
            font.italic: true
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }
    }

    // Inline delegate for watcher observations
    Component {
        id: observationDelegate
        QQC2.ItemDelegate {
            required property var modelData
            width: ListView.view.width
            icon.name: modelData.severity === "critical" ? "data-error"
                        : modelData.severity === "warn" ? "data-warning"
                        : "information"
            contentItem: Label {
                text: modelData.text
                wrapMode: Text.WordWrap
                opacity: 0.85
            }
        }
    }

    // Inline delegate for skills — checkbox + name + description
    Component {
        id: skillDelegate
        QQC2.ItemDelegate {
            required property var modelData
            width: ListView.view.width
            contentItem: RowLayout {
                spacing: Kirigami.Units.smallSpacing
                QQC2.CheckBox {
                    checked: statsSheet.activeSkillNames.indexOf(modelData.name) !== -1
                    onToggled: statsSheet.toggleSkillRequested(modelData.name, checked)
                    Accessible.name: modelData.name
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 0
                    QQC2.Label {
                        text: modelData.name
                        font.bold: true
                        Layout.fillWidth: true
                        elide: Text.ElideRight
                    }
                    QQC2.Label {
                        text: modelData.description || ""
                        opacity: 0.6
                        font.pixelSize: Kirigami.Theme.smallFont.pixelSize
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                        maximumLineCount: 2
                        elide: Text.ElideRight
                    }
                }
            }
        }
    }

    // Inline delegate for goals
    Component {
        id: goalDelegate
        QQC2.ItemDelegate {
            required property var modelData
            width: ListView.view.width
            contentItem: ColumnLayout {
                QQC2.Label {
                    text: modelData.title
                    font.bold: true
                    Layout.fillWidth: true
                    elide: Text.ElideRight
                }
                QQC2.Label {
                    text: i18n("Priority %1 · %2", modelData.priority, modelData.state)
                    opacity: 0.6
                    font.pixelSize: Kirigami.Theme.smallFont.pixelSize
                }
            }
        }
    }

    // Small counter tile (label + big number)
    component Counter: ColumnLayout {
        property string label: ""
        property int value: 0

        QQC2.Label {
            text: parent.label
            font.pixelSize: Kirigami.Theme.smallFont.pixelSize
            opacity: 0.6
        }
        QQC2.Label {
            text: parent.value
            font.bold: true
            font.pixelSize: Kirigami.Theme.defaultFont.pixelSize * 1.5
        }
    }
}
