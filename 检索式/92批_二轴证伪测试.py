#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""92批·二轴结构之证伪测试（上级出题，本方执行）

题：若二轴成立，则①②③型（否决/改序/降强度）实例应皆伴随「治法冲突」之明文；
    若有一例不含冲突理由，二轴即倒。
测试面：`不可攻之` 全库 58 处，按前文去重 53 条。
⛔ 机械分桶只作筛，判定须逐条人读（闸门9 第九款）。本脚本不下结论。

结果（92批）：A 两位冲突 22｜B 同位阈值 20｜C 兼有 7｜D 皆无 4
  → B+D = 24/53 = 45% 与第二病位无关 → R88 二轴之【范围】被证伪，结构不倒但须收窄。
  ⚠ 已知筛法之漏：「心下硬」未被 TWO 命中（TWO 用「心下硬满」），故 D 桶含 1 条实属 A/C。
"""
import os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
from corpus_guard import load_one, BOOKS

TWO = re.compile(r"呕多|柴胡|少阳|表未解|外未解|太阳|心下硬|心下痞硬|胃气极虚|胃虚")
THR = re.compile(r"初头硬|后必溏|后必薄|后必滑|无燥屎|不转矢气|未定成硬|里还未实|不实|微满|虚烦|栀子豉汤")

def main():
    T = {b: load_one(b) for b, _ in BOOKS}
    seen, out = set(), []
    for b in T:
        for m in re.finditer("不可攻之", T[b]):
            pre, post = T[b][max(0, m.start()-150):m.start()], T[b][m.end():m.end()+150]
            k = re.sub(r"[^一-鿿]", "", pre[-26:])
            if k in seen:
                continue
            seen.add(k)
            out.append((b, m.start(), pre + post))
    buckets = {"A 两位冲突": [], "B 同位阈值": [], "C 兼有": [], "D 皆无(须人读)": []}
    for r in out:
        two, thr = bool(TWO.search(r[2])), bool(THR.search(r[2]))
        buckets[("C 兼有" if thr else "A 两位冲突") if two
                else ("B 同位阈值" if thr else "D 皆无(须人读)")].append(r)
    print("「不可攻之」去重 %d 条" % len(out))
    for k, v in buckets.items():
        print("  %-16s %2d (%.0f%%)" % (k, len(v), 100 * len(v) / len(out)))
    print("\n--- D 桶全文（须人读判定）---")
    for b, p, s in buckets["D 皆无(须人读)"]:
        print("〔%s·%d〕%s\n" % (b, p, s))

if __name__ == "__main__":
    main()
