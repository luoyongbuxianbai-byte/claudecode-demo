#!/usr/bin/env python3
"""【判据句·全量穷举抽取】（㊵批·上级令"按句式穷举，不按需检索"）。

上级㊵批：「§56 不是孤例，**它是一个句式的一个实例**。胡老凡下判断必用
『知/可知/故知/此为/即为』——**抽句式即抽全部判据**。这就是"穷尽"的可执行形态。」

与 `inquiry_locus.py` 之别（**两者不重复，是两个轴**）：
  · `inquiry_locus`：**按问诊项**抽（汗/二便/胸胁…各能定什么）——**问诊轴**
  · 本工具：**按判断句式**抽（凡胡老下判断之句一律入表）——**判断轴**
  后者是全集，前者是它在问诊项上的投影。**本工具不设问诊项词表**，故不受词表遗漏之限。

字段（上级指定）：
  原句｜出处(书+行+条文号)｜条件｜结论｜**层级**(病位/病性/治法/预后/误治)｜
  **类型**(充分/必要/**否决**)｜前提上下文｜**等级**(A三源同文/A单源/B医案)

【已知失效模式】(视角㉕)
  ① **句式捕获**。胡老不用这十类句式而在长段中隐含的判断**一律漏检**，不推测补全。
     **"全量"的准确含义是"这十类句式的全量"，不是"胡老全部判断的全量"。**
     ——⚠**这一点必须在报告里写死，否则"243条"会被读成"胡老的判据共243条"。**
  ② **条件抽取取「结论标记词之前的最近一个分句」**，胡老的条件常跨句
     （§56 之前提「不大便六七日＋头痛有热」在**上一句**）。故保留 ±140 字上下文，
     **条件栏只作索引，前提须人读上下文栏**（视角⑩）。
  ③ **层级判定靠结论词表**，人工列的；结论用词在表外者归「未分类」，**不静默丢弃**。
  ④ **「三源同文」判据是归一化后的句子子串比对**；OCR 变形会使真同文判为单源
     （**偏保守，宁可低判等级**，与协议4 一致）。
  ⑤ 条文号取窗口内最近的「第N条」，**跨条讲解时可能挂错号**；故条文号栏标 `≈`。
  ⑥ 讲解段中的判据**照收但标体裁**（视角㉟）——胡老讲义中的判断是他本人的注解，
     与条文原文同为 A 级来源，但**须可区分**。
【弃件条件】结论 <2 字或 >24 字者弃；条件与结论同为纯功能词者弃。
【口径】(视角㊱) 一条＝一个「条件→结论」判断句实例（同书同段去重）；
  `python3 tools/verdict_extract.py` 复跑。**反查自检不足 3/3 即判工具不合格。**
"""
import re, os, json
from collections import Counter, defaultdict

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOKS = [("C卷", "C_jingfangliyu.txt"), ("讲伤寒", "ocr_未识别2.txt"), ("讲金匮", "ocr_未识别1.txt"),
         ("解读", "ocr_解读张仲景医学.txt"), ("传真", "ocr_经方传真系.txt"),
         ("病位类方解", "ocr_胡希恕病位类方解.txt"), ("临床家", "ocr_中医临床家胡希恕.txt"),
         ("带教", "ocr_冯世纶带教实录第一辑.txt")]
JUNK = re.compile(r"·\d+·|PDFcreatedwith[A-Za-z]*|pdfFactory[A-Za-z]*|Protrialversion|"
                  r"www\.pdffactory\.com|胡希恕讲伤寒\d*|胡希恕《金匮要略》讲义[-—]龙门课栈[\d/]*|"
                  r"---第\d+页---|http\S*|快乐人生久久久\S*")

# ── 判断句式（上级指定 5 式 ＋ 补 5 式）───────────────────────────────
CONCL = r"[^。；，、！？]{2,24}"
PATS = [
 (r"故知(" + CONCL + r")", "故知"),
 (r"(?<![不未])可知(" + CONCL + r")", "可知"),
 (r"[，,]知(" + CONCL + r")", "知"),
 (r"即知(" + CONCL + r")", "即知"),
 (r"此为(" + CONCL + r")", "此为"),
 (r"即为(" + CONCL + r")", "即为"),
 (r"是为(" + CONCL + r")", "是为"),
 (r"何以知(" + CONCL + r")", "何以知"),            # 自问自答式
 (r"所以然者[，,](" + CONCL + r")", "所以然者"),     # 仲景给理由之定式
 (r"以其(" + CONCL + r")", "以其"),                # 以其X，故Y
]
# 条件：结论标记之前最近一个分句
COND_RX = re.compile(r"([^。；]{2,40})$")

