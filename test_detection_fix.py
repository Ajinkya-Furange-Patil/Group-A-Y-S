"""
Quick test to verify AI agent detection improvements.
Tests if Kiro, Codex, Antigravity, and Copilot agents can be detected.
"""
import sys
import os

# Add the System Scanner directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "System Scanner"))

from scanner.modules import process_scanner

print("=" * 70)
print("Testing AI Agent Detection Improvements")
print("=" * 70)
print()

print("Testing AI_DAEMON_NAMES dictionary...")
print(f"Total daemon names: {len(process_scanner.AI_DAEMON_NAMES)}")
print()

# Test for new entries
test_agents = [
    "kiro.exe",
    "kiro-server.exe",
    "codex.exe",
    "codex-server.exe",
    "antigravity.exe",
    "antigravity-daemon.exe",
    "copilot.exe",
]

print("Checking for new AI agent signatures:")
for agent in test_agents:
    if agent in process_scanner.AI_DAEMON_NAMES:
        print(f"  ✓ {agent:30s} -> {process_scanner.AI_DAEMON_NAMES[agent]}")
    else:
        print(f"  ✗ {agent:30s} -> NOT FOUND")
print()

print("Testing AI_DAEMON_PREFIXES tuple...")
print(f"Prefixes: {process_scanner.AI_DAEMON_PREFIXES}")
print()

# Test prefix matching
test_prefixes = ["kiro", "codex", "antigravity", "copilot"]
print("Checking for new prefix patterns:")
for prefix in test_prefixes:
    if prefix in process_scanner.AI_DAEMON_PREFIXES:
        print(f"  ✓ {prefix}")
    else:
        print(f"  ✗ {prefix} -> NOT FOUND")
print()

print("=" * 70)
print("Testing _match_ai_daemon() function...")
print("=" * 70)
print()

# Test the matching function
test_cases = [
    ("kiro.exe", "C:\\Program Files\\Kiro\\kiro.exe"),
    ("kiro-server.exe", "C:\\Users\\App\\kiro-server.exe"),
    ("codex.exe", "/usr/local/bin/codex.exe"),
    ("antigravity.exe", "C:\\Apps\\antigravity.exe"),
    ("copilot.exe", "C:\\Program Files\\GitHub Copilot\\copilot.exe"),
    ("kiro_v2.exe", "C:\\Apps\\kiro_v2.exe"),  # Test prefix matching
    ("notepad.exe", "C:\\Windows\\notepad.exe"),  # Should not match
]

for name, exe in test_cases:
    is_daemon, key, label = process_scanner._match_ai_daemon(name, exe)
    status = "✓ MATCHED" if is_daemon else "✗ NOT MATCHED"
    if is_daemon:
        print(f"{status} - {name:25s} -> {label} (key: {key})")
    else:
        print(f"{status} - {name:25s}")
print()

print("=" * 70)
print("Running actual process scan...")
print("=" * 70)
print()

findings, module_info = process_scanner.run()

print(f"Module Status: {module_info.status}")
print(f"Duration: {module_info.duration_sec:.3f}s")
print(f"Total findings: {module_info.findings_count}")
print()

if findings:
    print("Detected AI processes:")
    for f in findings:
        daemon_status = "[DAEMON]" if f.details.get("is_ai_daemon") else "[RUNTIME]"
        print(f"  {daemon_status} {f.title}")
        print(f"    PID: {f.details.get('pid')}, Risk: {f.risk_level.value}")
        if f.details.get("exe"):
            print(f"    Path: {f.details.get('exe')}")
        print()
else:
    print("No AI processes detected on this system.")
    print("(This is expected if no AI agents are running)")
print()

print("=" * 70)
print("Test Complete!")
print("=" * 70)
