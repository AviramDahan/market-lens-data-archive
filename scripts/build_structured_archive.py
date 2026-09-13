from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath


INCLUDED_DIRECTORIES = (
    "agent_results/decisions",
    "agent_results/summaries",
    "agent_results/diagnostics",
    "agent_results/runtime",
    "agent_results/position_monitor",
    "agent_results/capital_replay",
)
INCLUDED_FILES = (
    "agent_results/dashboard_snapshot.json",
    "agent_results/telegram_notifications.jsonl",
    "agent_tracker/market_lens_agent_portfolio_budget_100k.xlsx",
)
EXCLUDED_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
FORBIDDEN_NAMES = {".env", ".env.local", "credentials.json", "secrets.json"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def selected_files(source: Path) -> list[Path]:
    source = source.resolve()
    selected: set[Path] = set()
    for relative in INCLUDED_DIRECTORIES:
        root = source / relative
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file() and not path.is_symlink():
                selected.add(path.resolve())
    for relative in INCLUDED_FILES:
        path = source / relative
        if path.is_file() and not path.is_symlink():
            selected.add(path.resolve())

    safe = []
    for path in selected:
        relative = path.relative_to(source)
        if path.suffix.lower() in EXCLUDED_SUFFIXES:
            continue
        if path.name.lower() in FORBIDDEN_NAMES or any(part.startswith(".env") for part in relative.parts):
            raise RuntimeError(f"Refusing to archive credential-like file: {relative.as_posix()}")
        safe.append(path)
    return sorted(safe, key=lambda path: path.relative_to(source).as_posix())


def build_archive(
    source: Path,
    output: Path,
    manifest_output: Path,
    *,
    source_repository: str,
    source_commit: str,
    created_at: str | None = None,
) -> dict:
    source = source.resolve()
    output = output.resolve()
    manifest_output = manifest_output.resolve()
    if source == output or source in output.parents:
        raise RuntimeError("Archive output must be outside the source checkout")
    files = selected_files(source)
    if not files:
        raise RuntimeError("No structured Market Lens files were found")

    entries = []
    for path in files:
        relative = path.relative_to(source).as_posix()
        entries.append({"path": relative, "bytes": path.stat().st_size, "sha256": sha256(path)})
    manifest = {
        "version": "market_lens_structured_archive_v1",
        "created_at": created_at or datetime.now(timezone.utc).isoformat(),
        "source_repository": source_repository,
        "source_commit": source_commit,
        "file_count": len(entries),
        "total_bytes": sum(item["bytes"] for item in entries),
        "media_included": False,
        "files": entries,
    }
    encoded_manifest = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")

    output.parent.mkdir(parents=True, exist_ok=True)
    manifest_output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in files:
            relative = PurePosixPath(path.relative_to(source).as_posix())
            archive.write(path, relative.as_posix())
        archive.writestr("archive_manifest.json", encoded_manifest)
    manifest_output.write_bytes(encoded_manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a verified Market Lens structured-data archive")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest-output", type=Path, required=True)
    parser.add_argument("--source-repository", required=True)
    parser.add_argument("--source-commit", required=True)
    args = parser.parse_args()
    manifest = build_archive(
        args.source,
        args.output,
        args.manifest_output,
        source_repository=args.source_repository,
        source_commit=args.source_commit,
    )
    print(json.dumps({key: manifest[key] for key in ("source_commit", "file_count", "total_bytes")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
