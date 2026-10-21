"""Build the explorer page from template.html + songs.json.
    docs/explorer_body.html  page content (for previews)
    docs/index.html          standalone page for GitHub Pages
"""
import json
from pathlib import Path

d = Path(__file__).parent
data = (d / "songs.json").read_text().replace("</", "<\\/")
body = (d / "template.html").read_text().replace("/*DATA*/", data)
(d / "explorer_body.html").write_text(body)
head, rest = body.split("<style>", 1)
css, html = rest.split("</style>", 1)
(d / "index.html").write_text('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
                              '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
                              + head + "<style>" + css + "</style>\n</head>\n<body>\n" + html + "\n</body>\n</html>\n")
print("docs/index.html written")
