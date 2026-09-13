#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""同段异写对照检索（111批立为常设法；126D 封装为 skill 脚本）。

⛔ 本脚本只做一件事：把一个查询词**机械地**展开成异写族，在十二书**逐书**检索，
   **逐书报数、不合并计数**，并把命中处的字位锚打印出来。

⛔ 它**不判断**「有没有」。0 命中只等于「本检索式在本书未命中」，
   **不等于「本书无此说」**（闸门9⑦：不得以检索宣称全库无）。

用法：
    python3 crossbook.py 脉缓                      # 自动展开异写族
    python3 crossbook.py 脉缓 缓脉 脉逐渐缓          # 追加人工异写
    python3 crossbook.py 脉缓 --ctx 80 --max 5     # 每书最多打 5 处，各带 80 字上下文
    python3 crossbook.py --pair 缓 胃气             # 双向式：缓…胃气 与 胃气…缓 各查
"""
import argparse
import os
import re
import sys

B = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, os.path.join(B, "tools"))
import corpus_guard  # noqa: E402  —— 闸门9 第六款：十二书统一入口


def expand(term):
    """机械展开异写族。⛔ 只做可解释的三类变形，不猜近义词——近义表达须人工补。"""
    fam = [("原词", re.escape(term))]
    if len(term) == 2:
        fam.append(("词序倒装", re.escape(term[1] + term[0])))
    if len(term) >= 2:
        # 修饰词插入：A(0-3字)B，如 脉缓 ↔ 脉逐渐缓、脉浮缓
        fam.append(("修饰词插入", re.escape(term[0]) + r".{1,3}" + re.escape(term[-1])))
    if len(term) >= 3:
        fam.append(("首尾相连", re.escape(term[0]) + re.escape(term[-1])))
    return fam


def scan(text, pat):
    return [m.start() for m in re.finditer(pat, text)]


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("terms", nargs="*", help="查询词；第一个自动展开异写族，其余按原样查")
    ap.add_argument("--pair", nargs=2, metavar=("A", "B"),
                    help="双向式：A…B 与 B…A 各查（GATE_2 必查项）")
    ap.add_argument("--gap", type=int, default=12, help="--pair 之最大间隔字数（默认 12）")
    ap.add_argument("--ctx", type=int, default=60, help="每处命中打印之上下文字数")
    ap.add_argument("--max", type=int, default=3, help="每书每式最多打印几处")
    a = ap.parse_args()

    fam = []
    if a.pair:
        x, y = a.pair
        fam = [("双向·%s…%s" % (x, y),
                re.escape(x) + r".{0,%d}" % a.gap + re.escape(y)),
               ("双向·%s…%s" % (y, x),
                re.escape(y) + r".{0,%d}" % a.gap + re.escape(x))]
        label = "%s ↔ %s" % (x, y)
    elif a.terms:
        fam = expand(a.terms[0])
        fam += [("人工补·" + t, re.escape(t)) for t in a.terms[1:]]
        label = a.terms[0]
    else:
        ap.error("须给 terms 或 --pair")

    books = corpus_guard.load_books()   # 任一本缺失即中止，不静默跳过

    print("═══ 同段异写对照检索：%s ═══" % label)
    print("检索式族（%d 式）：" % len(fam))
    for name, pat in fam:
        print("  - %-14s %s" % (name, pat))
    print()

    total = {}
    hdr = "%-14s" % "书" + "".join("%10s" % n[:9] for n, _ in fam) + "%8s" % "合计"
    print(hdr)
    print("-" * len(hdr))
    detail = []
    for bk, txt in books.items():
        row, s = [], 0
        for name, pat in fam:
            hits = scan(txt, pat)
            row.append(len(hits))
            s += len(hits)
            for off in hits[:a.max]:
                detail.append((bk, name, off,
                               txt[max(0, off - a.ctx // 2): off + a.ctx // 2]))
        total[bk] = s
        print("%-14s" % bk + "".join("%10d" % v for v in row) + "%8d" % s)

    print()
    print("⛔ **逐书报数，不合并计数**——合并会把「只在一本里有」读成「普遍如此」。")
    hit_books = [b for b, v in total.items() if v]
    print("命中之书：%d / 12　%s" % (len(hit_books), "｜".join(hit_books) or "（无）"))

    if detail:
        print("\n─── 命中处（前 %d/式/书）───" % a.max)
        for bk, name, off, seg in detail:
            print("〔A·%s·%d〕[%s] …%s…" % (bk, off, name, seg.replace("\n", "")))

    print("""
⛔⛔ 读数之前先读这句：
   0 命中 = **本检索式在本书未命中**，≠「本书无此说」。
   欲作否定性断言，须另补：①近义表达（本脚本不猜）②概念级通读（见 hxs-reading）
   ③闸门9⑦：不得以检索宣称「全库无此规则」。
   本次所用检索式族**须原样抄入证据册**，只留结论者不算取证（GATE_2 record_required）。""")


if __name__ == "__main__":
    main()
