import os

def process_file(filepath):
    print(f"Processing {filepath}...")
    with open(filepath, 'r') as f:
        lines = f.readlines()

    new_lines = []
    skip_demo_source = False

    for line in lines:
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())

        # 1. Handle demo_source removal
        if stripped.startswith("- id: demo_source"):
            skip_demo_source = True
            continue

        if skip_demo_source:
            # Stop skipping if we hit the next list item or a new section
            if stripped.startswith("- id:") or (stripped and not line.startswith(" ")):
                skip_demo_source = False
            else:
                continue

        # 2. Rename demo_output
        if "- name: demo_output" in stripped:
            new_lines.append(line.replace("demo_output", "all_sources"))
            continue

        # 3. Handle destinations removal logic REMOVED.
        # We preserve destinations now.

        new_lines.append(line)

    with open(filepath, 'w') as f:
        f.writelines(new_lines)
    print(f"Updated {filepath}")

files = ['my_config.yaml', 'configs/config.prod.yaml']
for f in files:
    if os.path.exists(f):
        process_file(f)
    else:
        print(f"File {f} not found.")
