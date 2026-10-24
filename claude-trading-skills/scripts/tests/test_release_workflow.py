"""Publishing must stay behind tag, ancestry, and remote-byte gates."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_release_workflow_is_tag_only_and_fail_closed() -> None:
    workflow = yaml.load(
        (ROOT / ".github/workflows/release.yml").read_text(), Loader=yaml.BaseLoader
    )
    assert workflow["on"] == {"push": {"tags": ["v*"]}}
    assert workflow["permissions"] == {"contents": "read"}
    job = workflow["jobs"]["release"]
    assert job["permissions"] == {"contents": "write"}
    assert job["runs-on"] == "ubuntu-latest"
    steps = job["steps"]
    assert all(
        len(step["uses"].split("@", 1)[1].split(" ")[0]) == 40 for step in steps if "uses" in step
    )
    runs = "\n".join(step.get("run", "") for step in steps)
    for required in (
        "git merge-base --is-ancestor",
        "git ls-remote --refs origin",
        "release_assets.py prepare",
        "gh release create",
        "--draft --verify-tag",
        "gh release download",
        "release_assets.py verify",
        'gh release edit "$RELEASE_TAG" --draft=false',
    ):
        assert required in runs
    commands = (
        "git merge-base --is-ancestor",
        "gh release create",
        "gh release download",
        "release_assets.py verify",
        'gh release edit "$RELEASE_TAG" --draft=false',
    )
    positions = [runs.index(command) for command in commands]
    assert positions == sorted(positions)
    assert 1 <= int(job["timeout-minutes"]) <= 15
    assert job["env"]["RELEASE_TAG"] == "${{ github.ref_name }}"
    for step in steps:
        if "run" in step:
            assert step["shell"] == "bash"
            assert step["run"].splitlines()[0] == "set -euo pipefail"
            assert "${{" not in step["run"]
    for line in runs.splitlines():
        if "gh release " in line or "prepare --tag" in line:
            assert '"$RELEASE_TAG"' in line
    assert "--draft --verify-tag" in runs


def test_release_workflow_guards_cannot_be_bypassed() -> None:
    workflow = yaml.load(
        (ROOT / ".github/workflows/release.yml").read_text(), Loader=yaml.BaseLoader
    )
    steps = workflow["jobs"]["release"]["steps"]
    runs = "\n".join(step.get("run", "") for step in steps)
    for line in runs.splitlines():
        # set -e ignores failures of non-final commands in && / || lists.
        assert "&& test" not in line and "|| true" not in line
        if line.strip().startswith("test "):
            assert "&&" not in line and "||" not in line
    edit = runs.index('gh release edit "$RELEASE_TAG" --draft=false')
    remote_checks = [i for i in range(len(runs)) if runs.startswith("git ls-remote --refs", i)]
    assert len(remote_checks) == 2
    assert runs.index("gh release download") < remote_checks[1] < edit
    assert runs.index("--json isDraft") < edit
    assert runs.index("release_assets.py prepare") < runs.index("git merge-base --is-ancestor")
    assert runs.index("Release already exists") < runs.index("gh release create")
    lines = [line.strip() for line in runs.splitlines()]
    exists = next(i for i, line in enumerate(lines) if "Release already exists" in line)
    assert lines[exists + 1] == "exit 1"
