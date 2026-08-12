#!/usr/bin/env python3
"""三路对照（㉖批·裁决六）：模板匹配 vs 坐标求值 vs 案例检索。

同一批 95 例、同一方库、同一金标准（胡老在同一段话里自己开出的方），
**只改覆盖判据**，其余全同。

【已知失效模式】(视角㉕)
  ① 方侧坐标由★(症状语言)切出，稀疏且噪声大——**这是当前命中率的瓶颈，非判据之过**。
  ② 案例检索一路的数来自 tools/case_index.py 的留一法(不同语料)，
     **与前两路不同源**，只可作量级参照，不可直接相减。
  ③ "落空"＝该路径产生不出任何候选。这是本表最有判别力的一栏（视角㉚：
     区分"答错"与"没答"）。
【弃件条件】用方未解析者不计入 N。
【口径】(视角㊱) 一例＝一条胡老自书判断句 ∧ 用方可解析；命中＝候选方名与金标准方名集合有交。
【复跑】python3 tools/three_path_compare.py
"""
import re, json, os
from collections import Counter
B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = open(os.path.join(B, "tools", "fang_signature.py"), encoding="utf-8").read().split("# ── 4.")[0]
exec(src.replace('os.path.dirname(os.path.abspath(__file__)), ".."', 'os.environ["HXS_B"], "."'))
raw = json.load(open(os.path.join(OUT, "_raw.json")))
cases = [r for r in raw["recs"] if r["fang"] != "(未解析)"]
def norm(f): return set(x for x in re.split(r"合|与", re.sub(r"(加减|加味)$", "", f)) if x)
def jac(a, b): return len(a & b) / len(a | b) if (a or b) else 0.
lib = {k: v for k, v in final.items() if v}
print("三路对照（N=%d，金标准=胡老实际用方）\n" % len(cases))
for mode in ["模板匹配(严格子集·现引擎)", "坐标求值(Jaccard排序·缺项不否决)", "坐标求值(覆盖率排序)"]:
    c = Counter()
    for r in cases:
        cs = sig(r["text"]); g = norm(r["fang"])
        if not cs: c["无坐标"] += 1; continue
        if mode.startswith("模板"):
            cand = sorted([n for n in lib if cs <= lib[n]], key=lambda n: len(lib[n]))
        elif "Jaccard" in mode:
            cand = sorted(lib, key=lambda n: -jac(cs, lib[n]))
        else:
            cand = sorted(lib, key=lambda n: (-len(cs & lib[n]) / len(cs), len(lib[n])))
        if not cand: c["落空"] += 1; continue
        c["CS" if g & norm(cand[0]) else "PC" if any(g & norm(x) for x in cand[:3]) else "MISS"] += 1
    N = len(cases)
    print("%-34s CS %4.1f%% | PC内 %4.1f%% | 未命中 %4.1f%% | **落空(止方) %4.1f%%**" % (
        mode, 100*c["CS"]/N, 100*(c["CS"]+c["PC"])/N, 100*c["MISS"]/N, 100*c["落空"]/N))
print("%-34s CS 20.0%% | PC内 31.7%% | 未命中 68.3%% | 落空 0.0%%  (㉕批·留一法·N=60·异源)" % "案例检索(参照)")
