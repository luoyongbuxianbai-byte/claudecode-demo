#!/usr/bin/env python3
"""【本位／标位】检验：加减之 Y 是否多属本位之外？(83批·用户模型之第一次可证伪检验)

## 用户模型（上级形式化·本工具所测者）
  · **本位**＝病邪集中反应之位＝胡老病位定义所指＝**六经名所标者**
  · **标位**＝其余有阳性反应之位，**客观存在、须处理，但非病邪所在**
  · **推论**：方证名只覆盖本位，**加减在补标位**；「故治A汤证**而Y者**」之 **Y，多为另一位之状态**。
  ⭐**若 Y 多属基方本位之外 → 用户模型得直接支持；若多与基方同位 → 不支持。**

## ⛔ 防自证闸门（跑之前写死）
  ① **两侧共用同一张「状态→病位」映射**，沿用 kuawei.py 之 W2P（原文派生）。
     **若基方侧与 Y 侧用不同标准，结论即是我方造的。**
  ② **基方之本位不由我方指派**，由其自身【辨证要点】经同一映射推出。
  ③ **须报随机配对基线**；不超基线即无信息量。
  ④ 报两个口径：宽（Y 有位不在基方位集内）／严（Y 与基方位全无交集）。
【弃件】基方本位未定 或 Y 位未定者，排除并计数。
【口径】(视角㊱) 一条＝一个三元组；`python3 tools/benwei_biaowei.py` 复跑。
"""
import re, os, json, random
from collections import Counter
B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
J = re.compile(r"·\d+·|PDFcreatedwith[A-Za-z]*|pdfFactory[A-Za-z]*|Protrialversion|"
               r"www\.pdffactory\.com|---第\d+页---|http\S{0,60}|快乐人生久久\S{0,40}")
C = J.sub("", re.sub(r"\s+", "", open(os.path.join(B, "sources", "C_jingfangliyu.txt"),
                                      encoding="utf-8", errors="ignore").read()))
W2P = {"表": ["表实","表虚","浮肿","身疼","无汗","汗出","恶风","恶寒","身痒","项背强","骨节疼","身重","脉浮"],
       "里": ["胃虚","里实","里寒","里热","大便难","大便硬","下利","呕逆","干呕","心下痞","腹满","腹痛",
              "小便不利","吐涎沫","纳差","便干","虚寒","急迫","烦热","身热","挛痛","不能食","溏泄"],
       "半表半里": ["胸胁苦满","口苦","咽干","目眩","胸满","往来寒热","心烦喜呕","胁下","默默"]}
assert all(len(w) >= 2 for v in W2P.values() for w in v), "⛔协议15：映射表出现单字"
RX = {k: re.compile("|".join(sorted(v, key=len, reverse=True))) for k, v in W2P.items()}
NEG = re.compile(r"(?:无|不|非|未)([一-鿿]{2,6})")
def locus(txt):
    bad = {m.group(1) for m in NEG.finditer(txt)}
    out = set()
    for k, rx in RX.items():
        for h in rx.findall(txt):
            if not any(h in b for b in bad): out.add(k)
    return out
NAME = re.compile(r"([一-鿿]{2,12}(?:汤|散|丸))(?:方)?【方剂组成】")
names = [(m.start(), m.group(1)) for m in NAME.finditer(C)]
def fn(p):
    b = None
    for s, n in names:
        if s < p: b = n
        else: break
    return b
base_locus = {}
for m in re.finditer(r"【辨证要点】(.{2,120}?)(?=【|《|$)", C):
    f = fn(m.start())
    if f and f not in base_locus:
        L = locus(m.group(1))
        if L: base_locus[f] = L
print("═══ 【本位／标位】检验 ═══")
print("基方本位可由其自身【辨证要点】推出者：**%d 方**（⛔不由我方指派）" % len(base_locus))
rows = json.load(open(os.path.join(B, "term_layer", "_gongnengwei.json")))["gnw"]
ok, drop = [], Counter()
for r in rows:
    bf = r["base"]
    if bf not in base_locus: drop["基方本位未定"] += 1; continue
    yl = locus(r["sym"])
    if not yl: drop["Y之位未定"] += 1; continue
    ok.append((bf, base_locus[bf], r["sym"], yl))
N = len(ok)
print("三元组 %d → 可判 **%d**（弃：%s）" % (len(rows), N, dict(drop)))
assert N > 0, "⛔N=0"
diff  = [x for x in ok if x[3] - x[1]]
alldf = [x for x in ok if not (x[3] & x[1])]
random.seed(7)
bls = [b for _, b, _, _ in ok]; yls = [y for _, _, _, y in ok]
rd = sum(1 for _ in range(6000) if random.choice(yls) - random.choice(bls)) / 6000
print("\n═══ ⭐结果 ═══")
print("  **宽口径（Y 有位不在基方位集内）：%d／%d ＝ %.1f%%**" % (len(diff), N, 100*len(diff)/N))
print("  **严口径（Y 与基方位全无交集）　：%d／%d ＝ %.1f%%**" % (len(alldf), N, 100*len(alldf)/N))
print("  ⛔**随机配对基线：%.1f%%**〔闸门③〕" % (100*rd))
r1 = len(diff)/N
print("\n  → **用户模型「加减在补标位」%s**" % (
    "⭐**得支持**（%.1f%% vs 基线 %.1f%%）" % (100*r1, 100*rd) if r1 > rd + 0.10 else
    "⚠**与基线接近（%.1f%% vs %.1f%%），本测无信息量**" % (100*r1, 100*rd)))
print("\n[异位实例·前 12]")
for bf, b_, sym, y_ in diff[:12]:
    print("  %-16s 本位[%s] ← Y「%s」位[%s]" % (bf, "／".join(sorted(b_)), sym[:20], "／".join(sorted(y_))))
assert locus("汗出恶风") == {"表"}, "⛔自检失败：表位映射错"
assert locus("心下痞硬") == {"里"}, "⛔自检失败：里位映射错"
assert not locus("子虚乌有"), "⛔自检失败：虚构句被定位"
assert locus("无里实证者") == set(), "⛔自检失败：否定语泄漏"
print("\n[自检] 表/里映射正确｜虚构句零命中｜否定语已剔")
json.dump(dict(N=N, wide=len(diff), strict=len(alldf), baseline=rd),
          open(os.path.join(B, "term_layer", "_benwei.json"), "w"), ensure_ascii=False, indent=1)
