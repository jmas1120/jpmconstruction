"""
build_site.py — builds the whole jpmconstruction.org site from photo folders + jobs.json.

Folders:  images/jobs/<job-folder>/   one folder per job, photos inside (jpg/jpeg/png/heic/webp)
jobs.json (optional, next to this script's parent): metadata per folder:
  { "<job-folder>": {"title": "MacEachern walk-in tub", "kind": "jpm" | "habitat" | "house",
                     "town": "Billerica, MA", "year": "2024", "blurb": "one or two sentences",
                     "cover": "IMG_1234.jpeg", "order": 10 } }
Anything missing is derived from the folder name. kind defaults to "jpm".
Run:  python3 tools/build_site.py     then commit + push.
Writes: images/web/<slug>/*.jpg (1600px) + thumbs (600px), jobs/<slug>.html, index.html
"""
import os, re, json, html, sys
from PIL import Image, ImageOps
try:
    import pillow_heif; pillow_heif.register_heif_opener()
except ImportError: pass
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC=os.path.join(ROOT,"images","jobs"); WEB=os.path.join(ROOT,"images","web"); JOBS=os.path.join(ROOT,"jobs")
META=json.load(open(os.path.join(ROOT,"jobs.json"))) if os.path.exists(os.path.join(ROOT,"jobs.json")) else {}
os.makedirs(WEB,exist_ok=True); os.makedirs(JOBS,exist_ok=True)
EXT=(".jpg",".jpeg",".png",".heic",".webp")
def slug(s): return re.sub(r"[^a-z0-9]+","-",s.lower()).strip("-")
def title_of(s): return re.sub(r"\s+"," ",s.replace("-"," ").replace("_"," ")).strip()
KIND_LABEL={"jpm":"JPM Construction","habitat":"Habitat for Humanity of Greater Lowell","house":"My own house"}

