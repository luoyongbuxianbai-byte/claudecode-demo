#!/usr/bin/env python3
"""【症状→病位·原文明文表】（㊳批·产能转向后的唯一可用建法）。

㊶批裁决：**病位是个案判断，不是语料属性**——统计在原理上测不了它。
故本表**只收胡老/仲景明说归属的句子**：
  「下利**属于里**呀，这个里就是胃肠之里」「其小便清者，**知不在里，仍在表也**」…
**无明文者留空，不以统计补。**

与被废止的 `symptom_locus.py` 之别：
  · 旧表：症状 × 六经名 **共现计数** → ㊳批永久冻结（W-1.18）
  · 本表：**只有一句原文明说「X 属 Y 位」才入表**；一条也不推。

【已知失效模式】(视角㉕)
  ① 句式捕获，胡老不用这些句式而在长段落中隐含归属者**一律漏检**，不推测补全。
  ② **归属句可能带条件**（「其小便清者，知不在里」——前提是「头痛发热」在场）；
     本工具保留 ±80 字上下文，**条件须人读，不得只取归属结论**。
  ③ 一症多归属（同一症在不同条件下归不同位）**照录不合并**，各占一行。
  ④ 只查 6 本主源书；医案层归属须另行取证。
【弃件条件】主语 >12 字或含标点者弃（断句错误）。
【口径】(视角㊱) 一条＝一句明文归属；`python3 tools/locus_explicit.py` 复跑。
"""
import re, os, json
from collections import Counter, defaultdict

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOKS = [("C卷", "C_jingfangliyu.txt"), ("讲伤寒", "ocr_未识别2.txt"), ("讲金匮", "ocr_未识别1.txt"),
         ("解读", "ocr_解读张仲景医学.txt"), ("传真系", "ocr_经方传真系.txt"),
         ("病位类方解", "ocr_胡希恕病位类方解.txt"), ("临床家", "ocr_中医临床家胡希恕.txt"),
         ("带教", "ocr_冯世纶带教实录第一辑.txt"), ("汤液经方系", "ocr_冯世纶2005汤液经方系_书名待定.txt"),
         ("伤寒论传真", "传真_伤寒论传真.txt"), ("金匮传真", "传真_金匮要略传真.txt"),
         ("中国汤液方证", "汤液_中国汤液方证.txt")]
JUNK = re.compile(r"·\d+·|PDFcreatedwith[A-Za-z]*|pdfFactory[A-Za-z]*|Protrialversion|www\.pdffactory\.com")

LOC = r"(半表半里|表|里)"
# ── 明文归属句式（每式都要求「主语 ＋ 归属动词 ＋ 病位词」同句）──
PATS = [
 (r"([一-鿿]{2,12})[，,]?\s*(?:属于|属|即属|乃属)\s*" + LOC, "属"),
 (r"([一-鿿]{2,12})[，,]?\s*(?:是|为|即是|即为)\s*" + LOC + r"(?:证|位|部)", "是…证"),
 (r"([一-鿿]{2,12})[，,]?\s*反映?于\s*" + LOC, "反映于"),
 (r"([一-鿿]{2,12})[，,]?\s*(?:知|可知|说明)(?:其)?(?:不在|在)\s*" + LOC, "知在/不在"),
 (r"([一-鿿]{2,12})[，,]?\s*者[，,]\s*" + LOC + r"(?:证|也)", "者…也"),
]
NOISE = re.compile(r"[，,。；;：:0-9A-Za-z]|这个|那么|所以|就是|我们|如果")
# ── 弃件闸门（㊳批自查：首跑 121 条中大量是「前面那一截」而非症状）──
# 抽样实证：「便称」(出自"便称为里证")、「太阳与少阴均」(六经名非症状)、
# 「可见此二三日时纯」「但不是说少阴病根本」——全是断句噪声。
DROP = re.compile(
    r"太阳|阳明|少阳|太阴|少阴|厥阴"                      # 六经名：是结论不是症状
    r"|便称|称为|叫做|所谓|即指|是指"                      # 定义叙述套语
    r"|可见|不是说|虽亦|当然|这就|为何|由此|故与|均$|纯$|本$|根本$"  # 叙述连接词
    r"|^(?:但|故|则|即|又|亦|其实|因为|所以|如果|若|凡)")   # 连词起首
