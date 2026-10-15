# jpmconstruction.org

Static site for JPM Construction (John Maslowski, Billerica MA), served by GitHub Pages at https://jpmconstruction.org.

## Adding work photos
1. Make a folder per job under `images/jobs/`, e.g. `images/jobs/MacEachern walk-in tub/`, and drop the photos in (any size; phone HEIC is fine with `pip install pillow-heif`).
2. Optional `caption.txt` in the folder for a one-line description.
3. Run `python3 tools/build_gallery.py` — it writes web-size copies to `images/web/`, a page per job under `jobs/`, and the tiles on the home page.
4. Commit and push. Originals in `images/jobs/` are kept in the repo as the master copies.

Company facts (license, address, phone) come from `JPM-Construction-HQ/FACTS.md`; change there first.
