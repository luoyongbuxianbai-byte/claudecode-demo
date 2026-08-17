#!/usr/bin/env python3
"""【术语异写映射层】＋ 41token 按异写重算（㉜批·术语假象订正）。

事故（㉛批）：我报「便溏与太阴全库共现 0 次 ⇒ 便溏→太阴连共现都不成立」。
上级质疑后实测：**太阴 ±150字窗口内，便溏 1、而「自利」145、「下利」308。**
→ **胡老不用「便溏」这个现代病历词，他用「自利」「下利」。**
   零共现是**词汇假象，不是医学事实**。该结论已撤回（W-1.16）。

本层作用：**只作检索桥接，不合并语义**（R22 同义词纪律不变）。
每条异写须带 `依据` 栏：
  A＝原文明确建立等价（"X者，Y之谓也"一类）
  D＝派生词形（同词根不同写法，如 大便溏/便溏/溏）
  [待证]＝仅为检索便利而设，**无原文等价证明，不得用于语义合并或判据**

【已知失效模式】(视角㉕)
  ① 异写表是**人工列的**，必然不全——漏一个词就少一批命中。**新增须补表并重算。**
  ② 桥接后的合计数**不可直接与桥接前比较**（分母变了）。
  ③ 异写 ≠ 同义：「下利」含「自利」与「协热利」等，**外延不同**；
     合计只用于**证伪"零共现"**，**不得用于证成"该词属某经"**。
【弃件条件】异写候选在全库 0 命中者不入表。
【口径】(视角㊱) 一处＝一行内一次命中；`python3 tools/term_alias.py` 复跑。
"""
import re, os, json
from collections import Counter

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOKS = [("C卷", "C_jingfangliyu.txt"), ("讲伤寒", "ocr_未识别2.txt"), ("讲金匮", "ocr_未识别1.txt"),
         ("解读张仲景医学", "ocr_解读张仲景医学.txt"), ("经方传真", "ocr_经方传真系.txt"),
         ("病位类方解", "ocr_胡希恕病位类方解.txt")]
JUNK = re.compile(r"·\d+·|PDFcreatedwith[A-Za-z]*|pdfFactory[A-Za-z]*|Protrialversion|www\.pdffactory\.com")
JING = ["太阳", "阳明", "少阳", "太阴", "少阴", "厥阴"]

# ── 术语异写映射（现代病历用语 ↔ 胡老用语）──
# 依据：A=原文明确等价｜D=派生词形｜[待证]=仅检索桥接，无等价证明
ALIAS = {
 "便溏":   (["自利", "下利", "大便溏", "溏", "大便稀", "泄泻", "下利清谷"], "[待证·㉞批复核未过]全库搜「X就是Y」式等价句 0 命中。**只作检索桥接，永不得用于语义合并或判据**"),
 "便秘":   (["大便难", "不大便", "大便硬", "不更衣", "大便不通"], "A·§180胃家实系列用「大便难/不大便」"),
 "胃脘痛": (["心下痛", "心下急", "心中疼", "胃脘疼"], "[待证·㉞批复核未过]等价句 0 命中，只作检索桥接"),
 "失眠":   (["不得眠", "不得卧", "不能卧", "卧起不安", "烦不得眠"], "A·§76「虚烦不得眠」§303「心中烦不得卧」"),
 "怕冷":   (["恶寒", "畏寒", "背恶寒", "恶风"], "A·§1「恶寒」为提纲用语"),
 "怕热":   (["恶热", "不恶寒反恶热", "喜凉"], "A·§182「不恶寒反恶热」"),
 "口干":   (["口燥", "咽干", "口舌干燥", "渴"], "[待证·㉞批复核未过]等价句0命中；且口干与渴外延不同，只作桥接"),
 "纳差":   (["不欲饮食", "不能食", "食欲不振", "默默不欲饮食", "食少"], "A·§96「嘿嘿不欲饮食」"),
 "腹胀":   (["腹满", "腹胀满", "胀满"], "D·派生词形"),
 "恶心":   (["欲呕", "干呕", "喜呕", "呕逆"], "[待证·㉞批复核未过]等价句 0 命中，只作检索桥接"),
 "乏力":   (["身重", "四肢沉重", "疲乏", "少气", "身倦"], "[待证·㉞批复核未过]等价句 0 命中，只作检索桥接"),
 "头晕":   (["头眩", "目眩", "冒眩", "眩晕", "头冒"], "A·§67「起则头眩」§263「目眩」"),
 "小便少": (["小便不利", "小便难", "小便短少"], "A·§71「小便不利」"),
 "汗多":   (["汗出", "自汗出", "大汗出", "汗自出"], "D·派生词形"),
}

