#!/usr/bin/env python3
"""
日本語版WikipediaからVTuberの正式表記および正確な読み仮名を取得するスクリプト。
公式MediaWiki APIを利用し、記事冒頭のリード文および所属一覧テンプレートから
著作権の保護対象外である客観的事実情報（名前と読みのペア）のみを抽出します。
標準ライブラリ（urllib, json, re）のみで動作します。
"""
import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

API_ENDPOINT = "https://ja.wikipedia.org/w/api.php"
USER_AGENT = "VTuberDictBuilder/1.0 (https://github.com/ELFIX000/vtuber-dict; open-source-vtuber-dict)"

KATAKANA_TO_HIRAGANA = str.maketrans(
    "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲンァィゥェォッャュョヴガギグゲゴザジズゼゾダヂヅデドバビブベボパピプペポヰヱヮヵヶ",
    "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをんぁぃぅぇぉっゃゅょゔがぎぐげござじずぜぞだぢづでどばびぶべぼぱぴぷぺぽゐゑゎかけ"
)

HIRAGANA_REGEX = re.compile(r"^[\u3041-\u3096\u3099-\u309fー]+$")

def to_hiragana(text: str) -> str:
    return text.translate(KATAKANA_TO_HIRAGANA)

def clean_reading(text: str) -> str:
    cleaned = re.sub(r"[\s・＝=－\-]+", "", text)
    return to_hiragana(cleaned)

def api_request(params: dict) -> dict:
    params["format"] = "json"
    url = f"{API_ENDPOINT}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            if attempt == 2:
                print(f"[WARN] API request failed: {e}", file=sys.stderr)
                return {}
            time.sleep(1.5)
    return {}

def fetch_table_nijisanji():
    """Wikipedia「にじさんじ」記事の所属テーブル({{読み|名前|よみ}})から抽出"""
    print("Fetching Nijisanji members from Wikipedia 'にじさんじ' article...")
    res = api_request({
        "action": "query",
        "prop": "revisions",
        "rvprop": "content",
        "titles": "にじさんじ"
    })
    results = []
    pages = res.get("query", {}).get("pages", {})
    for page in pages.values():
        revs = page.get("revisions", [])
        if not revs:
            continue
        content = revs[0].get("*", "")
        # {{読み|名前|よみ}} パターン
        pattern = re.compile(r"\{\{読み\|([^|]+)\|([^}]+)\}\}")
        for raw_name, raw_reading in pattern.findall(content):
            name = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", raw_name).strip()
            reading = clean_reading(raw_reading)
            if name and HIRAGANA_REGEX.match(reading):
                results.append({
                    "name": name,
                    "readings": [reading],
                    "affiliation": "にじさんじ",
                    "category": "人名",
                    "source": "https://ja.wikipedia.org/wiki/にじさんじ"
                })
    print(f"Retrieved {len(results)} members from Nijisanji article.")
    return results

def fetch_table_vspo():
    """Wikipedia「ぶいすぽっ! Virtual eSports Project」のテーブルから抽出"""
    print("Fetching VSPO members from Wikipedia article...")
    res = api_request({
        "action": "query",
        "prop": "revisions",
        "rvprop": "content",
        "titles": "ぶいすぽっ! Virtual eSports Project"
    })
    results = []
    pages = res.get("query", {}).get("pages", {})
    for page in pages.values():
        revs = page.get("revisions", [])
        if not revs:
            continue
        content = revs[0].get("*", "")
        # | 名前<br/>（よみ） パターン
        pattern = re.compile(r"\|\s*([^\s<|]+)<br\s*/?>\s*（([^）]+)）")
        for raw_name, raw_reading in pattern.findall(content):
            name = raw_name.strip()
            reading = clean_reading(raw_reading)
            if name and HIRAGANA_REGEX.match(reading):
                results.append({
                    "name": name,
                    "readings": [reading],
                    "affiliation": "ぶいすぽっ！",
                    "category": "人名",
                    "source": "https://ja.wikipedia.org/wiki/ぶいすぽっ!_Virtual_eSports_Project"
                })
    print(f"Retrieved {len(results)} members from VSPO article.")
    return results

def get_category_page_titles(cat_title: str, max_depth: int = 1, current_depth: int = 0) -> set:
    """指定カテゴリ配下の記事タイトル一覧を取得（再帰的にサブカテゴリも探索）"""
    titles = set()
    res = api_request({
        "action": "query",
        "list": "categorymembers",
        "cmtitle": cat_title,
        "cmlimit": "500",
        "cmtype": "page|subcat"
    })
    members = res.get("query", {}).get("categorymembers", [])
    for m in members:
        t = m.get("title", "")
        if m.get("ns") == 14:  # Subcategory
            if current_depth < max_depth:
                titles.update(get_category_page_titles(t, max_depth, current_depth + 1))
        elif m.get("ns") == 0:  # Page
            titles.add(t)
    return titles

