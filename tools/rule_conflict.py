#!/usr/bin/env python3
"""条款冲突静态扫描器（㉟批立·三次同型自相矛盾驱动）。

立此工具之由：引擎内已**三次**查获同一概念上的相反表述——
  ① PP-2「久病不愈」作瘀血判据 vs 公理A4被否定判据「病程久暂不得单独作判据」
  ② ㉜批我的统计结论 vs R24 自己写的「归属须原文明文」
  ③ A4.5 规则1/3「属性未满足→不命中→止方」 vs R5②/R6/R24③
三次的共同点：**新规则挂载时，没有工序去扫描它与哪些既有条款字面冲突。**
协议12 管的是「新规则与既有规则的**联合效果**」（跑对照），
**本工具管「新旧条款在同一概念上是否**字面相反**」（静态检查）——二者互补。

做法：把引擎切成条款块，对每个**受控概念**抽取该块的**极性**（禁/许），
同一概念上出现相反极性者列为冲突候选，**由人判**（很多是合法的分层，如
"未采不得充当反义" vs "属性不符→不命中" —— 前者说未知，后者说不符，不冲突）。

【已知失效模式】(视角㉕)
  ① **只查字面极性，不懂语义**。合法分层会被误报（如上例）——
     故输出一律称「冲突**候选**」，**不自动改任何条款**。
  ② 概念表是人工列的，漏概念即漏冲突。
  ③ 同一块内既禁又许（"禁X，但Y情形许"）会被记为块内自冲突，须人读。
  ④ **本工具只能发现字面冲突，发现不了"沉默冲突"**——
     新规则该覆盖旧条款却只字未提的情形，它查不出。这是已知的能力上界。
【弃件条件】块长 <40 字者跳过（多为标题行）。
【口径】(视角㊱) 一条＝一个(条款,概念,极性)三元组；`python3 tools/rule_conflict.py` 复跑。
"""
import re, os
from collections import defaultdict

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
E = open(os.path.join(B, "hxs_engine_v79_full.md"), encoding="utf-8").read().split("\n")

HEAD = re.compile(r"^(R\d+[a-z]?|公理A\d+(?:\.\d+)?|纲领[一二三四五六七]|协议\d+|"
                  r"W-\d+\.\d+|视角[㉓㉔㉕㉖㉗㉘㉙㉚㉛㉜㉝㉞㉟㊱])")

# ── 受控概念：每个给出识别词 ──
CONCEPT = {
 "止方/不出方":      r"止方|不出方|不得出方|禁止出方",
 "未采/未知之处置":  r"未采|未知|悬挂|未取证",
 "属性完整/合取":    r"属性完整|全部满足|悉具|全项命中|逐项合取",
 "排除之依据":       r"排除唯一依据|反义|否决证|E否决|闭合排除",
 "病名之用":         r"病名|西医病名|现代病名",
 "六经之位置":       r"六经.{0,8}(入口|闸门|优先|派生|末端|第一步)",
 "统计/共现之用":    r"共现|词频|统计.{0,4}(结论|依据|排序)",
 "同义合并":         r"同义词|异写|归并|合并语义",
 "脏腑经络":         r"脏腑|经络",
 "个体反应vs体系禁忌": r"医源|既往药物|个体安全约束|体系禁忌",
}
BAN = r"禁止|不得|禁|不可|一律不|永不|作废|撤回|不许"
ALLOW = r"允许|须|必须|应当|即可|方可|得以|照常成立|仍入候选|仍须"

# ── 切块 ──
blocks, cur, buf = [], None, []
for l in E:
    m = HEAD.match(l)
    if m:
        if cur and len("".join(buf)) >= 40: blocks.append((cur, "\n".join(buf)))
        cur, buf = m.group(1), [l]
    elif cur:
        buf.append(l)
if cur and len("".join(buf)) >= 40: blocks.append((cur, "\n".join(buf)))

# ── 抽 (条款,概念,极性) ──
tri = defaultdict(lambda: defaultdict(list))
for rid, body in blocks:
    for cname, crx in CONCEPT.items():
        for line in body.split("\n"):
            if not re.search(crx, line): continue
            pol = None
            if re.search(BAN, line): pol = "禁"
            if re.search(ALLOW, line): pol = "许" if pol is None else "禁∧许(同句)"
            if pol: tri[cname][pol].append((rid, line.strip()[:96]))

L = ["# 条款冲突静态扫描（㉟批）", "",
     "> 生成：`tools/rule_conflict.py`（文件头含【已知失效模式】与能力上界）。", "",
     "> **本工具只查字面极性，不懂语义。** 合法分层（如「未采不得充当反义」vs",
     "> 「属性不符→不命中」——前者说*未知*，后者说*不符*）会被误报。",
     "> 故一律称「冲突**候选**」，**不自动改任何条款**。", "",
     "> ⚠**已知能力上界**：查得出**字面冲突**，查不出**沉默冲突**",
     "> ——新规则该覆盖旧条款却只字未提的情形，本工具无能为力。", ""]
n_cand = 0
for cname in CONCEPT:
    d = tri[cname]
    if not d: continue
    pols = [p for p in d if p != "禁∧许(同句)"]
    flag = len(set(pols)) > 1
    if flag: n_cand += 1
    L += ["## 概念【%s】%s" % (cname, " ⚠**冲突候选**" if flag else ""), ""]
    for p, items in sorted(d.items()):
        L.append("**%s**（%d 处）：" % (p, len(items)))
        seen = set()
        for rid, line in items:
            if rid in seen: continue
            seen.add(rid)
            L.append("- `%s` %s" % (rid, line.replace("|", "／")))
        L.append("")
L += ["---", "", "**冲突候选概念数：%d／%d。**" % (n_cand, len([c for c in CONCEPT if tri[c]])),
      "", "> 下一步由人逐条判：是**真冲突**（须订正），",
      "> 还是**合法分层**（须在两条条款里互相点名，写明分工）。"]
open(os.path.join(B, "term_layer", "条款冲突扫描.md"), "w", encoding="utf-8").write("\n".join(L))

print("条款块 %d 个｜受控概念 %d 个" % (len(blocks), len(CONCEPT)))
for cname in CONCEPT:
    d = tri[cname]
    if not d: continue
    pols = [p for p in d if p != "禁∧许(同句)"]
    mark = "⚠冲突候选" if len(set(pols)) > 1 else ""
    print("  %-22s %s %s" % (cname, "／".join("%s%d" % (p, len(v)) for p, v in sorted(d.items())), mark))
