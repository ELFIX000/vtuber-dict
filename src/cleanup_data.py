#!/usr/bin/env python3
"""
マスターデータ(data/vtubers.json)からWikidata由来の不正確な読み（ファンネーム、愛称、配信ネタ等）
を一括検知・クリーンアップし、正確な正規読みに統一するスクリプト。
"""
import json
import re
from pathlib import Path

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

def is_kana_only(text: str) -> bool:
    cleaned = re.sub(r"[\s・＝=－\-]+", "", text)
    return bool(re.match(r"^[\u3040-\u309F\u30A0-\u30FF\u30FC]+$", cleaned))

def cleanup_records():
    base_dir = Path(__file__).resolve().parent.parent
    data_file = base_dir / "data" / "vtubers.json"
    overrides_file = base_dir / "data" / "overrides.json"

    with open(data_file, "r", encoding="utf-8") as f:
        records = json.load(f)

    # 1. overrides を読み込み
    override_map = {}
    if overrides_file.exists():
        with open(overrides_file, "r", encoding="utf-8") as f:
            for item in json.load(f):
                override_map[item["name"]] = item

    cleaned_count = 0
    new_records = []

    for item in records:
        name = item["name"]
        readings = item.get("readings", [])
        original_readings = list(readings)

        # A. 手動オーバーライドがある場合最優先
        if name in override_map:
            item["readings"] = override_map[name]["readings"]
            if "affiliation" in override_map[name] and override_map[name]["affiliation"] != "VTuber":
                item["affiliation"] = override_map[name]["affiliation"]
            if item["readings"] != original_readings:
                print(f"[OVERRIDE] {name}: {original_readings} -> {item['readings']}")
                cleaned_count += 1
            new_records.append(item)
            continue

        # B. 名前自体が仮名のみ（カタカナ・ひらがな）の場合
        if is_kana_only(name):
            canonical = clean_reading(name)
            valid = {canonical}
            if "ゑ" in canonical:
                valid.add(canonical.replace("ゑ", "え"))
            if "ゐ" in canonical:
                valid.add(canonical.replace("ゐ", "い"))
            
            # 正しい読みに一本化（ファンネーム・あだ名を除去）
            new_readings = [r for r in readings if r in valid]
            if not new_readings:
                new_readings = [canonical]
            item["readings"] = sorted(list(set(new_readings)))
            if item["readings"] != original_readings:
                print(f"[KANA-CLEAN] {name}: {original_readings} -> {item['readings']}")
                cleaned_count += 1
            new_records.append(item)
            continue

        # C. Wikipedia由来（source に wikipedia が含まれる）または Wikipediaで確認できるもの
        # 複数読みがある場合で、明らかに名前の一部の短縮形や別名があれば整理
        # 例: 剣持刀也: ['けんもちとうや', 'ぶれいどもあなまん'] -> ['けんもちとうや']
        if len(readings) > 1:
            # カタカナが含まれる場合（例: フレン・E・ルスタリオ）
            # 明らかに名前と無関係な読字を除去
            pass

        new_records.append(item)

    # 既知の明らかなゴミ読みのフィルタリング
    blacklist_readings_map = {
        "剣持刀也": ["けんもちとうや"],
        "フレン・E・ルスタリオ": ["ふれんいーるすたりお"],
        "中野公": ["なかのおおやけ"],
        "しぐれうい": ["しぐれうい"],
        "佃煮のりお": ["つくだにのりお"],
        "バーチャル美少女ねむ": ["ばーちゃるびしょうじょねむ"],
        "ゴールドシップ": ["ごーるどしっぷ"],
        "アキ・ローゼンタール": ["あきろーぜんたーる"],
        "アイラニ・イオフィフティーン": ["あいらにいおふぃふてぃーん"],
        "ワトソン・アメリア": ["わとそんあめりあ"],
        "すーぱーそに子": ["すーぱーそにこ"],
        "天羽しろっぷ": ["あまうしろっぷ"],
        "鏑木ろこ": ["かぶらきろこ"],
        "バーチャルのじゃロリ狐娘Youtuberおじさん": ["ばーちゃるのじゃろりきつねむすめゆーちゅーばーおじさん"]
    }

    for item in new_records:
        name = item["name"]
        if name in blacklist_readings_map:
            before = item["readings"]
            item["readings"] = blacklist_readings_map[name]
            if before != item["readings"]:
                print(f"[SPECIFIC-CLEAN] {name}: {before} -> {item['readings']}")
                cleaned_count += 1

    # まだ登録されていない新規追加エントリを new_records に追加
    existing_names = {item["name"] for item in new_records}
    for name, o_item in override_map.items():
        if name not in existing_names:
            new_records.append({
                "name": name,
                "readings": o_item["readings"],
                "affiliation": o_item.get("affiliation", "VTuber"),
                "category": o_item.get("category", "人名"),
                "source": "manual_override"
            })
            print(f"[NEW-OVERRIDE] Added new entry from overrides: {name} -> {o_item['readings']}")
            cleaned_count += 1

    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(new_records, f, ensure_ascii=False, indent=2)

    print(f"\nCleanup complete. Modified {cleaned_count} entries.")

if __name__ == "__main__":
    cleanup_records()
