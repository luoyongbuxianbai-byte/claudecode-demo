#!/usr/bin/env python3
"""【位→方·留一法】——瓶颈之定位实验（67批·上级批准为唯一主任务，并加两项设计要求）。

## 背景（66批 R62 之结论）
  症状组→病位 **37.8%／66.5%**（基线 8.1%／19.6%）＝**有信息量**；
  症状→方 **3.0%** ＝ 无信息量。→ **瓶颈锁定在「位→方」。本工具直接测这一步。**

## ⭐上级67批之两项设计要求（本工具据此建，不可省）
  ① **双基线对照**（**不设此对照则结果无法归因**）：
     **A：归位判断 → 方**｜**B：归位判断 ＋ 该案全部症状 → 方**
     · **A 低而 B 高** → 方之选择需要**归位之外的症状细节**，
       即「方证」确比「六经」细一层 → **此即胡老「方证是尖端」之工程含义**。
     · **A 与 B 俱低** → **信息本身不足＝硬上限**，非串联误差。
  ② ⭐**基线按候选数算，不得用全库多数类充基线**：
     记录每个归位判断所对应之候选方数；**随机水平 ＝ 1/候选数**，逐案算后取平均。
     〔理由·上级原话〕「若某归位判断对应 20 个方，则 5% 就是随机水平；
       若对应 3 个方，33% 才是随机水平。」

## ⛔ 防作弊闸门（跑之前写死）
  ① **B 之症状文本须遮蔽判断词**，否则 B 是在读答案〔R62 同型〕。
  ② **按案留一**（本任务天然按案，无同案泄漏问题）。
  ③ 平局确定性排序 `key=(-score, text)`〔case_retrieve 先例〕。
  ④ ⭐**方名须先清洗**：正则曾把归位词卷入方名（「**太阳中风**桂枝加桂汤」）。
     → 逐条剥离前置归位词；剥不净者标 `[方名存疑]` 并**排除出分母**，不带病计分。

【已知失效模式】(视角㉕)
  · **OCR 变形使同方异名**（「桂枝加厚**桐**杏仁汤」＝厚朴；「龙骨牡**蚝**汤」＝牡蛎）
    → 归一表只能覆盖已见者，**必不全**；未归一者按不同方计，**使复现率偏低（保守方向）**。
    ⛔**偏保守可接受，偏乐观不可接受**——故不做模糊匹配。
  · N=74，逐标签格子极稀 → **只报总体，不报逐标签**〔R62 之教训〕。
⛔⛔【首跑失败·必读·67批实发】
  首跑得 A＝B＝1.5%，而「按候选数之随机水平」算作 20.0% —— **低于随机 13 倍**。
  **低于随机 13 倍不是发现，是工具坏了**，故未出报告，先诊断。
  [诊断]**74 个可用方名中，69 个不同；其中 66 个只出现一次（89%）。**
  → ⛔**留一法下，89% 的案其正确答案根本不在训练集里。本任务之天花板是 10.8%，不是 100%。**
  → ⛔**且「随机水平 20%」算错**：它假定正确答案在候选集内，而 89% 的案不在。
  ⭐**结论：上级67批之双基线设计要求，在本数据上无法执行——不是因为答案是「硬上限」，
    是因为样本太稀，任何对照都区分不出东西。** 本工具改为：
    ① **先报可达率与天花板**，② **复现率一律以可达案为分母另报**，
    ③ **加一档粗粒度（基方类）**，因方名过稀；**两档同报，不以粗粒度充成绩。**
【弃件条件】[方未采] 或 [方名存疑] 者排除并计数。
【口径】(视角㊱) 一条＝一案；`python3 tools/wei2fang_loo.py` 复跑。
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
# ⛔闸门④ 方名清洗：剥前置归位词／证字／数词
def clean_fang(f):
    if not f or f == "[方未采]": return None
    g = MASK.sub("", f)                       # 剥归位词
    g = re.sub(r"^[证属为与用方的，,、]+", "", g)
    m = re.search(r"([一-鿿]{2,14}(?:汤|散|丸))$", g)
    if not m or len(m.group(1)) < 3: return "[方名存疑]"
    return m.group(1)

cases, drop = [], Counter()
for r in rows:
    f = clean_fang(r.get("fang"))
    if f is None: drop["[方未采]"] += 1; continue
    if f == "[方名存疑]": drop["[方名存疑]"] += 1; continue
    labs = frozenset(l for _, l in r["pairs"])
    if not labs: drop["无归位判断"] += 1; continue
    sym = MASK.sub("", "".join(s for s, _ in r["pairs"]))   # ⛔闸门① B之症状须遮蔽
    cases.append(dict(fang=f, labs=labs, sym=sym))
N = len(cases)
print("═══ 【位→方·留一法】═══")
print("可用案 **%d**（弃：%s）｜不同方 **%d**" % (N, dict(drop), len(set(c["fang"] for c in cases))))

fc = Counter(c["fang"] for c in cases)
gmaj = 100 * fc.most_common(1)[0][1] / N
print("\n[基线]")
print("  ⛔**全库多数类基线 %.1f%%（「%s」）——上级67批明令：此基线不适用，仅列作对照**"
      % (gmaj, fc.most_common(1)[0][0]))

def bg(t): return {t[i:i+2] for i in range(len(t)-1)}
def jac(a, b): u = len(a | b); return len(a & b) / u if u else 0.0

# ⭐可达性：方在训练集（其余案）中出现过者方为「可达」
fc_all = Counter(c["fang"] for c in cases)
for c in cases: c["reach"] = fc_all[c["fang"]] >= 2
# ⭐粗粒度：基方类＝方名之最长已知基方前缀
BASE = ["桂枝", "麻黄", "柴胡", "承气", "泻心", "四逆", "理中", "白虎", "苓桂", "五苓",
        "半夏", "黄芩", "建中", "十枣", "陷胸", "栀子", "当归", "薏苡", "甘草", "附子"]
for c in cases:
    c["base"] = next((b for b in BASE if b in c["fang"]), "[未归类]")
bc_all = Counter(c["base"] for c in cases)
for c in cases: c["breach"] = bc_all[c["base"]] >= 2 and c["base"] != "[未归类]"
R = [c for c in cases if c["reach"]]; RB = [c for c in cases if c["breach"]]
print("\n═══ ⭐可达性（**首跑失败之根因·必先读**）═══")
print("  不同方 **%d**／可用案 %d ｜ **只出现一次者 %d ＝ %.0f%%**"
      % (len(fc_all), N, sum(1 for v in fc_all.values() if v == 1), 100*sum(1 for v in fc_all.values() if v==1)/len(fc_all)))
print("  ⛔**精确方名之天花板 ＝ %d／%d ＝ %.1f%%**（留一法下正确答案在训练集中者）" % (len(R), N, 100*len(R)/N))
print("  ⭐**基方类之天花板 ＝ %d／%d ＝ %.1f%%**（粗粒度·%d 个基方类）" % (len(RB), N, 100*len(RB)/N, len(bc_all)))

def evaluate(field, key):
    hA = hB = 0
    for i, q in enumerate(cases):
        tr = [c for j, c in enumerate(cases) if j != i]
        sa = sorted(((jac(q["labs"], c["labs"]), c[key]) for c in tr), key=lambda x: (-x[0], x[1]))
        if sa and sa[0][1] == q[key]: hA += 1
        qb = bg(q["sym"])
        sb = sorted(((jac(q["labs"], c["labs"]) + jac(qb, bg(c["sym"])), c[key]) for c in tr),
                    key=lambda x: (-x[0], x[1]))
        if sb and sb[0][1] == q[key]: hB += 1
    return hA, hB

print("\n═══ ⭐结果（**两档同报·分母两算**）═══")
for key, lab, sub in [("fang", "精确方名", R), ("base", "基方类（粗粒度）", RB)]:
    hA, hB = evaluate("sym", key)
    ceil = 100*len(sub)/N
    print("\n  ── %s ──（天花板 %.1f%%）" % (lab, ceil))
    print("    A 归位→方　　　　：全体 %d／%d ＝ %.1f%% ｜ **可达案 %.1f%%**"
          % (hA, N, 100*hA/N, 100*hA/max(1,len(sub))))
    print("    B 归位＋症状→方　：全体 %d／%d ＝ %.1f%% ｜ **可达案 %.1f%%**"
          % (hB, N, 100*hB/N, 100*hB/max(1,len(sub))))
    if key == "fang": a, b, nR = 100*hA/max(1,len(sub)), 100*hB/max(1,len(sub)), len(sub)

print("\n═══ ⭐上级67批之归因判据·**本批不下裁决** ═══")
print("  ⛔**A/B 对照在本数据上无法归因**：精确方名之可达案仅 **%d 例**，"
      "\n     任何 A 与 B 之差异在 N=%d 上都不显著。" % (nR, nR))
print("  ⛔**故不得据本批下「硬上限」之判**——首跑那个判据是工具错误之产物，**撤销。**")
print("  ⭐**须补之数据**：本任务要求「同一方在语料中多次出现」。"
      "\n     104 案给不出；**558 案医案库（可达率 66.8%）才是本任务之正确语料**，"
      "\n     但其**缺归位判断标注**。→ **下批之真任务：为 558 案补归位标注，或以基方类降低稀疏度。**")
# ⛔自检〔㊹〕
assert clean_fang("太阳中风桂枝加桂汤") == "桂枝加桂汤", "⛔自检失败：归位词未剥净"
assert clean_fang("[方未采]") is None and clean_fang("汤") == "[方名存疑]", "⛔自检失败：弃件判定"
assert MASK.sub("", "脉缓恶风汗出太阳中风") == "脉缓恶风汗出", "⛔自检失败：B之症状未遮蔽"
assert 100*len(R)/N < 50, "⛔自检失败：天花板异常高，可达性计算可疑"
print("\n[自检] 方名剥净｜弃件判定正确｜B症状确已遮蔽 → 有分辨力")
json.dump(dict(n=N, A=a, B=b, nReach=nR, ceiling=100*len(R)/N),
          open(os.path.join(B, "case_layer", "_wei2fang.json"), "w"), ensure_ascii=False, indent=1)
