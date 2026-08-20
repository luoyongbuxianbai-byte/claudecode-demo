#!/usr/bin/env python3
"""【复现率评测】＋【转方对·方证鉴别实证表】＋【舌轴按书分层】＋【人读金标准抽样】（㊺批）。

上级㊺批全部采纳㊹批四条建议，按建议排序下任务。本工具承任务 1/2/3/4。

## 一、复现率（任务1·上级"数字难看照报"）
  **可达率**＝该步所需判据在引擎内可查到（㊹批 66.8%）。
  **复现率**＝**引擎按 R31 三步实跑，能否得出与胡老相同的经/方**。
  ⚠**这是第一个真指标**，也是第一个**可以失败**的指标。
  [口径·冻结]三步机械跑：
    第一步 六提纲 token 匹配 → 候选经；第二步 表/里闭合排除 → 余集；
    第三步 在候选经内比方证★ → 首选方。
    **命中判定**：经命中＝引擎候选经含胡老所判之经；方命中＝引擎首选方＝胡老所用方。
  ⚠**本评测的已知不公平处（必须写在前面）**：
    ① 引擎的方证★多为**条文摘句**，而医案是**现代白话病历**，词面本就对不上；
    ② 医案常为**合方/加味**，引擎首选只出一方 → 合方案几乎必然判不中；
    ③ 三步跑的是**机械匹配**，不含 LLM 的语义理解——
       **这测的是「引擎规则单独能走多远」，不是「引擎+模型能走多远」。**
    → **故复现率低不等于引擎无用**（见上级㊺批定位：引擎应作**外挂闸门**非生成器）。

## 二、转方对（任务2·上级称"本批最深"）
  「**A方效/无效 → 改B方**」＝**天然对照实验**（视角⑥因果／⑭反事实）。
  这是方证鉴别**最硬的数据**：同一病人、同一时点前后，只有方变了。

## 三、舌轴按书分层（任务3·㊹批已知未验项）
  ㊹批「苔白无分辨力」是 558 案合并统计。**须按书分层重测**，
  排除体裁效应（C卷记舌详／讲义类记舌略）后方可启用。

【已知失效模式】(视角㉕)
  ① 复现率之三步匹配是**词面匹配**，非语义。**它的失败有两种：引擎没有该判据（真缺口）
     ／引擎有但词面对不上（术语关）**——本工具**分开计**，不合并。
  ② 转方对靠「无效/不效/未效/症不减/改与/再与/转方」等词。胡老不用这些词而
     直接写「二诊…与X汤」者，**只能判为"转方但效否不明"**，单列。
  ③ 舌分层后各书样本骤减，**n<20 者一律标样本不足**，不下结论。
  ④ 金标准抽样只做**抽样与字段模板**，**人工标注本工具做不了**——如实标"待人读"。
【弃件条件】案文无方名者不入复现率分母。
【口径】(视角㊱) 复现率分母＝有明确「经或方」记载之案；`python3 tools/reproduce_eval.py` 复跑。
"""
import re, os, json, random
from collections import Counter, defaultdict

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JUNK = re.compile(r"·\d+·|PDFcreatedwith[A-Za-z]*|pdfFactory[A-Za-z]*|Protrialversion|"
                  r"www\.pdffactory\.com|胡希恕讲伤寒\d*|---第\d+页---|http\S*|快乐人生久久\S*")
def load(fn):
    """协议16：逐行清洗＋降幅告警。"""
    p = os.path.join(B, "sources", fn)
    if not os.path.exists(p): return ""
    raw = open(p, encoding="utf-8", errors="ignore").read()
    n0 = len(re.sub(r"\s+", "", raw))
    T = "".join(JUNK.sub("", re.sub(r"\s+", "", ln)) for ln in raw.split("\n"))
    if n0 and len(T) / n0 < 0.5:
        raise SystemExit("⛔协议16 中止：%s 降幅 %.0f%%" % (fn, 100 * (1 - len(T) / n0)))
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
        if len(b) >= 60: cases.append(dict(book=bk, body=b))