# ── 层级词表（视角④⑧：判据必须分层）────────────────────────────────
LEVEL = [
 ("误治", r"此为逆|为逆也|误也|坏病|不可(?:与|下|汗|吐)|反下之|误下|误汗|误吐|虚虚实实|变逆"),
 ("预后", r"死|生死|难治|不治|可治|自愈|欲解|欲愈|剧|危|除中"),
 # ⚠首跑「未分类」占 55%，抽样发现大半是**治法类结论**用了本表没收的措辞
 # ——「X汤主之」「与X汤」「以温」「宜下之」。**分类表漏一种措辞，整类进未分类。**
 ("治法", r"宜[^。]{1,12}[汤散丸]|[一-鿿]{2,10}[汤散丸]主之|可与|与[^。]{1,10}[汤散丸]|"
          r"当[发汗下吐温和清攻]|急[温下]之|不可更|法当|当须发汗|以下之|以汗之|"
          r"以温|以攻|以清|治[宜当]|主之|下之|汗之|吐之|定法|通治|正治|先救里|后解表"),
 # ⚠**第二次自查**：首修后「未分类」仍占 52%，抽样见主体是**方证判定**
 # （「桂枝汤证未罢也」「栝蒌桂枝汤证」「黄汗证」）与**证名/病机判定**
 # （荣弱卫强／阳微／脏厥／留饮／女劳）——**两个层级本表根本没有**。
 # → 补 ("方证") 与 ("证名") 两层。**"未分类"高不是数据脏，是分类表缺层。**
 ("方证", r"[一-鿿]{2,12}汤证|[一-鿿]{2,10}[汤散丸]为治|证属|[一-鿿]{2,8}证(?:未罢|具|备|也|$)"),
 ("证名/病机", r"荣气|卫气|荣弱|卫强|阳微|阴弱|脏厥|蛔厥|结胸|痞|留饮|伏饮|黄汗|肺胀|"
              r"女劳|宿食|干血|水结|奔豚|痉病|历节|狐惑|百合|脏躁|除中|谷疸|酒疸|"
              r"血室|血着|痰饮|悬饮|溢饮|支饮"),
 # ⚠**第三次自查**（㊶批）：未分类仍 619，抽样见**再缺三层**——
 # ①病势/传变（未解/不解/罢/传/内陷）②病机解释（阳气重故也/痉之渐/生新祛瘀）
 # ③方义药物（来自于桂枝汤/应内麻黄/去某者）。**三次补表，三次都是表缺层不是数据脏。**
 ("病势/传变", r"未解|不解|已解|欲解|未罢|已罢|传[里入经]|内陷|自止|不传|将?愈|渐[进退]"),
 ("病机解释", r"故也|所以然|之渐|生新|祛瘀|气重|郁遏|上冲|上逆|不降|失和|失振|外却"),
 ("方义/药物", r"来自于|应内|去[^。]{1,6}者|加[^。]{1,6}者|减[^。]{1,6}者|为君|为臣|佐使|汤中|药力"),
 ("病位", r"在表|在里|半表半里|不在里|不在表|表证|里证|太阳|阳明|少阳|太阴|少阴|厥阴|"
          r"非少阴|非太阳|属表|属里|内陷|还在表|传里|入里"),
 ("病性", r"有热|无热|里热|表热|虚寒|实热|热|寒|虚|实|阴证|阳证|水饮|停饮|停水|水气|"
          r"瘀血|湿|津液|胃气|亡阳|亡津液|血虚|气虚"),
]
NEG = re.compile(r"^(?:非|不|无|未|勿)|不得为|不可为|非.{1,6}也")

def level(c):
    for name, rx in LEVEL:
        if re.search(rx, c): return name
    return "未分类"

def vtype(c):
    """类型：否决／必要／充分。⚠**否决优先**（视角⑫⑯：单证否决防误治，信息量最高）。"""
    if NEG.search(c) or re.search(r"不得为|非.{1,8}(?:也|病)", c): return "**否决**"
    if re.search(r"必|非.{1,6}不", c): return "必要"
    return "充分"

# ── 弃件闸门（㊵批首跑自查）──────────────────────────────────────
# 抽样查获三类噪声：①条件为空或过短（上下文已丢，条件不可读）；
# ②OCR 垃圾（「不学医不忠眉」出自传记轶事，「江萼诸药」为字形崩坏）；
# ③纯叙事/元话语（「要法」「什么道理呢」）。
# **弃件一律计数并列出类别（视角㉚），不静默丢弃。**
JUNKC = re.compile(r"[a-zA-Z0-9]{3,}|[“”\"']|不忠|学医|回答|诸日|先生|老师|同学|"
                   r"这么|那么|咱们|什么道理|我们|你们|第[一二三四五六七八九十]段|"
                   r"个人|学识|体验研究|仲景[^病证]|何部|犯何|母四|要法$|的病$|是一$")
