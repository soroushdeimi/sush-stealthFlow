#!/usr/bin/env python3
"""
Update Repository URLs Script
Automatically updates all repository URLs to match the actual GitHub repository
"""

import os
import re
from pathlib import Path

def update_repository_urls():
    """Update all repository URLs in the project"""
    
    # Define the repository mapping
    old_repo = "YOUR-USERNAME/stealthflow"
    new_repo = "soroushdeimi/sush-stealthFlow"
    
    old_username = "YOUR-USERNAME"
    new_username = "soroushdeimi"
    
    # Files to update
    files_to_update = [
        "README.md",
        "package.json",
        "setup.sh",
        "helm/stealthflow/Chart.yaml",
        "helm/stealthflow/values.yaml",
        "docs/CLIENT_INSTALL.md",
        "docs/TROUBLESHOOTING.md",
        "docs/FAQ.md"
    ]
    
    # Patterns to replace
    replacements = [
        (f"github.com/{old_repo}", f"github.com/{new_repo}"),
        (f"githubusercontent.com/{old_repo}", f"githubusercontent.com/{new_repo}"),
        (f"ghcr.io/{old_username}/stealthflow", f"ghcr.io/soroushdeimi/sush-stealthflow"),
        (f"ghcr.io/{old_username}/stealthflow-signaling", f"ghcr.io/soroushdeimi/sush-stealthflow-signaling"),
        (old_username, new_username)
    ]
    
    project_root = Path(__file__).parent
    updated_files = []
    
    for file_path in files_to_update:
        full_path = project_root / file_path
        
        if not full_path.exists():
            print(f"⚠️  File not found: {file_path}")
            continue
            
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Apply all replacements
            for old_pattern, new_pattern in replacements:
                content = content.replace(old_pattern, new_pattern)
            
            # Only write if content changed
            if content != original_content:
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                updated_files.append(file_path)
                print(f"✅ Updated: {file_path}")
            else:
                print(f"ℹ️  No changes needed: {file_path}")
                
        except Exception as e:
            print(f"❌ Error updating {file_path}: {e}")
    
    print(f"\n🎉 Repository URL update complete!")
    print(f"Updated {len(updated_files)} files:")
    for file_path in updated_files:
        print(f"  - {file_path}")
    
    print(f"\n📝 New repository: https://github.com/{new_repo}")

if __name__ == "__main__":
    update_repository_urls()