CSS="""
:root{--ink:#161616;--blue:#1cb0e6;--bg:#fff;--muted:#6b6b6b;--line:#e6e6e6}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;color:var(--ink);background:var(--bg)}
a{color:inherit}
.wrap{max-width:1180px;margin:0 auto;padding:0 20px}
nav{position:sticky;top:0;background:rgba(255,255,255,.96);backdrop-filter:saturate(1.2) blur(6px);border-bottom:4px solid var(--blue);z-index:5}
nav .wrap{display:flex;align-items:center;justify-content:space-between;height:64px}
nav img{height:38px;width:auto}
nav ul{list-style:none;display:flex;gap:22px;margin:0;padding:0;font-weight:600;font-size:15px}
nav a{text-decoration:none}nav a:hover{color:var(--blue)}
.hero{position:relative;min-height:62vh;display:grid;place-items:center;text-align:center;color:#fff;background:#222 center/cover no-repeat;}
.hero::after{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.25),rgba(0,0,0,.65))}
.hero > *{position:relative;z-index:1}
.hero h1{font-size:clamp(34px,6vw,64px);margin:0 0 8px;letter-spacing:-.5px;text-transform:uppercase;font-style:italic}
.hero p{font-size:clamp(17px,2.2vw,22px);margin:0 0 22px;opacity:.95}
.btn{display:inline-block;background:var(--blue);color:#fff;text-decoration:none;font-weight:700;padding:12px 22px;border-radius:6px}
.btn.ghost{background:transparent;border:2px solid #fff;margin-left:10px}
section{padding:56px 0}
h2{font-size:30px;margin:0 0 6px;text-transform:uppercase;font-style:italic;letter-spacing:-.3px}
h2 + p.lead{margin:0 0 22px;color:var(--muted)}
.bar{height:6px;width:90px;background:var(--blue);margin:10px 0 24px}
.filters{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:18px}
.filters button{border:1px solid var(--line);background:#fff;padding:8px 14px;border-radius:999px;font-weight:600;cursor:pointer}
.filters button.on{background:var(--ink);color:#fff;border-color:var(--ink)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:18px}
.card{position:relative;display:block;border-radius:10px;overflow:hidden;background:#eee;text-decoration:none;aspect-ratio:4/3}
.card img{width:100%;height:100%;object-fit:cover;display:block;transition:transform .35s}
.card:hover img{transform:scale(1.04)}
.card .cap{position:absolute;left:0;right:0;bottom:0;padding:34px 14px 12px;background:linear-gradient(180deg,transparent,rgba(0,0,0,.78));color:#fff}
.card .cap b{display:block;font-size:17px}.card .cap span{font-size:13px;opacity:.9}
.tag{position:absolute;top:10px;left:10px;background:var(--blue);color:#fff;font-size:11px;font-weight:700;padding:4px 8px;border-radius:4px;text-transform:uppercase;letter-spacing:.4px}
.tag.habitat{background:#2a9d3b}.tag.house{background:#e6a11c}
.about{display:grid;grid-template-columns:1.2fr .8fr;gap:36px;align-items:start}
.about .facts{background:#f6f8fa;border-left:6px solid var(--blue);padding:18px 20px;border-radius:6px}
.about .facts div{margin:6px 0}.about .facts b{display:inline-block;min-width:150px;color:var(--muted);font-weight:600}
.contact{background:var(--ink);color:#fff}.contact a{color:#8fd8f5}
footer{padding:22px 0;color:var(--muted);font-size:14px;border-top:1px solid var(--line)}
/* job page */
.jobhead{padding:36px 0 10px}.jobhead .meta{color:var(--muted)}
.masonry{columns:3 280px;column-gap:14px}.masonry a{display:block;margin:0 0 14px;break-inside:avoid;border-radius:8px;overflow:hidden;background:#eee}
.masonry img{width:100%;display:block}
.lb{position:fixed;inset:0;background:rgba(0,0,0,.92);display:none;place-items:center;z-index:50}
.lb.on{display:grid}.lb img{max-width:94vw;max-height:88vh;object-fit:contain}
.lb button{position:absolute;top:50%;transform:translateY(-50%);background:none;border:0;color:#fff;font-size:44px;cursor:pointer;padding:20px}
.lb .prev{left:4px}.lb .next{right:4px}.lb .close{top:10px;right:14px;transform:none;font-size:34px}
.lb .n{position:absolute;bottom:14px;left:0;right:0;text-align:center;color:#bbb;font-size:13px}
@media (max-width:760px){.about{grid-template-columns:1fr}nav ul{gap:14px;font-size:14px}}
"""
LB_JS="""
(function(){const links=[...document.querySelectorAll('.masonry a')];if(!links.length)return;const lb=document.createElement('div');lb.className='lb';lb.innerHTML='<button class="close">&times;</button><button class="prev">&#8249;</button><img><button class="next">&#8250;</button><div class="n"></div>';document.body.appendChild(lb);let i=0;const img=lb.querySelector('img'),n=lb.querySelector('.n');
function show(k){i=(k+links.length)%links.length;img.src=links[i].href;n.textContent=(i+1)+' / '+links.length;lb.classList.add('on');}
links.forEach((a,k)=>a.addEventListener('click',e=>{e.preventDefault();show(k);}));
lb.querySelector('.prev').onclick=()=>show(i-1);lb.querySelector('.next').onclick=()=>show(i+1);lb.querySelector('.close').onclick=()=>lb.classList.remove('on');
lb.addEventListener('click',e=>{if(e.target===lb)lb.classList.remove('on')});
document.addEventListener('keydown',e=>{if(!lb.classList.contains('on'))return;if(e.key==='Escape')lb.classList.remove('on');if(e.key==='ArrowLeft')show(i-1);if(e.key==='ArrowRight')show(i+1);});})();
"""
NAV='''<nav><div class="wrap"><a href="{p}"><img src="{p}images/logo/jpm-logo.png" alt="JPM Construction"></a><ul><li><a href="{p}#work">Work</a></li><li><a href="{p}#habitat">Habitat</a></li><li><a href="{p}#about">About</a></li><li><a href="{p}#contact">Contact</a></li></ul></div></nav>'''
CONTACT='''<section class="contact" id="contact"><div class="wrap"><h2>Have a project in mind?</h2><div class="bar"></div>
<p>Call or text <a href="tel:+19788313131">978 831 3131</a> or email <a href="mailto:jmas1120.jm@gmail.com">jmas1120.jm@gmail.com</a>. Billerica, Massachusetts.</p></div></section>
<footer><div class="wrap">JPM Construction · John Maslowski · 31 Fredrickson Rd, Billerica MA 01821 · Construction Supervisor License 90601</div></footer>'''

