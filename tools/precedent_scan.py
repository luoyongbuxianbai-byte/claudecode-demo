#!/usr/bin/env python3
"""【先例检索】给定「症候组合」，检出胡老实际如何判、用何方（53批·指令三之执行件）。

上级53批：「558 案中，**『便溏且脉有力』者胡老如何判**——此为本案关键先例，
全库检索，报其归经与方。」

⭐**本工具的意义不在这一次查询**：它把「拿一组症候去问胡老实际怎么做」变成**可复跑的动作**。
  R42 已判案例检索为方证层主机制（25.0% vs 规则 3.0%）；**本工具是它的人读接口**。

【已知失效模式】(视角㉕)
  ① **「脉有力」在胡老书中不止一种写法**（有力 99／脉实 29／沉实 13／脉大 25；
     而「按之有力」「沉而有力」**0 命中**）。词表漏一种写法即漏一批案
     〔R41⑪：词表未命中一律不得读作"不存在"〕。→ 故**分档报**：
     `严格`(明写"有力"/"脉实") ／ `宽`(并入"脉大/弦/滑/沉实"等**可能**有力之脉)。
     **两档必须分开报，不得合并**——宽档含推断，严档才是明文。
  ② **「脉大」≠「脉有力」**：〔A·§257 注解「脉浮**大**主热盛」；另有「**大中空**的脉」〕
     ——**大可以中空**。故「大」入宽档并标 `[大≠必有力]`。
  ③ **归经靠案文明写六经名**；无明写者入「未标经」，**不得据方倒推经**
     （倒推即用结论证前提·视角②）。
  ④ 案内可能同时出现「有力」与「无力」（论及鉴别时），**窗口内两者并见者单列存疑**。
  ⑤ 切案口径同 case_retrieve/tier_score；**一案多诊者按整案计一次**。
【弃件条件】案文 <60 字者弃；症候词与脉词相距 >400 字者弃（疑跨案）。
【口径】(视角㊱) 一案＝一个切案区间；「命中」＝案内同时出现症候词与脉词且相距 ≤400 字；
  `python3 tools/precedent_scan.py` 复跑。
"""
import re, os, sys
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
    if n0 and len(T) / n0 < 0.5:
        raise SystemExit("⛔协议16 中止：%s" % fn)
    return T


BOOKS = [("C卷", "C_jingfangliyu.txt"), ("临床家", "ocr_中医临床家胡希恕.txt"),
         ("带教", "ocr_冯世纶带教实录第一辑.txt"), ("传真", "ocr_经方传真系.txt"),
         ("解读", "ocr_解读张仲景医学.txt")]
CASE_START = re.compile(r"【验案】|【检案】|例\s*\d{1,3}[，,、]?[一-鿿]{2,3}[，,]|病案号\s*\d+|"
                        r"[一-鿿]{1,3}某[，,]\s*(?:男|女)(?:性)?[，,]|"
                        r"\d{4}年\d{1,2}月\d{1,2}日初诊|初诊日期\s*\d{4}")
cases = []
for bk, fn in BOOKS:
    T = load(fn)
    if not T: continue
    st = [m.start() for m in CASE_START.finditer(T)]
    for i, s0 in enumerate(st):
        e = st[i + 1] if i + 1 < len(st) else min(len(T), s0 + 2500)
        b = T[s0:e][:2500]
        if len(b) >= 60: cases.append(dict(book=bk, seq=len(cases), body=b))

# ── 查询定义 ─────────────────────────────────────────────────────
SYMPT = ["便溏", "大便溏", "便稀", "大便稀", "溏薄", "下利", "自利", "大便不成形", "微溏"]
# ⛔⛔**首跑事故·本工具自查（㊹批闸门第六次应验）**：初版把「有力」直接当脉象词，
#   得「严档 25 案」——**逐案读后发现绝大多数的「有力」修饰的是药，不是脉**：
#   「加补中**有力**的人参」「水蛭虻虫均为**有力**的祛瘀药」「麻黄汤虽为强**有力**的发汗药」
#   「猪苓为一寒性**有力**的利尿药」「益气固表最**有力**」。
#   实测：五源「有力」共 **62** 次，**前8字含「脉」者仅 16**，
#   而这 16 中还有 **「通脉四逆汤等更为有力」×4 是假阳**（「通**脉**」含脉字）。
#   → **真脉象「有力」全库约 12 处。**
#   ⭐**这本身就是对本次查询最要紧的回答**：**胡老极少用「有力」描述脉**——
#     他的脉力语汇是**脉实／脉弦／脉滑／脉紧／脉大**。**词表错，查什么都查不到。**
PULSE_RX_STRICT = re.compile(r"脉(?!四逆|证)[^。，,；;]{0,6}有力|脉实|实者当下")
PULSE_RX_WIDE = re.compile(r"脉[^。，,；;]{0,4}(?:弦|滑|大|紧|洪|实)")
PULSE_NEG = ["无力", "脉微", "脉细", "微细", "脉弱", "沉细", "细弱"]
JING = ["太阳", "阳明", "少阳", "太阴", "少阴", "厥阴"]
FANG_RX = re.compile(r"([一-鿿]{2,20}(?:汤|散|丸))")
LEAD = re.compile(r"^(?:宜|用|与|予|服|投|拟|方用|治以|治宜|就是|这个|那个|所以|当以|改与|"
                  r"再与|故与|即与|乃与|先与|后与|仍宜|给服|改服|据证与|是|的)+")


