#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""条目既有研究反查（126AF 立｜**126AG 四修 ＋ 术语族**）

**为什么有这个工具。**
126AF 顺序首读 §74–§94，我在读记里把 **§91** 和 **§80／§81** 各自重新推导了一遍——
而二者早有专题册，且 126I 在 §80／§81 上立过明禁「⛔ 不得预先自动调和」，我撞上了。
⇒ 触发点明确：**顺序读到某条时，我没有查该条是否已有专题册。**

⛔⛔ **本工具只用于【定位】。**
⭐ 上级 126AG：「**不能把它做成『看到旧结论就照抄』的工具——旧结论只用于定位，
当前原文仍须独立阅读。**」⇒ 它告诉你**哪里说过**，⛔ 它不告诉你**那里说得对**。

126AG 四修（上级逐条指出之风险）
--------------------------------
① ⭐ **编号边界** —— 126AF 版查 `§80` 会命中 `§800`／`§8012`。现加**右边界**：
   条号之后不得紧跟数字。（⚠ 左边界由形态本身给出：`第N条`／`§N`／`N条`。）
② ⭐ **截断必须显式** —— 126AF 版只印前 2 条禁令句、每条截到 110 字符，
   **限定语会被截掉而读者不知道**。现在：凡有省略必印 `⚠ 已省略 N 条`，
   并给**完整结果之取法**（`--full <条号>`）。
③ ⭐ **「现行资产」是错的名字** —— 旧研究册也可能含**已撤回结论**。
   现改称**「非报告类文件」**，并对每个命中文件跑一次**撤回登记反查**，
   命中则标 `⚠ 该文件含撤回登记之 probe 字串`。
④ ⭐ **rg 异常退出须区分** —— 126AF 版把「rg 失败」与「零命中」表现成一样。
   现在三态分明：`FAILED`（检索本身失败）／`EMPTY`（跑通且零命中）／`HIT`。
   ⛔ **`FAILED` 时本工具以非零码退出**，⛔ 不得当作「没有旧账」。

⭐ **新增：方名／术语族反查**（126AF 限度①）
   `--terms 真武汤 栀子干姜汤` —— 旧册常只写方名而不写条号，条号反查必漏。
   ⚠ 术语族**由调用者给出**，⛔ 本工具不自动展开异写（⇒ 见 `hxs-crossbook`）。

用法
----
  python3 tools/prior_work.py 91 80 81
  python3 tools/prior_work.py --range 95 103
  python3 tools/prior_work.py --range 95 103 --terms 小柴胡汤 小建中汤
  python3 tools/prior_work.py --terms 倒装 主之 --full-terms   # 命题关键词路径，不省略
  python3 tools/prior_work.py --full 91          # 某条之【完整】命中，不省略

⛔ **限度（⛔ 不得据其输出宣称「此条无旧账」）**
  ① **改写型漏检**：旧册若既不写条号、也不写你给的术语，查不到。
  ② 它**不判断**旧册说了什么 ⇒ 命中之后**必须去读**。
  ③ `EMPTY` 只表示「按这些字面形态没查到」，⛔ 不表示「本工程从未研究过」。
