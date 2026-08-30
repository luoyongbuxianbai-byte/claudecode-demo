#!/usr/bin/env python3
"""【症状-功能位-填充药表】＋【剂量判据层】(64批·上级⑨ ＋ 61批欠账二批之剂量层)。

上级⑨【功能位模型】：**方 = 基方证 + Σ(症状→功能位→填充药)**；
  ⭐**功能位由症状定义，非由药性定义**；**填充药可替换**（仲景填连轺治表位湿热，
  后世填连翘银花）；八纲六经三毒为功能位之组织框架。
  上级所举六锚（**本工具首跑前已逐条验证，全部命中**）：
    项背强急→葛根｜咳逆喘满→厚朴杏仁｜气上冲剧→重桂枝｜
    胃虚津伤心下痞硬→参姜芍｜陷少阴→附子｜痰饮惊狂→蜀漆龙牡。

剂量层（61批定为下批首项，**连续两批未做，本批清账**）：
  上级59/61批：须标「**加量→兼填何位／增强何位**」，**而非简单「加量→增效」**
  ——因【一药多位】机制（R60⑧）：一药可同时填两个位，加量常是为第二个位。

⛔【与附录H 之关系·须先说清，免得重复计数】
  附录H（57/58批）走的是「此于A汤加X，故治A汤证而Y者」之**完整三元组**，得 40 条。
  本工具**只锚右半句**「故治…而Y者」，C卷实得 **76 处** —— 因为**左半句常不写**
  （方解直接说「故治桂枝汤证而咳逆喘满者」，不重复「此于桂枝汤加厚朴杏仁」）。
  → **本表是附录H 的右半扩展，不是替代**；**X（填充药）须回方剂组成差集补**，
    补不出者标 `[填充药未定]`，**不猜**〔协议4 宁弃勿猜〕。

【已知失效模式】(视角㉕)
  ① **「故治A证而Y者」中的 A 可能不是方名而是泛指**（「故治疗该方证而有血虚的征候者」）
     → A 解析不出方名者标 `[基方泛指]`，**不并入任何方**。
  ② **Y 常是多症并列**（「胃气虚衰、津液不足、心下痞硬而脉沉迟」）→ **整段照录，不拆**；
     拆分须人读〔58批孤证拆分之教训：机械拆分会把并列证拆成独立判据〕。
  ③ **剂量语之「重用」在八书中大量修饰非药物**〔precedent_scan「有力」同型错〕
     → 正向闸门：「重用」后须紧跟**已知药名**，否则弃并计数。
  ④ **填充药之差集依赖 fang_structure 之组成解析**，该解析有 OCR 缺陷 → 补不出属常态。
【弃件条件】Y 段长度 <2 或 >40 字者弃并计数。
【口径】(视角㊱) 一条＝一个「故治…而…者」句；`python3 tools/gongnengwei.py` 复跑。
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
T = {bk: JUNK.sub("", re.sub(r"\s+", "", open(os.path.join(B, "sources", fn),
     encoding="utf-8", errors="ignore").read()))
     for bk, fn in BOOKS if os.path.exists(os.path.join(B, "sources", fn))}
C = T["C卷"]

fs = json.load(open(os.path.join(B, "term_layer", "_fang_structure.json")))
HERBS = sorted({h for p in fs["pairs"] for h in p["herbs"]} |
               {"桂枝","芍药","甘草","生姜","大枣","葛根","厚朴","杏仁","附子","人参","半夏",
                "茯苓","白术","黄芩","柴胡","石膏","知母","麻黄","大黄","干姜","龙骨","牡蛎",
                "蜀漆","当归","川芎","泽泻","猪苓","黄连","栀子","枳实","阿胶","地黄","麦冬",
                "五味子","细辛","吴茱萸","黄芪","薏苡仁","桃仁","丹皮","芒硝","栝蒌根","天花粉"},
               key=len, reverse=True)
HERB_RX = re.compile("|".join(map(re.escape, HERBS)))

# ══ ⑨ 症状→功能位→填充药 ════════════════════════════════════
# ⛔首跑漏「气上冲」——非语料无，系正则不许「证」与「而」之间有逗号
#   （原文作「故治桂枝汤证，而气上冲剧烈者」）。R41⑪「精确串漏一字」同型·**第12例**。
GT = re.compile(r"故治([^。；]{2,30}?)(?:证)?[，]?而(?:又见)?([^，。；]{2,40}?)者")
rows, drop = [], Counter()
for m in GT.finditer(C):
    base, sym = m.group(1), m.group(2)
    if not (2 <= len(sym) <= 40): drop["Y段长度越界"] += 1; continue
    fang = re.search(r"[一-鿿]{2,12}(?:汤|散|丸)", base)
    ctx = C[max(0, m.start() - 160):m.start()]
    add = [h for h in dict.fromkeys(HERB_RX.findall(ctx))
           if re.search(r"(?:加|增|重用|倍)[^，。]{0,8}" + re.escape(h), ctx)]
    rows.append(dict(base=fang.group(0) if fang else "[基方泛指]", sym=sym,
                     add=add or ["[填充药未定]"], src=m.group(0)[:70]))
print("═══ ⑨**症状→功能位→填充药**（C卷·「故治…而…者」）═══")
print("命中 **%d 条**（弃 %s）" % (len(rows), dict(drop)))
nb = sum(1 for r in rows if r["base"] == "[基方泛指]")
nx = sum(1 for r in rows if r["add"] == ["[填充药未定]"])
print("  基方可解析 **%d**／泛指 %d｜填充药可补 **%d**／未定 %d〔失效模式①④〕"
      % (len(rows) - nb, nb, len(rows) - nx, nx))
print("\n[上级⑨六锚之复核·逐条]")
for probe in ["项背强急", "咳逆喘满", "气上冲", "心下痞硬", "少阴", "惊狂"]:
    hit = [r for r in rows if probe in r["sym"]]
    print("  %-8s → %s" % (probe, ("✅ %s｜填充药 %s" % (hit[0]["base"], "／".join(hit[0]["add"])))
                           if hit else "⛔**未命中**"))

# ══ 剂量判据层 ═══════════════════════════════════════════════
print("\n═══ **剂量判据层**（61批欠账·八书全库）═══")
dose, ddrop = [], Counter()
DOSE_PATS = [(r"(重用|倍用|增大?|加重)([一-鿿]{2,4})", "增"), (r"(减(?:少|轻)?)([一-鿿]{2,4})的?用量", "减")]
for bk in T:
    for rx, direc in DOSE_PATS:
        for m in re.finditer(rx, T[bk]):
            herb = m.group(2)
            if not HERB_RX.fullmatch(herb):   # ⛔正向闸门〔失效模式③〕
                ddrop["「%s」后非药名" % m.group(1)] += 1; continue
            win = T[bk][m.start():m.start() + 130]
            why = re.search(r"故治([^，。；]{2,40}?)者", win) or re.search(r"(?:以|在于|所以)治([^，。；]{2,20})", win)
            dose.append(dict(book=bk, op=m.group(1), herb=herb, direc=direc,
                             why=why.group(1) if why else "[未言其故]", ctx=win[:100]))
seen, ud = set(), []
for d in dose:
    k = (d["book"], d["op"], d["herb"], d["ctx"][:40])
    if k in seen: continue
    seen.add(k); ud.append(d)
# ⭐**跨书去重**：同一方解在 C卷/解读/传真 三版重出，按书去重会把 1 条判据数成 3 条〔㊱〕
xseen, xd = set(), []
for d in sorted(ud, key=lambda x: x["book"] != "C卷"):
    k = (d["op"].replace("增大", "增"), d["herb"])
    if k in xseen: continue
    xseen.add(k); xd.append(d)
# ⭐**上级61批之要求：分「增强本位」与「兼填第二位」**
JIAN = re.compile(r"而(?:又)?(?:有|见)|兼|并|的[一-鿿]{2,4}证")
for d in xd:
    d["kind"] = "⭐兼填第二位" if JIAN.search(d["why"]) else "增强本位"
print("命中 **%d 条**（去重后 **%d**）｜⛔正向闸门弃 %d 条：%s"
      % (len(dose), len(ud), sum(ddrop.values()), dict(list(ddrop.items())[:4])))
print("⭐**跨书去重后 %d 条**（同一方解在C卷/解读/传真三版重出，按书去重会把1条数成3条）" % len(xd))
withy = [d for d in xd if d["why"] != "[未言其故]"]
print("⭐**其中言明「故治…者」者 %d 条 ＝ %.0f%%——只有这些是判据，其余是叙述。**"
      % (len(withy), 100 * len(withy) / max(1, len(xd))))
kc = Counter(d["kind"] for d in withy)
print("⭐**上级61批所要之分类实测：%s**" % dict(kc))
print("\n[⭐**上级59/61批之要求：须判「加量→兼填何位」抑或「增强本位」**]")
for d in withy:
    print("  〔%s〕**%s%s** → 故治「%s」 ← **%s**" % (d["book"], d["op"], d["herb"], d["why"][:32], d["kind"]))

# ── ⛔自检〔㊹必然失败样例〕 ──────────────────────────────────
assert not GT.findall("此段子虚乌有并无任何故治句式"), "⛔自检失败：虚构句命中故治式"
assert GT.findall("故治桂枝汤证而咳逆喘满者"), "⛔自检失败：真故治句未命中"
assert not HERB_RX.fullmatch("亦所以"), "⛔自检失败：非药名通过药名闸门"
assert HERB_RX.fullmatch("茯苓"), "⛔自检失败：真药名未过闸门"
print("\n[自检] 虚构句零命中｜真句命中｜非药名被闸门挡下｜真药名通过 → 有分辨力")

json.dump(dict(gnw=rows, dose=xd), open(os.path.join(B, "term_layer", "_gongnengwei.json"), "w"),
          ensure_ascii=False, indent=1)
L = ["# 附录L：症状-功能位-填充药表 ＋ 剂量判据层（64批·上级⑨ ＋ 61批剂量欠账）", "",
     "> ⭐**上级⑨**：**方 = 基方证 + Σ(症状→功能位→填充药)**；",
     "> **功能位由症状定义，非由药性定义**；**填充药可替换**。", "",
     "> ⛔**与附录H 之别**：附录H 走完整三元组（40条），本表只锚右半句「故治…而Y者」",
     "> （C卷 **%d** 处），因左半句常省。**本表是附录H 的右半扩展，非替代。**" % len(rows), "",
     "## 一、上级⑨六锚之复核", "", "| 症状（功能位） | 基方 | 填充药 | 结果 |", "|---|---|---|---|"]
for probe in ["项背强急", "咳逆喘满", "气上冲", "心下痞硬", "少阴", "惊狂"]:
    hit = [r for r in rows if probe in r["sym"]]
    L.append("| %s | %s | %s | %s |" % (probe, hit[0]["base"] if hit else "—",
             "／".join(hit[0]["add"]) if hit else "—", "✅" if hit else "⛔未命中"))
L += ["", "## 二、逐条（%d 条·基方可解析 %d／填充药可补 %d）" % (len(rows), len(rows)-nb, len(rows)-nx), "",
      "| 基方 | ⭐症状（＝功能位之定义者） | 填充药 |", "|---|---|---|"]
for r in rows:
    L.append("| %s | **%s** | %s |" % (r["base"], r["sym"], "／".join(r["add"])))
L += ["", "## 三、剂量判据层（八书·跨书去重 %d 条·**言明「故治」者 %d 条＝%.0f%%**）" % (
        len(xd), len(withy), 100*len(withy)/max(1,len(xd))), "",
      "> ⭐**上级59/61批之规定**：须标「**加量→兼填何位／增强何位**」，**非简单「加量→增效」**",
      "> ——因【一药多位】（R60⑧）：一药可同时填两位，加量常是为第二个位。", "",
      "⛔**只有言明「故治…者」的 %d 条是判据，其余 %d 条是叙述**，不得混用。" % (len(withy), len(xd)-len(withy)), "",
      "| 出处 | 操作 | 药 | 故治（＝所填之位） | ⭐类型 |", "|---|---|---|---|---|"]
for d in withy:
    L.append("| %s | %s | **%s** | %s | **%s** |" % (d["book"], d["op"], d["herb"], d["why"], d["kind"]))
open(os.path.join(B, "term_layer", "附录L_功能位与剂量判据层.md"), "w").write("\n".join(L))
print("→ term_layer/附录L_功能位与剂量判据层.md")
