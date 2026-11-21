# Is your code calling a retiring Claude model?

## What this is

Every app that uses Claude names a specific model version in its code, such as `claude-sonnet-4-5`. Anthropic retires older versions on a published schedule. After the retirement date, any app still asking for that version stops getting answers.

Those version names usually get written into code once and then forgotten. Nobody looks at them again until a feature breaks. This project is a small script that finds every Claude model name in a project and flags the ones Anthropic has scheduled for retirement or already retired. For each one, it names the version to switch to.

Independent project by Joe Hughes. Anthropic has not reviewed or endorsed this project.

## Who this is for

- Managers and admins can read this section and "Why this matters now" to decide whether a team should run the check.
- Developers can go straight to "Run the check." It takes about five minutes and needs no account or API key.

## Why this matters now

Anthropic marked `claude-sonnet-4-5-20250929` as deprecated, meaning scheduled for retirement, on September 30, 2026. It retires on November 30, 2026. The recommended replacement is `claude-sonnet-5-5`. Source: [Anthropic model deprecations](https://platform.claude.com/docs/about-claude/model-deprecations).

AI coding assistants make the problem more common. In an audit of Claude-written code for Anthropic's own API, an automated script found that 108 of 114 answers written without web search (95%) named a model Anthropic no longer offered, almost always `claude-sonnet-4-5`. If an AI assistant wrote some of your code, check it.

## How the check works

The rest of this guide is hands-on. The script reads your project's files and looks for text shaped like a Claude model name. It compares each name with a copy of Anthropic's retirement table and reports one of these states:

| State | What it means |
|---|---|
| `RETIRED` | Anthropic has shut this version off. Calls to it fail. |
| `DEPRECATED` | Still works, but Anthropic has set a retirement date. |
| `UNLISTED` | Not in the table and not offered to your account. Only with `--live`. |
| `UNKNOWN` | Not in the table. Run with `--live` to find out more. |
| Active | Current. Shown only with `--all`. |

## Run the check

You need Python 3.9 or later. On Windows, type `py` wherever this guide says `python`. The basic check needs no API key and no other packages.

```bash
git clone https://github.com/JoeBHughes/model-id-check.git
cd model-id-check
python model_id_check.py /path/to/your/project
```

No Git? On the repository page, click **Code**, then **Download ZIP**. Unzip it and open a terminal in the `model-id-check` folder.

Sample output:

```text
Checked against deprecations table as of 2026-11-20
app.py:5  claude-sonnet-4-20250514  RETIRED: retired 2026-06-15. Calls fail. Use claude-sonnet-5-5
config.yaml:1  claude-3-5-haiku-20241022  RETIRED: retired 2026-02-19. Calls fail. Use claude-haiku-4-5-20251001
app.py:4  claude-sonnet-4-5  DEPRECATED: deprecated, retires 2026-11-30. Use claude-sonnet-5-5

3 of 5 model ID(s) at or above 'deprecated'.
```

Each line gives the file, the line number, the model name, its state and the replacement.

## Check against your live account

The bundled table covers the models on Anthropic's deprecations page. To catch names that appear nowhere in that table, add `--live`. The script then asks Anthropic's Models API which models your API key can use.

```bash
pip install anthropic
export ANTHROPIC_API_KEY=...   # PowerShell: $env:ANTHROPIC_API_KEY = Read-Host "Key"
python model_id_check.py /path/to/your/project --live
```

A name that appears in neither the table nor the live list is marked `UNLISTED`.

## Run it on every code change

Teams can make the check automatic. GitHub Actions, GitHub's built-in automation, can run the script every time someone proposes a code change in a pull request. The check fails when the change names a deprecated or retired model.

To set it up, copy `model_id_check.py`, `deprecations.json` and `.github/workflows/model-id-check.yml` into your repository. The script exits with code 1 when it finds a problem, which is the signal GitHub Actions and other CI systems read as a failure.

## Options

| Option | What it does |
|---|---|
| `path` | File or folder to scan. Defaults to the current folder. |
| `--live` | Also checks names against the Models API. Needs `ANTHROPIC_API_KEY`. |
| `--include-docs` | Also scans Markdown files and notebooks. |
| `--fail-on` | Lowest problem that fails the run: `retired`, `deprecated` (default) or `unknown`. |
| `--json` | Prints findings as JSON. |
| `--all` | Also lists model names that are current. |
| `--table` | Path to a different `deprecations.json`. |

## How the script decides

1. The script searches code and config files for strings shaped like Claude model names, such as `claude-sonnet-5-5` or `claude-opus-4-20250514`. Package names such as `claude-agent-sdk` don't match.
2. It drops any date suffix or `-latest`, so a short name like `claude-sonnet-4-5` matches its dated entry.
3. It looks the name up in `deprecations.json` and reports the state, the retirement date and the replacement.
4. With `--live`, it also checks names the table doesn't cover against the Models API.

## Fix what it finds

1. Replace each flagged name with the replacement the script names.
2. Put the model name in one place, such as a single constant or a config value, so the next change is one edit.
3. Run your tests. A newer model can answer differently, so check any output your code reads.

## Keep the table current

`deprecations.json` is a copy of Anthropic's deprecations table, dated in its `as_of` field. When Anthropic announces a change, update the matching entry and the date. Pull requests that update the table are welcome.

## Limits

- The script finds model names written as literal text. It can't see a name that your code builds while it runs or reads from a secret store.
- Amazon Bedrock and Google Cloud Vertex AI use their own model names and retirement schedules. On those platforms, treat the results as a starting point.
- The table is only as current as its `as_of` date. Use `--live` before a release.

## Run the tests

```bash
pip install pytest
python -m pytest tests
```

## License

MIT
