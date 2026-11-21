from pathlib import Path

import model_id_check as m

HERE = Path(__file__).parent
TABLE = HERE.parent / "deprecations.json"


def run(*args):
    return m.main([str(HERE / "fixtures"), "--table", str(TABLE), *args])


def findings():
    _, table = m.load_table(TABLE)
    return {f["model"]: f for f in m.scan(HERE / "fixtures", table)}


def test_alias_matches_dated_deprecated_entry():
    f = findings()["claude-sonnet-4-5"]
    assert f["state"] == "deprecated"
    assert f["retires"] == "2026-11-30"
    assert f["replacement"] == "claude-sonnet-5-5"


def test_retired_models_flagged():
    f = findings()
    assert f["claude-sonnet-4-20250514"]["state"] == "retired"
    assert f["claude-3-5-haiku-20241022"]["replacement"] == "claude-haiku-4-5-20251001"


def test_current_models_pass_and_packages_ignored():
    f = findings()
    assert f["claude-sonnet-5-5"]["state"] == "active"
    assert f["claude-haiku-5-5"]["state"] == "active"
    assert "claude-agent-sdk" not in f


def test_unknown_without_live_and_unlisted_with_live():
    _, table = m.load_table(TABLE)
    assert m.classify("claude-made-up-9", table)[0] == "unknown"
    assert m.classify("claude-made-up-9", table, live_ids={"claude-sonnet-5-5"})[0] == "unlisted"


def test_exit_codes():
    assert run() == 1
    assert run("--fail-on", "retired") == 1
    assert m.main([str(HERE / "fixtures" / "app.py"), "--table", str(TABLE), "--fail-on", "retired"]) == 1
