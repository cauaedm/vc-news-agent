
import re

with open("pegn_raw.txt", "r", encoding="utf-8") as f:
    content = f.read()

search_term = "investimento"
matches = [m.start() for m in re.finditer(search_term, content, re.IGNORECASE)]

with open("pegn_snippet.txt", "w", encoding="utf-8") as out:
    if not matches:
        out.write(f"'{search_term}' not found.\n")
    else:
        out.write(f"Found {len(matches)} occurrences of '{search_term}'.\n\n")
        # Print up to 3 occurrences
        count = 0
        for index in matches:
            if count >= 3: break
            
            # extract context
            start = max(0, index - 500)
            end = min(len(content), index + 500)
            snippet = content[start:end]
            
            out.write(f"--- Occurence at {index} ---\n")
            out.write(snippet)
            out.write("\n\n")
            count += 1
