/*
    SPDX-FileCopyrightText: 2026 Joshua Roman
    SPDX-License-Identifier: GPL-2.0-or-later
*/

// Proactive watcher — runs at a configurable interval, collects lightweight
// system stats, and surfaces conditions that warrant attention.
//
// The widget kicks this off via a Timer; the watcher returns a list of
// "observations" that the agent can react to when the user next asks, or
// that can be displayed as a Plasma notification if severe enough.

.pragma library

var POLL_INTERVAL_MS = 30000;  // 30s
var MAX_OBSERVATIONS = 20;

var _lastPoll = 0;
var _recentObservations = [];

function observations() {
    return _recentObservations;
}

function clearObservations() {
    _recentObservations = [];
}

// Returns a shell command that emits a single line of <key>=<value> pairs.
// The output is parsed by handlePollOutput.
function buildPollCommand(userHome) {
    var home = (userHome || "$HOME").replace(/'/g, "'\\''");
    return "echo \"DISK_USED_PCT=$(df -P / | tail -1 | awk '{print $5}' | tr -d '%')\" && " +
           "echo \"MEM_AVAIL_MB=$(free -m | awk '/^Mem:/ {print $7}')\" && " +
           "echo \"LOAD=$(cat /proc/loadavg | awk '{print $1}')\" && " +
           "echo \"BATTERY=$(cat /sys/class/power_supply/BAT0/capacity 2>/dev/null || cat /sys/class/power_supply/BAT1/capacity 2>/dev/null || echo unknown)\" && " +
           "echo \"BATTERY_STATUS=$(cat /sys/class/power_supply/BAT0/status 2>/dev/null || echo unknown)\" && " +
           "echo \"UPTIME=$(uptime -p 2>/dev/null || uptime)\" && " +
           "echo \"PACKAGE_UPDATES=$(command -v apt >/dev/null && apt list --upgradable 2>/dev/null | grep -c upgradable || echo 0)\" && " +
           "echo \"HOME_SIZE_MB=$(du -sm " + home + " 2>/dev/null | awk '{print $1}' || echo 0)\"";
}

function handlePollOutput(stdout) {
    var stats = {};
    var lines = stdout.split("\n");
    for (var i = 0; i < lines.length; i++) {
        var m = lines[i].match(/^([A-Z_]+)=(.*)$/);
        if (m) stats[m[1]] = m[2];
    }

    var now = Date.now();
    if (now - _lastPoll < 5000) return []; // throttle
    _lastPoll = now;

    var obs = [];

    // Low disk
    var diskPct = parseInt(stats.DISK_USED_PCT) || 0;
    if (diskPct >= 95) {
        obs.push({ severity: "critical", text: "Disk " + diskPct + "% full — investigate or clean up." });
    } else if (diskPct >= 85) {
        obs.push({ severity: "warn", text: "Disk " + diskPct + "% full." });
    }

    // Low memory
    var memAvail = parseInt(stats.MEM_AVAIL_MB) || 0;
    if (memAvail > 0 && memAvail < 200) {
        obs.push({ severity: "warn", text: "Only " + memAvail + " MB RAM available." });
    }

    // Load average
    var load = parseFloat(stats.LOAD) || 0;
    if (load > 4) {
        obs.push({ severity: "info", text: "Load average " + load + " — system is busy." });
    }

    // Battery low
    var batt = parseInt(stats.BATTERY) || -1;
    var battStatus = stats.BATTERY_STATUS || "unknown";
    if (batt >= 0 && batt <= 15 && battStatus === "Discharging") {
        obs.push({ severity: "warn", text: "Battery at " + batt + "% — consider plugging in." });
    }

    // Package updates
    var updates = parseInt(stats.PACKAGE_UPDATES) || 0;
    if (updates >= 5) {
        obs.push({ severity: "info", text: updates + " package updates available." });
    }

    // Push and rotate
    for (var j = 0; j < obs.length; j++) {
        _recentObservations.push(obs[j]);
    }
    while (_recentObservations.length > MAX_OBSERVATIONS) {
        _recentObservations.shift();
    }

    return obs;
}