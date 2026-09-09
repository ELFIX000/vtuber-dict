#!/usr/bin/env python3
"""
各IME形式への辞書データ一括ジェネレータ。
- Google日本語入力 / Mozc (UTF-8, TSV)
- Microsoft IME (UTF-16LE BOM, CRLF, TSV)
- ATOK (UTF-16LE BOM, CRLF, TSV)
- macOS 日本語入力 (XML Property List .plist)
- 全形式同梱 ZIP アーカイブ
"""
import json
import os
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

def load_data(data_path: Path):
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)

def build_google_ime(entries, output_path: Path):
    """Google日本語入力 / Mozc (UTF-8 TSV)"""
    lines = []
    for item in entries:
        name = item["name"]
        comment = item.get("affiliation", "VTuber")
        for r in item.get("readings", []):
            lines.append(f"{r}\t{name}\t固有名詞\t{comment}")
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Generated: {output_path} ({len(lines)} entries)")

def build_ms_ime(entries, output_path: Path):
    """Microsoft IME (UTF-16LE BOM, CRLF TSV)"""
    lines = []
    for item in entries:
        name = item["name"]
        comment = item.get("affiliation", "VTuber")
        for r in item.get("readings", []):
            lines.append(f"{r}\t{name}\t人名\t{comment}")
    content = "\r\n".join(lines) + "\r\n"
    # Write UTF-16LE with BOM
    output_path.write_bytes(b"\xff\xfe" + content.encode("utf-16-le"))
    print(f"Generated: {output_path} ({len(lines)} entries)")

def build_atok(entries, output_path: Path):
    """ATOK (UTF-16LE BOM, CRLF TSV)"""
    lines = []
    for item in entries:
        name = item["name"]
        comment = item.get("affiliation", "VTuber")
        for r in item.get("readings", []):
            lines.append(f"{r}\t{name}\t固有固有名詞人名\t{comment}")
    content = "\r\n".join(lines) + "\r\n"
    output_path.write_bytes(b"\xff\xfe" + content.encode("utf-16-le"))
    print(f"Generated: {output_path} ({len(lines)} entries)")

def build_macos_plist(entries, output_path: Path):
    """macOS ユーザ辞書 (XML plist)"""
    plist_entries = []
    for item in entries:
        name = item["name"]
        for r in item.get("readings", []):
            plist_entries.append(
                f"    <dict>\n"
                f"        <key>phrase</key>\n"
                f"        <string>{_escape_xml(name)}</string>\n"
                f"        <key>shortcut</key>\n"
                f"        <string>{_escape_xml(r)}</string>\n"
                f"    </dict>"
            )

    body = "\n".join(plist_entries)
    xml_content = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
        '<plist version="1.0">\n'
        '<array>\n'
        f'{body}\n'
        '</array>\n'
        '</plist>\n'
    )
    output_path.write_text(xml_content, encoding="utf-8")
    print(f"Generated: {output_path} ({len(plist_entries)} entries)")

def _escape_xml(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )

def create_zip(dist_dir: Path, zip_name: str = "vtuber-dict-all.zip"):
    readme_text = (
        "【VTuber変換辞書 各IME向けインポート方法】\n\n"
        "1. Google日本語入力 / Mozc:\n"
        "   設定 > 辞書ツール > 管理 > 新規辞書にインポート > google_ime.txt を選択\n\n"
        "2. Microsoft IME (Windows):\n"
        "   プロパティ > 詳細設定 > 辞書/学習 > テキストファイルからの登録 > ms_ime.txt を選択\n\n"
        "3. macOS (日本語入力):\n"
        "   システム設定 > キーボード > ユーザ辞書 に macos_user_dict.plist をドラッグ＆ドロップ\n\n"
        "4. ATOK:\n"
        "   ATOKメニュー > 辞書メンテナンス > 単語一括処理 > atok.txt を選択\n"
    )
    readme_path = dist_dir / "README.txt"
    readme_path.write_text(readme_text, encoding="utf-8")

    zip_path = dist_dir / zip_name
    targets = [
        "google_ime.txt",
        "ms_ime.txt",
        "atok.txt",
        "macos_user_dict.plist",
        "README.txt",
    ]
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for t in targets:
            file_path = dist_dir / t
            if file_path.exists():
                z.write(file_path, arcname=t)
    print(f"Generated ZIP package: {zip_path}")

def main():
    base_dir = Path(__file__).resolve().parent.parent
    data_file = base_dir / "data" / "vtubers.json"
    dist_dir = base_dir / "dist"
    dist_dir.mkdir(exist_ok=True)

    entries = load_data(data_file)
    # overrides があれば適用（二重防御）
    overrides_file = base_dir / "data" / "overrides.json"
    if overrides_file.exists():
        overrides = load_data(overrides_file)
        entry_map = {item["name"]: item for item in entries}
        for o in overrides:
            if o["name"] in entry_map:
                entry_map[o["name"]]["readings"] = o["readings"]
                if "affiliation" in o and o["affiliation"] != "VTuber":
                    entry_map[o["name"]]["affiliation"] = o["affiliation"]
            else:
                entries.append(o)
    print(f"Loaded {len(entries)} VTuber records.")

    build_google_ime(entries, dist_dir / "google_ime.txt")
    build_ms_ime(entries, dist_dir / "ms_ime.txt")
    build_atok(entries, dist_dir / "atok.txt")
    build_macos_plist(entries, dist_dir / "macos_user_dict.plist")
    create_zip(dist_dir)
    print("✨ Build completed successfully!")

if __name__ == "__main__":
    main()
