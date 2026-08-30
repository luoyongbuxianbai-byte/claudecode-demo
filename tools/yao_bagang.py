#!/usr/bin/env python3
"""【方-八纲对应表】＋【558案加减可解释率回归】（56批·指令四五）。

上级56批：「从 C卷 232 条方解逐味抽，格式 `药｜所治病位｜所治病性/毒｜胡老方解原语`。
  **动态加减由此表自动解释**：加某药＝补某状态，减某药＝去某状态。」
  并令回归：「558 案，报**方-八纲对应表能否解释每案的加减**。不能解释者列表，即为缺口。」

⭐**本表之性质须先写死**：它是**从胡老方解原语反查出来的索引**，
  **不是我方为药物新造的属性表**〔视角㉒〕。每味药只登记**胡老自己怎么说它**，
  **我方不加一字功效**。药在方解中未被单独提及者，**留空标 [方解未单论]**，不推。

【已知失效模式】(视角㉕)
  ① **方解论的是「方」不是「药」**。胡老常整体说「此方治…」而不逐味拆。
     故本表之「药→状态」多为**从含该药之方的方解中截取**，
     **句中该药未被点名者一律不收**——宁少勿猜（协议4）。
  ② **一药多用**：麻黄伍桂枝发汗、伍石膏则「反治汗出」——**同药异用照录不合并**〔㉓〕。
     故本表**行数 > 药数**是设计。
  ③ **回归之「可解释」口径极宽**：只问「该加减药在表内有无登记」，
     **不问登记的状态是否真对应该案**。**故可解释率是上界，不是正确率。**
  ④ 加减串靠正则，OCR 变形漏检；**漏检计入"不可解释"，偏保守**。
【弃件条件】方解段缺失者跳过并计入 no_jiefang；药名 <2 字者弃。
【口径】(视角㊱) 一条＝一个「药 × 一句方解原语 × 出处行」；
  可解释率分母＝**案中出现加减且加减药可解析**之案数；`python3 tools/yao_bagang.py` 复跑。
"""
import re, os, json
from collections import Counter, defaultdict

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JUNK = re.compile(r"·\d+·|PDFcreatedwith[A-Za-z]*|pdfFactory[A-Za-z]*|Protrialversion|"
                  r"www\.pdffactory\.com|^_+$")

# ── C卷解析（沿用 cvol_rebuild 之边界法：下一方名行才是本方终点）──────
CL = [re.sub(r"\s+", "", x) for x in
      open(os.path.join(B, "sources", "C_jingfangliyu.txt"), encoding="utf-8", errors="ignore").read().split("\n")]
NUM = re.compile(r"^[一二三四五六七八九十百零〇]+[、.．]")
anchors = [i for i, s in enumerate(CL) if s.startswith("【方剂组成】")]
def cname(i):
    for j in range(i - 1, max(0, i - 8), -1):
        s = CL[j]
        if not s or JUNK.match(s) or s.startswith("【"): continue
        return NUM.sub("", s), j
    return "", i
names = [cname(i) for i in anchors]

fangs = []
for k, i in enumerate(anchors):
    end = names[k + 1][1] if k + 1 < len(anchors) else len(CL)
    body = CL[i:end]
    secs, cur = {}, None
    for ln_off, s in enumerate(body):
        m = re.match(r"^【(方剂组成|用法|方解|仲景对本方证的论述|辨证要点|验案)】", s)
        if m: cur = m.group(1); secs[cur] = (i + ln_off + 1, s[len(m.group(0)):])
        elif cur: secs[cur] = (secs[cur][0], secs[cur][1] + s)
    fangs.append(dict(name=names[k][0], line=anchors[k] + 1,
                      zu=secs.get("方剂组成", (0, ""))[1],
                      jie=secs.get("方解", (0, "")), yao_line=secs.get("方解", (0, ""))[0]))
print("C卷解析 **%d 方**（有方解者 %d）\n"
      % (len(fangs), sum(1 for f in fangs if f["jie"][1])))

# ── 药名表：从【方剂组成】反抽（**正向识别**：药名即组成里出现的中文串）────
DOSE = re.compile(r"[（(][^）)]*[)）]|\d+\.?\d*\s*(?:克|两|升|枚|钱|分|合|斤|片|个|字)|"
                  r"[一二三四五六七八九十]+(?:枚|两|升|钱|分|合|斤|片)")
herbs = Counter()
for f in fangs:
    for tok in re.split(r"[、，,；;]", DOSE.sub("|", f["zu"])):
        for h in re.split(r"\|", tok):
            h = re.sub(r"[^一-鿿]", "", h)
            if 2 <= len(h) <= 6: herbs[h] += 1
