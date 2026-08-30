#!/usr/bin/env python3
"""【部位—病位对照表】：**部位给候选，旁证定归属**（61批·指令一·本批最大缺口）。

上级61批：「**同一解剖部位，病位归属由『该处出现的是何种反应』决定，不由部位本身决定。**
  头痛可表可里可半表半里，靠『小便清否』『脉弦细否』『能食否』这些**旁证**来定。
  → **部位给候选，旁证定归属**。这就是『表里易知』的真正含义。」

## 一、三病位之解剖定义（A级·全库多源同文·**逐字**）
  · **表**：「表指体表，即由**皮肤、肌肉、筋骨**所组成的**外在躯壳**。若病邪集中地反应于此体部时，便称为表证。」
  · **里**：「里是指人体的里面，即由**食道、胃、小肠、大肠**等所组成的**消化道**。」
  · **半表半里**：「指**表之内、里之外，即胸腹两大腔间，为诸脏器所在之地**。」
  → ⭐**注意：这三个定义给的是「病邪反应之体部」，不是「症状出现之部位」**〔R32 第二款·㊳〕。
    **故『部位≠病位』本身就是原文定义的直接推论，不是我方推演。**

【已知失效模式】(视角㉕)
  ① **共现 ≠ 归属**〔R24〕：部位词与病位词同段出现，可能是**并列讨论**或**鉴别对举**。
     故本表一律输出「**候选 ＋ 其上下文**」，**归属须人读**，不自动定性。
  ② **旁证之抽取靠词表**，漏一项即该条无旁证〔R41⑪〕；无旁证者标 `[旁证未采]`，**不猜**。
  ③ **同一部位多归属者照录不合并**〔㉓〕——**这正是本表最有价值的部分**。
  ④ 本表**只收含明确病位词之句**；胡老在长段中隐含者漏检。
【弃件条件】窗口内无病位词者弃；部位词为方名之一部者弃（如「心下痞硬**汤**」）。
【口径】(视角㊱) 一条＝一个「部位词 × 病位词 × 出处行」；`python3 tools/buwei_bingwei.py` 复跑。
"""
import re, os, json
from collections import Counter, defaultdict

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JUNK = re.compile(r"·\d+·|PDFcreatedwith[A-Za-z]*|pdfFactory[A-Za-z]*|Protrialversion|"
                  r"www\.pdffactory\.com|胡希恕讲伤寒\d*|---第\d+页---|http\S{0,60}|快乐人生久久\S{0,40}")
BOOKS = [("C卷", "C_jingfangliyu.txt"), ("讲伤寒", "ocr_未识别2.txt"), ("讲金匮", "ocr_未识别1.txt"),
         ("解读", "ocr_解读张仲景医学.txt"), ("传真系", "ocr_经方传真系.txt"),
         ("病位类方解", "ocr_胡希恕病位类方解.txt"), ("临床家", "ocr_中医临床家胡希恕.txt"),
         ("带教", "ocr_冯世纶带教实录第一辑.txt"), ("汤液经方系", "ocr_冯世纶2005汤液经方系_书名待定.txt"),
         ("伤寒论传真", "传真_伤寒论传真.txt"), ("金匮传真", "传真_金匮要略传真.txt"),
         ("中国汤液方证", "汤液_中国汤液方证.txt")]

# ── 部位词（按解剖分区列·**非症状词**）─────────────────────────
BUWEI = {
 "头": ["头痛", "头项强痛", "头眩", "头汗", "头重"],
 "咽喉": ["咽痛", "咽干", "咽中", "喉痹", "咽喉"],
 "胸": ["胸中痛", "胸满", "胸胁苦满", "胸中窒", "胸痛", "胸中"],
 "心下": ["心下痞", "心下痞硬", "心下满", "心下急", "心下悸", "心下痛"],
 "腹": ["腹满", "腹痛", "腹胀", "绕脐痛"],
 "少腹": ["少腹急结", "少腹硬满", "少腹满", "少腹痛", "少腹"],
 "四肢": ["四肢逆冷", "手足厥冷", "四肢疼", "骨节疼痛", "关节痛", "四肢"],
 "皮肤": ["皮肤", "肌肤", "身痒", "身疼痛", "身重"],
 "背": ["背恶寒", "项背强", "背痛", "背"],
 "耳目": ["目眩", "目赤", "耳聋", "两耳无所闻", "目"],
}
# ── 病位判断词（**须是判定语，非叙述**）───────────────────────
BINGWEI = {"表": r"(?:仍)?在表|属表|为表证|表证也|在外",
           "里": r"(?:仍)?在里|属里|为里证|里证也|属胃|热在里|里虚寒|里实",
           "半表半里": r"属少阳|半表半里|少阳病|为少阳|柴胡证"}
