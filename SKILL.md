---
name: repo-audit-dual-ai
description: >-
  Audit a local Git repository with deterministic engineering-health metrics and
  optional recommendations from Claude Code or OpenAI Codex. Use when a user asks
  to inspect repository quality, test readiness, documentation, automation, code
  structure, or maintenance risks without uploading source code.
---

# Repository audit with Claude or Codex

Run `scripts/audit_repo.py` against a repository the user owns or is authorized to inspect. The
script reads files and Git metadata but does not execute repository code, install dependencies,
run tests, or upload source. It writes `repo-audit.json` and `repo-audit.md` under the requested
output directory.

Choose the provider deliberately:

- Use `--provider none` for a fully local deterministic report.
- Use `--provider codex --model MODEL` when the user wants Codex recommendations.
- Use `--provider claude --model MODEL` when the user wants Claude recommendations.

The optional model receives only aggregate counts, booleans, and scores. It does not receive source
text, file paths, repository names, commit messages, author identities, or remote URLs. Provider
failure does not invalidate the deterministic report; record it as unavailable.

Use a separate output directory. Review the JSON `status`, dimension scores, limitations, and AI
status before presenting conclusions. Do not describe detected test files as passing tests: this
tool detects test structure but never runs the suite.

Read [references/report-schema.md](references/report-schema.md) when integrating or validating the
JSON format. Installation and CLI examples are in [README.md](README.md).

