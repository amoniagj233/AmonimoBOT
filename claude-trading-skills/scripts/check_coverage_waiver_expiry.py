"""Offline expiry report; GitHub notification requires explicit --notify."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.ci_test_matrix import ROOT, MatrixError, exception_expiry_report, load_policy

MARKER = "<!-- coverage-waiver-expiry-523 -->"
SUPERSEDED_MARKER = "<!-- coverage-waiver-expiry-523-superseded -->"
ISSUE = 523
BOT = "github-actions[bot]"


def build_report(root: Path, today: date) -> dict:
    # Validate with the canonical loader, but allow past dates for monitoring.
    # CI continues to use its real date and rejects expired exceptions.
    policy = load_policy(root, today=date.min)
    rows = exception_expiry_report(policy, today)
    for row in rows:
        if row["days_remaining"] < 0:
            row["status"] = "expired"
    return {"as_of": today.isoformat(), "exceptions": rows}


def alert_body(report: dict, owner: str) -> str | None:
    alerts = [row for row in report["exceptions"] if row["status"] != "active"]
    if not alerts:
        return None
    lines = [MARKER, f"@{owner} coverage exceptions require action before CI expiry.", ""]
    for row in alerts:
        # Stable across daily runs; notify again only on meaningful state changes.
        state = "EXPIRED" if row["status"] == "expired" else "EXPIRING"
        lines.append(
            f"- {state}: `{row['kind']}` / `{row['id']}` expires {row['expires_on']} "
            f"(tracking #{row['issue']})."
        )
    lines += [
        "",
        "Retire or justify renewal of each exception. Expiry day is valid; CI fails the next day.",
    ]
    return "\n".join(lines)


def gh_api(endpoint: str, *, body: str | None = None, method: str = "GET", paginate: bool = False):
    args = ["gh", "api", endpoint, "--method", method]
    if paginate:
        args += ["--paginate", "--slurp"]
    if body is not None:
        args += ["--input", "-"]
    result = subprocess.run(
        args,
        input=json.dumps({"body": body}) if body is not None else None,
        text=True,
        capture_output=True,
        check=True,
        timeout=120,
    )
    return json.loads(result.stdout)


def alert_states(body: str) -> dict[tuple[str, str, str, str], str]:
    """Read stable alert rows, independently of surrounding prose and row order."""
    return {
        (kind, identifier, expiry, issue): state
        for state, kind, identifier, expiry, issue in re.findall(
            r"^- (EXPIRING|EXPIRED): `([^`]+)` / `([^`]+)` expires "
            r"(\d{4}-\d{2}-\d{2}) \(tracking #(\d+)\)\.$",
            body,
            re.MULTILINE,
        )
    }


def needs_new_alert(previous: str, current: str) -> bool:
    old = alert_states(previous)
    return any(
        identity not in old or (state == "EXPIRED" and old[identity] != "EXPIRED")
        for identity, state in alert_states(current).items()
    )


def notify(report: dict, repo: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9-]+/[A-Za-z0-9_.-]+", repo):
        raise ValueError("repository must be owner/name")
    owner = repo.split("/")[0]
    pages = gh_api(f"repos/{repo}/issues/{ISSUE}/comments?per_page=100", paginate=True)
    managed = [
        comment
        for page in pages
        for comment in page
        if comment["user"]["login"] == BOT and comment.get("body", "").startswith(MARKER)
    ]
    if len(managed) > 1:
        raise ValueError("multiple managed expiry comments; reconcile manually")
    existing = managed[0] if managed else None
    body = alert_body(report, owner)
    if body is None:
        if existing is None:
            return "no-alert"
        body = (
            MARKER
            + "\nNo exceptions currently expire within 14 days. Waiver retirement remains tracked in #523."
        )
    if existing and existing["body"] == body:
        return "unchanged"
    if existing:
        if not needs_new_alert(existing["body"], body):
            gh_api(f"repos/{repo}/issues/comments/{existing['id']}", body=body, method="PATCH")
            return "updated"
        # Retire first: if POST fails, the next run retries with no active comment.
        # A failed PATCH aborts before POST, preserving the duplicate guard.
        superseded = existing["body"].replace(MARKER, SUPERSEDED_MARKER, 1)
        superseded = superseded.replace(f"@{owner}", owner)
        gh_api(
            f"repos/{repo}/issues/comments/{existing['id']}",
            body=superseded + "\n\nSuperseded by a subsequent expiry alert.",
            method="PATCH",
        )
    gh_api(f"repos/{repo}/issues/{ISSUE}/comments", body=body, method="POST")
    return "created"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--notify", metavar="OWNER/REPO", help="Opt in to updating Issue #523")
    args = parser.parse_args(argv)
    try:
        report = build_report(args.root, datetime.now(timezone.utc).date())
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        if args.notify:
            print(notify(report, args.notify))
    except (MatrixError, OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
