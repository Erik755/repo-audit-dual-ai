# Privacy

## Local collection

The deterministic audit reads the selected repository locally. It records aggregate facts such as
file counts, line counts, language totals, configuration-presence booleans, commit count, activity
span, and sampled churn totals.

The generated report does not intentionally include:

- source-code contents;
- absolute or relative file paths;
- repository or organization names;
- remote URLs;
- commit messages;
- author names or email addresses;
- branch or tag names;
- credentials or environment-variable values.

Reports are written only to the output directory selected by the user. The project contains no
telemetry, analytics, upload client, or background service.

## Optional AI review

When `--provider codex` or `--provider claude` is selected, the provider receives only the aggregate
inventory, signal booleans, history totals, deterministic scores, and stated limitations already
described in `references/report-schema.md`. The repository path and source are not included in the
prompt. The provider runs from a newly created empty temporary directory.

The provider may process and retain submitted metrics according to its own terms, account settings,
and policies. Users should review those terms before enabling the AI review. Selecting
`--provider none` performs no model invocation.

## Limits

File names are examined locally to classify project signals but are not written to the report or AI
prompt. Source files are decoded locally only to count lines. Git commands read numeric timestamps
and churn; identity and message fields are not requested.

