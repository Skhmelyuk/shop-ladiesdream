import re
from collections import defaultdict

def find_duplicate_selectors(file_path):
    with open(file_path, 'r') as f:
        content = f.read()

    # Remove comments
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
    
    # Find all selectors (roughly)
    # This regex looks for things before {
    selectors = re.findall(r'([^{}]+)\s*\{', content)
    
    counts = defaultdict(list)
    for i, s in enumerate(selectors):
        s = s.strip()
        if not s: continue
        # Normalize: remove newlines, multiple spaces
        s = re.sub(r'\s+', ' ', s)
        counts[s].append(i)
        
    duplicates = {s: indices for s, indices in counts.items() if len(indices) > 1}
    
    for s, indices in sorted(duplicates.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"Selector '{s}' found {len(indices)} times.")

if __name__ == "__main__":
    find_duplicate_selectors('/home/skmelyuk/Documents/projects/shop-ladiesdream/shop/static/main/style.css')
