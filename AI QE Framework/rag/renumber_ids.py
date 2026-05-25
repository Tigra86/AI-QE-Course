#!/usr/bin/env python3

import json
import os
from pathlib import Path
import re

def extract_number_from_id(id_str):
    """Extract numeric part from ID like Q001 -> 1"""
    if id_str and len(id_str) > 1 and id_str[0] == 'Q':
        try:
            return int(id_str[1:])
        except ValueError:
            return 999999
    return 999999

def collect_all_ids():
    """Collect all Q-IDs from eval files in sorted order"""
    all_ids = set()
    eval_dir = Path("eval")
    
    print("Collecting IDs from eval files...")
    
    for eval_file in eval_dir.glob("*.jsonl"):
        print(f"Reading {eval_file.name}")
        
        with open(eval_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    if 'id' in data:
                        all_ids.add(data['id'])
                except json.JSONDecodeError as e:
                    print(f"JSON error in {eval_file.name} line {line_num}: {e}")
    
    # Sort IDs by numeric value
    sorted_ids = sorted(list(all_ids), key=extract_number_from_id)
    
    print(f"Found {len(sorted_ids)} unique IDs")
    print("First 10:", sorted_ids[:10])
    print("Last 10:", sorted_ids[-10:])
    
    return sorted_ids

def create_id_mapping(sorted_ids):
    """Create mapping from old IDs to new consecutive IDs"""
    mapping = {}
    
    for i, old_id in enumerate(sorted_ids, 1):
        new_id = f"Q{i:03d}"
        mapping[old_id] = new_id
    
    print(f"Created mapping for {len(mapping)} IDs")
    print("Sample mappings:")
    for i, (old, new) in enumerate(mapping.items()):
        if i < 10:  # Show first 10
            print(f"  {old} -> {new}")
        elif i >= len(mapping) - 5:  # Show last 5
            print(f"  {old} -> {new}")
    
    return mapping

def update_jsonl_file(filepath, id_mapping):
    """Update a JSONL file with new IDs"""
    print(f"Updating {filepath}")
    
    lines = []
    changes = 0
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                lines.append(line)
                continue
            
            try:
                data = json.loads(line)
                if 'id' in data and data['id'] in id_mapping:
                    old_id = data['id']
                    data['id'] = id_mapping[old_id]
                    changes += 1
                
                lines.append(json.dumps(data, ensure_ascii=False))
                
            except json.JSONDecodeError as e:
                print(f"JSON error in {filepath} line {line_num}: {e}")
                lines.append(line)
    
    # Write back to file
    with open(filepath, 'w', encoding='utf-8') as f:
        for line in lines:
            f.write(line + '\n')
    
    print(f"  Updated {changes} IDs in {filepath}")
    return changes

def update_json_file(filepath, id_mapping):
    """Update a JSON file with new IDs"""
    print(f"Updating {filepath}")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        changes = 0
        
        # Handle different JSON structures
        if isinstance(data, dict):
            for key, value in data.items():
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
        
        # Write back to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"  Updated {changes} IDs in {filepath}")
        return changes
        
    except Exception as e:
        print(f"Error updating {filepath}: {e}")
        return 0

def main():
    print("=== ID Renumbering Script ===")
    
    # Step 1: Collect all IDs
    sorted_ids = collect_all_ids()
    
    # Step 2: Create mapping
    id_mapping = create_id_mapping(sorted_ids)
    
    # Save mapping for reference
    with open('id_mapping.json', 'w') as f:
        json.dump(id_mapping, f, indent=2)
    print("Saved ID mapping to id_mapping.json")
    
    # Step 3: Update eval files
    print("\nUpdating eval files...")
    eval_dir = Path("eval")
    total_changes = 0
    
    for eval_file in eval_dir.glob("*.jsonl"):
        changes = update_jsonl_file(eval_file, id_mapping)
        total_changes += changes
    
    # Step 4: Update datasets files
    print("\nUpdating dataset files...")
    datasets_dir = Path("datasets")
    
    for dataset_file in datasets_dir.glob("*.jsonl"):
        changes = update_jsonl_file(dataset_file, id_mapping)
        total_changes += changes
    
    # Step 5: Update rules files
    print("\nUpdating rules files...")
    rules_dir = Path("rules")
    
    for rules_file in rules_dir.glob("*.json"):
        changes = update_json_file(rules_file, id_mapping)
        total_changes += changes
    
    print(f"\n=== COMPLETED ===")
    print(f"Total changes made: {total_changes}")
    print(f"IDs renumbered from Q001 to Q{len(sorted_ids):03d}")

if __name__ == "__main__":
    main()