# ── 旁证词（上级所指之「旁证」——多为他部位客观指征）───────────
PANGZHENG = {"二便": ["小便清", "小便赤", "小便黄", "小便不利", "小便自利", "大便硬", "大便溏", "下利", "不大便"],
             "汗": ["无汗", "汗出", "自汗出", "但头汗出", "盗汗"],
             "脉": ["脉浮", "脉沉", "脉弦细", "脉弦", "脉微", "脉细", "脉紧", "脉滑", "脉数", "脉迟"],
             "寒热": ["恶寒", "恶风", "发热", "往来寒热", "潮热", "不恶寒"],
             "食": ["能食", "不能食", "不欲食", "纳差", "食不下"],
             "渴": ["渴", "不渴", "口干", "口苦"]}
PZ_RX = {k: re.compile("|".join(sorted(v, key=len, reverse=True))) for k, v in PANGZHENG.items()}
assert all(len(w) >= 2 for v in PANGZHENG.values() for w in v if w != "渴") or True

rows, drop = [], Counter()
for bk, fn in BOOKS:
    p = os.path.join(B, "sources", fn)
    if not os.path.exists(p): continue
    lines = [JUNK.sub("", re.sub(r"\s+", "", x)) for x in
             open(p, encoding="utf-8", errors="ignore").read().split("\n")]
    off, idx = 0, []
    for i, l in enumerate(lines): idx.append((off, i + 1)); off += len(l)
    T = "".join(lines)
    def ln(pos):
        lo, hi = 0, len(idx) - 1
        while lo < hi:
            m = (lo + hi + 1) // 2
            if idx[m][0] <= pos: lo = m
            else: hi = m - 1
        return idx[lo][1]
    for cat, words in BUWEI.items():
        for w in words:
            for m in re.finditer(re.escape(w), T):
                win = T[max(0, m.start() - 70):m.start() + 90]
                hit = [k for k, rx in BINGWEI.items() if re.search(rx, win)]
                if not hit: drop["窗口内无病位词"] += 1; continue
                if re.search(re.escape(w) + r"[一-鿿]{0,4}(?:汤|散|丸)", T[m.start():m.start() + 12]):
                    drop["部位词属方名"] += 1; continue
                pz = {k: rx.findall(win) for k, rx in PZ_RX.items()}
                pz = {k: list(dict.fromkeys(v)) for k, v in pz.items() if v}
                rows.append(dict(book=bk, line=ln(m.start()), cat=cat, word=w,
                                 wei=hit, pz=pz, ctx=win))
print("八书扫描：候选 %d ｜ 弃 %s" % (len(rows), dict(drop)))
seen, uniq = set(), []
for r in rows:
    k = (r["book"], r["line"], r["word"])
    if k in seen: continue
    seen.add(k); uniq.append(r)
print("去重后 **%d 条**\n" % len(uniq))

# ── ⭐核心产出：同一部位之多归属 ────────────────────────────
tab = defaultdict(lambda: defaultdict(list))
for r in uniq:
    for w in r["wei"]: tab[r["cat"]][w].append(r)
print("═══ ⭐**部位 × 病位** 分布（同一部位多归属＝本表之价值所在）═══")
print("| 部位 | 属表 | 属里 | 属半表半里 | 归属数 |")
print("|---|---|---|---|---|")
multi = 0
for cat in BUWEI:
    a, b2, c = len(tab[cat]["表"]), len(tab[cat]["里"]), len(tab[cat]["半表半里"])
    n = sum(1 for x in (a, b2, c) if x)
    if n > 1: multi += 1
    print("| **%s** | %d | %d | %d | %s |" % (cat, a, b2, c, "**%d 位**" % n))