def parse_lead_reading(title: str, extract: str):
    """Wikipediaリード文冒頭から正式表記とふりがなを抽出"""
    clean_title = re.sub(r"\s*\(.*?\)$", "", title).strip()
    m = re.match(r"^(?:[^\s（(]+(?:\s+[^\s（(]+)*)[（(]([^）)]+)[）)]", extract)
    if not m:
        return None
    inside = m.group(1)
    first_part = re.split(r"[,、;；]", inside)[0].strip()
    if re.search(r"[a-zA-Z0-9]", first_part):
        return None
    reading = clean_reading(first_part)
    if HIRAGANA_REGEX.match(reading):
        return clean_title, reading
    return None

def fetch_category_vtubers():
    """VTuberカテゴリ配下の記事リード文から抽出"""
    print("Collecting VTuber article titles from Wikipedia categories...")
    categories = [
        "Category:バーチャルYouTuberグループ所属のバーチャルYouTuber",
        "Category:バーチャルYouTuber",
    ]
    all_titles = set()
    for cat in categories:
        titles = get_category_page_titles(cat, max_depth=1)
        all_titles.update(titles)
        time.sleep(0.5)

    # 一般項目・除外タイトルのフィルタ
    ignore_keywords = ["一覧", "歴史", "プロジェクト:", "テンプレート:", "Portal:", "音楽", "イベント", "賞", "用語"]
    filtered_titles = [
        t for t in all_titles
        if not any(k in t for k in ignore_keywords)
    ]
    print(f"Found {len(filtered_titles)} candidate articles. Fetching extracts...")

    results = []
    chunk_size = 40
    for i in range(0, len(filtered_titles), chunk_size):
        chunk = filtered_titles[i:i + chunk_size]
        res = api_request({
            "action": "query",
            "prop": "extracts",
            "exintro": "1",
            "explaintext": "1",
            "titles": "|".join(chunk)
        })
        pages = res.get("query", {}).get("pages", {})
        for p in pages.values():
            title = p.get("title", "")
            extract = p.get("extract", "")
            parsed = parse_lead_reading(title, extract)
            if parsed:
                name, reading = parsed
                results.append({
                    "name": name,
                    "readings": [reading],
                    "affiliation": "VTuber",
                    "category": "人名",
                    "source": f"https://ja.wikipedia.org/wiki/{urllib.parse.quote(title)}"
                })
        time.sleep(0.3)

    print(f"Retrieved {len(results)} valid VTuber items from Wikipedia articles.")
    return results

def main():
    parser = argparse.ArgumentParser(description="Fetch VTuber names and readings from Wikipedia API")
    parser.add_argument("--dry-run", action="store_true", help="Do not write to data file")
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent.parent
    data_file = base_dir / "data" / "vtubers.json"
    overrides_file = base_dir / "data" / "overrides.json"

    # 1. 各ソースから取得
    wiki_items = []
    wiki_items.extend(fetch_table_nijisanji())
    wiki_items.extend(fetch_table_vspo())
    wiki_items.extend(fetch_category_vtubers())

    # 重複の整理
    merged_map = {}
    for item in wiki_items:
        name = item["name"]
        if name not in merged_map:
            merged_map[name] = item
        else:
            for r in item["readings"]:
                if r not in merged_map[name]["readings"]:
                    merged_map[name]["readings"].append(r)

    print(f"Total unique VTubers fetched from Wikipedia: {len(merged_map)}")

    if args.dry_run:
        print("Dry run completed.")
        return

    # 既存データの読み込み
    with open(data_file, "r", encoding="utf-8") as f:
        existing = json.load(f)

    # overridesの読み込み
    overrides = []
    if overrides_file.exists():
        with open(overrides_file, "r", encoding="utf-8") as f:
            overrides = json.load(f)
    override_map = {item["name"]: item for item in overrides}

    # マージ処理（Wikipediaの正確な読みを優先）
    existing_map = {item["name"]: item for item in existing}
    added_count = 0
    updated_count = 0

    for name, item in merged_map.items():
        if name not in existing_map:
            existing.append(item)
            existing_map[name] = item
            added_count += 1
        else:
            # 既存エントリの読みを更新/修正
            cur = existing_map[name]
            cur_readings = set(cur.get("readings", []))
            new_readings = set(item.get("readings", []))
            # Wikipediaの正式読みが含まれていなければ追加
            if not new_readings.issubset(cur_readings):
                cur["readings"] = sorted(list(cur_readings | new_readings))
                updated_count += 1

    # overrides を最優先適用（誤読の完全上書き）
    override_count = 0
    for name, o_item in override_map.items():
        if name in existing_map:
            existing_map[name]["readings"] = o_item["readings"]
            if "affiliation" in o_item and o_item["affiliation"] != "VTuber":
                existing_map[name]["affiliation"] = o_item["affiliation"]
            override_count += 1
        else:
            existing.append({
                "name": name,
                "readings": o_item["readings"],
                "affiliation": o_item.get("affiliation", "VTuber"),
                "category": o_item.get("category", "人名"),
                "source": "manual_override"
            })
            override_count += 1

    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

    print(f"Summary: {added_count} added, {updated_count} updated, {override_count} overrides applied.")
    print(f"Total master records: {len(existing)}")

if __name__ == "__main__":
    main()
