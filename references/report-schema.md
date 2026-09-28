# Report schema

`repo-audit.json` uses schema version `1.0`. The root object contains:

- `schema_version`: fixed string `1.0`.
- `generated_at`: UTC timestamp.
- `status`: `complete` when deterministic collection completed.
- `repository`: anonymous structural facts (`git_repository`, `tracked_head_available`).
- `inventory`: file, source, test, documentation, language, and line-count aggregates.
- `signals`: booleans for documentation, CI, packaging, linting, formatting, and update automation.
- `history`: commit count, activity span, and churn totals. No names or messages.
- `scores`: five transparent dimensions and the total score out of 100.
- `limitations`: statements describing what was not executed or inferred.
- `ai_review`: provider status plus optional summary and prioritized recommendations.

## Score dimensions

| Dimension | Maximum | Evidence |
|---|---:|---|
| Documentation | 15 | README, contribution guide, license, changelog, docs tree |
| Test readiness | 25 | test files, test/source ratio, CI, test and coverage configuration |
| Automation | 20 | CI, linting, formatting, dependency updates, pre-commit hooks |
| Code structure | 25 | source presence, average and maximum file size, large-file count |
| History health | 15 | Git availability, commit count, activity span, recent churn |

The AI review receives only the values already present in these aggregate sections and never
modifies a score.

