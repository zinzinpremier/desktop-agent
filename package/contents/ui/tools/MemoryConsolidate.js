/*
    SPDX-FileCopyrightText: 2026 Joshua Roman
    SPDX-License-Identifier: GPL-2.0-or-later
*/

.pragma library

var name = "memory_consolidate";
var displayName = "Memory Consolidate";
var description = "Walk ~/.local/share/plasmallm/chats/*.jsonl, extract keyword-tagged snippets from each chat, and store them in ~/.local/share/plasmallm/memory/index.json so memory_recall can inject relevant past context into future prompts. Idempotent — re-running refreshes the index.";
var parameters = {
    type: "object",
    properties: {
        justification: { type: "string", description: "A brief 1 sentence justification for why you are running this command." },
        maxSnippetsPerChat: { type: "int", description: "Cap snippets per chat file (default 8)" }
    },
    required: ["justification"]
};
var sandboxed = false;
var sideEffect = true;

function execute(args, context) {
    var home = (context.config.userHome || "$HOME").replace(/'/g, "'\\''");
    var chatsDir = home + "/.local/share/plasmallm/chats";
    var memoryDir = home + "/.local/share/plasmallm/memory";
    var indexFile = memoryDir + "/index.json";
    var max = args.maxSnippetsPerChat || 8;
    if (typeof max !== "number" || max < 1) max = 8;
    if (max > 50) max = 50;

    var tmpPy = "/tmp/plasma-mem-py-" + Math.random().toString(36).substring(2, 10) + ".py";
    var tmpArgs = "/tmp/plasma-mem-args-" + Math.random().toString(36).substring(2, 10) + ".json";
    var op = { chatsDir: chatsDir, memoryDir: memoryDir, indexFile: indexFile, maxSnippets: max };
    var writeArgs = "printf '%s' '" + JSON.stringify(op).replace(/'/g, "'\\''") + "' > '" + tmpArgs + "'";

    // The script walks every .jsonl, parses each line as {role, content, ...},
    // and for each user/assistant message extracts:
    //   - keywords: lowercase alphanumeric tokens of length >= 4
    //   - snippet: first 220 chars of the content
    //   - file/line/index so memory_recall can cite back to the chat
    var py =
        "import json, os, re, sys, datetime\n" +
        "op = json.load(open('" + tmpArgs + "'))\n" +
        "chats_dir = op['chatsDir']\n" +
        "memory_dir = op['memoryDir']\n" +
        "idx_path = op['indexFile']\n" +
        "max_per = op['maxSnippets']\n" +
        "os.makedirs(memory_dir, exist_ok=True)\n" +
        "kw_re = re.compile(r'[A-Za-zÀ-ÿ]{4,}')\n" +
        "stop = set(['the','and','that','this','with','from','they','have','been','will','what','when','where','your','their','them','pour','avec','sans','vous','nous','mais','donc','elle','elles','tout','tous','tres','plus','moins','encore','alors','comme','because','would','could','should','about','into','over','there','these','those'])\n" +
        "snippets = []\n" +
        "files = []\n" +
        "if os.path.isdir(chats_dir):\n" +
        "    files = sorted([os.path.join(chats_dir, f) for f in os.listdir(chats_dir) if f.endswith('.jsonl')])\n" +
        "for fp in files:\n" +
        "    per_count = 0\n" +
        "    try:\n" +
        "        with open(fp, 'r', encoding='utf-8', errors='ignore') as fh:\n" +
        "            for line_no, line in enumerate(fh):\n" +
        "                line = line.strip()\n" +
        "                if not line: continue\n" +
        "                try:\n" +
        "                    entry = json.loads(line)\n" +
        "                except Exception:\n" +
        "                    continue\n" +
        "                role = entry.get('role','')\n" +
        "                if role not in ('user','assistant'): continue\n" +
        "                content = (entry.get('content') or '')\n" +
        "                if not isinstance(content, str) or len(content) < 20: continue\n" +
        "                tokens = [t.lower() for t in kw_re.findall(content)]\n" +
        "                kws = [t for t in tokens if t not in stop]\n" +
        "                if len(kws) < 3: continue\n" +
        "                # Cap noise: only top-frequency tokens become keywords.\n" +
        "                counts = {}\n" +
        "                for t in kws:\n" +
        "                    counts[t] = counts.get(t, 0) + 1\n" +
        "                top = sorted(counts.items(), key=lambda kv: -kv[1])[:8]\n" +
        "                keywords = [t for t,_ in top]\n" +
        "                snippet = content[:220].replace('\\n',' ').strip()\n" +
        "                snippets.append({\n" +
        "                    'file': os.path.basename(fp),\n" +
        "                    'line': line_no,\n" +
        "                    'role': role,\n" +
        "                    'keywords': keywords,\n" +
        "                    'snippet': snippet\n" +
        "                })\n" +
        "                per_count += 1\n" +
        "                if per_count >= max_per: break\n" +
        "    except Exception as e:\n" +
        "        print('SKIP', fp, str(e), file=sys.stderr)\n" +
        "out = {'generated': datetime.datetime.now().isoformat(), 'files_indexed': len(files), 'snippets': snippets}\n" +
        "json.dump(out, open(idx_path, 'w'), ensure_ascii=False, indent=2)\n" +
        "print('OK indexed ' + str(len(snippets)) + ' snippets from ' + str(len(files)) + ' files')\n" +
        "os.remove('" + tmpArgs + "')\n";

    var writePy = "printf '%s' '" + py.replace(/'/g, "'\\''").replace(/\n/g, "\\n") + "' > '" + tmpPy + "'";
    context.exec("mkdir -p '" + memoryDir + "' && " + writeArgs + " && " + writePy + " && python3 '" + tmpPy + "' && rm -f '" + tmpPy + "'", name, args);
}