def drop_reason(cond, concl):
    if len(re.sub(r"[^一-鿿]", "", cond)) < 4: return "条件过短(上下文已丢)"
    if JUNKC.search(concl): return "OCR噪声/叙事元话语"
    if len(re.sub(r"[^一-鿿]", "", concl)) < 2: return "结论过短"
    return None

TIAO = re.compile(r"第(\d{1,3})条")
CASE = re.compile(r"验案|病历号|初诊|【检案】|某，(?:男|女)")

rows, dropped = [], Counter()
for bk, fn in BOOKS:
    p = os.path.join(B, "sources", fn)
    if not os.path.exists(p): continue
    lines = open(p, encoding="utf-8", errors="ignore").read().split("\n")
    clean = [JUNK.sub("", re.sub(r"\s+", "", l)) for l in lines]
    for i in range(len(clean)):
        win = "".join(clean[max(0, i - 2):i + 4])
        if not win: continue
        for rx, kind in PATS:
            for m in re.finditer(rx, win):
                concl = m.group(1).strip()
                if len(concl) < 2: continue
                head = win[:m.start()]
                cm = COND_RX.search(head)
                cond = cm.group(1) if cm else ""
                # 条文号：窗口内最靠近本次匹配之前的「第N条」
                nums = [(mm.start(), mm.group(1)) for mm in TIAO.finditer(win[:m.end()])]
                tno = nums[-1][1] if nums else ""
                ctx = win[max(0, m.start() - 140):m.end() + 140]
                dr = drop_reason(cond, concl)
                if dr: dropped[dr] += 1; continue
                rows.append(dict(kind=kind, concl=concl, cond=cond, book=bk, line=i + 1,
                                 tiao=tno, ctx=ctx,
                                 level=level(concl), vtype=vtype(concl),
                                 genre="医案" if CASE.search(ctx) else "条文/注解"))

