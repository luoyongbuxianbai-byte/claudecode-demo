#!/usr/bin/env python3
"""【按状态数分层·定方率重测】(68批·用户指出·上级列为本批优先任务)。

## 假说（用户提出·先写死再测）
  用户：「**吐大量清涎沫、苔白 → 甘草干姜汤**，第一时间胡希恕就会想到。」
  → **此步不需检索先例，是直接对应。** 故定方机制按状态数分三档，**不可混测**：
    ① **1–2 状态**（二味方/基础方）→ 直接对应，**预期高**
    ② **3–4 状态** → 基方＋加味（附录H）
    ③ **≥5 状态** → 合方＋多加味，**先例不重复，即 67 批 95% 之来源**
  **若①档显著高 → 3% 系「任务分布问题」而非能力问题。**

⛔【本工具可能推翻该假说·这是它存在的理由】
  **若①档并不高于③档，则假说证伪。先测再说，不预设结论。**

⛔【跑之前必须先报的一件事·否则本测无意义】
  **各档 N 是多少？** 67 批已知 68 可用案、平均 2.0 状态/案 ——
  **极可能绝大多数案落在①档，则「分档」实为「不分」。**
  → **本工具第一步就是打印分布；任一档 N<10 者，一律不下结论，只报 N。**

【已知失效模式】(视角㉕)
  ① **状态数＝归位判断标签数**，而标签由抽取工具所得，**抽漏即状态数偏低**〔R41⑪〕
     → 故本表之「状态数」是**下界**，非真值。**须标。**
  ② **①档若同时也是「方最常见」的那档，其高复现可能来自基线而非直接对应**
     → **逐档各报其档内多数类基线**，不与总基线比〔67批教训〕。
  ③ 分档后 N 骤减，**逐档天花板须各报**〔67批：不报天花板则数字无法解读〕。
【口径】(视角㊱) 一案一条；`python3 tools/fenceng_dingfang.py` 复跑。
"""
import re, os, json
from collections import Counter

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows = json.load(open(os.path.join(B, "case_layer", "_zhengwei.json")))
PAN = ["太阳表实","太阳表虚","太阳中风","太阳伤寒","太阳病","太阳表证","太阳",
       "阳明里热","阳明里实","阳明内热","阳明病","阳明","少阳病","少阳证","少阳",
       "太阴里寒","太阴里虚","太阴病","太阴","少阴病","少阴","厥阴病","厥阴",
       "里虚寒","里虚","里实","里寒","里热","里饮","里湿热","表不解","表未解",
       "表虚","表实","上热","下寒","上热下寒","寒热错杂","水饮","外邪","瘀血",
       "血虚","津虚","水气","痰饮","湿热","虚寒","实热"]
MASK = re.compile("|".join(map(re.escape, sorted(PAN, key=len, reverse=True))))
BASE = ["桂枝","麻黄","柴胡","承气","泻心","四逆","理中","白虎","苓桂","五苓",
        "半夏","黄芩","建中","十枣","陷胸","栀子","当归","薏苡","甘草","附子"]
def clean(f):
    if not f or f == "[方未采]": return None
    g = re.sub(r"^[证属为与用方的，,、]+", "", MASK.sub("", f))
    m = re.search(r"([一-鿿]{2,14}(?:汤|散|丸))$", g)
    return m.group(1) if m and len(m.group(1)) >= 3 else None

cases = []
for r in rows:
    f = clean(r.get("fang"))
    labs = frozenset(l for _, l in r["pairs"])
    if not f or not labs: continue
    cases.append(dict(fang=f, labs=labs, n=len(labs),
                      base=next((b for b in BASE if b in f), "[未归类]"),
                      sym=MASK.sub("", "".join(s for s, _ in r["pairs"]))))
print("═══ 【按状态数分层·定方率】═══")
print("可用案 **%d**" % len(cases))
dist = Counter(c["n"] for c in cases)
print("\n⛔[**第一步：分布·若某档 N<10 则该档不下结论**]")
print("  状态数分布：%s" % dict(sorted(dist.items())))
def band(n): return "①1–2状态" if n <= 2 else "②3–4状态" if n <= 4 else "③≥5状态"
bd = Counter(band(c["n"]) for c in cases)
for k in ("①1–2状态", "②3–4状态", "③≥5状态"):
    print("  **%s：N＝%d**%s" % (k, bd[k], "  ⛔**N<10，不下结论**" if bd[k] < 10 else ""))
print("\n⛔**状态数系抽取所得标签数，是下界非真值**〔失效模式①〕")

def bg(t): return {t[i:i+2] for i in range(len(t)-1)}
def jac(a, b): u = len(a | b); return len(a & b)/u if u else 0.0
print("\n═══ ⭐逐档结果（**各档天花板、各档基线，均档内算**）═══")
print("| 档 | N | 天花板 | 复现率(全体) | 复现率(可达) | 档内多数类基线 | 判定 |")
print("|---|---|---|---|---|---|---|")
for k in ("①1–2状态", "②3–4状态", "③≥5状态"):
    sub = [c for c in cases if band(c["n"]) == k]
    if not sub: continue
    bc = Counter(c["base"] for c in sub)
    reach = [c for c in sub if bc[c["base"]] >= 2 and c["base"] != "[未归类]"]
    ceil = 100*len(reach)/len(sub)
    hit = 0
    for i, q in enumerate(sub):
        tr = [c for j, c in enumerate(sub) if j != i]
        if not tr: continue
        qb = bg(q["sym"])
        s = sorted(((jac(q["labs"], c["labs"]) + jac(qb, bg(c["sym"])), c["base"]) for c in tr),
                   key=lambda x: (-x[0], x[1]))
        if s[0][1] == q["base"]: hit += 1
    rc = Counter(c["base"] for c in reach)
    basel = 100*rc.most_common(1)[0][1]/len(reach) if reach else 0
    acc_r = 100*hit/len(reach) if reach else 0
    verdict = ("⛔**N<10，不下结论**" if len(sub) < 10 else
               "✅**超档内基线**" if acc_r > basel else "⛔**未超档内基线**")
    print("| **%s** | %d | %.0f%% | %.1f%% | **%.1f%%** | %.1f%% | %s |"
          % (k, len(sub), ceil, 100*hit/len(sub), acc_r, basel, verdict))
# ⭐用户所举之例：直接对应之验证
print("\n═══ ⭐**用户所举之例·直接对应之独立验证**（不走留一法）═══")
for sym, exp in [("涎沫", "甘草干姜"), ("冒眩", "泽泻"), ("气上冲", "桂枝甘草")]:
    hits = [c for c in cases if sym in c["sym"]]
    print("  「%s」在 %d 案中出现｜其方：%s" % (sym, len(hits), "／".join(sorted({c["fang"] for c in hits})) or "—"))
assert MASK.sub("", "汗出恶风太阳中风") == "汗出恶风", "⛔自检失败：遮蔽无效"
print("\n[自检] 遮蔽有效")
