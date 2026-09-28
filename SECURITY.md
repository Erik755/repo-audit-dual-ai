# Security policy

## Supported version

Security fixes are applied to the latest commit on the `main` branch. Tagged releases may be added
later; until then, no earlier snapshot is separately supported.

## Reporting a vulnerability

Use GitHub's private vulnerability reporting or a private draft security advisory for this
repository. Do not publish an issue containing exploit details, credentials, private repository
content, or personal data.

Include the affected commit, operating system, Python version, reproduction steps, expected result,
observed result, and the minimum evidence needed to validate the report. Remove repository source,
paths, tokens, and provider transcripts unless they are essential and safe to share.

## Security boundary

The auditor does not execute code from the repository under inspection. It invokes Git with fixed
argument lists for numeric history data. Optional provider CLIs receive an aggregate prompt from an
empty temporary directory. Codex is requested with an ephemeral read-only sandbox; Claude is
requested without tool access and without session persistence.

The project cannot control a provider CLI installation, account policy, operating-system compromise,
or malicious Git executable already present on the host. Run it in an environment appropriate for
the sensitivity of the repository.

