#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""顺序首读账本（126F·上级执行单 §5.6）。

工程只做四件事：**保存、定位、漏段检查、版本核对**。⛔ 不编译医学规则。

口径（上级执行单）：
  · 顺序首读 A 与主题跳读 B **分别记账**，B 不计入 A 之连续覆盖
  · 覆盖率 = 已完成连续单元区间**并集**字符数 ÷ 该版本本书清洗字符数；重复不重复计数
  · 断点保存 `last_completed_unit` 与 `next_offset`，会话到边界即存，不回头问读哪段
  · ⛔ 「文字读过」不证明「构念没有漏掉」——本工具只报**文本阅读覆盖**，
    不得改名为「理论理解率」

用法：
    python3 tools/reading_ledger.py --status          # 报覆盖、断点、漏段
    python3 tools/reading_ledger.py --next 讲伤寒       # 取下一段待读文本
    python3 tools/reading_ledger.py --verify          # 核源版本与区间自洽
"""
import hashlib
import json
import os
import sys

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(B, "evidence", "顺序首读账本.json")
sys.path.insert(0, os.path.join(B, "tools"))
import corpus_guard  # noqa: E402

# 上级执行单 §5.2 之固定队列。⛔ 执行排队，非出版时序、非证据等级。
QUEUE = ["讲伤寒", "讲金匮", "C卷", "病位类方解", "临床家", "传真系",
         "汤液经方系", "中国汤液方证", "伤寒论传真", "金匮要略传真", "带教", "解读"]

# ⚠ 体裁分区：同一文件内体裁改变处，speaker 不得由文件级标签继承（126F 实证）。
GENRE_SPLITS = {
    "讲伤寒": [
        {"start": 0, "end": 387513, "genre": "lecture_transcript",
         "speaker": "hu_lecture", "note": "讲课正文"},
        {"start": 387513, "end": 395556, "genre": "appended_article",
         "speaker": "unresolved",
         "note": "《胡希恕的六经辨证观》——与 C卷 绪论同名同序，60字窗 20% 精确重合"
                 "（余差疑 OCR）。⛔ 署名／引录关系未核，不继承文件级 hu_lecture"},
    ],
}


def blank():
    return {"schema": "reading_ledger_v0", "created": "126F",
            "caveat": "本账本只报文本阅读覆盖；⛔ 不得改名为理论理解率或构念覆盖率",
            "books": {}}


def load():
    if os.path.exists(LEDGER):
        return json.load(open(LEDGER, encoding="utf-8"))
    return blank()


def save(d):
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    json.dump(d, open(LEDGER, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def src_id(book):
    t = corpus_guard.load_one(book)
    return {"book": book, "cleaned_len": len(t),
            "cleaned_sha12": hashlib.sha256(t.encode("utf-8")).hexdigest()[:12],
            "loader": "tools/corpus_guard.py::load_one"}


def merge(spans):
    """区间并集——重复阅读不重复计数。"""
    if not spans:
        return []
    s = sorted((x["start"], x["end"]) for x in spans)
    out = [list(s[0])]
    for a, z in s[1:]:
        if a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], z)
        else:
            out.append([a, z])
    return out


def gaps(un, total):
    """漏段检查：并集之外的区间。"""
    g, cur = [], 0
    for a, z in un:
        if a > cur:
            g.append([cur, a])
        cur = max(cur, z)
    if cur < total:
        g.append([cur, total])
    return g


def status(d):
    print("═══ 顺序首读账本（A 档·连续首读）═══")
    print("⛔ 本表只报**文本阅读覆盖**，不报理解、不报构念覆盖。\n")
    tot_read = tot_all = 0
    for bk in QUEUE:
        sid = src_id(bk)
        rec = d["books"].get(bk, {})
        un = merge(rec.get("sequential_units", []))
        read = sum(z - a for a, z in un)
        tot_read += read
        tot_all += sid["cleaned_len"]
        mark = "✅" if read >= sid["cleaned_len"] else ("▶" if read else "·")
        print("%s %-12s %7d / %7d = %6.3f%%  单元 %d  断点 %s" % (
            mark, bk, read, sid["cleaned_len"],
            100 * read / sid["cleaned_len"], len(rec.get("sequential_units", [])),
            rec.get("next_offset", 0)))
        if rec.get("sequential_units"):
            gp = gaps(un, sid["cleaned_len"])
            if len(gp) > 1:
                print("    ⚠ 漏段 %d 处：%s" % (len(gp) - 1, gp[:-1]))
        if rec.get("src") and rec["src"]["cleaned_sha12"] != sid["cleaned_sha12"]:
            print("    ⛔⛔ 源版本已变！账本记 %s，现为 %s ⇒ 区间失效，须重核" % (
                rec["src"]["cleaned_sha12"], sid["cleaned_sha12"]))
    print("\n十二书合计 %d / %d = %.4f%%" % (tot_read, tot_all, 100 * tot_read / tot_all))
    done = sum(1 for bk in QUEUE
               if sum(z - a for a, z in merge(d["books"].get(bk, {}).get(
                   "sequential_units", []))) >= src_id(bk)["cleaned_len"])
    print("完整通读：**%d / 12 本**" % done)
    b = d.get("topical_reads", 0)
    print("主题跳读（B 档，⛔ 不计入上表）：%d 次" % b)


def nxt(d, book, budget=6000):
    sid = src_id(book)
    rec = d["books"].get(book, {})
    off = rec.get("next_offset", 0)
    t = corpus_guard.load_one(book)
    print("═══ %s 下一段 ═══" % book)
    print("源 %s｜全长 %d｜起点 %d" % (sid["cleaned_sha12"], sid["cleaned_len"], off))
    for g in GENRE_SPLITS.get(book, []):
        if g["start"] <= off < g["end"]:
            print("⚠ 体裁分区：%s｜speaker=%s｜%s" % (g["genre"], g["speaker"], g["note"]))
    print("⛔ 下列分块长度是**传输预算**，不是语义边界。"
          "读完条文还要读完评议，到语义终点才可标完整。\n")
    print(t[off:off + budget])


def main():
    d = load()
    if "--next" in sys.argv:
        i = sys.argv.index("--next")
        nxt(d, sys.argv[i + 1],
            int(sys.argv[i + 2]) if len(sys.argv) > i + 2 and sys.argv[i + 2].isdigit() else 6000)
    elif "--verify" in sys.argv:
        ok = True
        for bk, rec in d["books"].items():
            sid = src_id(bk)
            if rec.get("src", {}).get("cleaned_sha12") != sid["cleaned_sha12"]:
                print("⛔ %s 源版本不符" % bk); ok = False
            for u in rec.get("sequential_units", []):
                if not (0 <= u["start"] < u["end"] <= sid["cleaned_len"]):
                    print("⛔ %s 区间越界：%s" % (bk, u)); ok = False
        print("核对完毕：%s" % ("✅ 自洽" if ok else "⛔ 有问题"))
    else:
        status(d)


if __name__ == "__main__":
    main()
