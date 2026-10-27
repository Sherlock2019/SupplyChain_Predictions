#!/usr/bin/env python3
"""Build and import the SCInsight Functions & Code Explorer Agentflows (documentation flows; stdlib only).

    python3 code_explorer/tools/build_code_explorer.py                      # 1. registry + codemap_spec.json from the source
    python3 flowise/code_explorer/deploy_code_map.py build                  # 2. Flowise exports (node classes of the installed Flowise)
    python3 flowise/code_explorer/deploy_code_map.py import --flowise-url http://127.0.0.1:3101

import creates or updates ONLY flows named "SCInsight — Functions & Code Explorer" / "SCInsight Code Explorer · ..." (category
"SCInsight Code Explorer"); it never touches other flows. Uses the admin account and the existing API key FLOWISE_SCI_API_KEY from .env.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))
from bootstrap import Flowise, log, read_env  # noqa: E402

CATEGORY = "SCInsight Code Explorer"


def build(compose_dir: Path) -> int:
    cmd = ["docker", "compose", "exec", "-T", "-w", "/usr/local/lib/node_modules/flowise", "flowise", "node", "/opt/flows/code_explorer/build-code-map.cjs"]
    res = subprocess.run(cmd, cwd=compose_dir, capture_output=True, text=True, check=False)
    if res.returncode != 0:
        raise SystemExit(f"build-code-map.cjs failed: {res.stderr[-2000:]}")
    flows = json.loads(res.stdout)
    manifest = []
    for f in flows:
        slug = "00_master" if f["category"] == "master" else f["category"]
        path = HERE / f"{slug}.json"
        path.write_text(json.dumps({"name": f["name"], "type": "AGENTFLOW", **f["flow"]}, ensure_ascii=False) + "\n", encoding="utf-8")
        manifest.append({"name": f["name"], "file": str(path.relative_to(ROOT)), "nodes": len(f["flow"]["nodes"]), "edges": len(f["flow"]["edges"])})
        log(f"{f['name']}: {len(f['flow']['nodes'])} nodes, {len(f['flow']['edges'])} edges -> {path.relative_to(ROOT)}")
    (HERE / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    return 0


def import_flows(args) -> int:
    env = read_env(Path(args.env_file))
    manifest = json.loads((HERE / "manifest.json").read_text())
    flowise = Flowise(args.flowise_url)
    flowise.wait()
    flowise.call("POST", "/api/v1/auth/login", {"email": env.get("FLOWISE_ADMIN_EMAIL", "admin@aurelia.local"), "password": env["FLOWISE_ADMIN_PASSWORD"]}, auth="none")
    flowise.api_key = env["FLOWISE_SCI_API_KEY"]
    existing = {r["name"]: r for r in flowise.call("GET", "/api/v1/chatflows?type=AGENTFLOW", auth="key")}
    ids = {}
    for m in manifest:
        data = json.loads((ROOT / m["file"]).read_text(encoding="utf-8"))
        body = {"name": m["name"], "flowData": json.dumps({"nodes": data["nodes"], "edges": data["edges"]}), "deployed": False, "isPublic": False,
                "type": "AGENTFLOW", "category": CATEGORY}
        row = flowise.call("PUT", f"/api/v1/chatflows/{existing[m['name']]['id']}", body, auth="key") if m["name"] in existing \
            else flowise.call("POST", "/api/v1/chatflows", body, auth="key")
        back = flowise.call("GET", f"/api/v1/chatflows/{row['id']}", auth="key")  # read back: what Flowise really stored
        stored = json.loads(back["flowData"])
        ok = len(stored["nodes"]) == m["nodes"] and len(stored["edges"]) == m["edges"]
        ids[m["name"]] = {"id": row["id"], "url": f"{args.flowise_url}/v2/agentcanvas/{row['id']}", "verified": ok}
        log(f"{m['name']} -> {row['id']} ({len(stored['nodes'])} nodes, {len(stored['edges'])} edges stored{'' if ok else ' — MISMATCH'})")
    (HERE / "imported.json").write_text(json.dumps(ids, indent=1) + "\n")
    print(json.dumps(ids, indent=1))
    return 0 if all(v["verified"] for v in ids.values()) else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--compose-dir", default=str(ROOT))
    i = sub.add_parser("import")
    i.add_argument("--env-file", default=str(ROOT / ".env"))
    i.add_argument("--flowise-url", default="http://127.0.0.1:3000")
    args = ap.parse_args()
    return build(Path(args.compose_dir)) if args.cmd == "build" else import_flows(args)


if __name__ == "__main__":
    sys.exit(main())
