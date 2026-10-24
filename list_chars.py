import re

files = ['src/engine/fight.asm', 'build/gen_fight/newchars_desc.inc']
all_results = {}

for file_path in files:
    try:
        with open(file_path, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        continue

    parts = re.split(r'(Char\w+:)', content)
    for i in range(1, len(parts), 2):
        name = parts[i].strip(':')
        body = parts[i+1]
        
        # Pattern: .db [any], 0 \n .dw ... \n .db ..., [0/1]
        match = re.search(r'\.db\s+[^,\n]+,\s+0\s*\n\s*\.dw\s+[^,\n]*\s*\n\s*\.db\s+[^,]+,\s*([01])', body)
        if match:
            flag = match.group(1)
            all_results[name] = 'MSU' if flag == '1' else 'ROM'

for name, status in sorted(all_results.items()):
    print(f"{name}: {status}")
