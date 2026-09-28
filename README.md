# Dual AI Repository Auditor

An independent, MIT-licensed repository health auditor for Claude Code and OpenAI Codex. It is a
new implementation with its own report format and scoring model. It is not compatible with Mercor's
submission schema and is not affiliated with Mercor, Anthropic, or OpenAI.

The deterministic audit stays local. Optional AI recommendations receive only aggregate metrics;
source code, paths, repository names, remotes, commit messages, and author identities are excluded.
The tool never installs dependencies or executes repository code.

## What it measures

- Source size and language distribution
- Test structure and test-to-source ratio
- Documentation and licensing signals
- CI, linting, formatting, dependency-update, and pre-commit automation
- Large-file and code-structure risk proxies
- Commit count, activity span, and recent churn totals without identities or messages

The overall score is deterministic and transparent. AI recommendations are additive and never
change the score.

## Install as a Codex skill

```powershell
git clone https://github.com/Erik755/repo-audit-dual-ai.git "$env:USERPROFILE\.codex\skills\repo-audit-dual-ai"
```

## Install as a Claude Code skill

```bash
git clone https://github.com/Erik755/repo-audit-dual-ai.git ~/.claude/skills/repo-audit-dual-ai
```

Python 3.10 or newer and Git are the only local requirements.

To install the command in an isolated environment:

```powershell
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install ".[test]"
& .\.venv\Scripts\repo-audit.exe --help
```

## Run locally without AI

```powershell
python scripts\audit_repo.py C:\path\to\repository --out C:\path\to\audit-output
```

## Add Codex recommendations through a ChatGPT sign-in

```powershell
python scripts\audit_repo.py C:\path\to\repository --out C:\path\to\audit-output --provider codex --model gpt-6-sol
```

The `codex` executable must be on `PATH` and signed in. The provider is launched from an empty
temporary directory with an ephemeral, read-only session.

## Add Claude recommendations

```bash
python scripts/audit_repo.py /path/to/repository --out /path/to/audit-output --provider claude --model MODEL_NAME
```

The `claude` executable must be on `PATH` and signed in. The provider is launched from an empty
temporary directory with no repository path in its prompt.

## Interpret results

`repo-audit.json` is the machine-readable record. `repo-audit.md` is the human-readable report.
Detected tests are evidence of test readiness, not evidence that the tests pass. A provider error
leaves the deterministic audit complete and marks only `ai_review.status` as `unavailable`.

## Development

```powershell
python -m unittest discover -s tests -v
python C:\path\to\skill-creator\scripts\quick_validate.py .
```

## Policies and legal notes

- [Privacy](PRIVACY.md) explains what stays local and what an optional AI provider receives.
- [Security](SECURITY.md) explains supported versions and responsible reporting.
- [Contributing](CONTRIBUTING.md) requires contributors to submit only work they may license.
- [Notice](NOTICE.md) records independence, trademark, authorization, and warranty boundaries.
- [Code of Conduct](CODE_OF_CONDUCT.md) governs project participation.

The software is released under the [MIT License](LICENSE). These documents describe project policy
and are not legal advice.


