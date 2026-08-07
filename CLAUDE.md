# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PlasmaLLM is a system-aware AI assistant widget for the KDE Plasma 6 desktop. It is a QML/JS Plasma applet (Plasmoid) that integrates LLM providers with system information gathering, web search, shell command execution, and desktop automation. The widget currently supports Ollama, LM Studio, OpenAI, Anthropic Claude, Google Gemini, and any OpenAI-compatible API.

This fork is rebranded as **"Desktop Agent"** (see `package/metadata.json`: `Id: com.john.desktopagent`). It extends the upstream with persistent memory tools, SMS tools, an `AppControl` tool, and a desktop-automation driver stack (Wayland remote-desktop session via D-Bus).

## Commands

There is no build step — QML is interpreted at runtime by `plasmashell`.

```bash
make install-dev   # Symlink package/ into ~/.local/share/plasma/plasmoids/<WIDGET_ID>
make install       # Copy package/ into ~/.local/share/plasma/plasmoids/<WIDGET_ID>
make remove        # Uninstall
make package       # Build PlasmaLLM-<version>.plasmoid (runs translations first)
make package-no-i18n   # Build .plasmoid without compiling translations
make translations  # Compile .po -> .mo files (xgettext + msgfmt)
make check-translations  # Verify no untranslated/fuzzy strings; aborts build on errors
make clean         # Remove built .plasmoid and .mo files
```

After `make install-dev` or edits to QML/JS, restart Plasma: `plasmashell --replace &`. View logs via `journalctl -u plasmashell --follow`.

**Note:** `WIDGET_ID` is now read dynamically from `metadata.json` (`com.john.desktopagent`). Install paths, packaging, and translation domain all use this value.

## Repository Layout

```
package/
  metadata.json                         # Plasmoid identity (Name, Id, Version)
  contents/
    config/
      main.xml                          # KConfigXT schema for Plasmoid.configuration.*
      config.qml                        # ConfigModel: tabs (General, Appearance, etc.)
    ui/
      main.qml                          # PlasmoidItem root, window lifecycle, top-level state
      FullRepresentation.qml            # Main chat UI (chat list, input, approval cards, slash cmds)
      ChatMessage.qml                   # Individual message bubble
      ToolApprovalCard.qml              # Approval UI for non-auto-run tool calls
      ToolResultBlock.qml               # Default console/tool result block
      api.js                            # System prompt builder + thin adapter dispatch
      sessionRunner.js                  # tmux/screen wrapper for persistent shell sessions
      profiles.js                       # JSON-encoded profile list save/load
      toolManager.js                    # Built-in + custom tool registry, schemas, sandboxing
      driverManager.js                  # D-Bus client for the desktop-automation driver
      adapters/
        index.js                        # getAdapter(apiType), getAllPresets()
        openai.js  openai_chat.js  openai_responses.js
        anthropic.js
        gemini.js  gemini_interactions.js
      tools/
        index.js                        # Registers all built-in tools; getTool/getToolConfigUI
        RunCommand.js ReadFile.js WriteFile.js ListDir.js SearchFiles.js
        HttpGet.js HttpRequest.js GetClipboard.js SetClipboard.js Notify.js
        OpenUrl.js WebSearch.js
        AppControl.js GetSMS.js SendSMS.js
        MemoryRead.js MemoryWrite.js MemorySearch.js
        driver/                         # Desktop automation (requires DBus session)
          StartSession.js DesktopGetState.js DesktopSetOperatingContext.js
          DesktopResetContext.js DesktopScroll.js DesktopClick.js
          DesktopInput.js DesktopMoveMouse.js DesktopWindowControl.js DesktopReadSelection.js
        *Config.qml                     # Per-tool configuration UI pages
        TOOLS.md                        # Authoritative tool architecture docs
    locale/                             # .po / .pot translation files
```

## Architecture

### Top-level flow

`main.qml` is a `PlasmoidItem` that owns window-level state and lazy-loads `FullRepresentation.qml`. `FullRepresentation.qml` renders the chat list, manages the input field, instantiates `ChatMessage`/`ToolApprovalCard`/`ToolResultBlock` items, and drives the agent loop. On user submit it calls into `api.js` (system prompt + adapter dispatch) and `toolManager.js` (tool routing and approval gating).

### Provider adapters (`ui/adapters/`)

All providers implement a uniform surface documented at the top of `adapters/index.js`:

```
fetchModels(endpoint, apiKey, callback)
buildTools(options)
buildContentArray(text, attachments)
sendStreaming({endpoint, apiKey, model, messages, temperature, maxTokens,
               tools, onChunk, onComplete}) -> handle
presets: [{name, url}, ...]
```

`api.js` and `main.qml` only ever touch the active adapter through `getAdapter(apiType)`. Add a new provider by writing a new adapter module and adding it to `adapters/index.js` — never put wire-level logic (SSE parsing, request shapes, tool-schema differences) in `api.js` or `FullRepresentation.qml`.

There are currently four adapters:
- `openai.js` (default; OpenAI-compatible Chat Completions)
- `openai_chat.js` / `openai_responses.js` (response-API variants selected via `usesResponsesAPI`)
- `anthropic.js`
- `gemini.js` / `gemini_interactions.js` (legacy vs. interactions API)

