# Contributing

Contributions are welcome when they preserve the project's privacy boundary and transparent scoring.

## Contribution requirements

By submitting a contribution, you certify that:

1. you wrote the contribution or have the right to submit it;
2. it does not copy code, prompts, schemas, documentation, or tests from a source whose license does
   not permit inclusion here;
3. you agree to license the contribution under this repository's MIT License;
4. you have removed credentials, private repository data, personal information, and proprietary
   test fixtures.

Do not submit generated code whose training source or licensing you cannot reasonably assess. When a
change is inspired by another project, describe the idea and provide its license; implement the
change independently.

## Development workflow

Run these checks before opening a pull request:

```bash
python -m unittest discover -s tests -v
python /path/to/skill-creator/scripts/quick_validate.py .
```

Add behavior-based tests for collection, scoring, provider boundaries, or privacy guarantees. Avoid
tests that only assert wording. A score change must update `references/report-schema.md` and explain
its rationale in the pull request.

## Pull requests

Keep each pull request focused. Describe the user-visible behavior, privacy impact, validation, and
any compatibility change. Maintainers may decline changes that broaden data collection, execute the
audited repository, conceal incomplete evidence, or make unsupported quality claims.

