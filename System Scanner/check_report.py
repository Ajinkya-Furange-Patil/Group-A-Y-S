import json

data = json.load(open('test_report.json'))
print(f'Total findings: {len(data["findings"])}')
print(f'Module count: {len(data["modules"])}')
print('\nModule status:')
for m in data['modules']:
    print(f'  {m["name"]:20s}: {m["status"]:10s} - {m["findings_count"]} findings')

print('\nProcessScanner details:')
process_module = next((m for m in data['modules'] if m['name'] == 'ProcessScanner'), None)
if process_module:
    print(f'  Status: {process_module["status"]}')
    print(f'  Duration: {process_module["duration_sec"]:.3f}s')
    print(f'  Findings: {process_module["findings_count"]}')
    if process_module.get('error_message'):
        print(f'  Error: {process_module["error_message"]}')
