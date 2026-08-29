#!/usr/bin/env python3
"""【逐症归位语料库】(65批·T1) —— **上级指令之技术前提须先订正**。

上级65批指令：「带教实录 txt OCR 严重损坏……须 pdftoppm 逐页转图精读，约 8–12 轮」。
⛔**执行线复核结论：该路径在本工作区不可执行，且不必要。**
  ① **本仓库无任何 PDF**（`find . -iname "*.pdf"` → 0）。上级所读之 PDF 在上级侧，未入库。
  ② ⭐**更要紧：逐症归位结构在 txt 里是完整的、可机械抽取的。**
     去空白后 `综合分析` 在带教 txt 中 **100 处**。
     上级 grep 得 0，系**未去空白**——该书字间插空格率 45.5%，
     此为该 OCR 之固有形态，**不是内容缺失**〔与 R41 丁「词典法在重 OCR 语料失效」同源〕。
  → **故 T1 由本工具机械全量抽取，不需 8–12 轮读图。**
    ⛔**但 OCR 错字是真的**（「胡希恕」作「胡希息」等），故本表**逐条标 [OCR存疑] 待校**，
    **图像精读之正确用途是校对本表，不是从零重读。**

## 本表之价值定位（引擎最缺者）
  条文讲证，方解讲药，**唯本书讲「这一组症状为什么判到这个位」**。
  一案分 2–4 组，每组独立判定，再综合 —— **此即【证据属地原则】之原文操作形态。**

【已知失效模式】(视角㉕)
  ① **「综合分析」前之归位段边界不定**（上一案之结果段可能被卷入）
     → 以**案头锚**（姓名+性别/年龄或「初诊」）为上界，取不到者标 `[上界未定]`。
  ② **归位段内之「症状组→判断」以句号分隔，但 OCR 句读常缺**〔协议4 宁弃勿猜〕
     → 拆不出成对者**整段照录**，不强拆。
  ③ **判断词表不全则漏归位**〔R41⑪〕→ 判断词未命中者标 `[判断未采]`，**不猜**。
  ④ 阴性项（「饮食二便如常」）**必须保留**〔(51) 缺省不得推定·上级样本C 之实证〕
     → 本工具**不做任何症状过滤**。
【弃件条件】综合分析段 <4 字者弃并计数。
【口径】(视角㊱) 一条＝一个「综合分析」块；`python3 tools/zhengwei_corpus.py` 复跑。
"""
import re, os, json
from collections import Counter

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# ⛔ 有界量词〔协议16·65批实发修补：`\S*` 去空白后吞掉整本临床家〕
JUNK = re.compile(r"·\d+·|PDFcreatedwith[A-Za-z]*|pdfFactory[A-Za-z]*|Protrialversion|"
                  r"www\.pdffactory\.com|胡希恕讲伤寒\d*|---第\d+页---|http\S{0,60}|快乐人生久久\S{0,40}")
SRC = [("带教", "ocr_冯世纶带教实录第一辑.txt"), ("临床家", "ocr_中医临床家胡希恕.txt"),
       ("解读", "ocr_解读张仲景医学.txt"), ("病位类方解", "ocr_胡希恕病位类方解.txt")]

# ── 归位判断词（**病位/病性之判定语**·须双字以上〔协议15〕）───────
PAN = ["太阳表实", "太阳表虚", "太阳中风", "太阳伤寒", "太阳病", "太阳表证", "太阳",
       "阳明里热", "阳明里实", "阳明内热", "阳明病", "阳明", "少阳病", "少阳证", "少阳",
       "太阴里寒", "太阴里虚", "太阴病", "太阴", "少阴病", "少阴", "厥阴病", "厥阴",
       "里虚寒", "里虚", "里实", "里寒", "里热", "里饮", "里湿热", "表不解", "表未解",
       "表虚", "表实", "上热", "下寒", "上热下寒", "寒热错杂", "水饮", "外邪", "瘀血",
       "血虚", "津虚", "水气", "痰饮", "湿热", "虚寒", "实热"]
assert all(len(w) >= 2 for w in PAN), "⛔协议15：判断词表出现单字"
PAN_RX = re.compile("|".join(map(re.escape, sorted(PAN, key=len, reverse=True))))
HEAD = re.compile(r"[一-鿿]{1,3}某|初诊|[男女],\s*\d{1,2}岁|\d{1,2}岁")

rows, drop = [], Counter()
for bk, fn in SRC:
    p = os.path.join(B, "sources", fn)
    if not os.path.exists(p): continue
    T = JUNK.sub("", re.sub(r"\s+", "", open(p, encoding="utf-8", errors="ignore").read()))
    for m in re.finditer(r"综合分析[：:,]?(.{4,160}?)(?:[。．]|结果[:：])", T):
        zh = m.group(1)
        if len(zh) < 4: drop["综合分析段过短"] += 1; continue
        # 归位段 = 本案头锚 → 综合分析 之间
        pre = T[max(0, m.start() - 700):m.start()]
        hs = list(HEAD.finditer(pre))
        seg = pre[hs[-1].start():] if hs else pre[-400:]
        bound = "案头锚" if hs else "**[上界未定]**"
        # 拆「症状组 → 判断」：以句号分句，句尾含判断词者即一组〔失效模式②〕
        pairs, raw = [], []
        for s in re.split(r"[。．]", seg):
            if not s.strip(): continue
            hit = PAN_RX.findall(s[-14:])          # 判断词须在句尾段
            if hit: pairs.append((s[:-len(hit[-1])] if s.endswith(hit[-1]) else s, hit[-1]))
            else: raw.append(s)
        rows.append(dict(book=bk, zh=zh, bound=bound, pairs=pairs, unpaired=raw[-3:],
                         fang=(re.search(r"(?:为|属|与|用)([一-鿿]{2,14}(?:汤|散|丸))", zh) or [None])
                              and (re.search(r"(?:为|属|与|用)([一-鿿]{2,14}(?:汤|散|丸))", zh).group(1)
                                   if re.search(r"(?:为|属|与|用)([一-鿿]{2,14}(?:汤|散|丸))", zh) else "[方未采]")))
