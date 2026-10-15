"""
export_from_photos.py — turn photo-review-answers.json (from Reference/Photo review/review.html)
into job folders under images/jobs/ by exporting the originals from the Mac Photos app.

Usage: python3 tools/export_from_photos.py ~/Downloads/photo-review-answers.json
Groups typed "jpm", "habitat" or "house" are exported; "skip" ignored. Groups with the same
job name are merged into one folder. Photos still in iCloud are downloaded by Photos during export
(this can take a while; keep Photos open). Afterwards run tools/build_site.py.
It also writes/updates jobs.json with kind + a placeholder title.
"""
import json, os, re, subprocess, sys
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ans=json.load(open(sys.argv[1]))
def slugname(s): return re.sub(r"[^A-Za-z0-9 ]+","",s).strip() or "Unnamed job"
jobs={}
for gid,v in ans.items():
    if v.get("type") in ("jpm","habitat","house"):
        name=slugname(v.get("name") or f"{v['type']} group {gid}")
        jobs.setdefault(name,{"kind":v["type"],"uuids":[]})["uuids"]+=v["uuids"]
meta_path=os.path.join(ROOT,"jobs.json"); meta=json.load(open(meta_path)) if os.path.exists(meta_path) else {}
for name,j in jobs.items():
    dest=os.path.join(ROOT,"images","jobs",name); os.makedirs(dest,exist_ok=True)
    ids=",".join(f'"{u}"' for u in j["uuids"])
    script=f'''
    set outFolder to POSIX file "{dest}" as alias
    tell application "Photos"
        set ids to {{{ids}}}
        set items to {{}}
        repeat with i in ids
            try
                set end of items to media item id (i as string)
            end try
        end repeat
        if (count of items) > 0 then export items to outFolder with using originals
    end tell'''
    print(f"exporting {len(j['uuids'])} → {dest}"); subprocess.run(["osascript","-e",script],check=False)
    meta.setdefault(name,{"title":name,"kind":j["kind"]})
json.dump(meta,open(meta_path,"w"),indent=1); print("jobs.json updated; now run tools/build_site.py")
