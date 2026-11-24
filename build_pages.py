"""Build the self-contained GitHub Pages demo from the local application."""
import json
from pathlib import Path
from actions import ORDERS, GUIDANCE
from resolver import KB, INDEX, STOP, idf

root = Path(__file__).resolve().parent
out = root / "docs"
out.mkdir(exist_ok=True)
page = (root/"static/index.html").read_text(encoding="utf-8-sig")
page = page.replace("Python + SQLite workspace", "GitHub Pages demo").replace("Cases are saved in the local SQLite database.", "Demo cases are saved in this browser.")
(out/"index.html").write_text(page.replace('<script src="app.js">','<script src="pages.js"></script><script src="app.js">'),encoding="utf-8")
app = (root/"static/app.js").read_text(encoding="utf-8-sig")
start = app.index("async function api(")
end = app.index("function bind(", start)
(out/"app.js").write_text(app[:start]+app[end:], encoding="utf-8")
data = dict(orders=ORDERS,guidance=GUIDANCE,stop=sorted(STOP),idf=idf,index=[(item["team"],vec) for item,vec in INDEX])
adapter = (root/"pages-adapter.js").read_text(encoding="utf-8-sig")
(out/"pages.js").write_text("const model = "+json.dumps(data)+";\n"+adapter,encoding="utf-8")
(out/".nojekyll").touch()
