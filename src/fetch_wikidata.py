#!/usr/bin/env python3
"""
Wikidata SPARQLエンドポイントからVTuberの公開データを取得し、
マスターデータ（data/vtubers.json）とマージするクリーンルーム抽出スクリプト。
標準ライブラリ（urllib, json）のみで動作します。
"""
import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
USER_AGENT = "VTuberDictBuilder/1.0 (https://github.com; open-source-vtuber-dict)"

# バーチャルYouTuber(Q60783350)のインスタンスを取得するSPARQLクエリ
QUERY_TEMPLATE = """
SELECT DISTINCT ?item ?itemLabel ?kana ?affiliationLabel WHERE {{
  ?item wdt:P31/wdt:P279* wd:Q60783350 .
  OPTIONAL {{ ?item wdt:P1814 ?kana . }}
  OPTIONAL {{ ?item wdt:P361 ?affiliation . }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "ja,en". }}
}}
LIMIT {limit}
"""

KATAKANA_TO_HIRAGANA = str.maketrans(
    "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲンァィゥェォッャュョヴガギグゲゴザジズゼゾダヂヅデドバビブベボパピプペポ",
    "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをんぁぃぅぇぉっゃゅょゔがぎぐげござじずぜぞだぢづでどばびぶべぼぱぴぷぺぽ"
)

def to_hiragana(text: str) -> str:
    """カタカナをひらがなに変換"""
    return text.translate(KATAKANA_TO_HIRAGANA)

def clean_reading(text: str) -> str:
    """不要な空白や記号を除去してひらがな化"""
    cleaned = re.sub(r"[\s・＝=－\-]+", "", text)
    return to_hiragana(cleaned)

def fetch_from_wikidata(limit: int = 1000):
    query = QUERY_TEMPLATE.format(limit=limit)
    params = urllib.parse.urlencode({"query": query, "format": "json"})
    url = f"{SPARQL_ENDPOINT}?{params}"

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/sparql-results+json"
        }
    )

    print(f"Fetching data from Wikidata SPARQL API (limit={limit})...")
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    results = []
    bindings = data.get("results", {}).get("bindings", [])
    for b in bindings:
        item_uri = b.get("item", {}).get("value", "")
        name = b.get("itemLabel", {}).get("value", "").strip()
        kana = b.get("kana", {}).get("value", "").strip()
        affiliation = b.get("affiliationLabel", {}).get("value", "").strip()

        # Wikidata IDそのままの名前はスキップ（日本語ラベル未設定等）
        if re.match(r"^Q\d+$", name):
            continue

        readings = []
        if kana:
            readings.append(clean_reading(kana))

        results.append({
            "name": name,
            "readings": list(dict.fromkeys(readings)),
            "affiliation": affiliation if affiliation and not re.match(r"^Q\d+$", affiliation) else "VTuber",
            "category": "人名",
            "source": item_uri
        })

    print(f"Retrieved {len(results)} items from Wikidata.")
    return results

def merge_records(existing_records, new_records):
    existing_map = {item["name"]: item for item in existing_records}
    added_count = 0
    updated_count = 0

    for item in new_records:
        name = item["name"]
        if name not in existing_map:
            if item["readings"]:
                existing_records.append(item)
                existing_map[name] = item
                added_count += 1
        else:
            cur = existing_map[name]
            for r in item["readings"]:
                if r not in cur.get("readings", []):
                    cur.setdefault("readings", []).append(r)
                    updated_count += 1

    return existing_records, added_count, updated_count

def main():
    parser = argparse.ArgumentParser(description="Fetch VTuber names from Wikidata SPARQL endpoint")
    parser.add_argument("--limit", type=int, default=500, help="Max records to query")
    parser.add_argument("--dry-run", action="store_true", help="Do not write to data file")
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent.parent
    data_file = base_dir / "data" / "vtubers.json"

    with open(data_file, "r", encoding="utf-8") as f:
        existing = json.load(f)

    fetched = fetch_from_wikidata(limit=args.limit)

    if args.dry_run:
        print(f"Dry run: {len(fetched)} items fetched. Not modifying data file.")
        return

    merged, added, updated = merge_records(existing, fetched)
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    print(f"Summary: {added} added, {updated} updated. Total master records: {len(merged)}")

if __name__ == "__main__":
    main()
