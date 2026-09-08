#!/usr/bin/env python3
"""
マスターデータのバリデーションスクリプト。
ひらがなチェック、重複検知、ブラックリスト検証を実施します。
"""
import json
import re
import sys
from pathlib import Path

# ひらがな、長音符、濁点付き・小書き文字
HIRAGANA_REGEX = re.compile(r"^[\u3041-\u3096\u3099-\u309fー]+$")

def load_blacklist(blacklist_path: Path) -> set:
    if not blacklist_path.exists():
        return set()
    with open(blacklist_path, "r", encoding="utf-8") as f:
        return {
            line.strip()
            for line in f
            if line.strip() and not line.strip().startswith("#")
        }

def validate_dataset(data_path: Path, blacklist_path: Path) -> bool:
    if not data_path.exists():
        print(f"[ERROR] Data file not found: {data_path}", file=sys.stderr)
        return False

    with open(data_path, "r", encoding="utf-8") as f:
        try:
            entries = json.load(f)
        except Exception as e:
            print(f"[ERROR] Failed to parse JSON: {e}", file=sys.stderr)
            return False

    if not isinstance(entries, list):
        print("[ERROR] Master data must be a JSON array.", file=sys.stderr)
        return False

    blacklist = load_blacklist(blacklist_path)
    seen_pairs = set()
    errors = []
    warnings = []

    for idx, item in enumerate(entries):
        if not isinstance(item, dict):
            errors.append(f"Item #{idx}: Must be an object")
            continue

        name = item.get("name", "").strip()
        readings = item.get("readings", [])
        affiliation = item.get("affiliation", "")

        if not name:
            errors.append(f"Item #{idx}: Missing or empty 'name'")
        if not readings or not isinstance(readings, list):
            errors.append(f"Item #{idx} ({name}): 'readings' must be a non-empty list")
            continue

        for r in readings:
            r = str(r).strip()
            if not r:
                errors.append(f"Item #{idx} ({name}): Empty reading found")
                continue

            if not HIRAGANA_REGEX.match(r):
                errors.append(
                    f"Item #{idx} ({name}): Reading '{r}' contains non-hiragana characters"
                )

            if r in blacklist:
                warnings.append(
                    f"Item #{idx} ({name}): Reading '{r}' is in blacklist (may cause typing collisions)"
                )

            pair = (r, name)
            if pair in seen_pairs:
                errors.append(f"Duplicate entry found: ({r} -> {name})")
            seen_pairs.add(pair)

    print(f"--- Validation Summary ---")
    print(f"Total entries: {len(entries)}")
    print(f"Total word pairs: {len(seen_pairs)}")
    print(f"Warnings: {len(warnings)}")
    for w in warnings:
        print(f"  [WARN] {w}")

    if errors:
        print(f"Errors found: {len(errors)}", file=sys.stderr)
        for err in errors:
            print(f"  [FAIL] {err}", file=sys.stderr)
        return False

    print("✅ All validation checks passed successfully!")
    return True

if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent
    data_file = base_dir / "data" / "vtubers.json"
    blacklist_file = base_dir / "data" / "blacklist.txt"

    success = validate_dataset(data_file, blacklist_file)
    sys.exit(0 if success else 1)
