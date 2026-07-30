#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
機種カタログ machines.json を生成するスクリプト（外部ライブラリ不要／標準ライブラリのみ）。

入力:
  manual_seed.json … 手入力の機種リスト（配列）。これが「正」で品質のベースライン。
出力:
  machines.json … アプリが取得するカタログ（{version, updatedAt, machines:[{name,type,maker}]}）。

オプション（環境変数 AUGMENT_WIKIPEDIA=1 のときだけ）:
  Wikipedia の公式 API（MediaWiki API）からカテゴリのページ一覧を取得し、
  シードに無い機種名を「best-effort」で追加する。カバレッジは限定的でノイズも入り得るため、
  既定では OFF。品質重視でまずはシードのみで運用し、必要なら ON にする。
"""

import json
import os
import sys
import datetime
import urllib.request
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
SEED_PATH = os.path.join(ROOT, "manual_seed.json")
OUT_PATH = os.path.join(ROOT, "machines.json")

# Wikipedia 拡張で見に行くカテゴリ（存在しなければ無視されるだけ・安全）。
WIKI_CATEGORIES = [
    ("Category:パチスロ", "slot"),
    ("Category:パチンコ", "pachinko"),
]
WIKI_API = "https://ja.wikipedia.org/w/api.php"
USER_AGENT = "SuroCashCatalogBot/1.0 (https://github.com/yamashitagames49-cpu/surocash-machines)"

# 明らかに機種でないページを除外するためのキーワード。
WIKI_EXCLUDE = ["一覧", "Category:", "Template:", "Wikipedia:", "メーカー", "会社",
                "ホール", "業界", "規則", "遊技", "の歴史", "問題"]


def norm(name: str) -> str:
    return name.strip()


def load_seed():
    with open(SEED_PATH, encoding="utf-8") as f:
        data = json.load(f)
    out = []
    for m in data:
        n = norm(m.get("name", ""))
        t = m.get("type", "slot")
        if n and t in ("slot", "pachinko"):
            out.append({"name": n, "type": t, "maker": m.get("maker", "")})
    return out


def classify(title: str) -> str:
    """タイトルからスロ/パチをざっくり判定（拡張用）。"""
    if title.startswith(("P", "e", "ぱちんこ", "パチンコ", "CR")):
        return "pachinko"
    return "slot"


def fetch_category_members(category: str):
    """MediaWiki API でカテゴリ内のページ名を取得（best-effort）。"""
    titles = []
    params = {
        "action": "query", "list": "categorymembers",
        "cmtitle": category, "cmlimit": "500", "cmtype": "page", "format": "json",
    }
    url = WIKI_API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    for m in data.get("query", {}).get("categorymembers", []):
        title = m.get("title", "")
        if title and not any(x in title for x in WIKI_EXCLUDE):
            titles.append(title)
    return titles


def augment_from_wikipedia(existing_names):
    added = []
    for category, default_type in WIKI_CATEGORIES:
        try:
            for title in fetch_category_members(category):
                if title in existing_names:
                    continue
                t = classify(title)
                # カテゴリ由来の型よりタイトル推定を優先しつつ、無矛盾なら採用
                added.append({"name": title, "type": t, "maker": ""})
                existing_names.add(title)
        except Exception as e:  # ネットワーク/カテゴリ不在は無視
            print(f"  [warn] {category}: {e}", file=sys.stderr)
    return added


def main():
    machines = load_seed()
    names = {m["name"] for m in machines}
    print(f"seed: {len(machines)} 件")

    if os.environ.get("AUGMENT_WIKIPEDIA") == "1":
        print("Wikipedia 拡張: ON")
        extra = augment_from_wikipedia(names)
        machines += extra
        print(f"  +{len(extra)} 件を追加")
    else:
        print("Wikipedia 拡張: OFF（シードのみ）")

    # 並び替え: スロット→パチンコ、その後 名前順
    machines.sort(key=lambda m: (0 if m["type"] == "slot" else 1, m["name"]))

    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    out = {"version": 1, "updatedAt": today, "machines": machines}
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"wrote {OUT_PATH}: {len(machines)} 件 (updatedAt={today})")


if __name__ == "__main__":
    main()