def near(body, a_list, rx, dist=400):
    """症候词 与 **脉正则**在案内相距 ≤dist 者判命中。
       ⚠脉侧改用**正则正向识别**（须「脉」字在场），不再用裸词表。"""
    out = []
    for a in a_list:
        for ma in re.finditer(re.escape(a), body):
            for mb in rx.finditer(body):
                if abs(ma.start() - mb.start()) <= dist:
                    out.append((a, mb.group()))
    return out


# ⛔**真医案闸门（本工具第二次自查）**：C卷/传真的**方剂章节**（【方剂组成】【方解】）
#   被 CASE_START 误切为「案」，首跑 25 案中 C卷#9/56/72/85/87/113 全是方剂章节而非医案。
#   → 正向识别：真医案须有**人口学或诊次标记**。
REAL_CASE = re.compile(r"初诊|岁|男|女|病案号|病历号|【验案】|【检案】|复诊|二诊")
def is_case(b):
    if not REAL_CASE.search(b): return False
    if b.count("【方剂组成】") or b.count("【方解】") >= 1: return False
    return True


def fangs(body):
    s = set()
    for f in FANG_RX.findall(body):
        f = LEAD.sub("", f)
        if len(f) >= 3: s.add(f)
    return s


cases = [c for c in cases if is_case(c["body"])]
rows = {"严格·脉+有力/脉实": PULSE_RX_STRICT, "宽·脉弦滑大紧洪实(推断)": PULSE_RX_WIDE}
print("切案 %d（分书 %s）\n" % (len(cases), dict(Counter(c["book"] for c in cases))))
print("═══ 查询：**便溏 ∧ 脉有力** ——「胡老实际怎么判、用何方」═══\n")

detail_all = {}
for label, prx in rows.items():
    hit, jc, fc, both = [], Counter(), Counter(), 0
    for c in cases:
        hs = near(c["body"], SYMPT, prx)
        if not hs: continue
        # ④ 同案内并见反义脉词者单列
        if near(c["body"], SYMPT, re.compile("|".join(PULSE_NEG))):
            both += 1
        js = sorted({j for j in JING if j in c["body"]})
        fs = fangs(c["body"])
        hit.append((c, hs[0], js, fs))
        if js:
            for j in js: jc[j] += 1
        else:
            jc["(未标经)"] += 1
        fc.update(fs)
    detail_all[label] = hit
    print("── %s ── 命中 **%d 案**（其中同案并见虚脉词者 %d 案·存疑）" % (label, len(hit), both))
    print("   归经分布：%s" % ("／".join("%s%d" % (k, v) for k, v in jc.most_common()) or "—"))
    print("   高频方（前12）：%s\n" % ("／".join("%s%d" % (k, v) for k, v in fc.most_common(12)) or "—"))

# ── 严档逐案明细（供人读·上级所要之"先例"）────────────────────
print("═══ 严档逐案明细（明写「有力/脉实」·供人读）═══")
for c, (a, b), js, fs in detail_all["严格·脉+有力/脉实"]:
    i = c["body"].find(b)
    print("〔%s#%d〕经：%s ｜ 方：%s" % (c["book"], c["seq"], "／".join(js) or "(未标)",
                                     "／".join(sorted(fs)[:4]) or "(未解析)"))
    print("    …%s…" % c["body"][max(0, i - 90):i + 60])

# ── ⭐宽档·按经分组逐案（上级所要之「先例」实体）────────────────
print("\n═══ ⭐宽档·按经分组逐案（**便溏 ∧ 脉不弱**·供人读）═══")
byj = defaultdict(list)
for c, (a, b), js, fs in detail_all["宽·脉弦滑大紧洪实(推断)"]:
    for j in (js or ["(未标经)"]): byj[j].append((c, b, fs))
for j in ["太阴", "少阴", "阳明", "少阳", "厥阴", "太阳", "(未标经)"]:
    if j not in byj: continue
    print("\n── 含「%s」%d 案 ──" % (j, len(byj[j])))
    for c, b, fs in byj[j][:4]:
        i = c["body"].find(b)
        print("  〔%s#%d〕脉：**%s** ｜ 方：%s" % (c["book"], c["seq"], b,
              "／".join(sorted(fs)[:3]) or "(未解析)"))
        print("     …%s…" % c["body"][max(0, i - 110):i + 110])

OUT = os.path.join(B, "case_layer", "先例_便溏与脉有力.md")
L = ["# 先例检索：**便溏 ∧ 脉有力**（53批·指令三）", "",
     "> 口径：五源 %d 案；命中＝案内症候词与脉词相距 ≤400 字。" % len(cases),
     "> ⚠**严档＝明写「有力/脉实」；宽档含「大/弦/滑」系推断**——两档分报，不合并。",
     "> ⚠〔A·§257 注解〕「脉浮**大**主热盛」，另有「**大中空**的脉」——**大可以中空，大≠必有力**。", ""]
for label, hit in detail_all.items():
    jc = Counter()
    for c, h, js, fs in hit:
        for j in (js or ["(未标经)"]): jc[j] += 1
    L += ["## %s ── **%d 案**" % (label, len(hit)), "",
          "归经：%s" % ("／".join("%s%d" % (k, v) for k, v in jc.most_common()) or "—"), ""]
    for c, (a, b), js, fs in hit:
        i = c["body"].find(b)
        L += ["- 〔%s#%d〕**经**：%s ｜ **方**：%s" % (c["book"], c["seq"], "／".join(js) or "(未标)",
              "／".join(sorted(fs)[:4]) or "(未解析)"),
              "  > …%s…" % c["body"][max(0, i - 90):i + 60]]
    L.append("")
open(OUT, "w").write("\n".join(L))
print("\n→ case_layer/先例_便溏与脉有力.md")