jobs=[]
for folder in sorted(os.listdir(SRC)):
    d=os.path.join(SRC,folder)
    if not os.path.isdir(d): continue
    files=sorted(f for f in os.listdir(d) if f.lower().endswith(EXT))
    if not files: continue
    m=META.get(folder,{})
    js=slug(folder); out=os.path.join(WEB,js); os.makedirs(out,exist_ok=True)
    shots=[]
    for i,f in enumerate(files,1):
        bn=f"{js}-{i:02d}.jpg"; tn=f"{js}-{i:02d}-thumb.jpg"
        if not os.path.exists(os.path.join(out,bn)):
            im=ImageOps.exif_transpose(Image.open(os.path.join(d,f))).convert("RGB")
            big=im.copy(); big.thumbnail((1600,1600)); big.save(os.path.join(out,bn),quality=84,optimize=True)
            th=im.copy(); th.thumbnail((640,640)); th.save(os.path.join(out,tn),quality=78,optimize=True)
        shots.append((f,bn,tn))
    cover=next((s for s in shots if s[0]==m.get("cover")),shots[0])
    jobs.append(dict(folder=folder,slug=js,title=m.get("title",title_of(folder)),kind=m.get("kind","jpm"),town=m.get("town",""),year=m.get("year",""),blurb=m.get("blurb",""),cover=cover,shots=shots,order=m.get("order",999)))
jobs.sort(key=lambda j:(j["order"],j["title"]))

