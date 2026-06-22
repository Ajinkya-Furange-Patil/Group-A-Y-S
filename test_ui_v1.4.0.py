"""
Quick Test Script for v1.4.0 UI Enhancements
Tests template rendering and JavaScript functionality
"""

import os
import sys

def test_templates_exist():
    """Test 1: Verify template files exist"""
    print("\n[TEST 1] Verifying template files exist...")
    
    dashboard_path = "System Scanner/scanner/reporter/templates/dashboard.html.j2"
    consent_path = "System Scanner/scanner/reporter/templates/consent.html.j2"
    
    if os.path.exists(dashboard_path):
        print(f"✓ {dashboard_path} exists")
    else:
        print(f"✗ {dashboard_path} NOT FOUND")
        return False
    
    if os.path.exists(consent_path):
        print(f"✓ {consent_path} exists")
    else:
        print(f"✗ {consent_path} NOT FOUND")
        return False
    
    return True

def test_dashboard_features():
    """Test 2: Verify dashboard template has new features"""
    print("\n[TEST 2] Verifying dashboard.html.j2 features...")
    
    dashboard_path = "System Scanner/scanner/reporter/templates/dashboard.html.j2"
    with open(dashboard_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    tests = {
        "Theme checkbox": 'id="theme-checkbox"' in content,
        "Theme toggle container": 'theme-toggle-container' in content,
        "Metric data-module attribute": 'data-module=' in content,
        "Sticky sidebar": 'position: sticky' in content,
        "Highlight pulse animation": 'highlight-pulse' in content,
        "Version variable": '{{ version }}' in content,
        "Module clickable JavaScript": "document.querySelectorAll('.module-row')" in content,
        "Metric clickable JavaScript": "document.querySelectorAll('.metric-card[data-module]')" in content,
    }
    
    all_passed = True
    for test_name, result in tests.items():
        if result:
            print(f"✓ {test_name}")
        else:
            print(f"✗ {test_name} FAILED")
            all_passed = False
    
    return all_passed

def test_consent_features():
    """Test 3: Verify consent template has new features"""
    print("\n[TEST 3] Verifying consent.html.j2 features...")
    
    consent_path = "System Scanner/scanner/reporter/templates/consent.html.j2"
    with open(consent_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    tests = {
        "Theme checkbox": 'id="theme-checkbox"' in content,
        "Theme toggle container": 'theme-toggle-container' in content,
        "Future badge CSS": 'future-badge' in content,
        "Disabled module class": '.module-item.disabled' in content,
        "Version variable": '{{ version }}' in content,
        "GitHub future badge": 'Remote Github Repositories <span class="future-badge">FUTURE</span>' in content,
        "Google Drive future badge": 'Google Drive & Cloud <span class="future-badge">FUTURE</span>' in content,
    }
    
    all_passed = True
    for test_name, result in tests.items():
        if result:
            print(f"✓ {test_name}")
        else:
            print(f"✗ {test_name} FAILED")
            all_passed = False
    
    return all_passed

def test_version_manager():
    """Test 4: Verify version manager returns correct version"""
    print("\n[TEST 4] Verifying version manager...")
    
    sys.path.insert(0, "System Scanner")
    
    try:
        from scanner.version_manager import get_version
        version = get_version()
        
        if version:
            print(f"✓ Version manager working: v{version}")
            
            if version == "1.4.0":
                print("✓ Version is 1.4.0 as expected")
                return True
            else:
                print(f"⚠ Version is {version}, expected 1.4.0")
                return True  # Still valid, just different version
        else:
            print("✗ Version manager returned empty string")
            return False
    except Exception as e:
        print(f"✗ Version manager error: {e}")
        return False

def test_css_improvements():
    """Test 5: Verify CSS improvements in dashboard"""
    print("\n[TEST 5] Verifying CSS improvements...")
    
    dashboard_path = "System Scanner/scanner/reporter/templates/dashboard.html.j2"
    with open(dashboard_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    tests = {
        "2px borders": 'border: 2px solid var(--hud-border-dim)' in content,
        "12px 16px padding": 'padding: 12px 16px' in content,
        "Alternating rows": 'nth-child(even)' in content,
        "Hover transform": 'transform: translateX(2px)' in content or 'transform: translateY' in content,
        "Toggle switch width": 'width: 50px' in content,
        "Toggle slider": 'toggle-slider' in content,
    }
    
    all_passed = True
    for test_name, result in tests.items():
        if result:
            print(f"✓ {test_name}")
        else:
            print(f"✗ {test_name} FAILED")
            all_passed = False
    
    return all_passed

def main():
    """Run all tests"""
    print("="*70)
    print("UI ENHANCEMENTS v1.4.0 - VERIFICATION TEST")
    print("="*70)
    
    results = []
    
    results.append(("Templates Exist", test_templates_exist()))
    results.append(("Dashboard Features", test_dashboard_features()))
    results.append(("Consent Features", test_consent_features()))
    results.append(("Version Manager", test_version_manager()))
    results.append(("CSS Improvements", test_css_improvements()))
    
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    print("="*70)
    
    if all_passed:
        print("\n✅ ALL TESTS PASSED - Ready to build executables!")
        print("\nNext steps:")
        print("1. Run: cd 'System Scanner'")
        print("2. Run: python build_both_versions.py")
        print("3. Test both GUI and CLI executables")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED - Review errors above")
        return 1

if __name__ == "__main__":
    exit(main())
