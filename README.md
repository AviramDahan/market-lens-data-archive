# Market Lens Data Archive

Heavy Market Lens paper-trading artifacts are stored as GitHub Release assets, not in the git tree, to keep checkouts fast.

Snapshot: 2026-09-12

Contents preserved:
- agent_results charts, decisions, screenshots, diagnostics, summaries, runtime, monitor summaries, replay data
- agent_tracker workbook

Do not delete: this archive is used for future strategy comparison, replay, QA, and performance research.

## Automatic structured backups

`Market Lens Daily Structured Archive` creates an immutable, source-commit-specific
GitHub Release every day. Daily frequency is intentional because the active
decision retention window can be shorter than one week. It archives decisions, summaries, diagnostics,
runtime and monitor metadata, replay data, the dashboard snapshot, the Telegram
dedupe ledger, and the current paper tracker. Derived charts and screenshots are
excluded.

Each release contains the ZIP, a SHA-256 checksum, and a JSON manifest with a
hash for every archived file. `latest.json` points to the most recently completed
archive. The workflow reads the public production repository and writes only to
this archive repository; it needs no cross-repository personal access token.