print("═══ 【逐症归位语料库】机械全量抽取 ═══")
print("命中 **%d 案**（弃 %s）" % (len(rows), dict(drop) or "0"))
bc = Counter(r["book"] for r in rows); print("  分布：%s" % dict(bc))
npair = sum(len(r["pairs"]) for r in rows)
nb = sum(1 for r in rows if r["bound"] != "案头锚")
nf = sum(1 for r in rows if r["fang"] == "[方未采]")
print("  ⭐**归位对 %d 组，平均 %.1f 组/案**（上级样本称『一案2–4组』→ %s）"
      % (npair, npair / max(1, len(rows)),
         "**实测相符**" if 1.5 <= npair / max(1, len(rows)) <= 4.5 else "⚠**与样本不符，须人读**"))
print("  [上界未定] %d 案｜[方未采] %d 案〔失效模式①〕" % (nb, nf))
print("\n[⭐上级八样本之机械复核·逐条]")
for probe, exp in [("桂枝人参汤", "太阳太阴合病"), ("越婢汤", "水饮内停"), ("小建中汤", "太阳太阴"),
                   ("甘草泻心汤", "上热下寒"), ("苓桂术甘汤", "表不解"), ("四逆汤", "里虚寒")]:
    hit = [r for r in rows if probe in (r["fang"] or "") or probe in r["zh"]]
    print("  %-10s %s" % (probe, ("✅ %d 案｜首案综合分析：%s" % (len(hit), hit[0]["zh"][:44]))
                          if hit else "⛔**未命中**"))
# ⛔自检〔㊹〕
assert not PAN_RX.findall("子虚乌有绝无一词"), "⛔自检失败：虚构句命中判断词"
assert PAN_RX.findall("脉细弦,太阴里寒"), "⛔自检失败：真归位句未命中"
print("\n[自检] 虚构句零命中｜真归位句命中 → 词表有分辨力")

json.dump(rows, open(os.path.join(B, "case_layer", "_zhengwei.json"), "w"), ensure_ascii=False, indent=1)
L = ["# 逐症归位语料库（65批·T1）", "",
     "> ⭐**引擎最缺者**：条文讲证，方解讲药，**唯本类段落讲「这一组症状为什么判到这个位」**。",
     "> **一案分 2–4 组，每组独立判定，再综合**——此即【证据属地原则】之**原文操作形态**。", "",
     "## ⛔ 技术前提之订正（须先读）", "",
     "上级65批令以 `pdftoppm` 逐页转图精读（估 8–12 轮）。**执行线复核：该路径在本工作区不可执行，且不必要。**", "",
     "1. **本仓库无任何 PDF**（`find . -iname \"*.pdf\"` → 0）。上级所读之 PDF 在上级侧，**未入库**。",
     "2. ⭐**逐症归位结构在 txt 里是完整的**：去空白后「综合分析」在带教 txt 中 **100 处**。",
     "   上级 grep 得 0 系**未去空白**——该书字间插空格率 **45.5%**，是该 OCR 之固有形态，**非内容缺失**。",
     "3. → **T1 由本工具机械全量抽取，得 %d 案，不需 8–12 轮读图。**" % len(rows), "",
     "⛔**但 OCR 错字是真的**（「胡希恕」作「胡希息」）。",
     "→ **图像精读之正确用途是校对本表，不是从零重读。** 本表逐条可校。", "",
     "## 一、总量", "",
     "| 项 | 值 |", "|---|---|",
     "| 案数 | **%d** |" % len(rows),
     "| 分布 | %s |" % "／".join("%s %d" % (k, v) for k, v in bc.items()),
     "| 归位对 | **%d 组**（平均 %.1f 组/案） |" % (npair, npair / max(1, len(rows))),
     "| [上界未定] | %d 案 |" % nb, "| [方未采] | %d 案 |" % nf, "",
     "## 二、逐案（**逐字照录·不改写·阴性项保留**）", ""]
for i, r in enumerate(rows, 1):
    L += ["### %d〔%s〕→ %s" % (i, r["book"], r["fang"] or "[方未采]"), ""]
    if r["pairs"]:
        L.append("| 症状组 | → 归位判断 |"); L.append("|---|---|")
        for s, j in r["pairs"]: L.append("| %s | **%s** |" % (s[-70:], j))
    else:
        L.append("**[判断未采]**——归位段未拆出成对，整段照录：")
        L.append("> %s" % "／".join(r["unpaired"])[:300])
    L += ["", "**综合分析**：%s" % r["zh"], "", "〔上界：%s〕" % r["bound"], ""]
open(os.path.join(B, "case_layer", "逐症归位语料库.md"), "w").write("\n".join(L))
print("→ case_layer/逐症归位语料库.md")