def bad_subj(s):
    if DROP.search(s): return True
    if len(s) < 2: return True
    return False

rows = []
dropped = {}
for bk, fn in BOOKS:
    p = os.path.join(B, "sources", fn)
    if not os.path.exists(p): continue
    for i, raw in enumerate(open(p, encoding="utf-8", errors="ignore")):
        l = JUNK.sub("", re.sub(r"\s+", "", raw))
        if not l or not re.search(LOC, l): continue
        for rx, kind in PATS:
            for m in re.finditer(rx, l):
                subj = m.group(1)
                if len(subj) > 12 or NOISE.search(subj): continue
                if bad_subj(subj): dropped[subj] = dropped.get(subj, 0) + 1; continue
                rows.append(dict(subj=subj, loc=m.group(2), kind=kind, book=bk, line=i + 1,
                                 ctx=l[max(0, m.start() - 80):m.end() + 80]))

# 去重（同书同行同主语同病位）
seen, uniq = set(), []
for r in rows:
    k = (r["book"], r["line"], r["subj"], r["loc"])
    if k in seen: continue
    seen.add(k); uniq.append(r)

bysubj = defaultdict(list)
for r in uniq: bysubj[r["subj"]].append(r)
multi = {s: v for s, v in bysubj.items() if len({x["loc"] for x in v}) > 1}

L = ["# 【症状→病位·原文明文表】（㊳批）", "",
     "> ㊶批裁决：**病位是个案判断，不是语料属性**——统计在原理上测不了它。",
     "> 故本表**只收胡老/仲景明说归属的句子**，**无明文者留空，不以统计补**。", "",
     "> ⛔与被废止的共现表之别：旧表是「症状×六经名共现计数」（已永久冻结·W-1.18）；",
     "> **本表一条也不推——只有一句原文明说「X 属 Y 位」才入表。**", "",
     "> ⚠**归属句可能带条件**（「其小便清者，**知不在里，仍在表也**」——前提是头痛发热在场）。",
     "> 上下文栏保留 ±80 字，**条件须人读，不得只取归属结论**。", "",
     "**共 %d 条明文归属句，涉 %d 个主语。**" % (len(uniq), len(bysubj)),
     "", "⛔**弃件 %d 种**（㊳批自查）：首跑 121 条中大量是「前面那一截」而非症状"
     "——「便称」(出自\"便称为里证\")、「太阳与少阴均」(六经名是结论不是症状)、"
     "「可见此二三日时纯」「但不是说少阴病根本」。已立闸门剔除。" % len(dropped), "",
     "| # | 主语 | 归属 | 句式 | 出处 | 上下文（**条件在此**） |", "|---|---|---|---|---|---|"]
for k, r in enumerate(sorted(uniq, key=lambda x: (x["loc"], x["subj"])), 1):
    L.append("| %d | **%s** | %s | %s | %s L%d | …%s… |" % (
        k, r["subj"], r["loc"], r["kind"], r["book"], r["line"], r["ctx"].replace("|", "／")))

L += ["", "---", "", "## 一主语多归属（**照录不合并**·各归属各有其条件）", "",
      "**%d 个主语出现多种归属。**" % len(multi), ""]
for s, v in sorted(multi.items(), key=lambda kv: -len(kv[1])):
    L.append("- **%s** → %s" % (s, "／".join(sorted({x["loc"] for x in v}))))

open(os.path.join(B, "term_layer", "症状病位_原文明文表.md"), "w", encoding="utf-8").write("\n".join(L))
json.dump(uniq, open(os.path.join(B, "term_layer", "_locus_explicit.json"), "w"),
          ensure_ascii=False, indent=1)
print("明文归属句 %d 条／主语 %d 个  ｜**弃件 %d 种**(断句噪声/六经名/叙述套语)"
      % (len(uniq), len(bysubj), len(dropped)))
print("按病位：", dict(Counter(r["loc"] for r in uniq)))
print("按句式：", dict(Counter(r["kind"] for r in uniq)))
print("按书：", dict(Counter(r["book"] for r in uniq)))
print("一主语多归属：%d 个 → %s" % (len(multi), list(multi)[:8]))
