#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""解释单元边界核验（126AB 立·上级令四）

> 上级 126AB 原文：「**精确锚与完整语境是两项检查；锚点存在不能证明语境读全。**」

本工程 126Y–126AA 连续三批在**同一条**（讲金匮·茯苓）上因**取证半径不足**而改判；
126AA 报告更把一个**越进下一条 482 字**的窗口称作「§100 讲解全段」。
⇒ 锚核对了，不等于单元读全了。**这是两项独立检查。**

用法
----
  # 给锚，问它落在哪一条、该条的真边界在哪
  python3 tools/unit_bounds.py 讲伤寒 --anchor 161934

  # 给区间，问它是否与条目边界对齐
  python3 tools/unit_bounds.py 讲伤寒 --range 122232 124000

  # 列出某区间内的所有条目起点
  python3 tools/unit_bounds.py 讲伤寒 --list 79000 84000

⛔ **本工具之限度**（⛔ 不得据其输出宣称「已读全」）：
  ① 只认两种显式标记：「**第N条**」与句末之「**N、**」——⛔ 无此二者之书（讲金匮多数篇章、
     编者整理系）仍测不出。⭐ 126AE 纳入「N、」形态，实测《讲伤寒》**六条**用此形
     （§24〔29942〕／§70〔92020〕／§71〔93930〕／§72〔96234〕／§74〔97653〕／§75〔98087〕），
     ⭐ 126AE **二改后实测七条**：§24〔29942〕／§70〔92020〕／§71〔93930〕／§72〔96234〕／
     **§73〔96660〕**／§74〔97653〕／§75〔98087〕——其中 §24／§71–§75 **全书只有此一形态**。
     ⚠ §73 前 **OCR 缺句号**（「这一条就简略了73、伤寒…」），一改之 `(?<=。)` 前瞻仍漏它 ⇒ 二改放宽。
  ② **两闸**（单调递增 ＋ 号差 ≤ 3）排除三类误切：作者在讲解中段**回指**之条文号；
     末篇之**章节小标题**（「2、六经的本质」「3、八纲解」「4、加减应用」等，号重置为 2/3/4）；
     讲解内之**数量列举**（「用 3、4 钱」）。⭐ 实测采用 **397** 处、排除 **35** 处，
     所采之号自 **1 递增至 398**，⚠ **仅一处跳跃 (340→342)** ⇒ **§341 之形态另需人读核**。
     ⛔ 两闸**不能**排除「回指了一个【更大且差 ≤ 3】的号」之情形。
  ③ 它检查的是**边界**，⛔ 不检查**是否真的逐字读过**该区间——
     ⭐ 126AC 实证：§64 边界报对而内容仍漏（开头那句「这不一定是误治」）。
  ⇒ ⛔⛔ **在 ②③ 解除之前，其输出只作【候选边界】，⛔ 不作全集。**
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from corpus_guard import load_one, BOOKS  # noqa: E402

MARK = re.compile(r'第(\d+)条')
# 另一形态：句末之「N、」。《讲伤寒》至少六条用此形（§24/70/71/72/74/75）。
# 126AE 前只作提示、不进 marks()，结果 §70/§71 被漏检 —— 故本批纳入，但须过单调性闸。
# 126AE 二改：原作 (?<=。) 前瞻，而 §73 前 OCR 缺句号（「这一条就简略了73、伤寒…」）⇒ 仍漏。
# 现放宽为「非数字 + N、 + 非数字」，改由【单调递增 ＋ 号差 ≤ GAP】两闸过滤噪声。
ALT = re.compile(r'(?<![0-9])(\d{1,3})、(?=[^\d])')
GAP = 3  # 相邻条号之最大允许跳跃


def _raw(text):
    """两形态之全部候选，按位置升序。每项 (pos, 号, 形态)。"""
    a = [(m.start(), int(m.group(1)), 'MARK') for m in MARK.finditer(text)]
    b = [(m.start(), int(m.group(1)), 'ALT') for m in ALT.finditer(text)]
    return sorted(a + b)


def marks(text, detail=False):
    """返回 [(pos, 条号)]，按位置升序。

    126AE：两形态合并，并过**条号单调递增**闸——
      · 作者在讲解中段复述之条文号（「咱们讲第12条」）多为回指，号小于当前 ⇒ 被排除；
      · 末篇之章节小标题（「2、六经的本质」「3、八纲解」…）号重置为 2/3/4 ⇒ 被排除；
      · 讲解内之数量列举（「用 3、4 钱」）号差过大或不递增 ⇒ 被排除。
    ⛔ 该闸不能排除「回指了一个【更大且差 ≤ 3】的号」之情形（限度②仍在）。
    """
    kept, dropped, last = [], [], -1
    for pos, n, kind in _raw(text):
        if n > last and (last < 0 or n - last <= GAP):
            kept.append((pos, n))
            last = n
        else:
            dropped.append((pos, n, kind))
    return (kept, dropped) if detail else kept


