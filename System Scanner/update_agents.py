import sys
import re

with open('scanner/modules/system_scanner.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update _scan_copilot_registry to _scan_agent_registry
text = text.replace('def _scan_copilot_registry() -> list[dict[str, Any]]:', 'def _scan_agent_registry() -> list[dict[str, Any]]:')
text = text.replace('copilot_entries = _scan_copilot_registry()', 'agent_entries = _scan_agent_registry()')

old_subkey_check = 'if "microsoft.copilot" in subkey.lower() or "copilot" in subkey.lower():'
new_subkey_check = 'if any(kw in subkey.lower() for kw in ("copilot", "antigravity", "codex", "kiro")):'
text = text.replace(old_subkey_check, new_subkey_check)

old_staged_check = 'if "microsoft.copilot" in subkey.lower():'
new_staged_check = 'if any(kw in subkey.lower() for kw in ("copilot", "antigravity", "codex", "kiro")):'
text = text.replace(old_staged_check, new_staged_check)

caller_old_regex = re.compile(r'        agent_entries = _scan_agent_registry\(\)\n        if copilot_entries:.*?(?=\n\n        module_info\.status = "success")', re.DOTALL)
caller_old_regex2 = re.compile(r'        agent_entries = _scan_agent_registry\(\)\n        if agent_entries:.*?(?=\n\n        module_info\.status = "success")', re.DOTALL)

caller_new = '''        agent_entries = _scan_agent_registry()
        if agent_entries:
            agents = {"Copilot": [], "Antigravity": [], "Codex": [], "Kiro": []}
            for e in agent_entries:
                val = str(e).lower()
                if "antigravity" in val: agents["Antigravity"].append(e)
                elif "codex" in val: agents["Codex"].append(e)
                elif "kiro" in val: agents["Kiro"].append(e)
                else: agents["Copilot"].append(e)

            for agent_name, entries in agents.items():
                if not entries: continue
                all_disabled = all("disabled" in e.get("interpretation", "").lower() for e in entries)
                risk = RiskLevel.INFO if all_disabled else RiskLevel.HIGH
                finding = Finding(
                    module_name=MODULE_NAME,
                    title=f"{agent_name} Agent — Registry Configuration Detected",
                    description=f"{agent_name} registry entries were found on this system. This indicates it is installed or its AppX package is registered.",
                    source="registry:AppXStore",
                    category=FindingCategory.AI_AGENT,
                    risk_level=risk,
                    confidence=0.95,
                    details={
                        "registry_entries": entries,
                        "entry_count": len(entries),
                        f"{agent_name.lower()}_disabled_by_policy": all_disabled,
                    },
                )
                findings.append(finding)
                logger.info("SystemScanner: %s finding added (risk=%s, entries=%d)", agent_name, risk, len(entries))'''

if caller_old_regex.search(text):
    text = caller_old_regex.sub(caller_new, text)
elif caller_old_regex2.search(text):
    pass
else:
    # Let's do a more robust replacement
    start_str = "        agent_entries = _scan_agent_registry()"
    end_str = "module_info.status = \"success\""
    start_idx = text.find(start_str)
    end_idx = text.find(end_str, start_idx)
    if start_idx != -1 and end_idx != -1:
        text = text[:start_idx] + caller_new + "\n\n        " + text[end_idx:]

text = text.replace('Microsoft Copilot AppX package is registered', 'AI Agent AppX package is registered')
text = text.replace('Microsoft Copilot AppX package is STAGED', 'AI Agent AppX package is STAGED')

with open('scanner/modules/system_scanner.py', 'w', encoding='utf-8') as f:
    f.write(text)

print('system_scanner.py updated successfully!')