txt = {}
def load():
    if txt: return txt
    for bk, fn in BOOKS:
        p = os.path.join(B, "sources", fn)
        txt[bk] = JUNK.sub("", re.sub(r"\s+", "", open(p, encoding="utf-8", errors="ignore").read())) \
            if os.path.exists(p) else ""
    return txt

def cooc(word, win=150):
    """word 与各六经名在 ±win 字窗口内的共现数。"""
    T = "".join(load().values())
    out = Counter(); n = T.count(word)
    for j in JING:
        for m in re.finditer(j, T):
            if word in T[max(0, m.start() - win):m.start() + win]:
                out[j] += 1
    return n, out

L = ["# 术语异写映射层 ＋ 零共现复核（㉜批）", "",
     "## 事故：我上批报的「便溏与太阴共现 0 次」是**术语假象**", "",
     "上级质疑后实测（±150字窗口，全库 1,543,352 字）：", "",
     "| 经 | 便溏 | **自利** | **下利** |", "|---|---|---|---|"]
T = "".join(load().values())
for j in ["太阴", "阳明", "少阴"]:
    wins = [T[max(0, m.start() - 150):m.start() + 150] for m in re.finditer(j, T)]
    L.append("| %s（窗口%d） | %d | **%d** | **%d** |" % (
        j, len(wins), sum(1 for w in wins if "便溏" in w),
        sum(1 for w in wins if "自利" in w), sum(1 for w in wins if "下利" in w)))
L += ["", "> **胡老不用「便溏」这个现代病历词，他用「自利」「下利」。**",
      "> 太阴窗口内：便溏 1 ／ **自利 145** ／ **下利 308**。",
      "> **零共现是词汇假象，不是医学事实。** 该结论已撤回（W-1.16）。", "",
      "> ⚠**这个假象污染了㉛批全部 41 token 的统计**——那张表是按现代病历用语建的。", "",
      "---", "", "## 异写映射表", "",
      "> **只作检索桥接，不合并语义**（R22 同义词纪律不变）。",
      "> 依据：**A**＝原文明确等价｜**D**＝派生词形｜**[待证]**＝仅检索便利，",
      "> **无原文等价证明，不得用于语义合并或判据**。", "",
      "| 现代用语 | 全库命中 | 胡老用语（异写） | 各自命中 | 依据 |", "|---|---|---|---|---|"]
data = {}
for mod, (als, basis) in ALIAS.items():
    n0 = T.count(mod)
    hits = [(a, T.count(a)) for a in als]
    hits = [(a, c) for a, c in hits if c > 0]
    data[mod] = dict(self=n0, alias=dict(hits), basis=basis)
    L.append("| **%s** | %d | %s | %s | %s |" % (
        mod, n0, "／".join(a for a, _ in hits), "／".join(str(c) for _, c in hits), basis))

L += ["", "---", "", "## 零共现复核：桥接前 vs 桥接后（与六经名 ±150字共现）", "",
      "| 词 | 桥接前(现代用语) | 桥接后(含胡老异写) | 结论是否翻转 |", "|---|---|---|---|"]
flip = 0
for mod, (als, _) in ALIAS.items():
    _, c0 = cooc(mod)
    ca = Counter()
    for a in als:
        _, c = cooc(a); ca.update(c)
    s0 = "／".join("%s%d" % (k, v) for k, v in c0.most_common(3)) or "**全零**"
    sa = "／".join("%s%d" % (k, v) for k, v in ca.most_common(3)) or "全零"
    f = "**是**" if (not c0 and ca) or (c0 and ca and c0.most_common(1)[0][0] != ca.most_common(1)[0][0]) else "否"
    if f == "**是**": flip += 1
    L.append("| %s | %s | %s | %s |" % (mod, s0, sa, f))
L += ["", "**桥接后结论翻转的词：%d／%d。**" % (flip, len(ALIAS)),
      "", "> **视角㉞（本批新立）**：任何基于词频/共现的结论，",
      "> **须先证明该词是胡老实际用语**；否则标「术语受限，不可作判据」。"]

open(os.path.join(B, "term_layer", "术语异写映射与零共现复核.md"), "w", encoding="utf-8").write("\n".join(L))
json.dump(data, open(os.path.join(B, "term_layer", "_alias_raw.json"), "w"), ensure_ascii=False, indent=1)
print("异写映射 %d 组｜结论翻转 %d 组" % (len(ALIAS), flip))
for mod, (als, _) in ALIAS.items():
    _, c0 = cooc(mod); ca = Counter()
    for a in als:
        _, c = cooc(a); ca.update(c)
    print("  %-8s 桥接前 %-22s → 桥接后 %s" % (
        mod, "／".join("%s%d" % x for x in c0.most_common(2)) or "**全零**",
        "／".join("%s%d" % x for x in ca.most_common(2)) or "全零"))