def unit_of(ms, pos, textlen):
    """pos 落在哪一条：返回 (条号, start, end)。"""
    prev = None
    for i, (p, n) in enumerate(ms):
        if p > pos:
            break
        prev = (i, p, n)
    if prev is None:
        return (None, 0, ms[0][0] if ms else textlen)
    i, p, n = prev
    end = ms[i + 1][0] if i + 1 < len(ms) else textlen
    return (n, p, end)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    book = sys.argv[1]
    names = [b[0] if isinstance(b, (tuple, list)) else b for b in BOOKS]
    if book not in names:
        sys.exit('⛔ 未知书名：%s（可选：%s）' % (book, '/'.join(names)))
    t = load_one(book)
    print('《%s》长度 %d' % (book, len(t)))
    kept, dropped = marks(t, detail=True)
    ms = kept
    n_alt = sum(1 for p, _ in ms for q, _, k in _raw(t) if q == p and k == 'ALT')
    print('  形态合并：「第N条」＋「N、」｜采用 %d 处（其中「N、」形态 %d 处）｜'
          '单调性闸排除 %d 处' % (len(ms), n_alt, len(dropped)))
    if dropped:
        ex = '｜'.join('%d〔%d〕%s' % (n, p, k) for p, n, k in dropped[:4])
        print('  被排除者示例：%s …（回指或章节小标题）' % ex)
    print('  ⛔ 输出只作【候选边界】，不作全集（见文件头限度②③）。')
    if not ms:
        print('⛔ 本书无显式条目标记 ⇒ 本工具测不出边界（限度①）。')
        return 0

    args = sys.argv[2:]
    if '--anchor' in args:
        pos = int(args[args.index('--anchor') + 1])
        n, a, b = unit_of(ms, pos, len(t))
        print('\n锚〔%d〕落在：第%s条 [%d,%d)　长 %d 字' % (pos, n, a, b, b - a))
        print('  距该条起点 %d 字｜距终点 %d 字' % (pos - a, b - pos))
        print('  条首：%s' % t[a:a + 40].replace('\n', ''))
        print('  条末：%s' % t[b - 40:b].replace('\n', ''))
        return 0

    if '--list' in args:
        i = args.index('--list')
        a, b = int(args[i + 1]), int(args[i + 2])
        print('\n[%d,%d) 内之条目起点：' % (a, b))
        for p, n in ms:
            if a <= p < b:
                print('  第%-4s条 〔%d〕 %s' % (n, p, t[p:p + 30].replace('\n', '')))
        return 0

    if '--range' in args:
        i = args.index('--range')
        a, b = int(args[i + 1]), int(args[i + 2])
        starts = {p for p, _ in ms}
        na, sa, ea = unit_of(ms, a, len(t))
        nb, sb, eb = unit_of(ms, max(a, b - 1), len(t))
        print('\n区间 [%d,%d)　长 %d 字' % (a, b, b - a))
        ok_a = a in starts
        ok_b = b in starts or b == len(t)
        print('  起点 %d：%s' % (a, '✅ 正落在条目起点（第%s条）' % na if ok_a
                                else '⛔ 不在条目起点 —— 落在第%s条内，距其起点 %d 字（真起点 %d）'
                                     % (na, a - sa, sa)))
        print('  终点 %d：%s' % (b, '✅ 正落在下一条目起点' if ok_b
                                else '⛔ 不在条目边界 —— 落在第%s条内，距其起点 %d 字' % (nb, b - sb)))
        if na != nb:
            span = [n for p, n in ms if a < p < b]
            print('  ⛔⛔ **跨条**：本区间横跨第%s条 … 第%s条（其间另有条目起点 %d 处：%s）'
                  % (na, nb, len(span), span[:12]))
            print('  ⇒ ⛔ **不得称之为「第%s条全段」**。' % na)
        else:
            print('  ⭐ 区间未跨条，所属：第%s条 真边界 [%d,%d)' % (na, sa, ea))
        return 0

    sys.exit(__doc__)


if __name__ == '__main__':
    sys.exit(main())
