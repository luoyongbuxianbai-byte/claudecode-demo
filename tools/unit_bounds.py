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
  ① 只认**形如「第N条」之显式标记**——⛔ 无此标记之书（讲金匮多数篇章、编者整理系）测不出；
     ⭐ **126AB 实测之假阳性**：《讲伤寒》**第24条**在 OCR 本中作「**24、太阳病……**」〔29943〕，
     ⛔ 本工具漏检 ⇒ 账本之「第23条／第24条」被误报为边界不齐。**该二单元实为正确。**
     ⇒ ⛔ **本工具报「不对齐」者须人读复核**，⛔ 不得据其输出径改账本；
  ② 条目标记**落在讲解中段之引用**（作者复述条文号）会被误当边界；
  ③ 它检查的是**边界**，⛔ 不检查**是否真的逐字读过**该区间。
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from corpus_guard import load_one, BOOKS  # noqa: E402

MARK = re.compile(r'第(\d+)条')
# ⚠ 另一形态：句末之「N、」（《讲伤寒》第24条即此形）。⛔ 误报风险高（讲解内之列举亦作「1、2、」）
#   ⇒ 只用于**提示**，⛔ 不进 marks()。
ALT = re.compile(r'(?<=。)(\d{1,3})、')


def marks(text):
    """返回 [(pos, 条号)]，按位置升序。⛔ 含作者复述之条文号（见限度②）。"""
    return [(m.start(), int(m.group(1))) for m in MARK.finditer(text)]


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
    ms = marks(t)
    print('《%s》长度 %d ｜ 检出「第N条」标记 %d 处' % (book, len(t), len(ms)))
    nalt = len(ALT.findall(t))
    if nalt:
        print('⚠ 另检出「N、」形态 %d 处（⛔ 未计入边界判定，⛔ 误报风险高）'
              '—— 第24条即此形〔29943〕' % nalt)
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
