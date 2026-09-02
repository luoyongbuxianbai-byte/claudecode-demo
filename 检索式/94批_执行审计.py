#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""94批·执行审计：引擎条款进入执行路径之比率（用户质问驱动）

口径（最宽）：执行路径 = 判案时实际会被读到的三文档
  hxs_engine_执行核.md ｜ hxs_engine_执行件.md ｜ 引擎头部 L1–191
「进入执行路径」= 该 R 条款号被三文档之任一【提到】。
⚠ 这是最宽口径——被提到即算，不要求真被用于判断。故实际使用率只会更低，不会更高。

用法：python3 检索式/94批_执行审计.py        # 闸门9 第十二款·每批开工第四检
"""
import os, re, sys

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def main():
    eng = open(os.path.join(B, "hxs_engine_v79_full.md"), encoding="utf-8").read()
    L = eng.split("\n")
    allR = sorted({int(m.group(1)) for m in re.finditer(r"^R(\d+)\s", eng, re.M)})
    docs = {
        "执行核": open(os.path.join(B, "hxs_engine_执行核.md"), encoding="utf-8").read(),
        "执行件": open(os.path.join(B, "hxs_engine_执行件.md"), encoding="utf-8").read(),
        "引擎头部": "\n".join(L[:191]),
    }
    print("引擎 %d 行｜R 条款 %d 条" % (len(L), len(allR)))
    un = set()
    for name, t in docs.items():
        ref = {r for r in (int(m.group(1)) for m in re.finditer(r"R(\d+)", t)) if r in allR}
        un |= ref
        print("  %-8s 引用 %2d/%d = %4.1f%%" % (name, len(ref), len(allR), 100 * len(ref) / len(allR)))
    print("  %-8s 引用 %2d/%d = %4.1f%%" % ("并集", len(un), len(allR), 100 * len(un) / len(allR)))
    never = [r for r in allR if r not in un]
    print("\n⛔ 从未进入任何执行路径 %d 条：%s" % (len(never), never))
    print("\n按批次切分：")
    for lo, hi, tag in [(1, 30, "㉚批前"), (31, 63, "31–63批"), (64, 999, "64批以后")]:
        rng = [r for r in allR if lo <= r <= hi]
        if not rng:
            continue
        hit = [r for r in rng if r in un]
        print("  R%-3d–R%-3d %-10s 共%2d条，入路径 %2d 条 = %3.0f%%"
              % (lo, min(hi, max(rng)), tag, len(rng), len(hit), 100 * len(hit) / len(rng)))
    print("\n附录引用：")
    for f in sorted({m.group(0) for m in re.finditer(r"附录[A-Z]", eng)}):
        w = [k for k, t in docs.items() if f in t]
        print("  %-6s 引擎内 %3d 次｜执行文档：%s" % (f, eng.count(f), "／".join(w) if w else "⛔无"))

if __name__ == "__main__":
    main()