# ── 方名归一（沿用 ㊹批表）──────────────────────────────────────
FANG_LEAD = re.compile(r"^(?:仍宜以|但其有典型的|一肢本例症状就能判定为|据证与|故胡老常以|"
                       r"而胡老用|表实的|表虚的|营卫失和之|此于|再以|为|与|予|用|以|服|改服|"
                       r"给服|先与|后改|后与|故予|故与|改与|再与|投|拟|处|方用|治以|治用|"
                       r"方拟|即与|乃与|遂与|宜|加|合)+")
FANG_OCR = {"小标胡": "小柴胡", "小标朐": "小柴胡", "小业胡": "小柴胡", "大标胡": "大柴胡",
            "大柏胡": "大柴胡", "标胡": "柴胡", "柏胡": "柴胡", "柴朐": "柴胡", "朐汤": "胡汤",
            "桂栗汤": "桂枝汤", "桂栗": "桂枝", "柠技": "桂枝", "桂枫": "桂枝",
            "麻杳石甘": "麻杏石甘", "麻杳": "麻杏", "生石贾": "生石膏", "生石青": "生石膏",
            "石贾": "石膏", "石青": "石膏", "射一麻黄": "射干麻黄", "半夏厚私": "半夏厚朴",
            "厚私": "厚朴", "莞英丸": "苓丸", "五陂": "五味", "知毋": "知母",
            "虞黄丙": "黄芪", "黄丙": "黄芪", "莞苓饮": "茯苓饮", "茯莎丸": "茯苓丸",
            "茯莎": "茯苓", "当当芍药": "当归芍药", "荞桂术甘": "苓桂术甘",
            "半东厚杨江": "半夏厚朴汤", "厚杨": "厚朴", "半东": "半夏", "阳子梗米": "附子粳米"}
def fnorm(f):
    f = FANG_LEAD.sub("", f)
    for a, b2 in FANG_OCR.items(): f = f.replace(a, b2)
    return f
FANG_RX = re.compile(r"([一-鿿]{2,14}(?:汤|散|丸))")

# ── 引擎侧：六提纲 token ＋ 方证★ ────────────────────────────────
E = re.sub(r"\s+", "", open(os.path.join(B, "hxs_engine_v79_full.md"), encoding="utf-8").read())
TIGANG = {   # R31 第一步：六提纲原文项（视角㉒：用胡老提纲原词，不自造）
 "太阳": ["脉浮", "头项强痛", "恶寒", "恶风"],
 "阳明": ["胃家实", "不恶寒反恶热", "自汗出", "潮热", "大便硬", "腹满痛", "谵语"],
 "少阳": ["口苦", "咽干", "目眩", "往来寒热", "胸胁苦满", "心烦喜呕", "默默不欲饮食",
          "嘿嘿不欲饮食"],
 "太阴": ["腹满而吐", "食不下", "自利", "腹自痛", "下利", "便溏", "大便溏"],
 "少阴": ["脉微细", "但欲寐"],
 "厥阴": ["消渴", "气上撞心", "心中疼热", "饥而不欲食", "食则吐蛔"],
}
BIAO = ["恶寒", "恶风", "脉浮", "无汗", "身疼痛", "头项强痛", "浮肿"]
LI = ["下利", "自利", "便溏", "大便硬", "不大便", "腹满", "干呕", "呕吐", "纳差", "不欲食"]
# 引擎方证★（标题行的 ★…★）
STAR = {}
for m in re.finditer(r"【([一-鿿·§\d/加()（）]{2,26})】[^★\n]{0,40}★([^★]{2,60})★", E):
    nm = re.sub(r"·.*$", "", m.group(1))
    STAR.setdefault(nm, m.group(2))
ENG_FANG = set(STAR) | set(re.findall(r"【([一-鿿]{2,14}(?:汤|散|丸))", E))
# 核心方名（供合方/加味名之包含判定）：库内方名去掉剂型尾后 ≥2 字者
CORE = {re.sub(r"[汤散丸]$", "", x) for x in ENG_FANG}
CORE = {x for x in CORE if len(x) >= 3}