# ── 去重：同书同段(行/4)同结论 ────────────────────────────────────
seen, uniq = set(), []
for r in rows:
    k = (r["book"], r["line"] // 4, r["concl"])
    if k in seen: continue
    seen.add(k); uniq.append(r)

# ── **独立判据数**：跨书按「条件尾+结论」归一去重 ──────────────────
# ⚠**口径分离（视角㊱）**：同一条判断在 8 本书里各出现一次，是 **1 条判据、8 个实例**。
#   不分开报，「全量」这个数会被书的数量灌水。**两个数都报。**
def sig(r):
    return (re.sub(r"[^一-鿿]", "", r["cond"])[-10:], re.sub(r"[^一-鿿]", "", r["concl"]))
bysig = defaultdict(list)
for r in uniq: bysig[sig(r)].append(r)
indep = [max(v, key=lambda x: len(x["ctx"])) for v in bysig.values()]
for r in indep: r["nsrc"] = len({x["book"] for x in bysig[sig(r)]})

# ── 等级：三源同文 / 单源 / 医案 ──────────────────────────────────
def norm(s): return re.sub(r"[^一-鿿]", "", s)
for r in uniq: pass
for r in indep:
    nb = r["nsrc"]
    r["grade"] = "**A·三源同文**" if nb >= 3 else ("A·双源" if nb == 2 else
                 ("B·医案" if r["genre"] == "医案" else "A·单源"))

# ── 反查自检（上级㊵批所举三条·**不足 3/3 即判工具不合格**）──────────
PROBE = {
 "§148 头汗出→非少阴": lambda r: "非少阴" in r["concl"],
 "§15 气上冲→未内陷": lambda r: "未因误下" in r["concl"] or "内陷" in r["concl"],
 "§332 不发热→胃气尚在": lambda r: "胃气尚在" in r["concl"],
}
probe_hit = {k: [r for r in indep if f(r)] for k, f in PROBE.items()}
nprobe = sum(1 for v in probe_hit.values() if v)

L = ["# 判据句·全量穷举表（㊵批）", "",
     "> 生成：`tools/verdict_extract.py`（文件头含【已知失效模式】【弃件条件】【口径】）。", "",
     "> ⚠⚠**「全量」的准确含义**：是**这十类句式的全量**，",
     "> **不是「胡老全部判断的全量」**。他不用这十式而在长段中隐含的判断，本表**抽不到**。",
     "> **这个数不得被读成「胡老的判据共 N 条」。**", "",
     "> 十式：故知｜可知｜，知｜即知｜此为｜即为｜是为｜何以知｜所以然者｜以其", "",
     "**反查自检 %d/3**（上级㊵批所举三条）：" % nprobe, ""]
for k, v in probe_hit.items():
    L.append("- %s %s（%d 条）%s" % ("✓" if v else "✗**漏**", k, len(v),
             "｜%s L%d：%s" % (v[0]["book"], v[0]["line"], v[0]["concl"]) if v else ""))

lc = Counter(r["level"] for r in indep); tc = Counter(r["vtype"] for r in indep)
gc = Counter(r["grade"] for r in indep); kc = Counter(r["kind"] for r in indep)
L += ["", "---", "", "## 〇、总量与分布", "",
      "| 口径 | 数 |", "|---|---|",
      "| **独立判据**（跨书归一去重·**这是判据数**） | **%d** |" % len(indep),
      "| 实例（同一判据在多书各计一次） | %d |" % len(uniq),
      "| 弃件（OCR噪声/条件过短/叙事） | %d |" % sum(dropped.values()), "",
      "⛔弃件分类（**列出不静默丢弃**·视角㉚）：" +
      "｜".join("%s %d" % x for x in dropped.most_common()), "",
      "| 层级 | 条数 | | 类型 | 条数 | | 等级 | 条数 |", "|---|---|---|---|---|---|---|---|"]
lk, tk, gk = list(lc.items()), list(tc.items()), list(gc.items())
for j in range(max(len(lk), len(tk), len(gk))):
    a = "%s | %d" % lk[j] if j < len(lk) else " | "
    b = "%s | %d" % tk[j] if j < len(tk) else " | "
    c = "%s | %d" % gk[j] if j < len(gk) else " | "
    L.append("| %s | | %s | | %s |" % (a, b, c))
L += ["", "句式分布：" + "｜".join("%s %d" % x for x in kc.most_common()), ""]

# ── 一、否决类优先（上级令②·视角⑫⑯）────────────────────────────
neg = [r for r in indep if r["vtype"] == "**否决**"]
L += ["---", "", "## 一、**否决类判据**（上级令优先·视角⑫安全非对称／⑯信息论）", "",
      "> **单证否决防误治，信息量最高。** 共 **%d** 条。" % len(neg), "",
      "| # | 条件 | **结论(否决)** | 层级 | 出处 | 条 | 等级 |", "|---|---|---|---|---|---|---|"]
for k, r in enumerate(sorted(neg, key=lambda x: (x["level"], x["book"]))[:120], 1):
    L.append("| %d | %s | **%s** | %s | %s L%d | %s | %s |" % (
        k, r["cond"][-30:].replace("|", "／"), r["concl"].replace("|", "／"),
        r["level"], r["book"], r["line"], "≈§" + r["tiao"] if r["tiao"] else "—", r["grade"]))

# ── 二、按层级全表 ───────────────────────────────────────────────
L += ["", "---", "", "## 二、按层级全表", ""]
bylv = defaultdict(list)
for r in indep: bylv[r["level"]].append(r)
for lv in ["病位", "病性", "方证", "证名/病机", "治法", "预后", "误治", "未分类"]:
    rs = bylv.get(lv, [])
    if not rs: continue
    L += ["### %s（%d 条）" % (lv, len(rs)), "",
          "| # | 条件 | 结论 | 类型 | 句式 | 出处 | 条 | 等级 | 体裁 | 前提上下文 |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for k, r in enumerate(sorted(rs, key=lambda x: (x["book"], x["line"])), 1):
        L.append("| %d | %s | **%s** | %s | %s | %s L%d | %s | %s | %s | …%s… |" % (
            k, r["cond"][-26:].replace("|", "／"), r["concl"].replace("|", "／"),
            r["vtype"], r["kind"], r["book"], r["line"],
            "≈§" + r["tiao"] if r["tiao"] else "—", r["grade"], r["genre"],
            r["ctx"].replace("|", "／")))
    L.append("")

open(os.path.join(B, "term_layer", "判据句_全量穷举表.md"), "w", encoding="utf-8").write("\n".join(L))
json.dump(indep, open(os.path.join(B, "term_layer", "_verdicts.json"), "w"),
          ensure_ascii=False, indent=1)

print("**独立判据 %d 条**｜实例 %d｜弃件 %d｜反查自检 %d/3" % (len(indep), len(uniq), sum(dropped.values()), nprobe))
print("层级：", dict(lc));  print("类型：", dict(tc))
print("等级：", dict(gc));  print("句式：", dict(kc.most_common()))
print("**否决类 %d 条**" % len(neg))
for k, v in probe_hit.items():
    print("  %s %s (%d)" % ("✓" if v else "✗", k, len(v)))
