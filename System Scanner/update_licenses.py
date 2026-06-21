import re

with open('scanner/modules/license_scanner.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace LICENSE_TAXONOMY
old_taxonomy = '''LICENSE_TAXONOMY = {
    "MIT": {
        "status": "Approved",
        "risk_level": RiskLevel.INFO,
        "description": "Permissive license. Allowed for enterprise usage.",
        "keywords": [r"\\bmit\\b"]
    },
    "Apache 2.0": {
        "status": "Approved",
        "risk_level": RiskLevel.INFO,
        "description": "Permissive license with patent grants. Allowed for enterprise usage.",
        "keywords": [r"\\bapache\\s*(2\\.0|2)?\\b"]
    },
    "LGPL": {
        "status": "Moderate",
        "risk_level": RiskLevel.MEDIUM,
        "description": "Weak copyleft. Dynamic linking is acceptable, but review is recommended.",
        "keywords": [r"\\blgpl\\b", r"\\blesser\\s+gpl\\b"]
    },
    "GPL": {
        "status": "Review / Banned",
        "risk_level": RiskLevel.HIGH,
        "description": "Strong copyleft. Restricts distribution and proprietary links. Flagged for legal review.",
        "keywords": [r"\\bgpl\\b", r"\\bgeneral\\s+public\\s+license\\b"]
    },
    "AGPL": {
        "status": "Review / Banned",
        "risk_level": RiskLevel.CRITICAL,
        "description": "Affero GPL. Restrictive network-triggered copyleft. Strictly flagged/banned in enterprise contexts.",
        "keywords": [r"\\bagpl\\b", r"\\baffero\\b"]
    },
    "Polyform Shield": {
        "status": "Review / Banned",
        "risk_level": RiskLevel.HIGH,
        "description": "Non-commercial restrictive license. Excludes commercial SaaS usage.",
        "keywords": [r"\\bpolyform\\s+shield\\b", r"\\bpolyform\\b"]
    },
    "Proprietary": {
        "status": "Review / Banned",
        "risk_level": RiskLevel.MEDIUM,
        "description": "Custom proprietary terms. Requires legal approval.",
        "keywords": [r"\\bproprietary\\b", r"\\ball\\s+rights\\s+reserved\\b", r"\\bconfidential\\b"]
    }
}'''

new_taxonomy = '''LICENSE_TAXONOMY = {
    "MIT": {
        "provider": "Massachusetts Institute of Technology",
        "status": "Approved",
        "risk_level": RiskLevel.INFO,
        "description": "Permissive license. Allowed for enterprise usage.",
        "keywords": [r"\\bmit\\b"]
    },
    "Apache 2.0": {
        "provider": "Apache Software Foundation",
        "status": "Approved",
        "risk_level": RiskLevel.INFO,
        "description": "Permissive license with patent grants. Allowed for enterprise usage.",
        "keywords": [r"\\bapache\\s*(2\\.0|2)?\\b"]
    },
    "LGPL": {
        "provider": "Free Software Foundation",
        "status": "Moderate",
        "risk_level": RiskLevel.MEDIUM,
        "description": "Weak copyleft. Dynamic linking is acceptable, but review is recommended.",
        "keywords": [r"\\blgpl\\b", r"\\blesser\\s+gpl\\b"]
    },
    "GPL": {
        "provider": "Free Software Foundation",
        "status": "Review / Banned",
        "risk_level": RiskLevel.HIGH,
        "description": "Strong copyleft. Restricts distribution and proprietary links. Flagged for legal review.",
        "keywords": [r"\\bgpl\\b", r"\\bgeneral\\s+public\\s+license\\b"]
    },
    "AGPL": {
        "provider": "Free Software Foundation",
        "status": "Review / Banned",
        "risk_level": RiskLevel.CRITICAL,
        "description": "Affero GPL. Restrictive network-triggered copyleft. Strictly flagged/banned in enterprise contexts.",
        "keywords": [r"\\bagpl\\b", r"\\baffero\\b"]
    },
    "Polyform Shield": {
        "provider": "Polyform Project",
        "status": "Review / Banned",
        "risk_level": RiskLevel.HIGH,
        "description": "Non-commercial restrictive license. Excludes commercial SaaS usage.",
        "keywords": [r"\\bpolyform\\s+shield\\b", r"\\bpolyform\\b"]
    },
    "Proprietary": {
        "provider": "Commercial Entity",
        "status": "Review / Banned",
        "risk_level": RiskLevel.MEDIUM,
        "description": "Custom proprietary terms. Requires legal approval.",
        "keywords": [r"\\bproprietary\\b", r"\\ball\\s+rights\\s+reserved\\b", r"\\bconfidential\\b"]
    }
}'''

text = text.replace(old_taxonomy, new_taxonomy)

# We also need to add "license_provider" to the finding details where appropriate
# Let's search for the finding creation.
# AST Import analyzer
old_import_finding = '''"license_type": lic_type,'''
new_import_finding = '''"license_type": lic_type,
                            "license_provider": LICENSE_TAXONOMY.get(lic_type, {}).get("provider", "Unknown"),'''
text = text.replace(old_import_finding, new_import_finding)

# Docstring analyzer
old_doc_finding = '''"license_type": found_license,'''
new_doc_finding = '''"license_type": found_license,
                                "license_provider": LICENSE_TAXONOMY[found_license]["provider"],'''
text = text.replace(old_doc_finding, new_doc_finding)

# LICENSE file analyzer
old_file_finding = '''"license_type": lic_name,'''
new_file_finding = '''"license_type": lic_name,
                        "license_provider": lic_info["provider"],'''
text = text.replace(old_file_finding, new_file_finding)

with open('scanner/modules/license_scanner.py', 'w', encoding='utf-8') as f:
    f.write(text)

print('Updated license_scanner.py successfully!')