"""
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIRS = ['evidence', 'reports', 'rules', 'docs']
HISTORICAL = re.compile(r'reports/报告_第\w+批\.md$')
BANS = re.compile(r'不得|⛔|撤回|明禁|禁令|已改|过强|须限定|不许')
SNIP = 240          # 禁令句之显示长度（126AF 为 110 ⇒ 限定语被截）
MAXBAN = 3          # 每文件最多印几条；超出必显式报省略


class SearchFailed(Exception):
    pass


def rg(pattern, fixed=True):
    """跑一次 rg。⛔ 退出码 2 ＝ **检索本身出错** ⇒ 抛异常，⛔ 不静默当零命中。
    （rg 约定：0 ＝ 有命中｜1 ＝ 无命中｜≥2 ＝ 出错）"""
    cmd = ['rg', '-n', '--no-heading']
    # ⚠ 126AG 实测：右边界用否定前瞻（`§80(?![0-9])`），而 rg 默认引擎（Rust regex）
    #   **不支持 look-around** ⇒ 退出码 2。⭐ 这一次恰好是第④修自己把失败暴露出来的
    #   （126AF 版会把它显示成「零命中」）⇒ 故须显式启用 PCRE2。
    cmd += ['-F'] if fixed else ['--pcre2']
    cmd += [pattern] + DIRS
    try:
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True,
                           text=True, timeout=120)
    except FileNotFoundError:
        raise SearchFailed('未找到 ripgrep（rg）')
    except subprocess.TimeoutExpired:
        raise SearchFailed('rg 超时（>120s）：%s' % pattern)
    if r.returncode >= 2:
        raise SearchFailed('rg 退出码 %d：%s\n%s'
                           % (r.returncode, pattern, r.stderr.strip()[:300]))
    return r.stdout.splitlines()


def num_forms(n):
    """一个条号之字面形态族。⭐ 126AG：加**右边界**，`§80` 不再命中 `§800`。"""
    n = str(n)
    # rg 正则；⛔ 不用 -F，因为需要否定前瞻式的右边界
    return [r'第%s条' % n, r'§%s(?![0-9])' % n, r'(?<![0-9])%s条' % n]


def collect(patterns, fixed):
    out = {}
    for pat in patterns:
        for line in rg(pat, fixed=fixed):
            parts = line.split(':', 2)
            if len(parts) < 3:
                continue
            out.setdefault(parts[0], set()).add((int(parts[1]), parts[2].strip()))
    return out


def retraction_probes():
    """撤回登记之全部 probe 字串（用于给命中文件打「⚠ 含已撤回内容」标）。"""
    p = os.path.join(ROOT, 'rules', 'report_index_v0.json')
    try:
        d = json.load(open(p, encoding='utf-8'))
    except Exception:
        return []
    probes = []
    for ch in d.get('chapters', []):
        for e in ch.get('entries', []):
            for r in e.get('retractions', []):
                probes += [s for s in r.get('probes', []) if len(s) >= 4]
    return probes


def report(n, probes, full=False):
    """返回 ('HIT'|'EMPTY', 非报告类文件数)。"""
    h = collect(num_forms(n), fixed=False)
    cur = {p: v for p, v in h.items() if not HISTORICAL.search(p)}
    old = {p: v for p, v in h.items() if HISTORICAL.search(p)}
    print('\n══ 第%s条 ══' % n)
    if not cur and not old:
        print('  **EMPTY** —— 按 %s 三种形态跑通且零命中。' % len(num_forms(n)))
        print('  ⛔ 这只表示「按这些字面形态没查到」，⛔ 不表示没研究过（限度①③）；'
              '⇒ 请另以**方名**再查：`--terms <方名>`')
        return 'EMPTY', 0
    if cur:
        print('  ▶ **非报告类文件**（⚠ 旧研究册也可能含**已撤回**结论 ⇒ 须查版本）：')
        for p in sorted(cur):
            lines = sorted(cur[p])
            bans = [t for _, t in lines if BANS.search(t)]
            # ③ 该文件是否含撤回登记之 probe
            body = ''
            try:
                body = open(os.path.join(ROOT, p), encoding='utf-8').read()
            except Exception:
                pass
            hitp = [s for s in probes if s in body]
            tag = '　⚠ **该文件含撤回登记之 probe 字串 %d 个**' % len(hitp) if hitp else ''
            print('    · %s　（%d 处）%s' % (p, len(lines), tag))
            show = bans if full else bans[:MAXBAN]
            for t in show:
                s = t if full else t[:SNIP]
                print('      ⛔ %s%s' % (s, '' if (full or len(t) <= SNIP) else ' …⚠【截断】'))
            if not full and len(bans) > MAXBAN:
                print('      ⚠⚠ **已省略 %d 条限制句** ⇒ 完整结果：'
                      '`python3 tools/prior_work.py --full %s`' % (len(bans) - MAXBAN, n))
    if old:
        print('  · 历史报告快照（%d 份，⛔ 是那一批的快照，⛔ 非现行状态）：%s'
              % (len(old), '、'.join(os.path.basename(p) for p in sorted(old)[:6])))
    return 'HIT', len(cur)


def terms(ts, probes, full=False):
    """⭐ 126AJ 补齐（上级令四）：**术语路径此前只报命中数** ——
    ⛔ 不显示**撤回候选**、⛔ 不显示**截断状态**，而条号路径两者都有。
    ⇒ 于是「按命题关键词查旧结论与撤回」这一步，**在术语路径上是空的**。现补齐。
    """
    print('\n══ 术语／方名／命题关键词反查 ══')
    print('　⚠ 词族由**调用者**给出，⛔ 本工具不自动展开异写（⇒ `hxs-crossbook`）')
    print('　⭐ **上级 126AJ 令四**：形成命题后，**除条号检索，再按命题关键词查旧结论与撤回**。')
    for q in ts:
        h = collect([q], fixed=True)
        cur = {p: v for p, v in h.items() if not HISTORICAL.search(p)}
        old = {p: v for p, v in h.items() if HISTORICAL.search(p)}
        if not cur and not old:
            print('\n  · 「%s」**EMPTY**（跑通且零命中）' % q)
            print('    ⛔ 零命中⛔ 不代表没有旧判断 —— 该判断可能以**别的措辞**写着（限度①）。')
            continue
        print('\n  · 「%s」命中 %d 个非报告类文件%s：'
              % (q, len(cur), ('｜历史报告快照 %d 份' % len(old)) if old else ''))
        for p in sorted(cur):
            lines = sorted(cur[p])
            bans = [t for _, t in lines if BANS.search(t)]
            # ⭐ 126AJ 补①：撤回登记 probe 反查（与条号路径同）
            try:
                body = open(os.path.join(ROOT, p), encoding='utf-8').read()
            except Exception:
                body = ''
            hitp = [x for x in probes if x in body]
            tag = '　⚠ **含撤回登记之 probe 字串 %d 个**' % len(hitp) if hitp else ''
            print('      · %s（%d 处）%s' % (p, len(lines), tag))
            # ⭐ 126AJ 补②：截断显式化（与条号路径同）
            show = bans if full else bans[:MAXBAN]
            for t in show:
                body_s = t if full else t[:SNIP]
                print('        ⛔ %s%s' % (body_s,
                      '' if (full or len(t) <= SNIP) else ' …⚠【截断】'))
            if not full and len(bans) > MAXBAN:
                print('        ⚠⚠ **已省略 %d 条限制句** ⇒ 完整结果：'
                      '`python3 tools/prior_work.py --terms %s --full-terms`'
                      % (len(bans) - MAXBAN, q))
    print('\n  ⛔⛔ **机器只做召回** —— 命中**必须去读原册**；'
          '⛔ 零命中⛔ 不代表没有旧判断（上级 126AJ 令四）。')


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    ts = []
    if '--terms' in args:
        i = args.index('--terms')
        ts = [x for x in args[i + 1:] if not x.startswith('--')]
        args = args[:i]
    probes = retraction_probes()
    print('⭐ 撤回登记 probe 字串：%d 个（用于标记命中文件是否含已撤回内容）' % len(probes))

    try:
        if args and args[0] == '--full':
            report(int(args[1]), probes, full=True)
            if ts:
                terms(ts, probes)
            return 0
        if args and args[0] == '--range':
            nums = list(range(int(args[1]), int(args[2]) + 1))
        else:
            nums = [int(x) for x in args]
        states, withprior = {}, []
        for n in nums:
            st, c = report(n, probes)
            states[n] = st
            if c:
                withprior.append(n)
        if ts:
            terms(ts, probes, full=('--full-terms' in sys.argv))
        print('\n── 小结 ──')
        print('  查 %d 条｜**HIT %d**（其中有非报告类文件者 %d 条：%s）｜**EMPTY %d**'
              % (len(nums), sum(1 for v in states.values() if v == 'HIT'),
                 len(withprior), withprior,
                 sum(1 for v in states.values() if v == 'EMPTY')))
        print('  ⛔ EMPTY ≠ 无旧账｜⛔ HIT 之后必须去读原册并**查其版本与撤回状态**；'
              '⛔ 本工具不裁决。')
    except SearchFailed as e:
        print('\n⛔⛔ **FAILED —— 检索本身失败，⛔ 本次输出【不可】当作「没有旧账」**：\n  %s' % e,
              file=sys.stderr)
        return 3
    return 0


if __name__ == '__main__':
    sys.exit(main())
