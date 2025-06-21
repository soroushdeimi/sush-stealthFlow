#!/usr/bin/env python3
"""
Final Repository Validation Script
Validates that all repository URLs are correctly updated
"""

import os
from pathlib import Path
import re

def validate_repository_urls():
    """Validate all repository URLs in the project"""
    
    print("🔍 StealthFlow Repository URL Validation")
    print("=" * 50)
    
    project_root = Path(__file__).parent
    correct_repo = "soroushdeimi/sush-stealthFlow"
    
    # Files to check
    critical_files = [
        "README.md",
        "package.json", 
        "setup.sh",
        "helm/stealthflow/Chart.yaml",
        "helm/stealthflow/values.yaml"
    ]
    
    # Patterns that should exist
    expected_patterns = [
        f"github.com/{correct_repo}",
        f"githubusercontent.com/{correct_repo}",
        "soroushdeimi/sush-stealthFlow"
    ]
    
    # Patterns that should NOT exist  
    forbidden_patterns = [
        "YOUR-USERNAME/stealthflow",
        "YOUR-USERNAME/",
        "github.com/YOUR-USERNAME"
    ]
    
    validation_results = []
    
    for file_path in critical_files:
        full_path = project_root / file_path
        
        if not full_path.exists():
            print(f"⚠️  File not found: {file_path}")
            validation_results.append((file_path, False, "File not found"))
            continue
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for forbidden patterns
            has_forbidden = False
            for pattern in forbidden_patterns:
                if pattern in content:
                    print(f"❌ {file_path}: Found forbidden pattern '{pattern}'")
                    has_forbidden = True
            
            # Check for expected patterns  
            has_expected = False
            for pattern in expected_patterns:
                if pattern in content:
                    has_expected = True
                    break
            
            if has_forbidden:
                validation_results.append((file_path, False, "Contains template URLs"))
                print(f"❌ {file_path}: FAILED - Contains template URLs")
            elif has_expected:
                validation_results.append((file_path, True, "Valid repository URLs"))
                print(f"✅ {file_path}: PASSED - Valid repository URLs")
            else:
                validation_results.append((file_path, True, "No repository URLs found"))
                print(f"ℹ️  {file_path}: No repository URLs found")
                
        except Exception as e:
            print(f"❌ Error checking {file_path}: {e}")
            validation_results.append((file_path, False, str(e)))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, success, _ in validation_results if success)
    total = len(validation_results)
    
    print(f"Files checked: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    
    if passed == total:
        print("\n🎉 ALL VALIDATIONS PASSED!")
        print(f"✅ Repository URLs correctly updated to: {correct_repo}")
        print("\n📝 Quick Start Commands:")
        print(f"Server: curl -sSL https://raw.githubusercontent.com/{correct_repo}/main/setup.sh")
        print(f"Client: git clone https://github.com/{correct_repo}.git")
        print(f"Docker: git clone https://github.com/{correct_repo}.git && cd sush-stealthFlow")
        return True
    else:
        print("\n❌ VALIDATION FAILED!")
        print("Please fix the issues above before proceeding.")
        return False

def check_project_structure():
    """Check if project structure is intact"""
    print("\n🏗️  Project Structure Validation")
    print("=" * 30)
    
    required_files = [
        "README.md",
        "stealthflow.py", 
        "requirements.txt",
        "docker-compose.yml",
        "client/core/stealthflow_client.py",
        "server/scripts/health-server.py",
        "utils/security.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Missing critical files:")
        for file_path in missing_files:
            print(f"  - {file_path}")
        return False
    else:
        print("✅ All critical files present")
        return True

if __name__ == "__main__":
    print("🚀 Starting Final Validation...\n")
    
    structure_ok = check_project_structure()
    urls_ok = validate_repository_urls()
    
    print("\n" + "=" * 60)
    if structure_ok and urls_ok:
        print("🎯 FINAL VALIDATION: ✅ PASSED")
        print("🚀 Project is ready for GitHub deployment!")
        print(f"📁 Repository: https://github.com/soroushdeimi/sush-stealthFlow")
    else:
        print("🎯 FINAL VALIDATION: ❌ FAILED")
        print("❗ Please address the issues above")
    print("=" * 60)