`getAllPresets()` flattens presets across adapters with an `apiType` tag so the UI can switch adapters when a preset is picked.

### Tools (`ui/tools/`)

A tool is a `.js` module that exports:

```
name, displayName, description, parameters (JSON Schema),
sandboxed, sideEffect, outputScheme, uiHidden,
execute(args, context)
```

The `context` object passed to `execute` exposes: `config`, `i18n`, `getSecret(key)`, `addDisplayMessage`, `replaceDisplayMessage`, `exec(cmd, name, args)`, `error(msg)`, and an `onDone(stdout, stderr, exitCode, attachmentsJson)` callback.

Registering a tool is a two-step process: (1) add an `.import` line and a `{ module, configUI }` entry in `tools/index.js`, (2) if the tool has per-tool config UI, add a `*Config.qml` file and reference it. Built-in tools with no per-tool config use `configUI: ""`.

Custom (user-defined) tools are stored in `Plasmoid.configuration.customTools` as a JSON array and parsed at runtime by `toolManager.getCustomTools(config)`. `buildCustomScriptTool(scriptDef)` parses `{param}` placeholders from a command template, generates a JSON schema, and wraps execution with optional `pkexec` prefix.

#### Security model (enforced in `toolManager.js`)

- **Enabled vs. Auto-run**: every tool has independent toggles. Non-auto-run tools surface a `ToolApprovalCard` and pause execution until the user clicks Approve. `web_search` is hardcoded auto-run. Auto-mode flags (`sessionAutoMode`, `sessionFullAutoMode`) override per-tool settings for the desktop driver stack.
- **Path sandboxing**: `isPathAllowed(path, whitelist, paths)` checks against `toolsPathWhitelist`. `expandPath`/`contractPath`/`contractAllPaths` translate `~`/`$HOME`/`$XDG_*` to absolute paths and redact them in LLM-facing output.
- **Justification**: most side-effect tools require a `justification` parameter that is shown on the approval card.
- **Size limits**: `toolsReadMaxBytes` (default 200KB), `toolsWriteMaxBytes` (1MB), `toolsHttpMaxBytes` (512KB).
- **uiHidden**: tools that emit their own rich UI via `addDisplayMessage` must set this so the default empty `ToolResultBlock` is not also rendered.

Full architecture and authoring guide: `package/contents/ui/tools/TOOLS.md`.

### Driver / desktop automation (`ui/tools/driver/` + `driverManager.js`)

A separate D-Bus service (`com.joshuaroman.plasmallm.DesktopDriver`) handles Wayland remote-desktop session handshake, screenshots, and input synthesis. `driverManager.js` is a singleton-style state holder (active session token, context UUID, cached open windows) used by `FullRepresentation.qml` and `api.js` to inject driving instructions into the system prompt.

The driver tools only appear in the tool list when `config.enableDesktopAutomation` is true and the D-Bus service answers `NameHasOwner`. Some driver tools (`DesktopClick`, `DesktopInput`, etc.) auto-run automatically when an active session is detected, controlled by `sessionAutoMode`.

### Configuration (`contents/config/`)

`main.xml` is the KConfigXT schema — every `<entry>` becomes a property on `Plasmoid.configuration`. `config.qml` lists the configuration tabs; each tab loads its `config<Name>.qml` page. Adding a new setting requires both a `<entry>` in `main.xml` and a UI control in the relevant config page.

### Translations

User-facing strings use `i18n(...)`. `make translations` extracts strings from `*.qml` and `*.js` under `contents/ui`/`contents/config` via `xgettext` into `locale/plasma_applet_<WIDGET_ID>.pot`, merges into each `.po` with `msgmerge`, and compiles `.mo` files via `msgfmt`. `make check-translations` aborts the build on any untranslated or fuzzy strings.

## Code Style (from `CONTRIBUTING.md`)

- QML/JS dialect: use `var` (not `let`/`const`) and the `function` keyword (not arrow functions).
- Colors come from `Kirigami.Theme`, never hardcoded.
- Import order in QML: Qt → KDE Plasma → P5Support → Kirigami → local JS.
- All new files must carry the SPDX header:
  ```
  /*
      SPDX-FileCopyrightText: 2026 Joshua Roman
      SPDX-License-Identifier: GPL-2.0-or-later
  */
  ```
- Avoid external dependencies; use what's already in Plasma/Qt.
- Branch from `master` as `feature/<description>` or `fix/<description>`. One logical change per PR.

## Branch / State Notes

The working tree currently has uncommitted modifications to many locale files, `FullRepresentation.qml`, `api.js`, `profiles.js`, `toolManager.js`, `tools/SearchFiles.js`, `tools/index.js`, and `metadata.json`. There are also several `.bak` files (`*.js.bak`, `main.xml.bak`, `metadata.json.bak`, `RunCommand.js.bak`) and two stray zip archives at the repo root (`ziBjML0B`, `zigHpbHB`). These are not tracked and should not be edited as the source of truth — they appear to be local edit backups.