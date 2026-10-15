"""
build_gallery.py — turn folders of photos into the site's job gallery.

Put photos in  images/jobs/<job-name>/   (one folder per job, any jpg/png/heic*).
Optional: a  caption.txt  in the folder = one-line description shown under the title.
Run:  python3 tools/build_gallery.py
It (1) makes web-size copies (max 1600 px) + thumbnails, (2) writes jobs/<job-name>.html,
(3) fills the job tiles between JOBS:START / JOBS:END in index.html.
*HEIC needs `pip install pillow-heif`.
"""
import os, re, html, sys
from PIL import Image, ImageOps
try:
    import pillow_heif; pillow_heif.register_heif_opener()
except ImportError:
    pass
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "images", "jobs"); WEB = os.path.join(ROOT, "images", "web"); JOBS = os.path.join(ROOT, "jobs")
os.makedirs(WEB, exist_ok=True); os.makedirs(JOBS, exist_ok=True)
EXT = (".jpg", ".jpeg", ".png", ".heic", ".webp")
def slug(s): return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
def title(s): return s.replace("-", " ").replace("_", " ").strip().title()
tiles = []
for job in sorted(os.listdir(SRC)):
    d = os.path.join(SRC, job)
    if not os.path.isdir(d): continue
    files = sorted(f for f in os.listdir(d) if f.lower().endswith(EXT))
    if not files: continue
    js = slug(job); out = os.path.join(WEB, js); os.makedirs(out, exist_ok=True)
    cap = ""
    cp = os.path.join(d, "caption.txt")
    if os.path.exists(cp): cap = open(cp, encoding="utf-8").read().strip()
    shots = []
    for i, f in enumerate(files, 1):
        im = ImageOps.exif_transpose(Image.open(os.path.join(d, f))).convert("RGB")
        big = im.copy(); big.thumbnail((1600, 1600)); bn = f"{js}-{i:02d}.jpg"; big.save(os.path.join(out, bn), quality=85, optimize=True)
        th = im.copy(); th.thumbnail((600, 600)); tn = f"{js}-{i:02d}-thumb.jpg"; th.save(os.path.join(out, tn), quality=80, optimize=True)
        shots.append((bn, tn))
    body = "\n".join(f'<a href="../images/web/{js}/{b}"><img src="../images/web/{js}/{t}" alt="{html.escape(title(job))} photo {i}"></a>' for i, (b, t) in enumerate(shots, 1))
    open(os.path.join(JOBS, js + ".html"), "w", encoding="utf-8").write(f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title(job))} | JPM Construction</title><link rel="icon" href="../images/logo/jpm-logo.png">
<style>body{{margin:0;font:16px/1.5 Arial,Helvetica,sans-serif;color:#1a1a1a}}header{{padding:20px;max-width:1000px;margin:0 auto}}header img{{max-width:260px;width:100%}}
.bar{{height:8px;background:#1cb0e6}}main{{max-width:1000px;margin:0 auto;padding:20px}}h1{{font-size:26px;margin:0 0 6px}}.muted{{color:#555}}
.g{{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:10px;margin-top:16px}}.g img{{width:100%;height:200px;object-fit:cover;border-radius:6px;display:block}}
a.back{{display:inline-block;margin-top:24px;color:#1cb0e6;font-weight:bold;text-decoration:none}}</style></head>
<body><header><a href="../"><img src="../images/logo/jpm-logo.png" alt="JPM Construction"></a></header><div class="bar"></div>
<main><h1>{html.escape(title(job))}</h1><p class="muted">{html.escape(cap)}</p><div class="g">
{body}
</div><a class="back" href="../">&larr; All work</a></main></body></html>""")
    tiles.append(f'<a href="jobs/{js}.html"><img src="images/web/{js}/{shots[0][1]}" alt="{html.escape(title(job))}"><span>{html.escape(title(job))}</span></a>')
ip = os.path.join(ROOT, "index.html"); s = open(ip, encoding="utf-8").read()
s = re.sub(r"<!-- JOBS:START -->.*?<!-- JOBS:END -->", "<!-- JOBS:START -->\n" + "\n".join(tiles) + "\n<!-- JOBS:END -->", s, flags=re.S)
open(ip, "w", encoding="utf-8").write(s)
print(f"{len(tiles)} job(s) built")
