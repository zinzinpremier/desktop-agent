/*
    SPDX-FileCopyrightText: 2026 Joshua Roman
    SPDX-License-Identifier: GPL-2.0-or-later
*/

.pragma library

.import "RunCommand.js" as RunCommand
.import "ReadFile.js" as ReadFile
.import "WriteFile.js" as WriteFile
.import "ListDir.js" as ListDir
.import "SearchFiles.js" as SearchFiles
.import "HttpGet.js" as HttpGet
.import "HttpRequest.js" as HttpRequest
.import "GetClipboard.js" as GetClipboard
.import "SetClipboard.js" as SetClipboard
.import "Notify.js" as Notify
.import "OpenUrl.js" as OpenUrl
.import "WebSearch.js" as WebSearch
.import "SpeakText.js" as SpeakText
.import "ContactLookup.js" as ContactLookup
.import "ListConversations.js" as ListConversations
.import "ReadConversation.js" as ReadConversation
.import "SendSMSByName.js" as SendSMSByName
.import "KioFile.js" as KioFile
.import "ManageSkills.js" as ManageSkills
.import "ManageGoals.js" as ManageGoals
.import "SearchHistory.js" as SearchHistory
.import "AppControl.js" as AppControl
.import "GetSMS.js" as GetSMS
.import "SendSMS.js" as SendSMS
.import "MemoryRead.js" as MemoryRead
.import "MemoryWrite.js" as MemoryWrite
.import "MemorySearch.js" as MemorySearch
.import "MemoryConsolidate.js" as MemoryConsolidate
.import "MemoryRecall.js" as MemoryRecall
.import "ReflexLearn.js" as ReflexLearn

.import "driver/StartSession.js" as StartSession
.import "driver/DesktopGetState.js" as DesktopGetState
.import "driver/DesktopSetOperatingContext.js" as DesktopSetOperatingContext
.import "driver/DesktopResetContext.js" as DesktopResetContext
.import "driver/DesktopScroll.js" as DesktopScroll
.import "driver/DesktopClick.js" as DesktopClick
.import "driver/DesktopInput.js" as DesktopInput
.import "driver/DesktopMoveMouse.js" as DesktopMoveMouse
.import "driver/DesktopWindowControl.js" as DesktopWindowControl
.import "driver/DesktopReadSelection.js" as DesktopReadSelection

var tools = [
    { module: RunCommand, configUI: "tools/RunCommandConfig.qml" },
    { module: WebSearch, configUI: "tools/WebSearchConfig.qml" },
    { module: ReadFile, configUI: "tools/ReadFileConfig.qml" },
    { module: WriteFile, configUI: "tools/WriteFileConfig.qml" },
    { module: ListDir, configUI: "tools/ListDirConfig.qml" },
    { module: SearchFiles, configUI: "tools/SearchFilesConfig.qml" },
    { module: HttpGet, configUI: "tools/HttpGetConfig.qml" },
    { module: HttpRequest, configUI: "tools/HttpRequestConfig.qml" },
    { module: GetClipboard, configUI: "tools/GetClipboardConfig.qml" },
    { module: SetClipboard, configUI: "tools/SetClipboardConfig.qml" },
    { module: Notify, configUI: "tools/NotifyConfig.qml" },
    { module: OpenUrl, configUI: "tools/OpenUrlConfig.qml" },
    { module: SpeakText, configUI: "" },
    { module: ContactLookup, configUI: "" },
    { module: ListConversations, configUI: "" },
    { module: ReadConversation, configUI: "" },
    { module: SendSMSByName, configUI: "" },
    { module: KioFile, configUI: "" },
    { module: ManageSkills, configUI: "" },
    { module: ManageGoals, configUI: "" },
    { module: SearchHistory, configUI: "" },
    { module: AppControl, configUI: "" },
    { module: GetSMS, configUI: "" },
    { module: SendSMS, configUI: "" },
    { module: MemoryRead, configUI: "" },
    { module: MemoryWrite, configUI: "" },
    { module: MemorySearch, configUI: "" },
    { module: MemoryConsolidate, configUI: "" },
    { module: MemoryRecall, configUI: "" },
    { module: ReflexLearn, configUI: "" },
    { module: StartSession, configUI: "" },
    { module: DesktopGetState, configUI: "" },
    { module: DesktopSetOperatingContext, configUI: "" },
    { module: DesktopResetContext, configUI: "" },
    { module: DesktopScroll, configUI: "" },
    { module: DesktopClick, configUI: "" },
    { module: DesktopInput, configUI: "" },
    { module: DesktopMoveMouse, configUI: "" },
    { module: DesktopWindowControl, configUI: "" },
    { module: DesktopReadSelection, configUI: "" }
];

function getTool(name) {
    for (var i = 0; i < tools.length; i++) {
        if (tools[i].module.name === name) return tools[i].module;
    }
    return null;
}

function getToolConfigUI(name) {
    for (var i = 0; i < tools.length; i++) {
        if (tools[i].module.name === name) return tools[i].configUI;
    }
    return "";
}

function getAllTools() {
    var out = [];
    for (var i = 0; i < tools.length; i++) {
        out.push(tools[i].module);
    }
    return out;
}
