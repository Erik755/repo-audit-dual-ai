#!/usr/bin/env python3
"""Generate a local repository-health report with optional dual-provider advice."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1.0"
IGNORED_DIRS = {
    ".git", ".hg", ".svn", ".venv", "venv", "node_modules", "vendor", "dist", "build",
    "target", "coverage", ".coverage", ".next", "out", "__pycache__", ".mypy_cache",
    ".pytest_cache", ".ruff_cache",
}
LANGUAGES = {
    ".py": "Python", ".js": "JavaScript", ".jsx": "JavaScript", ".ts": "TypeScript",
    ".tsx": "TypeScript", ".java": "Java", ".kt": "Kotlin", ".kts": "Kotlin",
    ".go": "Go", ".rs": "Rust", ".rb": "Ruby", ".php": "PHP", ".cs": "C#",
    ".c": "C", ".h": "C/C++", ".cc": "C/C++", ".cpp": "C/C++", ".hpp": "C/C++",
    ".swift": "Swift", ".scala": "Scala", ".sh": "Shell", ".ps1": "PowerShell",
    ".vue": "Vue", ".svelte": "Svelte", ".dart": "Dart", ".ex": "Elixir", ".exs": "Elixir",
}
TEXT_EXTENSIONS = set(LANGUAGES) | {
    ".md", ".rst", ".txt", ".toml", ".yaml", ".yml", ".json", ".xml", ".ini", ".cfg",
    ".gradle", ".properties", ".sql", ".html", ".css", ".scss",
}
MANIFESTS = {
    "pyproject.toml", "setup.py", "setup.cfg", "requirements.txt", "package.json", "pom.xml",
    "build.gradle", "build.gradle.kts", "go.mod", "cargo.toml", "gemfile", "composer.json",
}
LOCKFILES = {
    "poetry.lock", "uv.lock", "pipfile.lock", "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "cargo.lock", "gemfile.lock", "composer.lock", "gradle.lockfile",
}


def _is_test(path: Path) -> bool:
    lower_parts = {part.lower() for part in path.parts}
    name = path.name.lower()
    return bool(
        lower_parts & {"test", "tests", "spec", "specs", "__tests__"}
        or name.startswith("test_")
        or re.search(r"(?:_test|\.test|\.spec)\.[^.]+$", name)
    )


def _walk(repo: Path) -> list[Path]:
    files: list[Path] = []
    for root, dirs, names in os.walk(repo):
        dirs[:] = sorted(d for d in dirs if d.lower() not in IGNORED_DIRS and not d.startswith(".rqe-history-"))
        root_path = Path(root)
        for name in sorted(names):
            path = root_path / name
            try:
                if path.is_file() and not path.is_symlink():
                    files.append(path)
            except OSError:
                continue
    return files


def _line_count(path: Path) -> int:
    try:
        if path.stat().st_size > 2_000_000:
            return 0
        return len(path.read_text(encoding="utf-8", errors="ignore").splitlines())
    except OSError:
        return 0


def collect_inventory(repo: Path) -> tuple[dict[str, Any], dict[str, bool]]:
    files = _walk(repo)
    relative = [path.relative_to(repo) for path in files]
    source_files = [path for path in files if path.suffix.lower() in LANGUAGES]
    test_files = [path for path in source_files if _is_test(path.relative_to(repo))]
    production_files = [path for path in source_files if path not in test_files]
    source_lines = {path: _line_count(path) for path in source_files}
    production_lines = sum(source_lines[path] for path in production_files)
    test_lines = sum(source_lines[path] for path in test_files)
    language_lines: Counter[str] = Counter()
    for path in source_files:
        language_lines[LANGUAGES[path.suffix.lower()]] += source_lines[path]

    root_names = {path.name.lower() for path in relative if len(path.parts) == 1}
    all_names = {path.name.lower() for path in relative}
    parts = [{part.lower() for part in path.parts} for path in relative]
    workflows = any(
        len(path.parts) >= 3 and path.parts[0].lower() == ".github" and path.parts[1].lower() == "workflows"
        for path in relative
    )
    signals = {
        "readme": any(name.startswith("readme") for name in root_names),
        "contributing": any(name.startswith("contributing") for name in root_names),
        "license": any(name.startswith(("license", "licence", "copying")) for name in root_names),
        "changelog": any(name.startswith(("changelog", "changes", "history")) for name in root_names),
        "docs_tree": any("docs" in path_parts or "doc" in path_parts for path_parts in parts),
        "ci": workflows or bool(root_names & {".gitlab-ci.yml", "azure-pipelines.yml", "jenkinsfile"}),
        "manifest": bool(all_names & MANIFESTS),
        "lockfile": bool(all_names & LOCKFILES),
        "gitignore": ".gitignore" in root_names,
        "test_config": bool(all_names & {"pytest.ini", "tox.ini", "jest.config.js", "jest.config.ts", "vitest.config.ts", "phpunit.xml"}),
        "coverage_config": bool(all_names & {".coveragerc", "codecov.yml", "codecov.yaml", "coveragerc"}),
        "lint_config": bool(all_names & {"ruff.toml", ".ruff.toml", ".eslintrc", ".eslintrc.json", "eslint.config.js", "eslint.config.mjs", ".golangci.yml", "checkstyle.xml"}),
        "format_config": bool(all_names & {".prettierrc", ".prettierrc.json", "prettier.config.js", ".editorconfig", "rustfmt.toml"}),
        "dependency_updates": any(
            path.as_posix().lower() in {".github/dependabot.yml", ".github/dependabot.yaml"}
            or path.name.lower() in {"renovate.json", "renovate.json5"}
            for path in relative
        ),
        "pre_commit": ".pre-commit-config.yaml" in root_names,
    }
    line_values = list(source_lines.values())
    inventory = {
        "files_total": len(files),
        "source_files": len(source_files),
        "production_source_files": len(production_files),
        "test_source_files": len(test_files),
        "source_lines": sum(line_values),
        "production_source_lines": production_lines,
        "test_source_lines": test_lines,
        "test_to_source_ratio": round(test_lines / max(1, production_lines), 4),
        "average_source_file_lines": round(sum(line_values) / max(1, len(line_values)), 1),
        "maximum_source_file_lines": max(line_values, default=0),
        "large_source_files": sum(1 for count in line_values if count >= 800),
        "languages_by_lines": dict(language_lines.most_common()),
    }
    return inventory, signals


def _git(repo: Path, *args: str, timeout: int = 30) -> str | None:
    executable = shutil.which("git")
    if not executable:
        return None
    try:
        result = subprocess.run(
            [executable, "-c", "core.pager=cat", *args], cwd=repo, capture_output=True,
            text=True, encoding="utf-8", errors="replace", timeout=timeout,
            stdin=subprocess.DEVNULL,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def collect_history(repo: Path) -> dict[str, Any]:
    inside = _git(repo, "rev-parse", "--is-inside-work-tree") == "true"
    if not inside:
        return {"git_repository": False, "commit_count": 0, "activity_span_days": 0,
                "recent_additions": 0, "recent_deletions": 0, "sampled_commits": 0}
    count_text = _git(repo, "rev-list", "--count", "HEAD") or "0"
    stamps_text = _git(repo, "log", "--format=%ct", "--reverse") or ""
    stamps = [int(value) for value in stamps_text.splitlines() if value.isdigit()]
    numstat = _git(repo, "log", "-n", "500", "--numstat", "--format=") or ""
    additions = deletions = 0
    for line in numstat.splitlines():
        columns = line.split("\t")
        if len(columns) >= 2:
            if columns[0].isdigit():
                additions += int(columns[0])
            if columns[1].isdigit():
                deletions += int(columns[1])
    commit_count = int(count_text) if count_text.isdigit() else len(stamps)
    span_days = int((stamps[-1] - stamps[0]) / 86400) if len(stamps) >= 2 else 0
    return {
        "git_repository": True,
        "commit_count": commit_count,
        "activity_span_days": max(0, span_days),
        "recent_additions": additions,
        "recent_deletions": deletions,
        "sampled_commits": min(500, commit_count),
    }


def calculate_scores(inventory: dict[str, Any], signals: dict[str, bool], history: dict[str, Any]) -> dict[str, int]:
    documentation = (
        6 * signals["readme"] + 3 * signals["contributing"] + 3 * signals["license"]
        + 2 * signals["changelog"] + 1 * signals["docs_tree"]
    )
    ratio = inventory["test_to_source_ratio"]
    ratio_points = 8 if ratio >= 0.5 else 6 if ratio >= 0.25 else 4 if ratio >= 0.1 else 2 if ratio > 0 else 0
    test_readiness = (
        8 * (inventory["test_source_files"] > 0) + ratio_points + 5 * signals["ci"]
        + 2 * signals["test_config"] + 2 * signals["coverage_config"]
    )
    automation = (
        6 * signals["ci"] + 5 * signals["lint_config"] + 3 * signals["format_config"]
        + 3 * signals["dependency_updates"] + 3 * signals["pre_commit"]
    )
    structure = 25 if inventory["source_files"] else 5
    structure -= min(10, inventory["large_source_files"] * 2)
    average = inventory["average_source_file_lines"]
    structure -= 5 if average >= 500 else 3 if average >= 300 else 0
    structure = max(0, structure)
    history_score = 0
    if history["git_repository"]:
        history_score += 3
        commits = history["commit_count"]
        history_score += 6 if commits >= 100 else 5 if commits >= 40 else 4 if commits >= 15 else 2 if commits >= 2 else 1
        span = history["activity_span_days"]
        history_score += 4 if span >= 365 else 3 if span >= 90 else 2 if span >= 30 else 1 if span > 0 else 0
        history_score += 2 if history["recent_additions"] + history["recent_deletions"] > 0 else 0
    scores = {
        "documentation": int(documentation),
        "test_readiness": int(test_readiness),
        "automation": int(automation),
        "code_structure": int(structure),
        "history_health": int(history_score),
    }
    scores["total"] = sum(scores.values())
    return scores


def _extract_json(text: str) -> dict[str, Any] | None:
    text = text.strip()
    candidates = [text]
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if fenced:
        candidates.append(fenced.group(1).strip())
    start, end = text.find("{"), text.rfind("}")
    if 0 <= start < end:
        candidates.append(text[start:end + 1])
    for candidate in candidates:
        try:
            value = json.loads(candidate)
            if isinstance(value, dict):
                return value
        except json.JSONDecodeError:
            continue
    return None


def _safe_ai_payload(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "inventory": report["inventory"],
        "signals": report["signals"],
        "history": report["history"],
        "scores": report["scores"],
        "limitations": report["limitations"],
    }


def _provider_prompt(report: dict[str, Any]) -> str:
    payload = json.dumps(_safe_ai_payload(report), sort_keys=True)
    return (
        "You are reviewing anonymous aggregate engineering-health metrics. No source code, names, "
        "paths, remotes, messages, or identities are available. Do not claim tests passed or infer "
        "a product domain. Return only JSON with executive_summary (one sentence) and priorities "
        "(an array of at most five objects with title, rationale, and effort where effort is one of "
        "small, medium, large). Prefer concrete actions supported by the metrics. Metrics: " + payload
    )


def request_ai(report: dict[str, Any], provider: str, model: str, timeout: int) -> dict[str, Any]:
    executable = shutil.which(provider)
    if not executable:
        return {"status": "unavailable", "provider": provider, "model": model,
                "reason": f"{provider} executable was not found on PATH"}
    prompt = _provider_prompt(report)
    output_file: Path | None = None
    with tempfile.TemporaryDirectory(prefix="repo-audit-provider-") as temp_dir:
        workdir = Path(temp_dir)
        if provider == "codex":
            output_file = workdir / "answer.txt"
            command = [
                executable, "exec", "--ephemeral", "--sandbox", "read-only",
                "--skip-git-repo-check", "--ignore-rules", "-c", "project_doc_max_bytes=0",
                "--output-last-message", str(output_file),
                "--model", model, "-",
            ]
            stdin_text = prompt
        else:
            command = [
                executable, "-p", prompt, "--output-format", "text", "--model", model,
                "--allowedTools", "", "--no-session-persistence",
            ]
            stdin_text = None
        try:
            process = subprocess.run(
                command, cwd=workdir, input=stdin_text, capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=timeout,
                stdin=subprocess.DEVNULL if stdin_text is None else None,
            )
        except subprocess.TimeoutExpired:
            return {"status": "unavailable", "provider": provider, "model": model,
                    "reason": f"provider exceeded the {timeout}-second timeout"}
        except OSError as exc:
            return {"status": "unavailable", "provider": provider, "model": model,
                    "reason": f"provider could not start: {exc.strerror or type(exc).__name__}"}
        if process.returncode != 0:
            return {"status": "unavailable", "provider": provider, "model": model,
                    "reason": f"provider exited with code {process.returncode}"}
        text = output_file.read_text(encoding="utf-8", errors="replace") if output_file and output_file.exists() else process.stdout
    value = _extract_json(text or "")
    if not value or not isinstance(value.get("executive_summary"), str) or not isinstance(value.get("priorities"), list):
        return {"status": "unavailable", "provider": provider, "model": model,
                "reason": "provider response did not match the expected JSON format"}
    priorities = []
    for item in value["priorities"][:5]:
        if not isinstance(item, dict):
            continue
        title, rationale, effort = item.get("title"), item.get("rationale"), item.get("effort")
        if isinstance(title, str) and isinstance(rationale, str) and effort in {"small", "medium", "large"}:
            priorities.append({"title": title[:120], "rationale": rationale[:500], "effort": effort})
    return {
        "status": "complete", "provider": provider, "model": model,
        "executive_summary": value["executive_summary"][:500], "priorities": priorities,
    }


def build_report(repo: Path, provider: str = "none", model: str | None = None, timeout: int = 600) -> dict[str, Any]:
    inventory, signals = collect_inventory(repo)
    history = collect_history(repo)
    report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "complete",
        "repository": {
            "git_repository": history["git_repository"],
            "tracked_head_available": history["commit_count"] > 0,
        },
        "inventory": inventory,
        "signals": signals,
        "history": history,
        "scores": calculate_scores(inventory, signals, history),
        "limitations": [
            "Repository code, dependency installation, builds, and tests were not executed.",
            "Test readiness is inferred from structure and configuration, not test outcomes.",
            "Static size and history signals cannot establish correctness or security.",
        ],
        "ai_review": {"status": "not_requested", "provider": "none", "model": None},
    }
    if provider != "none":
        if not model:
            raise ValueError("--model is required when an AI provider is selected")
        report["ai_review"] = request_ai(report, provider, model, timeout)
    return report


def render_markdown(report: dict[str, Any]) -> str:
    scores = report["scores"]
    inventory = report["inventory"]
    lines = [
        "# Repository audit", "", f"Overall deterministic score: **{scores['total']}/100**", "",
        "## Scorecard", "",
        "| Dimension | Score | Maximum |", "|---|---:|---:|",
        f"| Documentation | {scores['documentation']} | 15 |",
        f"| Test readiness | {scores['test_readiness']} | 25 |",
        f"| Automation | {scores['automation']} | 20 |",
        f"| Code structure | {scores['code_structure']} | 25 |",
        f"| History health | {scores['history_health']} | 15 |", "",
        "## Inventory", "",
        f"- Files scanned: {inventory['files_total']}",
        f"- Source files: {inventory['source_files']}",
        f"- Test source files: {inventory['test_source_files']}",
        f"- Source lines: {inventory['source_lines']}",
        f"- Test-to-production line ratio: {inventory['test_to_source_ratio']:.2f}",
        f"- Large source files: {inventory['large_source_files']}", "",
        "## Languages by lines", "",
    ]
    if inventory["languages_by_lines"]:
        lines.extend(f"- {language}: {count}" for language, count in inventory["languages_by_lines"].items())
    else:
        lines.append("- No recognized source-language files found.")
    lines.extend(["", "## AI review", ""])
    ai = report["ai_review"]
    if ai["status"] == "complete":
        lines.extend([ai["executive_summary"], ""])
        for item in ai["priorities"]:
            lines.append(f"- **{item['title']}** ({item['effort']}): {item['rationale']}")
    elif ai["status"] == "unavailable":
        lines.append(f"Unavailable: {ai['reason']}")
    else:
        lines.append("Not requested. The deterministic report is complete.")
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {item}" for item in report["limitations"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--provider", choices=("none", "codex", "claude"), default="none")
    parser.add_argument("--model")
    parser.add_argument("--timeout", type=int, default=600)
    args = parser.parse_args()
    repo = args.repository.resolve()
    if not repo.is_dir():
        parser.error("repository must be an existing directory")
    if args.provider != "none" and not args.model:
        parser.error("--model is required when --provider is codex or claude")
    report = build_report(repo, args.provider, args.model, max(1, args.timeout))
    args.out.mkdir(parents=True, exist_ok=True)
    json_path = args.out / "repo-audit.json"
    markdown_path = args.out / "repo-audit.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    print(f"complete: deterministic score {report['scores']['total']}/100")
    print(f"wrote {json_path}")
    print(f"wrote {markdown_path}")
    if report["ai_review"]["status"] == "unavailable":
        print(f"AI review unavailable: {report['ai_review']['reason']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

