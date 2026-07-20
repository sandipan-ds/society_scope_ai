"""Evaluation runner for the chat layer.

Runs the query set in `data/eval_queries/eval_queries.jsonl` through
POST /chat/query (in-process, no live server needed) and scores:

  1. routing accuracy      — did the router pick the expected route?
  2. refusal consistency   — unauthorized queries refused, without leaking data
  3. citation correctness  — document-backed answers cited; SQL answers not
  4. content checks        — must_contain / must_not_contain substrings

Usage (from the repo root):

    python scripts/run_eval.py                  # run all cases
    python scripts/run_eval.py --category public
    python scripts/run_eval.py --id una-03
    python scripts/run_eval.py --quiet          # failures + summary only

Exit code is 0 when every case passes, 1 otherwise (CI-friendly).

Case format (JSONL, one object per line):

    {"id": "pub-01", "category": "public", "query": "...",
     "user": "resident1@society.in" | null,
     "expect_route": "public|private|hybrid|refused",
     "expect_refusal": true|false        (default false),
     "expect_citations": true|false      (optional),
     "must_contain": ["..."],            (optional, case-insensitive)
     "must_not_contain": ["..."]}        (optional, case-insensitive)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "backend"))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

DEFAULT_FILE = REPO_ROOT / "data" / "eval_queries" / "eval_queries.jsonl"
DEV_PASSWORD = "replace-on-first-login"

client = TestClient(app)
_tokens: dict[str, str] = {}


def token_for(email: str) -> str:
    if email not in _tokens:
        resp = client.post("/auth/login", json={"email": email, "password": DEV_PASSWORD})
        if resp.status_code != 200:
            raise RuntimeError(f"login failed for {email}: {resp.text}")
        _tokens[email] = resp.json()["access_token"]
    return _tokens[email]


def run_case(case: dict) -> list[str]:
    """Execute one case; returns a list of failure reasons (empty = pass)."""
    headers = {}
    if case.get("user"):
        headers["Authorization"] = f"Bearer {token_for(case['user'])}"

    resp = client.post("/chat/query", json={"query": case["query"]}, headers=headers)
    if resp.status_code != 200:
        return [f"HTTP {resp.status_code}: {resp.text[:120]}"]
    body = resp.json()

    answer = body["answer"]
    lower = answer.lower()
    failures: list[str] = []

    if body["route_type"] != case["expect_route"]:
        failures.append(f"route: expected {case['expect_route']}, got {body['route_type']}")

    if body["refused"] != case.get("expect_refusal", False):
        failures.append(f"refused: expected {case.get('expect_refusal', False)}, got {body['refused']}")

    if "expect_citations" in case:
        has_citations = len(body["citations"]) > 0
        if has_citations != case["expect_citations"]:
            failures.append(
                f"citations: expected {'>=1' if case['expect_citations'] else '0'}, "
                f"got {len(body['citations'])}"
            )

    for needle in case.get("must_contain", []):
        if needle.lower() not in lower:
            failures.append(f"answer missing {needle!r}")

    for needle in case.get("must_not_contain", []):
        if needle.lower() in lower:
            failures.append(f"answer leaked forbidden {needle!r}")

    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the chat evaluation query set.")
    parser.add_argument("--file", type=Path, default=DEFAULT_FILE, help="JSONL eval file")
    parser.add_argument("--category", choices=["public", "private", "unauthorized", "hybrid"])
    parser.add_argument("--id", dest="case_id", help="run a single case by id")
    parser.add_argument("--quiet", action="store_true", help="print failures and summary only")
    args = parser.parse_args()

    cases = [
        json.loads(line)
        for line in args.file.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if args.category:
        cases = [c for c in cases if c["category"] == args.category]
    if args.case_id:
        cases = [c for c in cases if c["id"] == args.case_id]
    if not cases:
        print("no cases matched")
        return 1

    results: list[tuple[dict, list[str]]] = []
    for case in cases:
        failures = run_case(case)
        results.append((case, failures))
        if not args.quiet or failures:
            status = "PASS" if not failures else "FAIL"
            user = case.get("user") or "anon"
            print(f"{status} {case['id']:7s} [{case['category']:12s}] ({user}) {case['query']}")
            for reason in failures:
                print(f"     -> {reason}")

    passed = sum(1 for _, f in results if not f)
    total = len(results)

    def metric(category: str) -> str:
        subset = [(c, f) for c, f in results if c["category"] == category]
        if not subset:
            return "—"
        ok = sum(1 for _, f in subset if not f)
        return f"{ok}/{len(subset)}"

    print("\n" + "=" * 60)
    print(f"TOTAL        {passed}/{total} passed")
    print(f"  public        {metric('public')}   (routing + citations + fallback)")
    print(f"  private       {metric('private')}   (scoping + content)")
    print(f"  unauthorized  {metric('unauthorized')}   (refusal + no leakage)")
    print(f"  hybrid        {metric('hybrid')}   (SQL + docs combined)")
    print("=" * 60)

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
