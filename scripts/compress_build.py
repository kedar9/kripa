#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


SKIP_NAMES = {".DS_Store"}


def should_skip(path: Path) -> bool:
    return any(part in SKIP_NAMES for part in path.parts)


def iter_files(root: Path, archive_path: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file()
        and path != archive_path
        and not should_skip(path.relative_to(root))
    )


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    fonts_dir = repo_root / "fonts"
    archive_path = fonts_dir / "Kripa.zip"

    if not fonts_dir.is_dir():
        print(f"Missing fonts directory: {fonts_dir}", file=sys.stderr)
        return 1

    files = iter_files(fonts_dir, archive_path)
    if not files:
        print(f"No files found in fonts directory: {fonts_dir}", file=sys.stderr)
        return 1

    with ZipFile(archive_path, "w", compression=ZIP_DEFLATED) as archive:
        for file_path in files:
            relative_path = file_path.relative_to(fonts_dir)
            archive.write(file_path, Path("kripa") / relative_path)

    print(f"Created archive: {archive_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())