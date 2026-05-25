#!/usr/bin/env python3

import json
import os
from pathlib import Path
import re

def read_with_bom_handling(filepath):
    """Read file handling BOM properly"""
    encodings = ['utf-8-sig', 'utf-8']
    
    for encoding in encodings:
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    
    # Fallback
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()

def write_without_bom(filepath, content):
    """Write file without BOM"""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def update_jsonl_file_fixed(filepath, id_mapping):
    """Update a JSONL file with BOM handling"""
    print(f"Updating {filepath}")
    
    content = read_with_bom_handling(filepath)
    lines = content.strip().split('\n')
    
    updated_lines = []
    changes = 0
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            updated_lines.append(line)
            continue
        
        try:
            data = json.loads(line)
            if 'id' in data and data['id'] in id_mapping:
                old_id = data['id']
                data['id'] = id_mapping[old_id]
                changes += 1
            
            updated_lines.append(json.dumps(data, ensure_ascii=False))
            
        except json.JSONDecodeError as e:
            print(f"JSON error in {filepath} line {line_num}: {e}")
            updated_lines.append(line)
    
    # Write back to file without BOM
    write_without_bom(filepath, '\n'.join(updated_lines) + '\n')
    
    print(f"  Updated {changes} IDs in {filepath}")
    return changes

def update_json_file_fixed(filepath, id_mapping):
    """Update a JSON file with BOM handling"""
    print(f"Updating {filepath}")
    
    try:
        content = read_with_bom_handling(filepath)
        data = json.loads(content)
        
        changes = 0
        
        # Handle different JSON structures
        if isinstance(data, dict):
            for key, value in list(data.items()):  # Convert to list to allow key changes
                if key in id_mapping:
                    # Key is an old ID - need to rename key
                    new_key = id_mapping[key]
                    data[new_key] = data.pop(key)
                    changes += 1
                elif isinstance(value, dict) and 'id' in value and value['id'] in id_mapping:
                    # Value has an id field
                    value['id'] = id_mapping[value['id']]
                    changes += 1
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and 'id' in item and item['id'] in id_mapping:
                    item['id'] = id_mapping[item['id']]
                    changes += 1
        
        # Write back to file without BOM
        write_without_bom(filepath, json.dumps(data, indent=2, ensure_ascii=False))
        
        print(f"  Updated {changes} IDs in {filepath}")
        return changes
        
    except Exception as e:
        print(f"Error updating {filepath}: {e}")
        return 0

def main():
    print("=== Fixing BOM and Continuing Renumbering ===")
    
    # Load existing mapping
    with open('id_mapping.json', 'r') as f:
        id_mapping = json.load(f)
    
    print(f"Loaded ID mapping with {len(id_mapping)} entries")
    
    total_changes = 0
    
    # Update datasets files with BOM handling
    print("\nUpdating dataset files with BOM handling...")
    datasets_dir = Path("datasets")
    
    for dataset_file in datasets_dir.glob("*.jsonl"):
        changes = update_jsonl_file_fixed(dataset_file, id_mapping)
        total_changes += changes
    
    # Update rules files with BOM handling
    print("\nUpdating rules files with BOM handling...")
    rules_dir = Path("rules")
    
    for rules_file in rules_dir.glob("*.json"):
        changes = update_json_file_fixed(rules_file, id_mapping)
        total_changes += changes
    
    print(f"\n=== BOM FIX COMPLETED ===")
    print(f"Additional changes made: {total_changes}")

if __name__ == "__main__":
    main()