for j in jobs:
    cards="\n".join(f'<a href="../images/web/{j["slug"]}/{b}"><img loading="lazy" src="../images/web/{j["slug"]}/{t}" alt="{html.escape(j["title"])} — photo {k}"></a>' for k,(f,b,t) in enumerate(j["shots"],1))
    meta=" · ".join(x for x in [KIND_LABEL.get(j["kind"],""),j["town"],j["year"]] if x)
    open(os.path.join(JOBS,j["slug"]+".html"),"w",encoding="utf-8").write(f'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(j["title"])} | JPM Construction</title><link rel="icon" href="../images/logo/jpm-logo.png"><style>{CSS}</style></head><body>
{NAV.format(p="../")}
<div class="wrap jobhead"><h2>{html.escape(j["title"])}</h2><div class="bar"></div><p class="meta">{html.escape(meta)}</p>{('<p>'+html.escape(j["blurb"])+'</p>') if j["blurb"] else ''}<p>{len(j["shots"])} photos — click any to view full size.</p></div>
<div class="wrap"><div class="masonry">{cards}</div><p style="margin:28px 0"><a class="btn" href="../#work">&larr; All work</a></p></div>
{CONTACT}<script>{LB_JS}</script></body></html>''')

def card(j):
    f,b,t=j["cover"]; sub=" · ".join(x for x in [j["town"],j["year"]] if x)
    return f'<a class="card" data-kind="{j["kind"]}" href="jobs/{j["slug"]}.html"><img loading="lazy" src="images/web/{j["slug"]}/{t}" alt="{html.escape(j["title"])}"><span class="tag {j["kind"]}">{html.escape({"jpm":"JPM","habitat":"Habitat","house":"Home"}[j["kind"]])}</span><div class="cap"><b>{html.escape(j["title"])}</b><span>{html.escape(sub)}&nbsp;</span></div></a>'
work=[j for j in jobs if j["kind"] in ("jpm","house")]; hab=[j for j in jobs if j["kind"]=="habitat"]
hero_img=next((f'images/web/{j["slug"]}/{j["cover"][1]}' for j in work),"") or next((f'images/web/{j["slug"]}/{j["cover"][1]}' for j in hab),"")
hero_style=f' style="background-image:url({hero_img})"' if hero_img else ""
index=f'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>JPM Construction | John Maslowski, Billerica MA</title>
<meta name="description" content="Remodeling and carpentry by John Maslowski in Billerica, Massachusetts. A portfolio of completed jobs, plus Habitat for Humanity builds he runs as Director of Construction.">
<link rel="canonical" href="https://jpmconstruction.org/"><link rel="icon" href="images/logo/jpm-logo.png">
<meta property="og:title" content="JPM Construction — John Maslowski"><meta property="og:description" content="Remodeling and carpentry, Billerica MA. See the work."><meta property="og:image" content="https://jpmconstruction.org/{hero_img or 'images/logo/jpm-logo.png'}">
<style>{CSS}</style></head><body>
{NAV.format(p="")}
<header class="hero"{hero_style}><div class="wrap"><img src="images/logo/jpm-logo.png" alt="" style="height:64px;width:auto;background:#fff;padding:8px 14px;border-radius:6px;margin-bottom:18px"><h1>Built right, by hand</h1><p>Remodeling and carpentry by John Maslowski · Billerica, Massachusetts</p><a class="btn" href="#work">See the work</a><a class="btn ghost" href="#contact">Get in touch</a></div></header>
<section id="work"><div class="wrap"><h2>The work</h2><div class="bar"></div><p class="lead">Organized by job. Click a job to see every photo.</p>
<div class="filters"><button class="on" data-k="all">All</button><button data-k="jpm">JPM jobs</button><button data-k="house">My own house</button></div>
<div class="grid" id="workgrid">{"".join(card(j) for j in work) or '<p class="lead">Photos are being added — check back soon.</p>'}</div></div></section>
<section id="habitat" style="background:#f6f8fa"><div class="wrap"><h2>Habitat for Humanity builds</h2><div class="bar"></div><p class="lead">By day John is Director of Construction for Habitat for Humanity of Greater Lowell. These are houses built with volunteers under his lead; the photos are shared with Habitat's permission and the work is Habitat's.</p>
<div class="grid">{"".join(card(j) for j in hab) or '<p class="lead">Coming soon.</p>'}</div></div></section>
<section id="about"><div class="wrap"><h2>About John</h2><div class="bar"></div><div class="about"><div><p>JPM Construction is John Maslowski's own carpentry and remodeling work in Billerica and the towns around it: kitchens, baths, decks, porches, stairs, framing repairs and finish work. This site is a portfolio of completed jobs, old and new, so you can see how the work turns out.</p><p>If you have a project in mind, reach out and we can talk about it.</p></div>
<div class="facts"><div><b>Name</b> John Maslowski</div><div><b>Based in</b> Billerica, MA</div><div><b>MA Construction Supervisor</b> License 90601</div><div><b>Day job</b> Director of Construction, Habitat for Humanity of Greater Lowell</div><div><b>Phone</b> <a href="tel:+19788313131">978 831 3131</a></div><div><b>Email</b> <a href="mailto:jmas1120.jm@gmail.com">jmas1120.jm@gmail.com</a></div></div></div></div></section>
{CONTACT}
<script>document.querySelectorAll('.filters button').forEach(b=>b.onclick=()=>{{document.querySelectorAll('.filters button').forEach(x=>x.classList.remove('on'));b.classList.add('on');const k=b.dataset.k;document.querySelectorAll('#workgrid .card').forEach(c=>c.style.display=(k==='all'||c.dataset.kind===k)?'':'none');}});</script>
</body></html>'''
open(os.path.join(ROOT,"index.html"),"w",encoding="utf-8").write(index)
print(f"built: {len(work)} work jobs, {len(hab)} habitat jobs")
