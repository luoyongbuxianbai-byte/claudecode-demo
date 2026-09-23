#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""topic_lookup.py —— 检索时同时呈现【原文】与【现行研究状态】，⛔ 不以摘要代原文（126BX·用户令）。

用户 WeKnora 对照核查之要求：
  「检索结果同时呈现原文和现行研究状态。原文不能被摘要替代；历史撤回内容可以查到，
    但不能作为当前结论无标记返回。」

本工具**不另造证据库、不造向量索引**——只把已有两件事接起来：
  ① `rules/report_index_v0.json`（现行命题、支持、反证、撤回登记 R-02）
  ② `tools/corpus_guard.py::load_one`（十二书清洗字位原文，唯一取数口径）

⛔ 本工具不判定任何命题真假，不做相似度检索，只做**字面匹配 + 原样呈现**。
⛔ 匹配是子串匹配，会漏掉改写与同义表达——漏检计入缺口，不代表「已确认不存在」。

用法：
    python3 tools/topic_lookup.py <关键词> [关键词2 ...]
    python3 tools/topic_lookup.py <关键词> --ctx 300      # 原文上下文窗口字数（默认200）
    python3 tools/topic_lookup.py <关键词> --book 讲金匮  # 指定书名（默认依次尝试全部12书）
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import corpus_guard  # noqa: E402

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(B, "rules", "report_index_v0.json")

STATUS_MARK = {
    "current": "⭐ 现行",
    "partial": "⚠ 部分（缺口已写明）",
    "open": "⛔ 未决",
    "retracted_registry": "⛔⛔ 撤回登记",
    "superseded": "⛔ 已被取代",
}

# 索引内偏移量常被 markdown 强调符包裹，如「〔**89599**〕」——须容许 *_ 等符号。
OFFSET_RE = re.compile(r"[〔\[][\s*_]*(\d{3,7})[\s*_]*[〕\]]")

# 检索优先书序：项目内最常引用的两本在前，其余按 BASELINE 顺序补齐。
BOOK_ORDER = ["讲伤寒", "讲金匮"] + [
    b for b in corpus_guard.BASELINE if b not in ("讲伤寒", "讲金匮")
]

_cache = {}


def _load(book):
    if book not in _cache:
        try:
            _cache[book] = corpus_guard.load_one(book)
        except SystemExit as e:
            _cache[book] = None
            print("  ⛔ %s 载入失败：%s" % (book, e))
    return _cache[book]


def find_offset_context(offset, ctx, forced_book=None):
    """在指定书（或依 BOOK_ORDER 逐本尝试）里取 offset 附近原文，返回 (book, text) 或 None。"""
    books = [forced_book] if forced_book else BOOK_ORDER
    for book in books:
        text = _load(book)
        if text is None:
            continue
        if 0 <= offset < len(text):
            lo = max(0, offset - ctx)
            hi = min(len(text), offset + ctx)
            return book, text[lo:hi]
    return None


def entry_blob(e):
    return "\n".join([
        e.get("proposition", ""), e.get("support", ""),
        e.get("counter", ""), e.get("note", ""),
    ])


def search_entries(d, terms):
    hits = []
    for ch in d["chapters"]:
        for e in ch["entries"]:
            blob = entry_blob(e)
            if all(t in blob for t in terms):
                hits.append((ch, e))
    return hits


def search_retractions(d, terms):
    hits = []
    for ch in d["chapters"]:
        for e in ch["entries"]:
            if e["status"] != "retracted_registry":
                continue
            for r in e.get("retractions", []):
                probe_blob = " ".join(r.get("probes", [])) + " " + r.get("text", "")
                if all(t in probe_blob for t in terms):
                    hits.append(r)
    return hits


def main():
    argv = sys.argv[1:]
    ctx = 200
    forced_book = None
    terms = []
    i = 0
    while i < len(argv):
        if argv[i] == "--ctx" and i + 1 < len(argv):
            ctx = int(argv[i + 1]); i += 2; continue
        if argv[i] == "--book" and i + 1 < len(argv):
            forced_book = argv[i + 1]; i += 2; continue
        terms.append(argv[i]); i += 1

    if not terms:
        print(__doc__)
        sys.exit(1)

    d = json.load(open(SRC, encoding="utf-8"))

    print("=" * 70)
    print("① 撤回登记匹配（⛔ 匹配到即说明：曾有人这样写过，且已被撤回）")
    print("=" * 70)
    ret_hits = search_retractions(d, terms)
    if not ret_hits:
        print("（无撤回登记之 probe 命中此关键词组合——⛔ 不代表该说法从未出现过，"
              "只代表未被本工程登记为撤回 probe，见 retraction_scan.py 之已知盲区）")
    for r in ret_hits:
        print("\n⛔⛔ %s（%s批撤回）" % (r["rid"], r["batch"]))
        print("  曾写：%s" % r["text"])
        print("  现行：%s" % r["replacement"][:400])
        print("  关联条目：%s" % ", ".join(r.get("linked", [])))

    print()
    print("=" * 70)
    print("② 现行索引条目匹配（当前命题/支持/反证——⛔ 这是索引，不是原文）")
    print("=" * 70)
    ent_hits = search_entries(d, terms)
    if not ent_hits:
        print("（无索引条目命中——⛔ 不代表本工程未讨论过该话题，只代表未以此字面登记）")
    all_offsets = []
    for ch, e in ent_hits:
        print("\n`%s`　%s（第%d章 %s）" % (e["id"], STATUS_MARK[e["status"]], ch["no"], ch["title"]))
        print("  当前命题：%s" % e["proposition"][:500])
        if e["status"] in ("partial", "open"):
            print("  ⚠ 反证/缺口：%s" % e["counter"][:400])
        print("  来源锚：%s" % ", ".join(e["anchors"]))
        blob = entry_blob(e)
        all_offsets.extend(int(m) for m in OFFSET_RE.findall(blob))

    print()
    print("=" * 70)
    print("③ 原文（未摘要，逐条给出书名+字位+上下文——⛔ 与②分开陈列，不合并改写）")
    print("=" * 70)
    seen = set()
    for off in all_offsets:
        if off in seen:
            continue
        seen.add(off)
        r = find_offset_context(off, ctx, forced_book)
        if r is None:
            print("\n〔%d〕 ⛔ 未在已尝试书目内命中偏移（可能属另一书或索引记录有误）" % off)
            continue
        book, text = r
        print("\n〔%d〕《%s》原文（±%d字）：" % (off, book, ctx))
        print("  " + text.replace("\n", " "))

    print()
    print("⛔⛔ 本工具不做的事：不判定命题真假，不做语义相似检索（只字面子串），"
          "不合并①②③为一段结论——三者须分开阅读。")


if __name__ == "__main__":
    main()
