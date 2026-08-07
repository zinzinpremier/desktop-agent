/*
    SPDX-FileCopyrightText: 2026 Joshua Roman
    SPDX-License-Identifier: GPL-2.0-or-later
*/

import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami
import org.kde.plasma.components as PlasmaComponents

Kirigami.OverlayDrawer {
    id: historyDrawer

    edge: Qt.LeftEdge
    modal: true
    modalPointerEvents: true

    property var historyFilesModel: null
    property bool isFetching: false
    property string searchFilter: ""

    signal loadRequested(string filePath)
    signal deleteRequested(string filePath)
    signal renameRequested(string filePath, string newTitle)
    signal exportRequested(string filePath)
    signal toggleStarRequested(string filePath)
    signal openFolderRequested()
    signal refreshRequested()

    title: i18n("Chat History")
    titleIcon: "clock"

    leftPadding: 0
    rightPadding: 0
    topPadding: 0
    bottomPadding: 0

    contentItem: ColumnLayout {
        implicitWidth: Kirigami.Units.gridUnit * 22
        spacing: 0

        RowLayout {
        Layout.fillWidth: true
        Layout.margins: Kirigami.Units.smallSpacing
        spacing: Kirigami.Units.smallSpacing

        QQC2.TextField {
            id: searchField
            Layout.fillWidth: true
            placeholderText: i18n("Search chats…")
            clearButtonShown: true
            onTextChanged: historyDrawer.searchFilter = text.toLowerCase()
            Keys.onEscapePressed: {
                text = "";
                historyDrawer.close();
            }
        }

        PlasmaComponents.ToolButton {
            icon.name: "folder-open"
            Accessible.name: i18n("Open history folder")
            PlasmaComponents.ToolTip.text: Accessible.name
            PlasmaComponents.ToolTip.visible: hovered
            onClicked: historyDrawer.openFolderRequested()
        }

        PlasmaComponents.ToolButton {
            icon.name: "view-refresh"
            Accessible.name: i18n("Refresh")
            PlasmaComponents.ToolTip.text: Accessible.name
            PlasmaComponents.ToolTip.visible: hovered
            onClicked: historyDrawer.refreshRequested()
        }
    }

        ListView {
        id: chatList
        Layout.fillWidth: true
        Layout.fillHeight: true
        clip: true
        spacing: 0
        model: filterModel

        delegate: QQC2.ItemDelegate {
            id: rowDelegate
            width: ListView.view.width
            height: rowLayout.implicitHeight + Kirigami.Units.smallSpacing * 2

            required property int index
            required property string file
            required property string name
            required property string dateTime
            required property string preview
            required property bool starred

            background: Rectangle {
                color: rowDelegate.hovered ? Kirigami.Theme.hoverColor : "transparent"
                Rectangle {
                    anchors.left: parent.left
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    width: 3
                    visible: rowDelegate.starred
                    color: Kirigami.Theme.highlightColor
                }
            }

            contentItem: ColumnLayout {
                id: rowLayout
                anchors.fill: parent
                anchors.margins: Kirigami.Units.smallSpacing
                spacing: 2

                RowLayout {
                    Layout.fillWidth: true
                    spacing: Kirigami.Units.smallSpacing

                    PlasmaComponents.ToolButton {
                        icon.name: rowDelegate.starred ? "rating" : "rating-unrated"
                        implicitWidth: Kirigami.Units.iconSizes.smallMedium
                        implicitHeight: implicitWidth
                        Accessible.name: rowDelegate.starred ? i18n("Unstar") : i18n("Star")
                        onClicked: historyDrawer.toggleStarRequested(rowDelegate.file)
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 0

                        QQC2.Label {
                            Layout.fillWidth: true
                            text: rowDelegate.name
                            font.bold: true
                            elide: Text.ElideRight
                        }
                        QQC2.Label {
                            Layout.fillWidth: true
                            text: rowDelegate.preview || i18n("(no preview)")
                            opacity: 0.7
                            font.italic: !rowDelegate.preview
                            elide: Text.ElideRight
                            maximumLineCount: 1
                        }
                    }

                    QQC2.Label {
                        text: rowDelegate.dateTime
                        opacity: 0.6
                        font.pixelSize: Kirigami.Theme.smallFont.pixelSize
                    }

                    PlasmaComponents.ToolButton {
                        id: overflowButton
                        icon.name: "overflow-menu"
                        implicitWidth: Kirigami.Units.iconSizes.smallMedium
                        implicitHeight: implicitWidth
                        Accessible.name: i18n("More")
                        onClicked: rowMenu.popup()

                        QQC2.Menu {
                            id: rowMenu
                            QQC2.MenuItem {
                                text: i18n("Open")
                                icon.name: "document-open"
                                onTriggered: historyDrawer.loadRequested(rowDelegate.file)
                            }
                            QQC2.MenuItem {
                                text: i18n("Rename…")
                                icon.name: "edit-rename"
                                onTriggered: {
                                    historyDrawer.renameTargetFile = rowDelegate.file;
                                    historyDrawer.renameOldTitle = rowDelegate.name.replace(/\.jsonl$/, "");
                                    renameField.text = historyDrawer.renameOldTitle;
                                    renamePopup.open();
                                }
                            }
                            QQC2.MenuItem {
                                text: i18n("Export to Markdown")
                                icon.name: "document-export"
                                onTriggered: historyDrawer.exportRequested(rowDelegate.file)
                            }
                            QQC2.MenuSeparator {}
                            QQC2.MenuItem {
                                text: i18n("Delete")
                                icon.name: "edit-delete"
                                onTriggered: {
                                    historyDrawer.deleteTargetFile = rowDelegate.file;
                                    deletePopup.open();
                                }
                            }
                        }
                    }
                }
            }

            onClicked: historyDrawer.loadRequested(rowDelegate.file)
        }

        // Empty / loading / no-results states
        QQC2.Label {
            anchors.centerIn: parent
            visible: historyDrawer.isFetching
            text: i18n("Loading…")
            opacity: 0.7
        }

        QQC2.Label {
            anchors.centerIn: parent
            visible: !historyDrawer.isFetching && chatList.count === 0 && historyDrawer.searchFilter === ""
            text: i18n("No chats yet — start a conversation to fill this list.")
            opacity: 0.6
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
            width: parent.width - Kirigami.Units.largeSpacing * 2
        }

        QQC2.Label {
            anchors.centerIn: parent
            visible: !historyDrawer.isFetching && chatList.count === 0 && historyDrawer.searchFilter !== ""
            text: i18n("No chats match \"%1\".", historyDrawer.searchFilter)
            opacity: 0.6
        }

        ListModel {
            id: filterModel
        }

        function rebuildFilter() {
            filterModel.clear();
            if (!historyDrawer.historyFilesModel) return;
            var src = historyDrawer.historyFilesModel;
            var q = historyDrawer.searchFilter;
            var starred = [];
            var normal = [];
            for (var i = 0; i < src.count; i++) {
                var entry = src.get(i);
                var matchesSearch = !q
                    || (entry.name && entry.name.toLowerCase().indexOf(q) !== -1)
                    || (entry.preview && entry.preview.toLowerCase().indexOf(q) !== -1);
                if (!matchesSearch) continue;
                if (entry.starred) starred.push(entry);
                else normal.push(entry);
            }
            for (var s = 0; s < starred.length; s++) filterModel.append(starred[s]);
            for (var n = 0; n < normal.length; n++) filterModel.append(normal[n]);
        }

        Connections {
            target: historyDrawer
            function onSearchFilterChanged() { chatList.rebuildFilter(); }
            function onHistoryFilesModelChanged() { chatList.rebuildFilter(); }
        }

        Component.onCompleted: rebuildFilter()

        QQC2.ScrollBar.vertical: QQC2.ScrollBar {}
        }
    }

    // Rename popup
    property string renameTargetFile: ""
    property string renameOldTitle: ""

    Kirigami.OverlaySheet {
        id: renamePopup
        anchors.centerIn: parent
        contentItem: ColumnLayout {
            spacing: Kirigami.Units.smallSpacing
            QQC2.TextField {
                id: renameField
                Layout.preferredWidth: Kirigami.Units.gridUnit * 20
                placeholderText: i18n("New title")
            }
            QQC2.Label {
                text: i18n("Use only letters, numbers, spaces, and dashes.")
                opacity: 0.6
                font.pixelSize: Kirigami.Theme.smallFont.pixelSize
            }
        }
        footer: RowLayout {
            Item { Layout.fillWidth: true }
            QQC2.Button {
                text: i18n("Cancel")
                onClicked: renamePopup.close()
            }
            QQC2.Button {
                text: i18n("Rename")
                highlighted: true
                onClicked: {
                    var sanitized = renameField.text.trim()
                        .replace(/\.jsonl$/, "")
                        .replace(/[^A-Za-z0-9 _-]/g, "")
                        .replace(/\s+/g, "-")
                        .replace(/-+/g, "-")
                        .replace(/^-+|-+$/g, "");
                    if (sanitized.length > 0 && sanitized !== historyDrawer.renameOldTitle) {
                        historyDrawer.renameRequested(historyDrawer.renameTargetFile, sanitized);
                    }
                    renamePopup.close();
                }
            }
        }
    }

    // Delete confirmation
    property string deleteTargetFile: ""
    Kirigami.OverlaySheet {
        id: deletePopup
        anchors.centerIn: parent
        contentItem: QQC2.Label {
            text: i18n("This permanently deletes the chat file. This cannot be undone.")
            wrapMode: Text.WordWrap
            Layout.preferredWidth: Kirigami.Units.gridUnit * 20
        }
        footer: RowLayout {
            Item { Layout.fillWidth: true }
            QQC2.Button {
                text: i18n("Cancel")
                onClicked: deletePopup.close()
            }
            QQC2.Button {
                text: i18n("Delete")
                highlighted: true
                onClicked: {
                    historyDrawer.deleteRequested(historyDrawer.deleteTargetFile);
                    deletePopup.close();
                }
            }
        }
    }
}