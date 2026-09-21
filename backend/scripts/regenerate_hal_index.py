#!/usr/bin/env python3
"""Regenerate memory/manuale/hal/hal-index.json fingerprints from YAML sources.

Keeps the compact catalog format (source_files + voices counts + md5).
Run after any Cap.*/HAL yaml edit so index stays 100% aligned.
"""
from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path

import yaml

HAL_DIR = Path("/workspace/memory/manuale/hal")
INDEX_PATH = HAL_DIR / "hal-index.json"


def _md5(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def _voice_count(path: Path) -> int:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return len(data.get("voci") or [])


def main() -> None:
    prev = json.loads(INDEX_PATH.read_text(encoding="utf-8")) if INDEX_PATH.exists() else {}
    yaml_files = sorted(
        p for p in HAL_DIR.glob("*.yaml")
        if p.name[0].isdigit() or p.name.startswith("00-")
    )
    source_files = []
    total = 0
    for path in yaml_files:
        n = _voice_count(path)
        total += n
        source_files.append({"file": path.name, "voices": n, "md5": _md5(path)})

    # Preserve new_chapters_m3 structure but refresh md5/voices from disk
    new_chapters = []
    for row in prev.get("new_chapters_m3") or []:
        yname = row.get("yaml") or f"{row.get('file')}.yaml"
        match = next((s for s in source_files if s["file"] == yname), None)
        entry = dict(row)
        if match:
            entry["voices"] = match["voices"]
            entry["md5"] = match["md5"]
        new_chapters.append(entry)

    out = {
        "version": "0.24-import-forme",
        "updated": date.today().isoformat(),
        "voices_total": total,
        "source_files": source_files,
        "new_chapters_m3": new_chapters,
        "notes": (
            "Fingerprints regenerated from YAML on disk. "
            "Live RAG reindex: POST /api/app/hal/knowledge/reindex?force=true (super_admin). "
            "2026-09-21: hub import A–E · HAL import.tutte-le-forme. "
            "2026-09-19: D-085 storage quota · Cestino · Cap.20 Ruota · "
            "cleanup Emergent · Cap.15 social · Cap.3 planimetrie."
        ),
    }
    INDEX_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"WROTE {INDEX_PATH} voices_total={total} files={len(source_files)}")
    cap21 = next(s for s in source_files if s["file"] == "21-valutatore-immobiliare.yaml")
    print(f"  Cap.21 md5={cap21['md5']} voices={cap21['voices']}")


if __name__ == "__main__":
    main()