def run_r31(body):
    """R31 三步机械跑。**词面匹配，不含语义理解。**"""
    # 第一步·提纲判经
    cand = {j: sum(1 for t in ts if t in body) for j, ts in TIGANG.items()}
    step1 = {j for j, n in cand.items() if n > 0}
    # 第二步·排除法（表/里 是否闭合）
    hb = any(w in body for w in BIAO); hl = any(w in body for w in LI)
    step2 = "表里皆现" if (hb and hl) else ("仅表" if hb else ("仅里" if hl else "皆未现"))
    # 第三步·方证★ 在候选经内比（本工具不分经，直接全库比★覆盖度）
    best, bs = None, 0
    for nm, star in STAR.items():
        toks = [t for t in re.split(r"[+/／、,，]", star) if len(re.sub(r"[^一-鿿]", "", t)) >= 2]
        if not toks: continue
        hit = sum(1 for t in toks if re.sub(r"[^一-鿿]", "", t)[:4] in body)
        sc = hit / len(toks)
        if sc > bs: best, bs = nm, sc
    return step1, step2, best, bs

LOC_RX = re.compile(r"(太阳|阳明|少阳|太阴|少阴|厥阴)")
rows = []
for c in cases:
    b = c["body"]
    真经 = set(LOC_RX.findall(b))
    真方 = {fnorm(x) for x in FANG_RX.findall(b)}
    真方 = {x for x in 真方 if len(x) >= 3}
    if not 真经 and not 真方: continue
    s1, s2, best, bs = run_r31(b)
    jing_ok = bool(真经 & s1) if 真经 else None
    fang_ok = (best in 真方) if (真方 and best) else None
    # 失败归因：引擎有该方(词面对不上) vs 引擎根本没有该方(真缺口)
    why = ""
    if fang_ok is False:
        why = "**术语关**(方在库,词面未匹中)" if (真方 & ENG_FANG) else "**真缺口**(方不在库)"
    rows.append(dict(book=c["book"], 真经=sorted(真经), 真方=sorted(真方)[:3],
                     引擎经=sorted(s1), 引擎方=best, score=round(bs, 2),
                     step2=s2, jing_ok=jing_ok, fang_ok=fang_ok, why=why))

jd = [r for r in rows if r["jing_ok"] is not None]
fd = [r for r in rows if r["fang_ok"] is not None]
jing_rate = 100.0 * sum(1 for r in jd if r["jing_ok"]) / max(1, len(jd))
fang_rate = 100.0 * sum(1 for r in fd if r["fang_ok"]) / max(1, len(fd))
whycnt = Counter(r["why"] for r in rows if r["why"])

# ── 二、转方对 ──────────────────────────────────────────────────
EFF = r"(?:无效|不效|未效|罔效|无明显疗效|症不减|不见好转|反加重|加重|未见)"
OK = r"(?:效|症减|好转|诸症减|已|愈|痊|明显好转)"
# ⚠**首跑事故**：初版要求「A方…效否…改B方」**在同一句内**（`[^。]`）完成，
#   只抽出 15 对；而 91% 的案有疗程反应记载。**医案里 A 方与 B 方常隔数句**
#   （「与桂枝汤三剂。二诊：症未减。……改与小柴胡汤」）。
#   → 放宽为**跨句窗口**（≤260 字，允许句号），并补「二诊/复诊/再诊」式转折。
#   **「同句内完成」是条文的写法，不是医案的写法**——又一次拿条文的形状去套医案。
PAIR = re.compile(r"([一-鿿]{2,14}(?:汤|散|丸))[\s\S]{0,120}?(%s|%s)[\s\S]{0,140}?"
                  r"(?:改|再|转|又|后|遂|乃|二诊|复诊|三诊|上方|继)[\s\S]{0,20}?"
                  r"([一-鿿]{2,14}(?:汤|散|丸))" % (EFF, OK))
pairs = []
for c in cases:
    for m in PAIR.finditer(c["body"]):
        a, r_, b2 = fnorm(m.group(1)), m.group(2), fnorm(m.group(3))
        # ⚠**转方对须两端都是引擎在库之方**：否则会混入「四环素及中药汤」（非方名）、
        #   「于桂枝甘草汤」（方解句非转方）等噪声。**A/B 皆须在库，方成对照。**
        if a == b2 or len(a) < 3 or len(b2) < 3: continue
        # ⚠**二次修**：初版要求方名**整名在库**，把合方/加味名（「小柴胡加生石膏合
        #   半夏厚朴汤」）全滤掉，244→24 且无效对归零。**医案之方多为合方加味，
        #   整名匹配是拿单方的形状去套合方。** → 改为「**含库内某方名**」即可。
        if not (any(k in a for k in CORE) and any(k in b2 for k in CORE)): continue
        eff = "**无效**" if re.fullmatch(EFF, r_) else "有效"
        pairs.append(dict(book=c["book"], A=a, eff=eff, Bf=b2, r=r_,
                          ctx=m.group(0)[:150]))
