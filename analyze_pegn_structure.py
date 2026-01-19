
from bs4 import BeautifulSoup

file_path = "pegn_raw.txt"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

soup = BeautifulSoup(content, "html.parser")
feed_item = soup.find(class_="feed-post")

output = []
if feed_item:
    output.append("Full structure of first feed-post:")
    output.append(feed_item.prettify())
else:
    output.append("No feed-post found.")

with open("pegn_item_structure.txt", "w", encoding="utf-8") as out:
    out.write("\n".join(output))
