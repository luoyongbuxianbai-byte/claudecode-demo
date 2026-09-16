#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""条目既有研究反查（126AF 立）

**为什么有这个工具。**
126AF 顺序首读 §74–§94，我在读记里把 **§91** 和 **§80／§81** 各自重新推导了一遍——
而二者**早有专题册**：
  · §91 ⇒ `evidence/并读核证_P02_治疗次序_第91条与第48条_126U.md`
          ＋ `evidence/并读核证_P01_治疗史之作用_第15_20_42_45条_126T.md`
  · §80／§81 ⇒ `evidence/研究纲领_v0_126H.md` §3.3 ＋ 126I 之 P0-005
⭐ 更糟的是：126I 在那里立过一条明禁——
  「⛔⛔ **不得预先把二者判为矛盾，也不得预先自动调和。**」
而我在 126AF 读记里**直接给出了调和**（「因【素有】与【新得】而禁忌相反」）。
⇒ 这是**盲区⑤·失忆型**（本工程立过而我不知道的现行纪律）之又一次发作，
　 且这一次它的**触发点是明确的**：**顺序读到某条时，我没有查该条是否已有专题册。**

⇒ 本工具把那一步变成一条可以真的跑出结果的命令。

用法
----
  python3 tools/prior_work.py 91 80 81          # 查这几条
  python3 tools/prior_work.py --range 74 94     # 查一个连续区间（顺序首读之常用形态）

输出
----
逐条列出**提到该条号**的仓库文件，并把命中行里的**禁令句**（含「不得」「⛔」「撤回」
「明禁」等）单独标出——因为**重复劳动只是浪费，撞上旧禁令才是出错**。

⛔ **本工具之限度**（⛔ 不得据其输出宣称「此条无旧账」）：
  ① 它按**字面条号**检索（「第91条」「§91」「91条」）。⛔ 旧册若只写方名（「真武汤」「栀子干姜汤」）
     而不写条号，**本工具查不到** —— 126AF 实测：`研究纲领_v0_126H.md` 之 §80 段
     正是以「§80」形态出现才被检出，而 `翻转组_三组五栏重编码.md` 之「真武汤」**未被检出**。
     ⇒ **条号反查之后，仍须以【方名】再查一次**（见 `hxs-crossbook` 之异写族）。
  ② 它**不判断**旧册说了什么，只告诉你**哪里说过** ——⛔ 命中之后必须去读。
  ③ 零命中**只表示「按这几个字面形态没查到」**，⛔ 不表示「本工程从未研究过」。
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 只查**研究资产**，不查语料、不查冻结件
DIRS = ['evidence', 'reports', 'rules', 'docs']
# 报告是历史快照，命中它们通常只说明「那一批提过」，与现行纪律无关 ⇒ 分开列
HISTORICAL = re.compile(r'reports/报告_第\w+批\.md$')
# 撞上这些词，说明旧册在那里立过限制 —— 这才是必须读的
BANS = re.compile(r'不得|⛔|撤回|明禁|禁令|已改|过强|须限定|不许')


def forms(n):
    """一个条号之字面形态族。⛔ 不含方名 —— 见限度①。"""
    return [f'第{n}条', f'§{n}', f'{n}条']


def hits(n):
    """返回 {路径: [(行号, 行文)]}，已按目录白名单过滤。"""
    out = {}
    for f in forms(n):
        try:
            r = subprocess.run(
                ['rg', '-n', '--no-heading', '-F', f] + DIRS,
                cwd=ROOT, capture_output=True, text=True, timeout=60)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            sys.exit('⛔ 需要 ripgrep（rg）')
        for line in r.stdout.splitlines():
            parts = line.split(':', 2)
            if len(parts) < 3:
                continue
            path, ln, txt = parts[0], parts[1], parts[2]
            out.setdefault(path, []).append((int(ln), txt.strip()))
    return out


def report(n):
    h = hits(n)
    cur = {p: v for p, v in h.items() if not HISTORICAL.search(p)}
    old = {p: v for p, v in h.items() if HISTORICAL.search(p)}
    print('\n══ 第%s条 ══' % n)
    if not cur and not old:
        print('  （按字面形态零命中 —— ⛔ 只表示没查到，不表示没研究过；仍须以方名再查）')
        return 0
    if cur:
        print('  ▶ 现行资产（**读记展开前必须去读**）：')
        for p in sorted(cur):
            lines = sorted(set(cur[p]))
            banned = [t for _, t in lines if BANS.search(t)]
            print('    · %s　（%d 处）' % (p, len(lines)))
            for t in banned[:2]:
                print('      ⛔ 该文件在此条上立过限制：%s' % (t[:110]))
    if old:
        print('  · 历史报告快照（%d 份）：%s' % (
            len(old), '、'.join(os.path.basename(p) for p in sorted(old)[:6])))
    return len(cur)


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    if args[0] == '--range':
        a, b = int(args[1]), int(args[2])
        nums = list(range(a, b + 1))
    else:
        nums = [int(x) for x in args]
    total = 0
    withprior = []
    for n in nums:
        c = report(n)
        total += c
        if c:
            withprior.append(n)
    print('\n── 小结 ──')
    print('  查 %d 条｜其中 **%d 条已有现行资产**：%s'
          % (len(nums), len(withprior), withprior))
    print('  ⛔ 零命中不等于无旧账（限度①③）；⛔ 命中之后必须去读，本工具不替你读。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