# ⛔⛔[**转方对之形状错误·本批第三次自查**]
#   「A方 → 无效 → B方」这个形状**抓不住医案里最有价值的那一类**：
#   **前医无效那一侧常常没有方名**——「曾服中药10余剂不效」「服复方硝酸甘油、
#   氨茶碱等无效」「屡治无效」。要求两端都有方名，等于把 220 例误治史全滤掉。
#   → 真正抓得住的是**三元组**：`无效史 → 胡老之证判 → 胡老之方`。
#   **它比转方对更有价值：它告诉我们胡老看见了别人没看见的什么。**
#   [实测]含前医治疗史之案 **220（39%）**；含胡老自己二诊/复诊之案 **485（87%）**；
#   两者兼有 192。**这是两类不同的对照，不得合并**（视角⑧层级）：
#     · 前医无效→胡老 ＝ **误治-救逆对**（视角⑭反事实）；
#     · 胡老一诊→二诊 ＝ **同一医家的方证细分**（视角⑥因果）。
TRIPLE = re.compile(
    r"(前医|曾服|已服|久治不效|屡治|经治不效|多方治疗|中西药|服[^。]{0,20}?)"
    r"[\s\S]{0,100}?(无效|不效|未效|不见好转|反加重|症不减|未见明显疗效)"
    r"[\s\S]{0,160}?"
    r"((?:此|证属|辨为|此为|据证)[^。]{2,40})?"
    r"[\s\S]{0,60}?(?:与|予|改与|投|方用|拟|治以[^。]{0,10}?与)"
    r"([一-鿿]{2,20}(?:汤|散|丸))")
triples = []
for c in cases:
    for m in TRIPLE.finditer(c["body"]):
        triples.append(dict(book=c["book"], hist=m.group(1)[:16], eff=m.group(2),
                            basis=(m.group(3) or "⛔未述依据")[:40],
                            fang=fnorm(m.group(4)), ctx=m.group(0)[:190]))
tseen, utriples = set(), []
for t in triples:
    k = (t["book"], t["fang"], t["basis"][:12])
    if k in tseen: continue
    tseen.add(k); utriples.append(t)
n_hist = sum(1 for c in cases if re.search(r"前医|曾服|已服|久治不效|屡治|经治不效|多方治疗|中西药", c["body"]))
n_self = sum(1 for c in cases if re.search(r"二诊|复诊|三诊|上方|继服", c["body"]))

seen, upairs = set(), []
for p in pairs:
    k = (p["A"], p["Bf"], p["eff"])
    if k in seen: continue
    seen.add(k); upairs.append(p)
neg_pairs = [p for p in upairs if p["eff"] == "**无效**"]
pc = Counter((p["A"], p["Bf"]) for p in neg_pairs)

# ── 三、舌轴按书分层 ────────────────────────────────────────────
SHE = {"苔白": r"苔白(?!腻)", "苔腻": r"苔.{0,2}腻", "舌红": r"舌[质尖]?红",
       "舌淡": r"舌[质]?淡", "舌暗/紫": r"舌[质]?[暗紫]|瘀斑", "苔黄": r"苔黄"}
# ⛔⛔[**㊺批推翻㊹批「苔白无分辨力」之结论·根因是我的词表**]
#   ㊹批病性词表含 `"虚": r"(?<!实)虚(?!寒)"` 与 `"实": r"实(?!热)"` **两个泛词**
#   ——「虚弱」「实际」「确实」在案文里到处都是，把它们计入后，
#   苔白的分布看起来是「虚153/实123/水饮120」**三向均匀**，于是我判「无分辨力」。
#   **去掉这两个泛词后，苔白在全部五本书里一致指向「水饮/湿」**：
#   C卷28/47｜临床家18/53｜带教15/37｜传真28/36｜解读31/48。
#   → **这是跨书一致的方向，不是体裁效应。㊹批那条硬规则须撤。**
#   **第五次「诊断出的结论其实是我的工具」。**
NAT = {"寒/虚寒": r"虚寒|里寒|阳虚", "热": r"里热|实热|郁热", "水饮/湿": r"水饮|停饮|痰饮|水气|湿",
       "瘀血": r"瘀血"}
