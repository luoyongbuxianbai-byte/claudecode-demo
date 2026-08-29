#!/usr/bin/env python3
"""【六经提纲症·敏感度/特异度实测】（54批·上级令「提纲是高特异低敏感」之可测化）。

上级54批：「**提纲是高特异、低敏感**。见之→强提示该经；不见→**不能排除**该经。
  而我们的引擎一直拿『提纲不见』去排除——**把低敏感当高敏感用**。」

⭐**本工具把这句话变成一个可以失败的数**〔视角⑬〕：
  对每个提纲症 s 与每经 j，在真医案库上算——
    **敏感度 Sens** ＝ P(s 在场 | 该案判为 j)      ——「该经的病人有多少带这个症」
    **特异度 Spec** ＝ P(s 不在场 | 该案非 j)      ——「非该经的病人有多少不带这个症」
    **阳性预测值 PPV** ＝ P(判为 j | s 在场)        ——「见到这个症，有多大把握是该经」
  **若上级之说成立，应见 Sens 低而 Spec 高。若 Spec 也低，则该症连"强提示"都算不上。**
  **这个实验可以失败，且两个方向都是信息。**

⛔**本工具最要紧的一条口径警告（必须与所有数字同读）**：
  金标准＝**案文明写之六经名**。而**案文提到某经 ≠ 该案被判为某经**——
  讲解、鉴别、合病列举都会使经名出现（视角㉟体裁关）。
  → **故本表之 Spec 系统性偏低、Sens 系统性偏高**（分母被污染）。
  → **本表只可用于「同一口径下各症之相对比较」，不可作绝对诊断学参数。**
  **㊱数必带口径：凡引用本表数字，须连本段一起引。**

【已知失效模式】(视角㉕)
  ① 金标准污染（见上），**这是本表最大的已知缺陷，未解**。
  ② 症状词表人工列，**漏一种写法即该症敏感度被低估**〔R41⑪〕。
     已按胡老用语列并附别写；**仍必然不全**。
  ③ 一案多经（合病）者**对每个在场经各计一次**，非互斥分类。
  ④ **未标经之案不入分母**——它们既不能证实也不能证伪，**不得当作"非该经"**〔(51)〕。
  ⑤ 病例数少之经（厥阴/少阴）**置信区间极宽**，n<20 者一律标「样本不足」。
【弃件条件】非真医案者弃（沿用 precedent_scan 之真医案闸门）。
【口径】(视角㊱) 一案＝一个切案区间；「症在场」＝案文含该症任一写法；
  `python3 tools/tigang_sens_spec.py` 复跑。
"""
import re, os
from collections import Counter, defaultdict

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JUNK = re.compile(r"·\d+·|PDFcreatedwith[A-Za-z]*|pdfFactory[A-Za-z]*|Protrialversion|"
                  r"www\.pdffactory\.com|胡希恕讲伤寒\d*|---第\d+页---|http\S{0,60}|快乐人生久久\S{0,40}")


def load(fn):
    p = os.path.join(B, "sources", fn)
    if not os.path.exists(p): return ""
    raw = open(p, encoding="utf-8", errors="ignore").read()
    n0 = len(re.sub(r"\s+", "", raw))
    T = "".join(JUNK.sub("", re.sub(r"\s+", "", ln)) for ln in raw.split("\n"))
    if n0 and len(T) / n0 < 0.5: raise SystemExit("⛔协议16 中止：%s" % fn)
    return T


BOOKS = [("C卷", "C_jingfangliyu.txt"), ("临床家", "ocr_中医临床家胡希恕.txt"),
         ("带教", "ocr_冯世纶带教实录第一辑.txt"), ("传真", "ocr_经方传真系.txt"),
         ("解读", "ocr_解读张仲景医学.txt")]
CASE_START = re.compile(r"【验案】|【检案】|例\s*\d{1,3}[，,、]?[一-鿿]{2,3}[，,]|病案号\s*\d+|"
                        r"[一-鿿]{1,3}某[，,]\s*(?:男|女)(?:性)?[，,]|"
                        r"\d{4}年\d{1,2}月\d{1,2}日初诊|初诊日期\s*\d{4}")
REAL_CASE = re.compile(r"初诊|岁|男|女|病案号|病历号|【验案】|【检案】|复诊|二诊")

cases = []
for bk, fn in BOOKS:
    T = load(fn)
    if not T: continue
    st = [m.start() for m in CASE_START.finditer(T)]
    for i, s0 in enumerate(st):
        e = st[i + 1] if i + 1 < len(st) else min(len(T), s0 + 2500)
        b = T[s0:e][:2500]
        if len(b) >= 60 and REAL_CASE.search(b) and "【方剂组成】" not in b and "【方解】" not in b:
            cases.append(dict(book=bk, seq=len(cases), body=b))

