#!/usr/bin/env python3
"""MDB/STS QA docs agent: diff watched repos, draft wiki updates via Bedrock, open a PR."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from fnmatch import fnmatch
from pathlib import Path

import yaml

AGENT_DIR = Path(__file__).resolve().parent
WIKI_ROOT = AGENT_DIR.parent
SOURCES_PATH = AGENT_DIR / "sources.yml"
WATERMARKS_PATH = AGENT_DIR / "state" / "watermarks.json"
SKILL_PATH = AGENT_DIR / "skills" / "qa-docs-expert.md"
ALLOWED_PREFIX = "src/content/docs/mdb-sts/"
BOT_BRANCH = "docs-agent/mdb-sts"
DEFAULT_MODEL = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
DEFAULT_REGION = "us-east-1"
MAX_DIFF_CHARS = 80_000
MAX_OUTPUT_TOKENS = 8192
BEDROCK_READ_TIMEOUT = 300
CLONE_DEPTH = 50
EMPTY_WINDOW = 20
PR_HEAD_REF = BOT_BRANCH
LAST_RUN_DIRNAME = "last-run"


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def run_git(args: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=False,
        text=True,
        capture_output=True,
    )
    if check and result.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed ({result.returncode})\n{result.stderr or result.stdout}"
        )
    return result


def path_matches(path: str, pattern: str) -> bool:
    path = path.replace("\\", "/").lstrip("./")
    pattern = pattern.replace("\\", "/")
    if fnmatch(path, pattern):
        return True
    name = path.rsplit("/", 1)[-1]
    if fnmatch(name, pattern):
        return True
    if pattern.endswith("/**"):
        prefix = pattern[:-3].rstrip("/")
        return path == prefix or path.startswith(prefix + "/")
    if pattern.startswith("**/") and pattern.endswith("/**"):
        mid = pattern[3:-3]
        return f"/{mid}/" in f"/{path}/" or path.startswith(mid + "/")
    if pattern.startswith("**/"):
        return fnmatch(name, pattern[3:]) or fnmatch(path, pattern)
    return False


def any_glob(path: str, globs: list[str]) -> bool:
    return any(path_matches(path, g) for g in globs)


def clone_repo(github: str, dest: Path, token: str | None) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if token:
        url = f"https://x-access-token:{token}@github.com/{github}.git"
    else:
        url = f"https://github.com/{github}.git"
    run_git(["clone", "--depth", str(CLONE_DEPTH), url, str(dest)])


def current_sha(repo_dir: Path) -> str:
    return run_git(["rev-parse", "HEAD"], cwd=repo_dir).stdout.strip()


def diff_args(repo_dir: Path, since_sha: str) -> list[str]:
    """Arguments after `git diff` that select the commit window."""
    if since_sha:
        probe = run_git(["cat-file", "-t", since_sha], cwd=repo_dir, check=False)
        if probe.returncode != 0:
            run_git(["fetch", "--depth", "200"], cwd=repo_dir, check=False)
        probe = run_git(["cat-file", "-t", since_sha], cwd=repo_dir, check=False)
        if probe.returncode == 0:
            return [f"{since_sha}..HEAD"]
    log = run_git(["log", "-n", str(EMPTY_WINDOW), "--pretty=%H"], cwd=repo_dir, check=False)
    shas = [line.strip() for line in log.stdout.splitlines() if line.strip()]
    if len(shas) >= 2:
        return [shas[-1], "HEAD"]
    return ["HEAD"]


def changed_files(repo_dir: Path, since_sha: str) -> list[str]:
    result = run_git(["diff", "--name-only", *diff_args(repo_dir, since_sha)], cwd=repo_dir, check=False)
    return [p.strip() for p in result.stdout.splitlines() if p.strip()]


def print_path_list(label: str, paths: list[str]) -> None:
    if not paths:
        return
    print(f"    {label}:")
    for path in paths:
        print(f"      - {path}")


def filtered_diff(repo_dir: Path, since_sha: str, paths: list[str]) -> str:
    if not paths:
        return ""
    result = run_git(["diff", *diff_args(repo_dir, since_sha), "--", *paths], cwd=repo_dir, check=False)
    text = result.stdout if result.returncode == 0 else ""
    if len(text) > MAX_DIFF_CHARS:
        half = MAX_DIFF_CHARS // 2
        text = text[:half] + "\n\n... [diff truncated] ...\n\n" + text[-half:]
    return text


def collect_changes(sources: dict, watermarks: dict, work_dir: Path, token: str | None) -> tuple[list[dict], dict, list[str]]:
    """Return (repo_packs, new_watermarks, allowed_wiki_paths)."""
    packs: list[dict] = []
    new_marks = {"repos": dict(watermarks.get("repos") or {})}
    allowed: list[str] = []
    shared_ignore = list(sources.get("ignore") or [])
    for repo in sources["repos"]:
        github = repo["github"]
        ignore = shared_ignore + list(repo.get("ignore") or [])
        pages = repo.get("pages") or []
        allowed.extend(pages)
        dest = work_dir / github.replace("/", "__")
        print(f"Cloning {github} …")
        clone_repo(github, dest, token)
        head = current_sha(dest)
        old = (new_marks["repos"].get(github) or {}).get("sha") or ""
        names = changed_files(dest, old)
        relevant = [p for p in names if not any_glob(p, ignore)]
        ignored_paths = [p for p in names if any_glob(p, ignore)]
        skipped = len(ignored_paths)
        new_marks["repos"][github] = {"sha": head}
        print(
            f"  {github}: {len(names)} files in window, {skipped} ignored, "
            f"{len(relevant)} sent {old or '∅'} → {head[:7]}"
        )
        print_path_list("sent", relevant)
        print_path_list("ignored", ignored_paths)
        if not relevant:
            continue
        diff = filtered_diff(dest, old, relevant)
        packs.append(
            {
                "github": github,
                "old_sha": old or "(empty window)",
                "new_sha": head,
                "files": relevant,
                "diff": diff,
                "pages": pages,
            }
        )
    # unique allowed paths
    seen: list[str] = []
    for p in allowed:
        if p not in seen:
            seen.append(p)
    return packs, new_marks, seen


def load_wiki_pages(wiki_root: Path, paths: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for rel in paths:
        full = wiki_root / rel
        if full.is_file():
            out[rel] = full.read_text(encoding="utf-8")
    return out


def build_user_message(packs: list[dict], wiki_pages: dict[str, str], allowed: list[str]) -> str:
    parts = [
        "Allowed wiki paths (only these may appear in files[].path):",
        *[f"- {p}" for p in allowed],
        "",
        "## Current wiki pages",
    ]
    for path, body in wiki_pages.items():
        parts.append(f"### {path}\n\n```markdown\n{body}\n```\n")
    parts.append("## Source diffs since last watermark")
    for pack in packs:
        parts.append(
            f"### {pack['github']} `{pack['old_sha']}` → `{pack['new_sha']}`\n"
            f"Relevant files:\n" + "\n".join(f"- {f}" for f in pack["files"]) + "\n\n"
            f"```diff\n{pack['diff'] or '(no diff text)'}\n```\n"
        )
    parts.append(
        "## Reply format\n"
        "Use ---JSON--- for pr_summary/uncertain only. "
        "Put each full page in ---FILE: path--- ... ---END FILE---. "
        "Do not put markdown bodies inside JSON."
    )
    return "\n".join(parts)


def bedrock_client():
    import boto3
    from botocore.config import Config

    region = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or DEFAULT_REGION
    kwargs: dict = {
        "region_name": region,
        # Sonnet + a full wiki prompt can exceed boto3's default 60s read timeout.
        "config": Config(read_timeout=BEDROCK_READ_TIMEOUT, connect_timeout=10),
    }
    key = os.getenv("AWS_ACCESS_KEY_ID", "")
    secret = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    if key and secret:
        kwargs["aws_access_key_id"] = key
        kwargs["aws_secret_access_key"] = secret
    return boto3.client("bedrock-runtime", **kwargs)


def call_bedrock(system: str, user: str) -> tuple[str, str]:
    model = os.getenv("BEDROCK_MODEL_ID") or DEFAULT_MODEL
    client = bedrock_client()
    response = client.converse(
        modelId=model,
        system=[{"text": system}],
        messages=[{"role": "user", "content": [{"text": user}]}],
        inferenceConfig={"maxTokens": MAX_OUTPUT_TOKENS, "temperature": 0.0},
    )
    parts: list[str] = []
    for block in response["output"]["message"]["content"]:
        if "text" in block:
            parts.append(block["text"])
    return "\n".join(parts), str(response.get("stopReason") or "")


FILE_BLOCK_RE = re.compile(
    r"^---FILE:\s*(.+?)---\s*\n(.*?)---END FILE---",
    re.MULTILINE | re.DOTALL,
)


def parse_model_output(raw: str) -> dict:
    """Parse ---JSON--- metadata plus ---FILE: path--- bodies (not JSON-escaped pages)."""
    text = raw.strip()
    files: list[dict] = []
    for match in FILE_BLOCK_RE.finditer(text):
        files.append(
            {
                "path": match.group(1).strip(),
                "markdown": match.group(2).strip() + "\n",
            }
        )

    meta: dict = {"pr_summary": "", "uncertain": []}
    json_marker = re.search(r"---JSON---\s*", text)
    blob = ""
    if json_marker:
        blob = text[json_marker.end() :].lstrip()
    else:
        fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if fence:
            blob = fence.group(1).strip()
        elif text.startswith("{"):
            blob = text
    if blob:
        try:
            parsed, _ = json.JSONDecoder().raw_decode(blob)
            if isinstance(parsed, dict):
                meta["pr_summary"] = str(parsed.get("pr_summary") or "")
                if isinstance(parsed.get("uncertain"), list):
                    meta["uncertain"] = parsed["uncertain"]
                if not files and isinstance(parsed.get("files"), list):
                    files = parsed["files"]
        except json.JSONDecodeError:
            if not files:
                raise

    meta["files"] = files
    return meta


def validate_and_write(wiki_root: Path, payload: dict, allowed: list[str]) -> list[Path]:
    written: list[Path] = []
    allowed_set = set(allowed)
    for item in payload.get("files") or []:
        rel = str(item.get("path") or "").replace("\\", "/").lstrip("./")
        markdown = item.get("markdown")
        if rel not in allowed_set:
            raise SystemExit(f"Refusing path not in allow-list: {rel}")
        if not rel.startswith(ALLOWED_PREFIX) or not rel.endswith(".md"):
            raise SystemExit(f"Refusing path outside MDB/STS markdown: {rel}")
        dest = (wiki_root / rel).resolve()
        root = wiki_root.resolve()
        if dest != root and root not in dest.parents:
            raise SystemExit(f"Path escapes wiki root: {rel}")
        if not isinstance(markdown, str) or not markdown.strip():
            raise SystemExit(f"Empty markdown for {rel}")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(markdown if markdown.endswith("\n") else markdown + "\n", encoding="utf-8")
        written.append(dest)
        print(f"Made edits to {rel}")
    return written


def git_has_changes(wiki_root: Path) -> bool:
    r = run_git(["status", "--porcelain"], cwd=wiki_root)
    return bool(r.stdout.strip())


def ensure_bot_branch(wiki_root: Path) -> None:
    run_git(["fetch", "origin", BOT_BRANCH], cwd=wiki_root, check=False)
    has_remote = run_git(["rev-parse", "--verify", f"origin/{BOT_BRANCH}"], cwd=wiki_root, check=False)
    if has_remote.returncode == 0:
        run_git(["checkout", "-B", BOT_BRANCH, f"origin/{BOT_BRANCH}"], cwd=wiki_root)
    else:
        run_git(["checkout", "-B", BOT_BRANCH], cwd=wiki_root)


def commit_and_pr(wiki_root: Path, title: str, body: str, skip_pr: bool) -> None:
    run_git(["config", "user.name", "qa-docs-agent"], cwd=wiki_root, check=False)
    run_git(["config", "user.email", "qa-docs-agent@users.noreply.github.com"], cwd=wiki_root, check=False)
    run_git(["add", "src/content/docs/mdb-sts", "agent/state/watermarks.json"], cwd=wiki_root)
    if not git_has_changes(wiki_root):
        print("Nothing to commit.")
        return
    run_git(["commit", "-m", title], cwd=wiki_root)
    if skip_pr:
        print("Skipping PR (--skip-pr). Commit is local only.")
        return
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if not token:
        print("No GITHUB_TOKEN; skipping push/PR.")
        return
    env = os.environ.copy()
    env["GH_TOKEN"] = token
    subprocess.run(["git", "push", "-u", "origin", BOT_BRANCH], cwd=wiki_root, check=True, env=env)
    listed = subprocess.run(
        ["gh", "pr", "list", "--head", PR_HEAD_REF, "--base", "main", "--json", "number"],
        cwd=wiki_root,
        check=True,
        text=True,
        capture_output=True,
        env=env,
    )
    existing = json.loads(listed.stdout or "[]")
    if existing:
        print(f"Updated existing PR #{existing[0]['number']}")
        subprocess.run(
            ["gh", "pr", "edit", str(existing[0]["number"]), "--body", body],
            cwd=wiki_root,
            check=False,
            env=env,
        )
        return
    subprocess.run(
        [
            "gh",
            "pr",
            "create",
            "--base",
            "main",
            "--head",
            PR_HEAD_REF,
            "--title",
            title,
            "--body",
            body,
        ],
        cwd=wiki_root,
        check=True,
        env=env,
    )
    print("Opened PR.")


def last_run_dir(work_dir: Path) -> Path:
    return work_dir / LAST_RUN_DIRNAME


def save_last_run(work_dir: Path, user: str, output: str | None = None) -> Path:
    dest = last_run_dir(work_dir)
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "user.txt").write_text(user, encoding="utf-8")
    if output is not None:
        (dest / "output.txt").write_text(output, encoding="utf-8")
    return dest


def print_model_meta(payload: dict) -> None:
    summary = str(payload.get("pr_summary") or "").strip()
    uncertain = payload.get("uncertain") or []
    files = payload.get("files") or []
    print(f"pr_summary: {summary or '(none)'}")
    if uncertain:
        print("uncertain:")
        for item in uncertain:
            print(f"  - {item}")
    if not files:
        print("No wiki edits from the model.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Draft MDB/STS wiki updates from source repo diffs.")
    parser.add_argument("--wiki-root", type=Path, default=WIKI_ROOT)
    parser.add_argument("--work-dir", type=Path, default=AGENT_DIR / ".work")
    parser.add_argument("--skip-pr", action="store_true", help="Write files and commit locally; do not push.")
    parser.add_argument("--dry-run", action="store_true", help="Fetch diffs only; do not call Bedrock or write.")
    args = parser.parse_args()

    wiki_root: Path = args.wiki_root.resolve()
    sources = load_yaml(SOURCES_PATH)
    watermarks = load_json(WATERMARKS_PATH)
    # Public CBIIT clones do not need a token. Set GH_PAT only for private source repos.
    clone_token = os.getenv("GH_PAT")

    packs, new_marks, allowed = collect_changes(sources, watermarks, args.work_dir, clone_token)
    if not packs:
        print("No QA-relevant changes. Leaving watermarks unchanged so a later relevant commit is not skipped.")
        return 0

    if args.dry_run:
        print("Dry run: would send diffs for", ", ".join(p["github"] for p in packs))
        return 0

    if not os.getenv("AWS_ACCESS_KEY_ID") or not os.getenv("AWS_SECRET_ACCESS_KEY"):
        print("AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are required to call Bedrock.", file=sys.stderr)
        return 1

    wiki_pages = load_wiki_pages(wiki_root, allowed)
    skill = SKILL_PATH.read_text(encoding="utf-8")
    user = build_user_message(packs, wiki_pages, allowed)
    save_last_run(args.work_dir, user)
    print(f"Calling Bedrock ({os.getenv('BEDROCK_MODEL_ID') or DEFAULT_MODEL}) …")
    raw, stop_reason = call_bedrock(skill, user)
    dest = save_last_run(args.work_dir, user, raw)
    try:
        shown = dest.resolve().relative_to(wiki_root).as_posix()
    except ValueError:
        shown = str(dest)
    print(f"Bedrock prompt/reply: {shown}/")
    if stop_reason == "max_tokens":
        print("Warning: Bedrock stopped at max_tokens; reply may be truncated.", file=sys.stderr)
    try:
        payload = parse_model_output(raw)
    except json.JSONDecodeError as exc:
        print("Model did not return parseable output:\n", raw[:2000], file=sys.stderr)
        hint = " (output was truncated)" if stop_reason == "max_tokens" else ""
        raise SystemExit(f"Parse error{hint}: {exc}") from exc
    print_model_meta(payload)

    in_ci = bool(os.getenv("CI"))
    if in_ci and not args.skip_pr:
        ensure_bot_branch(wiki_root)

    WATERMARKS_PATH.write_text(json.dumps(new_marks, indent=2) + "\n", encoding="utf-8")
    validate_and_write(wiki_root, payload, allowed)

    summary = str(payload.get("pr_summary") or "MDB/STS wiki draft from docs-agent.").strip()
    uncertain = payload.get("uncertain") or []
    body_lines = [
        summary,
        "",
        "## Source SHAs",
        *[f"- `{p['github']}`: `{p['old_sha']}` → `{p['new_sha']}`" for p in packs],
    ]
    if uncertain:
        body_lines += ["", "## Uncertain", *[f"- {u}" for u in uncertain]]
    body_lines += [
        "",
        "Reviewer: every “how we test” claim should be backed by a path in the source diff. Do not auto-merge.",
    ]
    body = "\n".join(body_lines)
    files = payload.get("files") or []
    title = (
        "docs(mdb-sts): agent draft from source diffs"
        if files
        else "docs-agent: no wiki edits (advance watermarks)"
    )

    if in_ci and not args.skip_pr:
        commit_and_pr(wiki_root, title, body, skip_pr=False)
    elif args.skip_pr:
        commit_and_pr(wiki_root, title, body, skip_pr=True)
    else:
        print(
            "Made edits in the working tree. Use --skip-pr to commit locally, or run the GitHub Action to open a PR."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
