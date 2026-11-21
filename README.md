# Is your code calling a retiring Claude model?

A short guide and a small Python script that finds every Claude model ID in your codebase and flags the ones Anthropic has deprecated or retired. It tells you the replacement for each one.

Independent project by Joe Hughes. Not affiliated with or endorsed by Anthropic.

## Why this matters

Model IDs get written into code once and then forgotten. Nobody looks at them again until a call fails.

Anthropic deprecated `claude-sonnet-4-5-20250929` on September 30, 2026, and retires it on November 30, 2026. The recommended replacement is `claude-sonnet-5-5`. Source: [Anthropic model deprecations](https://platform.claude.com/docs/about-claude/model-deprecations).

Coding agents make this worse. In an audit of Claude-written Claude API code, an automated script found that 108 of 114 answers written without web search (95%) named a model the Models API no longer listed, almost always `claude-sonnet-4-5`. If an agent wrote some of your code, check it.

## Quickstart

You need Python 3.9 or later. The basic check needs no API key and no other packages.

```bash
git clone https://github.com/<your-account>/model-id-check.git
cd model-id-check
python model_id_check.py /path/to/your/project
```

Sample output:

```text
Checked against deprecations table as of 2026-11-20
app.py:5  claude-sonnet-4-20250514  RETIRED: retired 2026-06-15. Calls fail. Use claude-sonnet-5-5
config.yaml:1  claude-3-5-haiku-20241022  RETIRED: retired 2026-02-19. Calls fail. Use claude-haiku-4-5-20251001
app.py:4  claude-sonnet-4-5  DEPRECATED: deprecated, retires 2026-11-30. Use claude-sonnet-5-5

3 of 5 model ID(s) at or above 'deprecated'.
```

The script exits with code 1 when it finds a problem, so you can use it in CI.

## Check against the live Models API

The bundled table covers the models on Anthropic's deprecations page. To catch IDs that appear nowhere in that table, add `--live`. The script then asks the Models API which models your key can call.

```bash
pip install anthropic
export ANTHROPIC_API_KEY=...   # PowerShell: $env:ANTHROPIC_API_KEY = "..."
python model_id_check.py /path/to/your/project --live
```

An ID that appears in neither the table nor the live list is marked `UNLISTED`.

## Run it on every pull request

Copy `model_id_check.py`, `deprecations.json` and `.github/workflows/model-id-check.yml` into your repository. GitHub Actions then runs the script on each pull request and fails the check when the code names a deprecated or retired model.

## Options

| Option | What it does |
|---|---|
| `path` | File or folder to scan. Defaults to the current folder. |
| `--live` | Also checks IDs against the Models API. Needs `ANTHROPIC_API_KEY`. |
| `--include-docs` | Also scans Markdown files and notebooks. |
| `--fail-on` | Lowest problem that fails the run: `retired`, `deprecated` (default) or `unknown`. |
| `--json` | Prints findings as JSON. |
| `--all` | Also lists model IDs that are current. |
| `--table` | Path to a different `deprecations.json`. |

## How the script decides

1. The script searches code and config files for strings shaped like Claude model IDs, such as `claude-sonnet-5-5` or `claude-opus-4-20250514`. Package names such as `claude-agent-sdk` don't match.
2. It drops any date suffix or `-latest`, so an alias like `claude-sonnet-4-5` matches its dated entry.
3. It looks the ID up in `deprecations.json` and reports the state, the retirement date and the replacement.
4. With `--live`, it also checks IDs the table doesn't cover against the Models API.

## Fix what it finds

1. Replace each flagged ID with the replacement the script names.
2. Put the model ID in one place, such as a single constant or a config value, so the next change is one edit.
3. Run your tests. A newer model can answer differently, so check any output your code parses.

## Keep the table current

`deprecations.json` is a copy of Anthropic's deprecations table, dated in its `as_of` field. When Anthropic announces a change, update the matching entry and the date. Pull requests that update the table are welcome.

## Limits

- The script finds model IDs written as literal text. It can't see an ID that your code builds at runtime or reads from a secret store.
- Amazon Bedrock and Google-managed Vertex AI use their own model IDs and retirement schedules. On those platforms, treat the results as a starting point.
- The table is only as current as its `as_of` date. Use `--live` before a release.

## Run the tests

```bash
pip install pytest
python -m pytest tests
```

## License

MIT
