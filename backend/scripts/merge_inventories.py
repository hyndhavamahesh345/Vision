import json, time
from pathlib import Path
output_dir = Path(__file__).parent.parent / 'output'
merged = {}
for inv_file in output_dir.glob('*_inventory.json'):
    data = json.load(open(inv_file))
    for item in data.get('inventory', []):
        name = item['name']
        qty = item['quantity']
        merged[name] = merged.get(name, 0) + qty
combined_path = output_dir / 'combined_inventory.json'
with open(combined_path, 'w') as f:
    json.dump({'total_items': merged, 'generated_at': time.strftime('%Y-%m-%d %H:%M:%S')}, f, indent=2)
print('Combined inventory written to', combined_path)
 