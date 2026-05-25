#!/usr/bin/env python3

import json
import os
from pathlib import Path

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

def collect_all_records():
    """Collect all records from eval files and assign unique consecutive IDs"""
    all_records = []
    eval_dir = Path("eval")
    
    print("Collecting all records from eval files...")
    
    for eval_file in sorted(eval_dir.glob("*.jsonl")):
        print(f"Reading {eval_file.name}")
        
        content = read_with_bom_handling(eval_file)
        lines = content.strip().split('\n')
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                if 'id' in data:
                    # Store the record with its file info
                    record_info = {
                        'file': eval_file.name,
                        'line': line_num,
                        'old_id': data['id'],
                        'data': data,
                        'raw_line': line
                    }
                    all_records.append(record_info)
            except json.JSONDecodeError as e:
                print(f"JSON error in {eval_file.name} line {line_num}: {e}")
    
    print(f"Found {len(all_records)} total records")
    
    # Create new consecutive ID mapping
    old_to_new_mapping = {}
    new_to_record_mapping = {}
    
    for i, record in enumerate(all_records, 1):
        new_id = f"Q{i:03d}"
        old_id = record['old_id']
        
        # Create a unique key for this specific record (old_id + file + line)
        record_key = f"{old_id}_{record['file']}_{record['line']}"
        
        old_to_new_mapping[record_key] = new_id
        new_to_record_mapping[new_id] = record
        
        # Update the record's data with new ID
        record['data']['id'] = new_id
        record['new_id'] = new_id
    
    print(f"Created {len(all_records)} unique consecutive IDs: Q001 to Q{len(all_records):03d}")
    
    return all_records, old_to_new_mapping, new_to_record_mapping

def update_eval_files(all_records):
    """Update eval files with new consecutive IDs"""
    print("\nUpdating eval files...")
    
    # Group records by file
    files_to_records = {}
    for record in all_records:
        filename = record['file']
        if filename not in files_to_records:
            files_to_records[filename] = []
        files_to_records[filename].append(record)
    
    eval_dir = Path("eval")
    
    for filename, file_records in files_to_records.items():
        filepath = eval_dir / filename
        print(f"Updating {filepath}")
        
        # Sort by line number to maintain order
        file_records.sort(key=lambda x: x['line'])
        
        updated_lines = []
        for record in file_records:
            updated_line = json.dumps(record['data'], ensure_ascii=False)
            updated_lines.append(updated_line)
        
        # Write back to file without BOM
        content = '\n'.join(updated_lines) + '\n'
        write_without_bom(filepath, content)
        
        print(f"  Updated {len(file_records)} records in {filepath}")

def update_datasets_and_rules(old_to_new_simple):
    """Update datasets and rules files using simple old->new mapping"""
    total_changes = 0
    
    print("\nUpdating dataset files...")
    datasets_dir = Path("datasets")
    
    for dataset_file in datasets_dir.glob("*.jsonl"):
        changes = update_jsonl_file_simple(dataset_file, old_to_new_simple)
        total_changes += changes
    
    print("\nUpdating rules files...")
    rules_dir = Path("rules")
    
    for rules_file in rules_dir.glob("*.json"):
        changes = update_json_file_simple(rules_file, old_to_new_simple)
        total_changes += changes
    
    return total_changes

def create_simple_mapping(all_records):
    """Create a simple old_id -> first_new_id mapping for datasets/rules"""
    simple_mapping = {}
    
    for record in all_records:
        old_id = record['old_id']
        new_id = record['new_id']
        
        # Use the first occurrence of each old_id
        if old_id not in simple_mapping:
            simple_mapping[old_id] = new_id
    
    return simple_mapping

def update_jsonl_file_simple(filepath, id_mapping):
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

def update_json_file_simple(filepath, id_mapping):
    """Update a JSON file with BOM handling"""
    print(f"Updating {filepath}")
    
    try:
        content = read_with_bom_handling(filepath)
        data = json.loads(content)
        
        changes = 0
        
        # Handle different JSON structures
        if isinstance(data, dict):
            # Create a list of items to avoid modifying dict during iteration
            items_to_update = []
            for key, value in data.items():
                if key in id_mapping:
                    items_to_update.append((key, value, 'key'))
                elif isinstance(value, dict) and 'id' in value and value['id'] in id_mapping:
                    items_to_update.append((key, value, 'value_id'))
            
            # Apply updates
            for key, value, update_type in items_to_update:
                if update_type == 'key':
                    # Key is an old ID - need to rename key
                    new_key = id_mapping[key]
                    data[new_key] = data.pop(key)
                    changes += 1
                elif update_type == 'value_id':
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
    print("=== Fixing Duplicate IDs with Proper Consecutive Numbering ===")
    
    # Step 1: Collect all records and create new consecutive IDs
    all_records, complex_mapping, record_mapping = collect_all_records()
    
    # Step 2: Create simple mapping for datasets/rules (old_id -> first_new_id)
    simple_mapping = create_simple_mapping(all_records)
    
    # Save mappings for reference
    with open('complex_id_mapping.json', 'w') as f:
        json.dump(complex_mapping, f, indent=2)
    
    with open('simple_id_mapping.json', 'w') as f:
        json.dump(simple_mapping, f, indent=2)
        
    print(f"Saved complex mapping with {len(complex_mapping)} entries to complex_id_mapping.json")
    print(f"Saved simple mapping with {len(simple_mapping)} entries to simple_id_mapping.json")
    
    # Step 3: Update eval files with unique consecutive IDs
    update_eval_files(all_records)
    
    # Step 4: Update datasets and rules files with simple mapping
    total_changes = update_datasets_and_rules(simple_mapping)
    
    print(f"\n=== COMPLETED ===")
    print(f"Total records processed: {len(all_records)}")
    print(f"New ID range: Q001 to Q{len(all_records):03d}")
    print(f"Additional changes in datasets/rules: {total_changes}")
    
    # Show some examples of what was fixed
    print(f"\nExample ID assignments:")
    for i, record in enumerate(all_records[:10]):
        print(f"  {record['old_id']} ({record['file']}) -> {record['new_id']}")
    if len(all_records) > 10:
        print(f"  ... and {len(all_records) - 10} more")

if __name__ == "__main__":
    main()