HERB = [h for h, c in herbs.items() if c >= 2]
HERB.sort(key=len, reverse=True)
print("药名（出现≥2方）**%d 味**\n" % len(HERB))

# ── 抽方解原语：**句中点名该药者方收**（失效模式①）────────────────
rows = defaultdict(list)
nojie = 0
for f in fangs:
    ln, jie = f["jie"]
    if not jie: nojie += 1; continue
    for sent in re.split(r"[。；;]", jie):
        if len(sent) < 6: continue
        # ⛔**首跑缺陷·自查捕获**：初版 `break` 使**一句只归一味**，
        #   而方解常一句论两味（"麻黄伍石膏清里热"）→ **系统性少收**，
        #   致「石膏」竟落入"不可解释"(45次)。**改为逐味全收，长名优先并遮蔽以防重复。**
        t = sent
        for h in HERB:                      # HERB 已按长度降序
            if h in t:
                rows[h].append(dict(fang=f["name"][:18], line=ln, sent=sent[:110]))
                t = t.replace(h, "\x00" * len(h))
print("方解逐味抽取：**%d 味有原语**（%d 味 [方解未单论]）｜方解缺失 %d 方\n"
      % (len(rows), len(HERB) - len(rows), nojie))

# ── 八纲槽位：**只按胡老方解用词归档，不新造功效词**────────────────
SLOT = {
 "表·解肌发汗": ["解肌", "发汗", "汗解", "解表", "发其汗", "取汗"],
 "表·气上冲": ["气上冲", "上冲", "降冲"],
 "里·攻实下结": ["攻下", "泻下", "下之", "荡涤", "破结", "攻坚", "除燥", "通便", "里实"],
 "里·清热": ["清热", "解热", "除热", "清里", "寒性", "苦寒", "甘寒", "泻火"],
 "里·温中逐寒": ["温中", "逐寒", "温胃", "祛寒", "温性", "辛温", "回阳", "振兴沉衰"],
 "里·补虚益胃": ["益胃", "健胃", "补中", "补虚", "滋液", "生津", "养液", "胃气", "安中"],
 "水毒·利尿逐水": ["利尿", "逐水", "利水", "逐饮", "化饮", "去水", "行水", "渗湿"],
 "血毒·祛瘀": ["祛瘀", "驱瘀", "破瘀", "行瘀", "活血", "瘀血", "下血"],
 "食毒·消导": ["消导", "消食", "宿食", "去实", "破气", "行气"],
 "半表半里·疏解": ["疏解", "解郁", "和解", "胸胁"],
 "止呕降逆": ["止呕", "降逆", "逐饮止呕", "治呕", "止逆"],
 "腹肌·缓急": ["缓急", "挛急", "腹满痛", "拘急", "治腹"],
 "止痛": ["镇痛", "止痛", "治痛"],
 "止咳平喘": ["定喘", "止咳", "治喘", "镇咳"],
}
SLOT_RX = {k: re.compile("|".join(sorted(v, key=len, reverse=True))) for k, v in SLOT.items()}
assert all(len(w) >= 2 for v in SLOT.values() for w in v), "协议15：槽位词表含单字"

tab, unslot = {}, []
for h, rs in rows.items():
    hit = defaultdict(list)
    for r in rs:
        for k, rx in SLOT_RX.items():
            if rx.search(r["sent"]): hit[k].append(r)
    if hit: tab[h] = hit
    else: unslot.append(h)
print("归入八纲槽位 **%d 味**｜**未归槽 %d 味**（有原语但未用上述用词·逐条列出）\n"
      % (len(tab), len(unslot)))
for k in SLOT:
    n = sum(1 for h in tab if k in tab[h])
    if n: print("   %-14s %3d 味" % (k, n))

# ── 指令五·558案加减可解释率回归 ────────────────────────────────
def load(fn):
    p = os.path.join(B, "sources", fn)
    if not os.path.exists(p): return ""
    raw = open(p, encoding="utf-8", errors="ignore").read()
    n0 = len(re.sub(r"\s+", "", raw))
    T = "".join(re.sub(r"·\d+·|http\S{0,60}|---第\d+页---", "", re.sub(r"\s+", "", ln)) for ln in raw.split("\n"))
    if n0 and len(T) / n0 < 0.5: raise SystemExit("⛔协议16 中止：%s" % fn)
    return T
