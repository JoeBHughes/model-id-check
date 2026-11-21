#!/usr/bin/env python3
"""Find Claude model IDs in a codebase and flag the ones that are deprecated or retired.

The script reads deprecations.json, a copy of Anthropic's model deprecations table.
With --live, it also asks the Models API which models your API key can use, so it
can flag IDs that appear in neither list.
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

# Matches model IDs such as claude-sonnet-5-5, claude-opus-4-20250514 or
# claude-3-5-haiku-latest. Package names like claude-agent-sdk do not match,
# because "agent" is not a model family.
MODEL_RE = re.compile(
    r"claude-(?:opus|sonnet|haiku|fable|mythos|instant)[a-z0-9.\-]*[a-z0-9]"
    r"|claude-[0-9][a-z0-9.\-]*[a-z0-9]"
)
CODE_EXT = {".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".go", ".java", ".rb",
            ".php", ".cs", ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".env"}
DOC_EXT = {".md", ".mdx", ".rst", ".txt", ".ipynb"}
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "dist", "build", "__pycache__", ".next"}
SEVERITY = {"retired": 3, "unlisted": 3, "deprecated": 2, "unknown": 1, "active": 0}


def base_id(model_id):
    """Drop a date suffix or -latest so aliases match their dated versions."""
    m = model_id.lower()
    m = re.sub(r"-\d{8}$", "", m)
    m = re.sub(r"-latest$", "", m)
    return m


def load_table(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    table = {}
    for entry in data["models"]:
        table[entry["id"]] = entry
        table.setdefault(base_id(entry["id"]), entry)
    return data, table


def live_model_ids():
    """Ask the Models API which models this API key can call."""
    import anthropic  # imported here so offline runs need no SDK
    client = anthropic.Anthropic()
    ids = set()
    for model in client.models.list():
        ids.add(model.id)
        ids.add(base_id(model.id))
    return ids


def classify(model_id, table, live_ids=None):
    entry = table.get(model_id) or table.get(base_id(model_id))
    if entry:
        return entry["state"], entry
    if live_ids is not None:
        if model_id in live_ids or base_id(model_id) in live_ids:
            return "active", None
        return "unlisted", None
    return "unknown", None


def iter_files(root, include_docs):
    exts = CODE_EXT | (DOC_EXT if include_docs else set())
    root = Path(root)
    if root.is_file():
        yield root
        return
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file() and (path.suffix.lower() in exts or path.name.startswith(".env")):
            yield path


def scan(root, table, live_ids=None, include_docs=False, skip=()):
    findings = []
    skip = {Path(p).resolve() for p in skip}
    for path in iter_files(root, include_docs):
        if path.resolve() in skip:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            for match in MODEL_RE.finditer(line):
                model_id = match.group(0)
                state, entry = classify(model_id, table, live_ids)
                findings.append({
                    "file": str(path), "line": lineno, "model": model_id, "state": state,
                    "retires": entry.get("retires") if entry else None,
                    "replacement": entry.get("replacement") if entry else None,
                })
    return findings


def describe(f):
    if f["state"] == "retired":
        return f"retired {f['retires']}. Calls fail. Use {f['replacement'] or 'a current model'}"
    if f["state"] == "deprecated":
        when = f["retires"] or "a date to be announced"
        return f"deprecated, retires {when}. Use {f['replacement'] or 'a current model'}"
    if f["state"] == "unlisted":
        return "not in the Models API list for your key"
    if f["state"] == "unknown":
        return "not in deprecations.json. Run with --live to check it"
    return "current"


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("path", nargs="?", default=".", help="file or folder to scan")
    p.add_argument("--table", default=str(Path(__file__).with_name("deprecations.json")),
                   help="path to deprecations.json")
    p.add_argument("--live", action="store_true",
                   help="also check IDs against the Models API (needs ANTHROPIC_API_KEY)")
    p.add_argument("--include-docs", action="store_true", help="also scan Markdown and notebooks")
    p.add_argument("--fail-on", choices=["retired", "deprecated", "unknown"], default="deprecated",
                   help="lowest problem that makes the script exit with code 1")
    p.add_argument("--json", action="store_true", help="print findings as JSON")
    p.add_argument("--all", action="store_true", help="also list current model IDs")
    args = p.parse_args(argv)

    data, table = load_table(args.table)
    live_ids = None
    if args.live:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            print("--live needs ANTHROPIC_API_KEY in your environment.", file=sys.stderr)
            return 2
        live_ids = live_model_ids()

    findings = scan(args.path, table, live_ids, args.include_docs, skip=[args.table])
    shown = findings if args.all else [f for f in findings if f["state"] != "active"]
    threshold = {"retired": 3, "deprecated": 2, "unknown": 1}[args.fail_on]
    failing = [f for f in findings if SEVERITY[f["state"]] >= threshold]

    if args.json:
        print(json.dumps({"table_as_of": data.get("as_of"), "findings": shown}, indent=2))
    else:
        print(f"Checked against deprecations table as of {data.get('as_of')}"
              + (" and the live Models API" if live_ids is not None else ""))
        if not shown:
            print(f"No problems found in {len(findings)} model ID(s).")
        for f in sorted(shown, key=lambda f: (-SEVERITY[f["state"]], f["file"], f["line"])):
            print(f"{f['file']}:{f['line']}  {f['model']}  {f['state'].upper()}: {describe(f)}")
        print(f"\n{len(failing)} of {len(findings)} model ID(s) at or above '{args.fail_on}'.")
    return 1 if failing else 0


if __name__ == "__main__":
    sys.exit(main())
