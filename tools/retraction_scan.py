#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""撤回传播定位器（126AA 立·上级令）

⛔⛔ 本工具**只做定位（召回）**，⛔ **不做裁决**。

上级 126AA 裁决原文：
    「二字串反查只作辅助召回。会漏掉改写，也会误报历史引用，
      ⛔ 不能据此宣布传播已清。」

因此本工具：
  · 命中 ⇒ 输出【候选位置】，交人读裁决（合格／违规）；
  · 零命中 ⇒ ⛔ **不输出「已清」字样**，只输出「本字串无命中」，
    并**同时打印已知盲区清单**，提醒改写型残留不会被命中。

数据来源：`rules/report_index_v0.json` :: R-02 :: retractions
  ⇒ ⛔ 不另建结论库（上级令：避免再复制一套互相竞争的结论库）。
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(ROOT, 'rules', 'report_index_v0.json')

# 扫描范围：一切可能被当作【现行结论】引用之处
SCAN_DIRS = ['evidence', 'reports', 'rules', 'docs', '.claude']
SCAN_EXT = ('.md', '.json', '.txt')

# ⛔ 撤回登记自身与历史批次报告：命中属【历史记录】，正常，单独分档
HISTORICAL = re.compile(r'(reports/报告_第\w+批\.md|rules/report_index_v0\.json)$')


def load_retractions():
    d = json.load(open(INDEX, encoding='utf-8'))
    for c in d['chapters']:
        for e in c['entries']:
            if e['id'] == 'R-02':
                r = e.get('retractions')
                if not r:
                    sys.exit('⛔ R-02 无 retractions 数组 —— 登记未结构化，停。')
                return r
    sys.exit('⛔ 索引中无 R-02 条目，停。')


def iter_files():
    for d in SCAN_DIRS:
        base = os.path.join(ROOT, d)
        if not os.path.isdir(base):
            continue
        for dp, _, fns in os.walk(base):
            for fn in fns:
                if fn.endswith(SCAN_EXT):
                    yield os.path.join(dp, fn)


def main():
    rets = load_retractions()
    files = list(iter_files())
    # 一次读盘，多字串匹配
    texts = {}
    for f in files:
        try:
            texts[f] = open(f, encoding='utf-8').read()
        except Exception:
            pass

    n_live = n_hist = n_zero = 0
    print('撤回传播定位 ｜ 登记 %d 项 ｜ 扫描 %d 文件' % (len(rets), len(texts)))
    print('⛔ 本工具只定位，不裁决。零命中⛔不代表传播已清。')
    print('=' * 72)

    for r in rets:
        live, hist = [], []
        for probe in r.get('probes', []):
            for f, t in texts.items():
                start = 0
                while True:
                    j = t.find(probe, start)
                    if j < 0:
                        break
                    line = t.count('\n', 0, j) + 1
                    rel = os.path.relpath(f, ROOT)
                    rec = (rel, line, probe, t[max(0, j - 40):j + 60].replace('\n', ' '))
                    (hist if HISTORICAL.search(rel) else live).append(rec)
                    start = j + 1
        if not live and not hist:
            n_zero += 1
            print('%-8s %-6s 本字串无命中　⚠ ⛔ 不等于传播已清（改写不命中）' % (r['rid'], r['batch']))
            continue
        n_live += len(live)
        n_hist += len(hist)
        print('%-8s %-6s 候选 %d（现行位置 %d ｜历史记录 %d）　%s'
              % (r['rid'], r['batch'], len(live) + len(hist), len(live), len(hist), r['text'][:46]))
        for rel, line, probe, ctx in live:
            print('    ⚠ 须裁决  %s:%d  [%s]' % (rel, line, probe))
            print('              …%s…' % ctx)
        if hist:
            print('    · 历史记录 %d 处（撤回登记／历批报告，命中属正常）' % len(hist))

    print('=' * 72)
    print('合计：现行位置候选 %d ｜历史记录 %d ｜零命中字串组 %d' % (n_live, n_hist, n_zero))
    print()
    print('⛔⛔ 已知盲区（本工具查不出，必须人读）：')
    print('  ① **改写型残留**——同一判断换了措辞，字串反查必漏。')
    print('  ② **蕴涵型残留**——某结论不复述被撤句，但其推理以它为前提。')
    print('  ③ **口头型残留**——只出现在对话回复里、未写进仓库者，本工具完全看不见。')
    print('     ⭐ 126AA 实例：RET-13／RET-15 在仓库资产内零命中，')
    print('        而它们确曾作为结论发出 ⇒ ⛔ 零命中恰恰不等于没发生。')
    print('  ④ **分母未建**——probes 之覆盖率未经枚举 ⇒ ⛔ 不得报比率。')
    print()
    print('⇒ 机器反查负责【定位】，语义复核负责【裁决】。（上级 126AA 裁决）')
    return 0


if __name__ == '__main__':
    sys.exit(main())
