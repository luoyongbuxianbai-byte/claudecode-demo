#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v8_p0scan.py —— V8 基线冻结·P0-A～P0-E 静态冲突扫描（114批·上级令）

⛔ 本器只扫不改。上级令：本批只允许冻结、盘点、映射、静态冲突扫描、状态定义、迁移设计。
"""
import os, re, sys
from collections import OrderedDict
B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V8 = os.path.join(B, "V8", "hxs_engine_v8_full.md")

# 九文件边界
def segs(L):
    ids = [(i, L[i]) for i in range(len(L)) if re.match(r"^# \d\d_", L[i])]
    out = []
    for k, (i, h) in enumerate(ids):
        j = ids[k+1][0] if k+1 < len(ids) else len(L)
        out.append((h.strip("# ").split("｜")[0].strip(), i+1, j))
    return out

P0 = OrderedDict([
 ("P0-A 12格/阴阳函数化", [r"12\s*格", r"阴阳\s*[＝=]\s*f\(寒热\)", r"位×寒热×虚实",
                    r"阳热实", r"阴寒虚", r"热而虚", r"寒而实", r"不热不实", r"不寒不虚"]),
 ("P0-B 虚实污染阴阳", [r"正气盛热实\s*[＝=]\s*阳", r"正气虚寒\s*[＝=]\s*阴",
                  r"虚\s*[＝=]\s*阴", r"实\s*[＝=]\s*阳", r"正气盛[^。]{0,6}阳",
                  r"正气虚[^。]{0,6}阴"]),
 ("P0-C 缺省→阴性", [r"未提及\s*[＝=]\s*阴性", r"阴性推定", r"未写即视为无",
                r"未载\s*[＝=]\s*", r"回顾模式[^。]{0,20}阴性"]),
 ("P0-D 幸存≠成立", [r"幸存", r"全部预设存活", r"预设为活候选", r"未被排除"]),
 ("P0-E 六格与经内状态混层", [r"太阳\s*[＝=]\s*表阳热实", r"六经\s*[＝=]\s*.{0,8}格",
                     r"第七经", r"表阳→太阳", r"六经内部"]),
])

def main():
    L = open(V8, encoding="utf-8").read().split("\n")
    S = segs(L)
    print("== V8 基线：%d 行｜%d 个文件段 ==\n" % (len(L), len(S)))
    for name, a, b in S:
        print("  %-22s L%-6d–L%-6d  %6d 行" % (name, a, b, b-a))
    def whichfile(ln):
        for name, a, b in S:
            if a <= ln < b: return name
        return "?"
    print("\n" + "="*72)
    for k, pats in P0.items():
        print("\n### %s" % k)
        tot = 0
        for p in pats:
            hits = [(i+1, L[i].strip()) for i in range(len(L)) if re.search(p, L[i])]
            if not hits: continue
            tot += len(hits)
            print("  「%s」%d 处" % (p, len(hits)))
            for ln, tx in hits[:4]:
                print("     L%-6d [%s] %s" % (ln, whichfile(ln)[:14], tx[:72]))
                # ⛔114批 自查之误检：L429/430「虚=阴」「实=阳」被计为冲突，
                #   而其前文为「所以不能建立：」、后文为「这样的硬等式。」——V8 是在**否定**它。
                #   假阳性率 67%。故本器必须同时打印上下各一行，供人读裁决。
                #   ⚠ 上下文只是**减少**误检，不消除；机械命中数**永不得**直接充作冲突数。
                print("        ↑前 %s" % L[ln-2].strip()[:64] if ln >= 2 else "")
                print("        ↓后 %s" % L[ln].strip()[:64] if ln < len(L) else "")
            if len(hits) > 4: print("     …另 %d 处" % (len(hits)-4))
        if not tot: print("  ✅ 零命中")
        else: print("  ⇒ 本类合计 %d 处，须逐条裁" % tot)
    return 0

if __name__ == "__main__":
    sys.exit(main())
