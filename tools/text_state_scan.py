#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""文本状态标记之机器扫（126AJ 立·还 126AI 之债）

**立此工具之由**（126AI `顺序首读_讲伤寒_027` §三）：
  抽查复读 §127 全 369 字，捕到**三项漏项**，且**都不是医学内容，是【文本状态标记】**
  ——音频缺失标记、OCR 未识别标记、章节边界。
  ⇒ 该册当时写明：「⭐ **可行之补救**：缺失标记／未识别标记／章节边界**可机器扫**
    ⇒ ⛔ **本批未做** ⇒ **下批**。」**本工具即此。**

⛔⛔ **协议16（静默数据销毁防护）**
  本工具**全部用【有界】模式**，⛔ **严禁**无界 `\\S*` 之类 JUNK 正则 ——
  无界正则会把整段吞掉而**不留任何痕迹**，这正是协议16 所禁者。
  每个模式之最大跨度**显式写在 `PATTERNS` 内**。

⛔⛔ **分类之纪律**（126AJ·上级指出）
  ⭐ **观测与成因须分开命名**：
    · **自陈缺失** —— 文本自己写了「音频缺失／丢失／没录上」⇒ **成因已由文本给出**；
    · **标记** —— 时间码、讲次号、省略号：⭐ **这些首先是【位置／讲次标记】**，
      ⛔ **不得未经核实直接命名为「音频缺失」**（上级原话：「『第17讲』**首先是讲次标记**」）；
    · **占位／未识别文本** —— `xx`、方框、空括注：⭐ 记作**占位**即可，
      ⛔ **「是 OCR 所致」是推论，⛔ 不是观测** ⇒ **成因待核**。
  ⛔⛔ **本工具报【观测】，⛔ 不报【成因】。**

⛔⛔ **本工具之限度（须与结果同读）**
  ① 它只查**已知形态**（见账本 `gap_marker_forms`）＋若干附加标记。
     ⛔ **第八种形态它查不出来** —— 而 126AI 之第六种、126AJ 之第七种
     都是**人读时撞见的**，⛔ 不是机器找出来的。⇒ **此工具⛔ 不能取代抽查复读。**
  ② 它报**标记之位置**，⛔ **不报缺了多少字** —— 缺失之长度**无从由文本内部测得**。
  ③ 章节标题之缺（如 COL-028「第八章」0 处）属**否定性事实**，
     ⛔ 本工具只能报「未检出」，⛔ 不能证明「原书无此章」。

用法：
    python3 tools/text_state_scan.py                 # 全书扫（讲伤寒）
    python3 tools/text_state_scan.py --book 讲金匮
    python3 tools/text_state_scan.py --range 154751 169825
    python3 tools/text_state_scan.py --unread        # 只报落在【未读区】者
"""
import os
import re
import sys

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(B, "tools"))
import corpus_guard  # noqa: E402

LEDGER = os.path.join(B, "evidence", "顺序首读账本.json")

# ⛔ 每一条都是**有界**的。括号内数字即该模式之最大跨度（字符）。
PATTERNS = [
    # ── 甲：**自陈缺失**（⭐ 文本自己说了缺，⇒ 成因已由文本给出） ──
    ("自陈缺失·显式括号", r"[（(]音频(?:缺失|丢失)[）)]", 8),
    ("自陈缺失·没录上", r"[（(][^）)]{0,24}没录上[）)]", 28),
    # ── 乙：**位置／讲次标记**（⛔ 成因未自陈，⛔ 不得径称「缺失」） ──
    ("标记·时间码", r"[（(]\s*\d{1,3}\s*[：:]\s*\d{1,2}\s*[—\-－~～]\s*\d{1,3}\s*[：:]\s*\d{1,2}", 26),
    ("标记·讲次号内嵌", r"第\s*\d{1,2}\s*讲", 6),
    ("标记·讲次号括注", r"[（(]第[一二三四五六七八九十百\d]{1,4}讲[）)]", 8),
    # ⭐ 省略号族：**限长**，⛔ 不得写成 `…+` 之无界形
    ("标记·省略号族", r"(?:⋯{2,12}|。{5,20}|\.{5,20}|…{2,12})", 20),
    # ── 丙：**占位／未识别文本**（⛔ 成因待核，⛔ 不得径称 OCR 所致） ──
    ("占位·x 串", r"(?<![A-Za-z])x{2,6}(?![A-Za-z])", 6),
    ("占位·方框", r"[□■]{1,12}", 12),
    ("占位·空括注", r"[（(]\s{0,4}[）)]", 6),
    # ── 丁：结构边界 ──
    ("结构·章标题", r"第[一二三四五六七八九十]{1,3}章[^\n]{0,24}", 28),
    ("结构·篇标题", r"辨[^\n]{0,8}病脉证并治[^\n]{0,4}", 16),
    # ── 戊：讲者自标之中断／自纠 ──
    ("自标·讲到这", r"(?:今天|咱们今天|咱们)[^\n]{0,6}(?:就)?讲到这", 12),
    ("自标·上次我讲", r"上次我讲[^\n]{0,12}", 16),
]


def units(book):
    import json
    if not os.path.isfile(LEDGER):
        return []
    d = json.load(open(LEDGER, encoding="utf-8"))
    return d.get("books", {}).get(book, {}).get("sequential_units", [])


def which_unit(us, pos):
    for u in us:
        if u["start"] <= pos < u["end"]:
            return u["title"]
    return None


def main():
    av = sys.argv[1:]
    book = av[av.index("--book") + 1] if "--book" in av else "讲伤寒"
    lo, hi = 0, None
    if "--range" in av:
        i = av.index("--range")
        lo, hi = int(av[i + 1]), int(av[i + 2])
    only_unread = "--unread" in av

    t = corpus_guard.load_one(book)
    hi = len(t) if hi is None else hi
    us = units(book)
    read_end = max([u["end"] for u in us], default=0)

    print("═══ 文本状态标记扫 · %s ═══" % book)
    print("范围 [%d,%d)｜全长 %d｜A 档已读至 %d" % (lo, hi, len(t), read_end))
    print("⛔ 本工具只查【已知形态】；⛔ 新形态查不出来，⛔ 不能取代抽查复读。\n")

    total = 0
    for name, pat, span in PATTERNS:
        rx = re.compile(pat)
        hits = []
        for m in rx.finditer(t, lo, hi):
            if len(m.group(0)) > span:          # ⛔ 有界自检：超出声明跨度即报错停
                print("⛔⛔ 模式 `%s` 命中长度 %d > 声明上限 %d @%d ⇒ **模式无界，停**"
                      % (name, len(m.group(0)), span, m.start()))
                return 2
            hits.append(m)
        if only_unread:
            hits = [m for m in hits if m.start() >= read_end]
        total += len(hits)
        print("── %s　命中 %d" % (name, len(hits)))
        for m in hits[:40]:
            u = which_unit(us, m.start())
            zone = u if u else ("**未读区**" if m.start() >= read_end else "已读区·单元外")
            print("   〔%6d〕 %-12s %s" % (m.start(), zone, m.group(0).replace("\n", "⏎")[:40]))
        if len(hits) > 40:
            print("   ⚠【截断】另有 %d 处未列 ⇒ 加 `--range` 缩窄再看" % (len(hits) - 40))

    print("\n合计 %d 处。" % total)
    print("⛔ 位置 ≠ 缺失长度：缺了多少字**无从由文本内部测得**（限度②）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