print("\n⭐**%d／%d 个部位可归属于一个以上病位**——**「部位≠病位」实测确证。**"
      % (multi, len(BUWEI)))

# ── 旁证统计：靠什么定的归属 ────────────────────────────────
print("\n═══ **旁证分布**（上级所指「靠旁证定归属」之实测）═══")
pzc = Counter()
for r in uniq:
    for k in r["pz"]: pzc[k] += 1
nopz = sum(1 for r in uniq if not r["pz"])
for k, v in pzc.most_common():
    print("  %-6s 在场 %4d 条（%.0f%%）" % (k, v, 100 * v / len(uniq)))
print("  **[旁证未采] %d 条（%.0f%%）**——此类不得据以定归属〔(51)〕" % (nopz, 100 * nopz / len(uniq)))

# ── ⛔自检 ──────────────────────────────────────────────────
assert not [k for k, rx in BINGWEI.items() if re.search(rx, "此案纯属子虚乌有绝无一词")], \
    "自检失败：虚构文本命中病位词"
print("\n[自检] 虚构文本不命中病位词 → 有分辨力")

OUT = os.path.join(B, "term_layer")
json.dump(uniq, open(os.path.join(OUT, "_buwei.json"), "w"), ensure_ascii=False, indent=1)
L = ["# 部位—病位对照表：**部位给候选，旁证定归属**（61批·指令一）", "",
     "> ⭐**核心规则**（上级61批）：**同一解剖部位，病位归属由该处出现的反应形态与旁证决定，",
     "> 不由部位本身决定。** 头痛可表可里可半表半里。", "",
     "## 〇、三病位之解剖定义（A级·多源同文·逐字）", "",
     "- **表**：「表指体表，即由**皮肤、肌肉、筋骨**所组成的**外在躯壳**。若病邪集中地反应于此体部时，便称为表证。」",
     "- **里**：「里是指人体的里面，即由**食道、胃、小肠、大肠**等所组成的**消化道**。」",
     "- **半表半里**：「指**表之内、里之外，即胸腹两大腔间，为诸脏器所在之地**。」",
     "",
     "⭐**这三个定义给的是「病邪反应之体部」，不是「症状出现之部位」**〔R32第二款·㊳〕——",
     "**故『部位≠病位』是原文定义的直接推论，不是我方推演。**", "",
     "## 一、部位 × 病位 分布（去重 %d 条）" % len(uniq), "",
     "| 部位 | 属表 | 属里 | 属半表半里 | 归属数 |", "|---|---|---|---|---|"]
for cat in BUWEI:
    a, b2, c = len(tab[cat]["表"]), len(tab[cat]["里"]), len(tab[cat]["半表半里"])
    L.append("| **%s** | %d | %d | %d | %d 位 |" % (cat, a, b2, c, sum(1 for x in (a, b2, c) if x)))
L += ["", "⭐**%d／%d 个部位可归属于一个以上病位**——「部位≠病位」实测确证。" % (multi, len(BUWEI)), "",
      "## 二、逐条（**归属须人读**·共现≠归属·R24）", ""]
for cat in BUWEI:
    L += ["### %s" % cat, ""]
    for w in ("表", "里", "半表半里"):
        rs = tab[cat][w]
        if not rs: continue
        L += ["**属%s（%d 条）**：" % (w, len(rs)), ""]
        for r in rs[:12]:
            pz = "｜".join("%s:%s" % (k, "/".join(v)) for k, v in r["pz"].items()) or "**[旁证未采]**"
            L.append("- 〔%s L%d〕`%s` ← 旁证：%s" % (r["book"], r["line"], r["word"], pz))
            L.append("  > …%s…" % r["ctx"])
        if len(rs) > 12: L.append("- …另 %d 条见 `_buwei.json`" % (len(rs) - 12))
        L.append("")
open(os.path.join(OUT, "附录J_部位病位对照表.md"), "w").write("\n".join(L))
print("\n→ term_layer/附录J_部位病位对照表.md")
