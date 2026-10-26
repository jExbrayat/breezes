"""Serve the interactive breeze map on http://localhost:8000.

Exports any run in out/ that is missing (or older) in web/data/ first, so
`uv run python scripts/serve.py` is enough after `scripts/run_alps.py`.
"""
import argparse
import functools
import http.server
import json
import sys

from breezes.dem import ROOT

sys.path.insert(0, str(ROOT / "scripts"))
import export_web  # noqa: E402

WEB = ROOT / "web"


def stale_runs():
    out = []
    for f in sorted((ROOT / "out").glob("*/fields.npz")):
        meta = WEB / "data" / f.parent.name / "meta.json"
        if (not meta.exists() or meta.stat().st_mtime < f.stat().st_mtime
                or json.loads(meta.read_text()).get("format") != export_web.FORMAT):
            out.append(f.parent.name)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--host", default="127.0.0.1")
    a = ap.parse_args()
    todo = stale_runs()
    if todo:
        print("exporting:", ", ".join(todo))
        export_web.main(todo)
    else:
        export_web.write_index()
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(WEB))
    with http.server.ThreadingHTTPServer((a.host, a.port), handler) as srv:
        print(f"Alpine Breeze Atlas → http://localhost:{a.port}   (Ctrl+C to stop)")
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