strat = []
for name, rx in SHE.items():
    for bk, _ in BOOKS:
        sub = [c["body"] for c in cases if c["book"] == bk and re.search(rx, c["body"])]
        if len(sub) < 20:
            strat.append((name, bk, len(sub), "样本不足", "")); continue
        nat = {k: sum(1 for x in sub if re.search(v, x)) for k, v in NAT.items()}
        top = sorted(nat.items(), key=lambda x: -x[1])
        spread = (top[0][1] - top[-1][1]) / max(1, len(sub))
        strat.append((name, bk, len(sub), "**有方向**" if spread >= 0.25 else "无方向",
                      "／".join("%s%d" % x for x in top[:3])))

# ── 四、人读金标准抽样 ──────────────────────────────────────────
random.seed(20260821)
gold = random.sample(cases, 30)

L = ["# 复现率 ／ 转方对 ／ 舌轴分层 ／ 金标准抽样（㊺批）", "",
     "> 生成：`tools/reproduce_eval.py`（文件头含【已知失效模式】【弃件条件】【口径】）。", "",
     "---", "", "## 一、⭐**复现率**（第一个可以失败的真指标）", "",
     "> **可达率**＝判据可查到（㊹批 66.8%）｜**复现率**＝**引擎按 R31 三步实跑能否得同答案**。", "",
     "⚠**本评测的已知不公平处（必须先说）**：",
     "> ① 引擎方证★多为**条文摘句**，医案是**现代白话病历**，词面本就对不上；",
     "> ② 医案常为**合方/加味**，引擎首选只出一方 → 合方案几乎必然判不中；",
     "> ③ 三步是**机械词面匹配，不含语义理解**——",
     "> **这测的是「引擎规则单独能走多远」，不是「引擎＋模型能走多远」。**", "",
     "| 指标 | 分母 | 命中 | **复现率** |", "|---|---|---|---|",
     "| **定经**（引擎候选经含胡老所判之经） | %d | %d | **%.1f%%** |" % (
         len(jd), sum(1 for r in jd if r["jing_ok"]), jing_rate),
     "| **定方**（引擎首选方＝胡老所用方） | %d | %d | **%.1f%%** |" % (
         len(fd), sum(1 for r in fd if r["fang_ok"]), fang_rate), "",
     "**定方失败之归因（分开计，不合并）：**", ""]
for k, v in whycnt.most_common():
    L.append("- %s：**%d** 例" % (k, v))
L += ["", "---", "", "## 二、⭐**转方对·方证鉴别实证表**（上级称「本批最深」）", "",
      "> 「**A方无效 → 改B方**」＝**天然对照实验**：同一病人、同一时点前后，**只有方变了**。",
      "> **这是方证鉴别最硬的数据，比任何条文对比都硬。**", "",
      "**共抽出转方对 %d 个（去重），其中 A方明确无效者 %d 个。**" % (len(upairs), len(neg_pairs)), "",
      "### ⭐A方无效 → B方（**方证鉴别之直接证据**）", "",
      "| # | A方(无效) | → | B方 | 出处 | 原文 |", "|---|---|---|---|---|---|"]
for i, p in enumerate(neg_pairs[:60], 1):
    L.append("| %d | **%s** | → | **%s** | %s | %s |" % (
        i, p["A"], p["Bf"], p["book"], p["ctx"].replace("|", "／")))
L += ["", "---", "", "### ⭐**误治-救逆三元组**：`无效史 → 胡老证判 → 胡老方`", "",
      "> ⛔**「A方→无效→B方」这个形状抓不住最有价值的那一类**：",
      "> **前医无效那一侧常常没有方名**（「曾服中药10余剂不效」）。要求两端都有方名，",
      "> 等于把 **%d 例误治史（%.0f%%）全滤掉**。" % (n_hist, 100.0*n_hist/len(cases)),
      "> → 改抽**三元组**。**它比转方对更有价值：它告诉我们胡老看见了别人没看见的什么。**", "",
      "> ⚠**两类对照不得合并**（视角⑧）：前医无效→胡老＝**误治-救逆对**（⑭反事实）；",
      "> 胡老一诊→二诊＝**同一医家的方证细分**（⑥因果）。实测前者 %d 例、后者 %d 例。"
      % (n_hist, n_self), "",
      "**抽出三元组 %d 个（去重）。**" % len(utriples), "",
      "| # | 无效史 | **胡老之证判** | **胡老之方** | 出处 |", "|---|---|---|---|---|"]
