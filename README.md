# Open VTuber IME Dictionary (VTuber変換辞書)

[![Build & Release](https://github.com/ELFIX000/vtuber-dict/actions/workflows/build.yml/badge.svg)](https://github.com/ELFIX000/vtuber-dict/actions/workflows/build.yml)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/ELFIX000/vtuber-dict)](https://github.com/ELFIX000/vtuber-dict/releases/latest)
[![収録VTuber数](https://img.shields.io/badge/収録VTuber数-1072人-2ea44f.svg)](data/vtubers.json)
[![収録単語数](https://img.shields.io/badge/収録単語数-1158語-0969da.svg)](dist/google_ime.txt)
[![License: CC0-1.0](https://img.shields.io/badge/License-CC0_1.0-blue.svg)](https://creativecommons.org/publicdomain/zero/1.0/)

VTuber（バーチャルYouTuber）の名前やユニット名を、各種日本語入力システム（IME）でスムーズに一発変換できるようにするオープンソースの変換辞書プロジェクトです。

---

## 🌟 特徴
- **マルチIME対応**: Google 日本語入力 / Mozc、Microsoft IME (Windows)、macOS ユーザ辞書、ATOK に対応。
- **高精度な読み仮名**: ファンネームや愛称と正式名称を区別し、純粋な名前の読みのみを厳選収録。
- **自動ビルド・履歴管理**: GitHub Actions による自動ビルド、CalVer（日付バージョン）での過去リリース全保存。コミュニティからのIssue/PRで手軽に追加・修正可能。

---

## 📥 ダウンロード

最新の辞書データは **[最新リリース（Latest Release）](https://github.com/ELFIX000/vtuber-dict/releases/latest)** または **[すべてのリリース履歴](../../releases)** からダウンロードできます。

- **`vtuber-dict-all.zip`**: 全形式同梱パッケージ（迷ったらこれ）
- **個別形式**:
  - `google_ime.txt`: Google日本語入力 / Mozc 向け (UTF-8 TSV)
  - `ms_ime.txt`: Microsoft IME (Windows) 向け (UTF-16LE BOM, CRLF TSV)
  - `macos_user_dict.plist`: macOS ユーザ辞書 向け (XML Property List)
  - `atok.txt`: ATOK 向け (UTF-16LE BOM, CRLF TSV)

---

## 💻 インポート手順

### 1. Google 日本語入力 / Mozc
1. タスクバーまたはメニューバーの入力メニューから **「プロパティ」** または **「辞書ツール」** を開きます。
2. 上部メニューの **「管理」 > 「新規辞書にインポート」** を選択します。
3. ファイルに `google_ime.txt` を指定し、辞書名（例: `VTuber`）を入力してインポートします。

### 2. Microsoft IME (Windows 10 / 11)
1. IMEアイコンを右クリックし、**「設定」 > 「学習と辞書」** （または辞書ツール）を開きます。
2. **「ユーザ辞書ツール」** を起動します。
3. メニューバーの **「ツール」 > 「テキストファイルからの登録」** を選択します。
4. `ms_ime.txt` を選択して読み込みます。

### 3. macOS (日本語入力)
1. **「システム設定」 > 「キーボード」 > 「ユーザ辞書...」** （または「テキスト置換」）を開きます。
2. ダウンロードした `macos_user_dict.plist` を、設定画面の一覧エリアに**直接ドラッグ＆ドロップ**します。
3. （※ iCloud同期が有効な場合、同じApple IDのiPhone / iPadにも自動反映されます）

### 4. ATOK
1. ATOKメニューの **「辞書メンテナンス」 > 「単語一括処理」** を開きます。
2. 「単語ファイル」に `atok.txt` を指定し、登録先辞書を選択して **「登録」** を実行します。

---

## 🛠️ 開発・ビルド方法

### 必要環境
- Python 3.9 以上（外部追加ライブラリ不要、標準ライブラリのみで動作）

### バリデーションの実行
```bash
python3 src/validator.py
```

### 辞書のビルド
```bash
python3 src/builder.py
```
実行後、`dist/` フォルダ配下に各IME用ファイルおよび `vtuber-dict-all.zip` が出力されます。

---

## 🤝 コントリビューション・データ修正

データの追加や修正はいつでも歓迎しています！

- **Issueからの申請**: 未登録のVTuberや読みの間違いがあれば、[Issues](../../issues) からテンプレートに沿って投稿してください。メンテナにより辞書データへ反映されます。
- **Pull Request**: `data/overrides.json` または `data/vtubers.json` に追加・修正を記述してPRを送ってください。PR作成時に GitHub Actions により `validator.py` が自動実行され、データの整合性が検証されます。

---

## 📜 ライセンスと帰属表示
- プログラムコード / スクリプト: **MIT License**
- 辞書データ (`data/` 配下および生成された辞書ファイル): **CC0 1.0 Universal (Public Domain)**
  - ※ 辞書データは固有名詞およびその読み仮名という著作権法上の保護対象外である客観的事実情報で構成されています。
  - データ抽出元:
    - [Wikidata](https://www.wikidata.org/) (licensed under [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/))
    - [日本語版 Wikipedia](https://ja.wikipedia.org/) (licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/))

