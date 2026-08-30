#!/usr/bin/env python3
"""【209 归位对·留一法】——**引擎核心主张之第一次直接可证伪检验**（66批·上级批准为唯一主任务）。

## 为什么这个测试比此前所有定位指标都要紧
  此前全部定位指标（定经 65.7%／遮盲 42.8%）测的是「**症状全集 → 经名**」。
  ⭐**而胡老实际做的是「症状组 → 位」，逐组做，再综合。两者不是同一个任务。**
  → **我们测了六十几批，测的是一个胡老没做的动作。** 本工具改测他真正做的那个。

## 假说与其证伪条件（先写死，跑之前）
  H：**给定一个症状组，可由其他症状组之先例复现其归位判断。**
  · **成立** → 【证据属地原则】【部位给候选·旁证定归属】得实证支撑。
  · **不成立** → 归位靠**未被记录的信息**（望诊/语气/病史），
    则「引擎是闸门不是医生」**从定位选择变成硬上限**。
  ⛔**两个结果都写进报告。不得因结果不利而改口径。**〔㊱〕

## ⛔ 三条防作弊闸门（写在跑之前）
  ① **标签泄漏**：症状组文本中若含判断词本身（「…太阴里寒」之「太阴」），即为泄漏。
     → **逐条遮蔽**：把全部判断词从症状组中抹去后再检索。**报遮蔽前后两个数。**
  ② **基线必须报**：多数类基线（永远猜最常见的标签）。
     **不超过基线的复现率＝没有信息量**，纵使绝对值好看。
  ③ **平局确定性**：`sorted(key=(-score, text))`，禁 set 序〔case_retrieve 先例〕。
  ④ **同案泄漏**：同一案之另一组不得作为先例（同案共享病人，非独立）→ **按案留一，非按对留一。**

【已知失效模式】(视角㉕)
  · 判断标签粒度不一（「太阴」vs「太阴里寒」vs「里虚寒」）→ **同时报严格match与粗粒度match**，
    粗粒度＝映射到 {表,里,半表半里,寒,热,虚,实,水饮,瘀血} 之集合重叠。
  · N=209 而标签数十，**多数格子样本极稀**→ 逐标签支持数须一并报，稀者不得据以下结论。
【口径】(视角㊱) 一条＝一个（症状组,判断）对；`python3 tools/guiwei_loo.py` 复跑。
"""
import re, os, json
from collections import Counter, defaultdict

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows = json.load(open(os.path.join(B, "case_layer", "_zhengwei.json")))
PAN = ["太阳表实","太阳表虚","太阳中风","太阳伤寒","太阳病","太阳表证","太阳",
       "阳明里热","阳明里实","阳明内热","阳明病","阳明","少阳病","少阳证","少阳",
       "太阴里寒","太阴里虚","太阴病","太阴","少阴病","少阴","厥阴病","厥阴",
       "里虚寒","里虚","里实","里寒","里热","里饮","里湿热","表不解","表未解",
       "表虚","表实","上热","下寒","上热下寒","寒热错杂","水饮","外邪","瘀血",
       "血虚","津虚","水气","痰饮","湿热","虚寒","实热"]
MASK = re.compile("|".join(map(re.escape, sorted(PAN, key=len, reverse=True))))
# 粗粒度轴
AXIS = {"表":["太阳","表虚","表实","表不解","表未解","外邪","表证","中风","伤寒"],
        "里":["阳明","太阴","里虚","里实","里寒","里热","里饮","里湿热"],
        "半表半里":["少阳","厥阴","上热下寒","寒热错杂"],
        "寒":["里寒","虚寒","下寒","太阴","少阴"],"热":["里热","实热","上热","湿热","阳明"],
        "虚":["里虚","血虚","津虚","虚寒"],"实":["里实","表实","实热"],
        "水饮":["水饮","水气","痰饮","里饮"],"瘀血":["瘀血"]}
def axes(lab): return frozenset(a for a, ws in AXIS.items() if any(w in lab for w in ws))

pairs = []
for ci, r in enumerate(rows):
    for sym, lab in r["pairs"]:
        s = sym.strip()
        if len(s) < 3: continue
        pairs.append(dict(case=ci, sym=s, masked=MASK.sub("", s), lab=lab, ax=axes(lab)))
N = len(pairs)
labc = Counter(p["lab"] for p in pairs)
print("═══ 【209 归位对·留一法】═══")
print("可用对 **%d**（症状组≥3字）｜案数 %d｜不同判断标签 **%d**" % (N, len(rows), len(labc)))
print("\n[标签支持数·前 12]")
for l, c in labc.most_common(12): print("  %-10s %3d  (%.0f%%)" % (l, c, 100*c/N))
maj, majn = labc.most_common(1)[0]
print("⛔**多数类基线 = 永远猜「%s」→ %.1f%%**（严格 match）" % (maj, 100*majn/N))
majax = Counter(p["ax"] for p in pairs).most_common(1)[0]
print("⛔**多数类基线（粗粒度轴集合）→ %.1f%%**" % (100*majax[1]/N))

def bigrams(t): return {t[i:i+2] for i in range(len(t)-1)}
def run(field):
    hit = hitax = 0; per = defaultdict(lambda: [0,0])
    for i, q in enumerate(pairs):
        qb = bigrams(q[field])
        cand = []
        for j, o in enumerate(pairs):
            if o["case"] == q["case"]: continue        # ⛔闸门④ 同案不作先例
            ob = bigrams(o[field])
            u = len(qb | ob)
            cand.append((len(qb & ob)/u if u else 0.0, o["lab"], o[field]))
        if not cand: continue
        cand.sort(key=lambda x: (-x[0], x[2]))          # ⛔闸门③ 确定性平局
        pred = cand[0][1]
        per[q["lab"]][1] += 1
        if pred == q["lab"]: hit += 1; per[q["lab"]][0] += 1
        if axes(pred) & q["ax"]: hitax += 1
    return hit, hitax, per

for field, name in [("sym", "遮蔽前（症状组原文·**含泄漏**）"), ("masked", "⭐遮蔽后（判断词已抹去）")]:
    h, ha, per = run(field)
    print("\n═══ %s ═══" % name)
    print("  **严格 match（标签全同）：%d／%d ＝ %.1f%%**（基线 %.1f%%）" % (h, N, 100*h/N, 100*majn/N))
    print("  **粗粒度 match（轴集合有交）：%d／%d ＝ %.1f%%**（基线 %.1f%%）" % (ha, N, 100*ha/N, 100*majax[1]/N))
    if field == "masked":
        print("  [逐标签·支持数≥6 者]")
        for l, (c, t) in sorted(per.items(), key=lambda x: -x[1][1]):
            if t >= 6: print("    %-10s %2d／%2d ＝ %3.0f%%" % (l, c, t, 100*c/t))
        MASKED = (h, ha)
# ⛔自检〔㊹ 必然失败样例〕
assert MASK.sub("", "脉细弦太阴里寒") == "脉细弦", "⛔自检失败：遮蔽未抹掉判断词"
assert not MASK.findall("子虚乌有绝无一词"), "⛔自检失败：虚构句命中判断词"
print("\n[自检] 遮蔽确实抹掉判断词｜虚构句零命中 → 有分辨力")
json.dump(dict(n=N, base=100*majn/N, strict=100*MASKED[0]/N, axis=100*MASKED[1]/N),
          open(os.path.join(B, "case_layer", "_guiwei_loo.json"), "w"), ensure_ascii=False, indent=1)