# ── 六经提纲症（按条文原文，附胡老别写）───────────────────────────
TIGANG = {
 "太阳": [("脉浮", ["脉浮"]), ("头项强痛", ["头项强痛", "项背强", "头痛"]),
          ("恶寒", ["恶寒", "恶风", "怕冷", "畏寒"])],
 "阳明": [("胃家实", ["胃家实", "大便硬", "不大便", "便秘", "燥屎"]),
          ("身热汗出", ["蒸蒸发热", "潮热", "自汗出", "日晡"]),
          ("不恶寒反恶热", ["不恶寒反恶热", "恶热"])],
 "少阳": [("口苦", ["口苦"]), ("咽干", ["咽干", "口咽干"]), ("目眩", ["目眩", "头眩", "眩晕", "头晕"])],
 "太阴": [("腹满而吐", ["腹满", "腹胀"]), ("自利", ["自利", "下利", "便溏", "大便溏", "便稀"]),
          ("食不下", ["食不下", "不欲食", "纳差", "不能食"]),
          ("腹自痛", ["腹痛", "腹自痛"])],
 "少阴": [("脉微细", ["脉微细", "脉微", "脉细", "沉细"]), ("但欲寐", ["但欲寐", "嗜睡", "精神不振"])],
 "厥阴": [("消渴", ["消渴"]), ("气上撞心", ["气上撞心", "气上冲"]),
          ("心中疼热", ["心中疼热", "心中热"]), ("饥不欲食", ["饥而不欲食", "饥不欲食"]),
          ("食则吐蛔", ["吐蛔"])],
}
JING = list(TIGANG)
JING_RX = {j: re.compile(j) for j in JING}

# ── 金标准：案文明写之经（⛔见文件头口径警告）────────────────────
lab = []
for c in cases:
    js = {j for j in JING if JING_RX[j].search(c["body"])}
    lab.append((c, js))
labeled = [(c, js) for c, js in lab if js]
print("真医案 %d ｜ **明写六经者 %d**（未标经 %d，按(51)不入分母）\n"
      % (len(cases), len(labeled), len(cases) - len(labeled)))
print("经之案数：%s\n" % "／".join("%s%d" % (j, sum(1 for _, js in labeled if j in js)) for j in JING))

L = ["# 六经提纲症·敏感度/特异度实测（54批）", "",
     "> ⛔**口径警告（引用本表必须连此段一起引）**：金标准＝**案文明写之六经名**，",
     "> 而**案文提到某经 ≠ 该案被判为某经**（讲解/鉴别/合病列举皆使经名出现·视角㉟）。",
     "> → **本表 Spec 系统性偏低、Sens 系统性偏高**。**只可作同口径下各症之相对比较。**", "",
     "| 经 | 提纲症 | n(该经) | **敏感度** | **特异度** | **PPV** | 读法 |", "|---|---|---|---|---|---|---|"]
print("| 经 | 提纲症 | n(该经) | 敏感度 | 特异度 | PPV | 读法 |")
print("|---|---|---|---|---|---|---|")
summary = []
for j in JING:
    pos = [c for c, js in labeled if j in js]
    neg = [c for c, js in labeled if j not in js]
    for name, words in TIGANG[j]:
        rx = re.compile("|".join(map(re.escape, words)))
        tp = sum(1 for c in pos if rx.search(c["body"]))
        fn_ = len(pos) - tp
        fp = sum(1 for c in neg if rx.search(c["body"]))
        tn = len(neg) - fp
        sens = tp / len(pos) if pos else 0
        spec = tn / len(neg) if neg else 0
        ppv = tp / (tp + fp) if (tp + fp) else 0
        note = "样本不足" if len(pos) < 20 else (
            "**高特异·低敏感**" if spec >= .8 and sens < .6 else
            "**两低·无提示力**" if spec < .8 and sens < .6 else
            "高敏感" if sens >= .6 and spec < .8 else "**高敏高特**")
        row = "| %s | %s | %d | **%.0f%%** | **%.0f%%** | %.0f%% | %s |" % (
            j, name, len(pos), 100 * sens, 100 * spec, 100 * ppv, note)
        print(row); L.append(row)
        summary.append((j, name, sens, spec, len(pos)))

# ── ⭐总判：上级之说是否成立 ────────────────────────────────────
ok = [s for s in summary if s[4] >= 20]
hi_spec = [s for s in ok if s[3] >= .8]
lo_sens = [s for s in ok if s[2] < .6]
both = [s for s in ok if s[3] >= .8 and s[2] < .6]
neither = [s for s in ok if s[3] < .8 and s[2] < .6]
print("\n═══ ⭐总判（样本足者 %d 项）═══" % len(ok))
print("  高特异(≥80%%) %d ｜ 低敏感(<60%%) %d ｜ **两者兼具＝『高特异低敏感』 %d**"
      % (len(hi_spec), len(lo_sens), len(both)))
print("  ⚠**两低（特异也不高）＝连强提示都算不上** %d 项：%s"
      % (len(neither), "／".join("%s·%s" % (x[0], x[1]) for x in neither) or "无"))
L += ["", "## ⭐总判（样本足者 %d 项）" % len(ok),
      "- 高特异(≥80%%) **%d** ｜ 低敏感(<60%%) **%d** ｜ **兼具＝「高特异低敏感」%d**"
      % (len(hi_spec), len(lo_sens), len(both)),
      "- ⚠**两低（连强提示都算不上）%d 项**：%s"
      % (len(neither), "／".join("%s·%s" % (x[0], x[1]) for x in neither) or "无")]
open(os.path.join(B, "case_layer", "提纲症_敏感度特异度.md"), "w").write("\n".join(L))
print("\n→ case_layer/提纲症_敏感度特异度.md")