for i, t in enumerate(utriples[:70], 1):
    L.append("| %d | %s%s | %s | **%s** | %s |" % (
        i, t["hist"], t["eff"], t["basis"].replace("|", "／"), t["fang"], t["book"]))
L += ["", "**高频转方对（A无效→B）：**", ""]
for (a, b2), n in pc.most_common(15):
    L.append("- **%s → %s**（%d 次）" % (a, b2, n))

L += ["", "---", "", "## 三、舌轴**按书分层重测**（㊹批已知未验项之了结）", "",
      "> ㊹批「苔白无分辨力」是 558 案**合并**统计。本节按书分层，排除体裁效应后再判。",
      "> **n<20 一律样本不足，不下结论。**", "",
      "| 舌象 | 书 | n | 判定 | 病性分布 |", "|---|---|---|---|---|"]
for name, bk, n, verdict, dist in strat:
    L.append("| %s | %s | %d | %s | %s |" % (name, bk, n, verdict, dist))

L += ["", "---", "", "## 四、人读金标准集·**抽样 30 案**（㊹批建议④·上级采纳）", "",
      "> ⚠**本工具只做抽样与字段模板；人工标注做不了**——如实标「待人读」。",
      "> 用途：作**工具准确率的外部基准**（视角㉛外部反查点在案例层的对应物）。", "",
      "**字段模板**：`案号｜采集项(逐项)｜病位+依据｜病性+依据｜寒热虚实｜兼夹｜方证+依据｜"
      "方药加减｜服后反应｜转方+依据`", "",
      "| # | 出处 | 案文首 90 字（**待人读标注**） |", "|---|---|---|"]
for i, c in enumerate(gold, 1):
    L.append("| %d | %s | %s |" % (i, c["book"], c["body"][:90].replace("|", "／")))

open(os.path.join(B, "case_layer", "复现率与转方对.md"), "w", encoding="utf-8").write("\n".join(L))
json.dump(dict(jing_rate=jing_rate, fang_rate=fang_rate, n_jing=len(jd), n_fang=len(fd),
               why=dict(whycnt), pairs=len(upairs), neg_pairs=len(neg_pairs),
               top_pairs=[["%s→%s" % k, v] for k, v in pc.most_common(15)]),
          open(os.path.join(B, "case_layer", "_reproduce.json"), "w"), ensure_ascii=False, indent=1)

print("案例 %d｜复现率·定经 **%.1f%%**(%d/%d)｜复现率·定方 **%.1f%%**(%d/%d)" % (
    len(cases), jing_rate, sum(1 for r in jd if r["jing_ok"]), len(jd),
    fang_rate, sum(1 for r in fd if r["fang_ok"]), len(fd)))
print("定方失败归因：", dict(whycnt))
print("转方对 %d 个｜A方无效者 %d 个" % (len(upairs), len(neg_pairs)))
print("**误治-救逆三元组 %d 个**｜含前医史之案 %d(%.0f%%)｜含胡老二诊之案 %d(%.0f%%)"
      % (len(utriples), n_hist, 100.0*n_hist/len(cases), n_self, 100.0*n_self/len(cases)))
print("  其中**未述依据**者 %d 个（＝隐含判断，最有价值的探测点）"
      % sum(1 for t in utriples if t["basis"].startswith("⛔")))
print("高频转方对：", "｜".join("%s→%s(%d)" % (a, b2, n) for (a, b2), n in pc.most_common(8)))
print("舌分层：", sum(1 for x in strat if x[3] == "**有方向**"), "有方向 /",
      sum(1 for x in strat if x[3] == "无方向"), "无方向 /",
      sum(1 for x in strat if x[3] == "样本不足"), "样本不足")