BOOKS = [("C卷", "C_jingfangliyu.txt"), ("讲伤寒", "ocr_未识别2.txt"), ("讲金匮", "ocr_未识别1.txt"),
         ("解读", "ocr_解读张仲景医学.txt"), ("传真系", "ocr_经方传真系.txt"),
         ("病位类方解", "ocr_胡希恕病位类方解.txt"), ("临床家", "ocr_中医临床家胡希恕.txt"),
         ("带教", "ocr_冯世纶带教实录第一辑.txt"), ("汤液经方系", "ocr_冯世纶2005汤液经方系_书名待定.txt"),
         ("伤寒论传真", "传真_伤寒论传真.txt"), ("金匮传真", "传真_金匮要略传真.txt"),
         ("中国汤液方证", "汤液_中国汤液方证.txt")]
CASE_START = re.compile(r"【验案】|【检案】|例\s*\d{1,3}[，,、]?[一-鿿]{2,3}[，,]|病案号\s*\d+|"
                        r"[一-鿿]{1,3}某[，,]\s*(?:男|女)(?:性)?[，,]|"
                        r"\d{4}年\d{1,2}月\d{1,2}日初诊|初诊日期\s*\d{4}")
cases = []
for fn in BOOKS:
    T = load(fn)
    st = [m.start() for m in CASE_START.finditer(T)]
    for i, s0 in enumerate(st):
        e = st[i + 1] if i + 1 < len(st) else min(len(T), s0 + 2500)
        b = T[s0:e][:2500]
        if len(b) >= 60: cases.append(b)
ADD = re.compile(r"[加去](?![减味重])([一-鿿]{2,5})")
# ⛔药名前缀归一（生石膏＝石膏／生龙骨＝龙骨…）——否则加减侧与表侧对不上
PRE = re.compile(r"^(?:生|炙|炒|制|煅|熟|大|小)")
def hnorm(h):
    """⛔第二次自查：初版优先返回原形，而「生石膏」原形虽在 rows 却未归槽，
       致其 45 次全落"不可解释"。→ **优先返回已归槽之形**。"""
    b2 = PRE.sub("", h)
    for cand in (h, b2):
        if cand in tab: return cand
    for cand in (h, b2):
        if cand in rows: return cand
    return h
n = expl = 0
miss = Counter()
for b in cases:
    hs = [hnorm(h) for h in ADD.findall(b)]
    hs = [h for h in hs if h in herbs or h in rows]
    if not hs: continue
    n += 1
    if all(h in tab for h in hs): expl += 1
    else:
        for h in hs:
            if h not in tab: miss[h] += 1
print("\n═══ 指令五·加减可解释率回归 ═══")
print("  含可解析加减之案 **%d**｜**全部加减药在表内有槽位者 %d ＝ %.1f%%**"
      % (n, expl, 100 * expl / max(n, 1)))
print("  ⚠**口径**：只问「该药在表内有无登记」，**不问登记状态是否真对应该案** → **此为上界，非正确率**。")
print("  不可解释之药（前15）：%s" % "／".join("%s(%d)" % (k, v) for k, v in miss.most_common(15)))

# ── 产出 ────────────────────────────────────────────────────
OUT = os.path.join(B, "term_layer")
json.dump({h: {k: v for k, v in tab[h].items()} for h in tab},
          open(os.path.join(OUT, "_yao_bagang.json"), "w"), ensure_ascii=False, indent=1)
L = ["# 方-八纲对应表（56批·指令四）", "",
     "> **性质**：**从胡老方解原语反查出来的索引，不是我方为药物新造的属性表**〔㉒〕。",
     "> 每味只登记**胡老自己怎么说它**；方解未单论者留空标 `[方解未单论]`，不推。",
     "> **口径**：C卷 %d 方／有方解 %d 方；药名（≥2方）%d 味；有原语 %d 味；归槽 %d 味。"
     % (len(fangs), sum(1 for f in fangs if f["jie"][1]), len(HERB), len(rows), len(tab)),
     "> ⚠一药多用照录不合并（麻黄伍桂枝发汗／伍石膏反治汗出）——**行数 > 药数是设计**。", "",
     "| 药 | 状态槽（八纲/三毒） | 胡老方解原语 | 出处 |", "|---|---|---|---|"]
for h in sorted(tab, key=lambda x: -sum(len(v) for v in tab[x].values())):
    for k, rs in tab[h].items():
        r = rs[0]
        L.append("| **%s** | %s | %s | C卷L%d〔%s〕 |" % (h, k, r["sent"][:70], r["line"], r["fang"]))
L += ["", "## ⚠有原语但未归槽（%d 味·逐条备查·视角㉚）" % len(unslot), "",
      "、".join(unslot)]
open(os.path.join(OUT, "附录F_方八纲对应表.md"), "w").write("\n".join(L))
print("\n→ term_layer/附录F_方八纲对应表.md")
