#!/usr/bin/env python3
"""【三档判分 ＋ 五机制联调】（㊽批·指令2前置证伪实验 ＋ 指令1联调）。

## 一、三档判分（上级㊽批·指令2 之前置证伪实验）
上级㊽批实测：**108 例可解析验案中，合方 13% ＋ 加味/加减 49% ＝ 56% 不是单方原方。**
→ 若判分要求方名**完全一致**，**天花板就在 44% 附近，与机制无关。**
**这可能推翻㊻批「机制错配」之诊断（同一区域第三次误诊）。**

本工具把定方复现率**分三档报**：
  ①**单方原方命中**：引擎首选 ＝ 案中方（现行判分，最严）
  ②**基方命中**：引擎首选 ＝ 案中方**去加减后之基方**（「桂枝汤加附子」→ 桂枝汤）
  ③**合方主方命中**：案中为合方，引擎首选 ＝ 合方**任一成分**
**若②③计入后显著上升 → 「机制错配」归因作废，真因是「引擎只会出单方原方」。**

⚠**这个实验的意义在于它可以失败**：若②③计入后仍无显著提升，
  则「机制错配」之诊断**反而被加强**。**两个方向都是信息。**

## 二、五机制联调（上级㊽批·指令1·最高优先）
R31三步 ＋ R34输入层(共症剔除) ＋ R33三轴(兼夹只入第三步) ＋ R35否决 ＋ R39中间层(汗之有无)
**串起来跑，逐案打印每步输入输出**。
**目的不是求高分，是查「某规则否决了另一规则的正确结论」之实例**（协议12）。

【已知失效模式】(视角㉕)
  ① **基方拆分靠字符串**（去「加X」「合X」「去X」）。胡老的方名有本身含「加」者
     （桂枝加葛根汤是**独立方**不是「桂枝汤+葛根」），**须先查在库整名，在库者不拆**。
  ② 三档是**放宽判分**，**必然使数字上升**——**上升本身不是成绩**；
     **要看的是上升幅度**：小幅＝机制问题为主，大幅＝判分口径问题为主。
  ③ 联调的「冲突实例」靠**机械比对**：单跑 R31 命中而联调后不命中者即疑似冲突。
     **它找得到"被否决掉的正确结论"，找不到"两条规则都错但恰好抵消"**。
【弃件条件】案中无方名者不入分母。
【口径】(视角㊱) **口径变更登记**：本工具引入②③两档＝判分口径放宽，
  **按㊹批防作弊条款，三档分别报，并同时报①档(旧口径)**；`python3 tools/tier_score.py` 复跑。
"""
import re, os, json
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
cases = []
for bk, fn in BOOKS:
    T = load(fn)
    if not T: continue
    st = [m.start() for m in CASE_START.finditer(T)]
    for i, s0 in enumerate(st):
        e = st[i + 1] if i + 1 < len(st) else min(len(T), s0 + 2500)
        b = T[s0:e][:2500]
        if len(b) >= 60: cases.append(dict(book=bk, body=b))

E = re.sub(r"\s+", "", open(os.path.join(B, "hxs_engine_v79_full.md"), encoding="utf-8").read())
STAR = {}
for m in re.finditer(r"【([一-鿿·§\d/加()（）]{2,26})】[^★\n]{0,40}★([^★]{2,60})★", E):
    STAR.setdefault(re.sub(r"·.*$", "", m.group(1)), m.group(2))
ENG_FANG = set(STAR) | set(re.findall(r"【([一-鿿]{2,14}(?:汤|散|丸))", E))

FANG_LEAD = re.compile(r"^(?:仍宜以|据证与|故胡老常以|而胡老用|表实的|表虚的|营卫失和之|"
                       r"此于|再以|为|与|予|用|以|服|改服|给服|先与|后改|后与|故予|故与|"
                       r"改与|再与|投|拟|方用|治以|治用|即与|乃与|遂与|宜)+")
FANG_OCR = {"小标胡": "小柴胡", "大标胡": "大柴胡", "标胡": "柴胡", "柏胡": "柴胡",
            "柴朐": "柴胡", "桂栗": "桂枝", "柠技": "桂枝", "麻杳": "麻杏",
            "生石贾": "生石膏", "生石青": "生石膏", "知毋": "知母", "黄丙": "黄芪",
            "莞苓饮": "茯苓饮", "茯莎": "茯苓", "当当芍药": "当归芍药",
            "荞桂术甘": "苓桂术甘", "半东": "半夏", "厚杨": "厚朴", "厚私": "厚朴"}
def fnorm(f):
    f = FANG_LEAD.sub("", f)
    for a, b2 in FANG_OCR.items(): f = f.replace(a, b2)
    return f
FANG_RX = re.compile(r"([一-鿿]{2,20}(?:汤|散|丸))")

# ── 基方拆分（失效模式①：在库整名者不拆）───────────────────────
SPLIT = re.compile(r"合|加(?![味减])|去")
def base_of(f):
    """去加减/合方后之基方集合。**在库整名者不拆**（桂枝加葛根汤是独立方）。"""
    if f in ENG_FANG: return {f}
    parts = set()
    for seg in re.split(r"合", f):
        seg = seg.strip()
        if not seg: continue
        if seg in ENG_FANG: parts.add(seg); continue
        m = re.match(r"^([一-鿿]{2,12}(?:汤|散|丸))", seg)
        if m and m.group(1) in ENG_FANG: parts.add(m.group(1)); continue
        cut = re.split(r"加(?![味减])|去", seg)[0]
        for suf in ("汤", "散", "丸"):
            if cut + suf in ENG_FANG: parts.add(cut + suf); break
        else:
            if cut in ENG_FANG: parts.add(cut)
    return parts or {f}

def is_compound(f):  return "合" in f
def is_modified(f):  return bool(re.search(r"加(?![味减])|加味|加减|去", f))

def best_fang(body):
    b, bs = None, 0
    for nm, star in STAR.items():
        toks = [t for t in re.split(r"[+/／、,，]", star) if len(re.sub(r"[^一-鿿]", "", t)) >= 2]
        if not toks: continue
        hit = sum(1 for t in toks if re.sub(r"[^一-鿿]", "", t)[:4] in body)
        sc = hit / len(toks)
        if sc > bs: b, bs = nm, sc
    return b

# ── 一、三档判分 ──────────────────────────────────────────────
n = t1 = t2 = t3 = 0
comp = mod = plain = 0
for c in cases:
    fs = {fnorm(x) for x in FANG_RX.findall(c["body"])}
    fs = {x for x in fs if len(x) >= 3}
    if not fs: continue
    n += 1
    if any(is_compound(x) for x in fs): comp += 1
    elif any(is_modified(x) for x in fs): mod += 1
    else: plain += 1
    bf = best_fang(c["body"])
    if not bf: continue
    if bf in fs: t1 += 1; t2 += 1; t3 += 1; continue
    bases = set()
    for x in fs: bases |= base_of(x)
    if bf in bases: t2 += 1; t3 += 1; continue
    # ③合方主方：案中为合方，引擎首选是其任一成分（含更宽的包含关系）
    if any(is_compound(x) for x in fs) and any(bf in x or x in bf for x in fs): t3 += 1

# ── 二、五机制联调 ────────────────────────────────────────────
TIGANG = {"太阳": ["脉浮", "头项强痛", "恶寒", "恶风"],
 "阳明": ["胃家实", "不恶寒反恶热", "自汗出", "潮热", "大便硬", "腹满痛", "谵语"],
 "少阳": ["口苦", "咽干", "目眩", "往来寒热", "胸胁苦满", "心烦喜呕", "嘿嘿不欲饮食"],
 "太阴": ["腹满而吐", "食不下", "自利", "腹自痛", "下利", "便溏", "大便溏"],
 "少阴": ["脉微细", "但欲寐"],
 "厥阴": ["消渴", "气上撞心", "心中疼热", "饥而不欲食", "食则吐蛔"]}
GONG = ["发热", "头痛", "喘"]                       # R34 第五款·表里共症
BIAO = ["恶寒", "恶风", "脉浮", "无汗", "身疼痛", "头项强痛", "浮肿"]
LI = ["下利", "自利", "便溏", "大便硬", "不大便", "腹满", "干呕", "呕吐", "纳差", "不欲食"]
PP = {"痰饮": ["苔白滑", "振水", "咳逆倚息", "痰"], "瘀血": ["舌暗", "舌紫", "瘀斑", "刺痛"],
      "水气": ["浮肿", "小便不利", "身肿"], "湿": ["苔腻", "身重"], "宿食": ["嗳腐", "干噫食臭"]}
VETO = [("大便溏∧腹微满→非柴胡证", ["便溏", "大便溏", "微溏"], ["腹微满", "腹满", "腹胀"], "柴胡"),
        ("躁无暂安→脏厥非蛔厥", ["躁无暂安", "无暂安时"], None, "乌梅")]
LOC_RX = re.compile(r"(太阳|阳明|少阳|太阴|少阴|厥阴)")

def integrated(body):
    """五机制联调。返回逐步轨迹。"""
    tr = {}
    # R34 输入层：剔共症
    gong = [g for g in GONG if g in body]
    tr["R34共症剔除"] = gong
    # R31 第一步：提纲判经（共症不参与）
    s1 = {}
    for j, ts in TIGANG.items():
        hit = [t for t in ts if t in body and t not in gong]
        if hit: s1[j] = hit
    tr["R31①提纲"] = s1
    # R31 第二步：表里闭合
    hb = [w for w in BIAO if w in body]; hl = [w for w in LI if w in body]
    tr["R31②表里"] = {"表征": hb[:3], "里征": hl[:3],
                      "闭合": "皆现" if (hb and hl) else ("仅表" if hb else ("仅里" if hl else "皆未现"))}
    # R39 中间层：表位者按汗之有无分流
    flow = ""
    if hb:
        flow = "无汗→麻黄剂类" if ("无汗" in body) else ("自汗→桂枝剂类" if re.search(r"汗出|自汗", body) else "汗未采")
    tr["R39中间层"] = flow
    # R33 轴一：兼夹（只入第三步，不改经）
    pp = {k: [w for w in ws if w in body] for k, ws in PP.items()}
    pp = {k: v for k, v in pp.items() if v}
    tr["R33兼夹(只入③)"] = list(pp)
    # R35 否决
    vetoed = []
    for name, a, b2, target in VETO:
        if any(x in body for x in a) and (b2 is None or any(x in body for x in b2)):
            vetoed.append((name, target))
    tr["R35否决"] = [v[0] for v in vetoed]
    # R31 第三步：方证（受否决约束）
    bf = best_fang(body)
    blocked = [t for _, t in vetoed if bf and t in bf]
    tr["R31③方证"] = bf
    tr["③被否决"] = blocked
    return set(s1), bf, blocked, tr

conf_cases = []
solo_ok = comb_ok = dd = 0
for c in cases:
    真方 = {fnorm(x) for x in FANG_RX.findall(c["body"])}
    真方 = {x for x in 真方 if len(x) >= 3}
    if not 真方: continue
    dd += 1
    bf0 = best_fang(c["body"])            # 单跑 R31 第三步
    s1, bf, blocked, tr = integrated(c["body"])
    ok0 = bf0 in 真方
    ok1 = (bf in 真方) and not blocked
    solo_ok += ok0; comb_ok += ok1
    if ok0 and not ok1:                   # ⭐协议12 要查的：联调否决了正确结论
        conf_cases.append(dict(book=c["book"], fang=bf0, blocked=blocked,
                               tr={k: str(v)[:90] for k, v in tr.items()},
                               head=c["body"][:110]))

L = ["# 三档判分 ＋ 五机制联调（㊽批）", "",
     "> 生成：`tools/tier_score.py`（文件头含【已知失效模式】【弃件条件】【口径】）。", "",
     "---", "", "## 一、⭐**三档判分**（指令2 之前置证伪实验）", "",
     "> 上级实测：合方 13% ＋ 加味 49% ＝ **56% 非单方原方**。",
     "> 若判分要求方名完全一致，**天花板就在 44% 附近，与机制无关**。", "",
     "**案中方之形态分布（本工具复核）：**", "",
     "| 形态 | 案数 | 占比 |", "|---|---|---|",
     "| 含**合方** | %d | %.0f%% |" % (comp, 100.0 * comp / max(1, n)),
     "| 含**加减/加味**（非合方） | %d | %.0f%% |" % (mod, 100.0 * mod / max(1, n)),
     "| **单方原方** | %d | **%.0f%%** |" % (plain, 100.0 * plain / max(1, n)), "",
     "**三档复现率：**", "",
     "| 档 | 判据 | 命中 | 复现率 |", "|---|---|---|---|",
     "| ① 单方原方命中（**旧口径**） | 引擎首选＝案中方 | %d | **%.1f%%** |" % (t1, 100.0 * t1 / max(1, n)),
     "| ② 基方命中（加减不同） | 引擎首选＝案中方之基方 | %d | **%.1f%%** |" % (t2, 100.0 * t2 / max(1, n)),
     "| ③ 合方主方命中 | 引擎首选＝合方任一成分 | %d | **%.1f%%** |" % (t3, 100.0 * t3 / max(1, n)),
     "", "**②相对①提升 %+.1f 点｜③相对①提升 %+.1f 点。**" % (
         100.0 * (t2 - t1) / max(1, n), 100.0 * (t3 - t1) / max(1, n)), "",
     "---", "", "## 二、**五机制联调**（指令1·最高优先）", "",
     "> R31三步 ＋ R34输入层 ＋ R33三轴 ＋ R35否决 ＋ R39中间层，串起来跑。",
     "> **目的不是求高分，是查「某规则否决了另一规则的正确结论」**（协议12）。", "",
     "| 跑法 | 分母 | 命中 | 率 |", "|---|---|---|---|",
     "| 单跑 R31 第三步 | %d | %d | %.1f%% |" % (dd, solo_ok, 100.0 * solo_ok / max(1, dd)),
     "| **五机制联调** | %d | %d | **%.1f%%** |" % (dd, comb_ok, 100.0 * comb_ok / max(1, dd)),
     "", "**联调 − 单跑 ＝ %+.1f 点。**" % (100.0 * (comb_ok - solo_ok) / max(1, dd)), "",
     "### ⭐**冲突实例：联调否决了单跑的正确结论**（协议12 之标的）", "",
     "**共 %d 例。**" % len(conf_cases), ""]
if conf_cases:
    L += ["| # | 出处 | 被否决之方 | 触发之否决 | 案文首 110 字 |", "|---|---|---|---|---|"]
    for i, x in enumerate(conf_cases[:40], 1):
        L.append("| %d | %s | **%s** | %s | %s |" % (
            i, x["book"], x["fang"], "／".join(x["blocked"]), x["head"].replace("|", "／")))
    L += ["", "### 逐步轨迹（前 5 例）", ""]
    for x in conf_cases[:5]:
        L.append("- **%s ／ %s**" % (x["book"], x["fang"]))
        for k, v in x["tr"].items(): L.append("  - `%s` %s" % (k, v))
        L.append("")
else:
    L += ["**0 例。** ⚠这个 0 须谨慎读：本工具的否决规则只挂了 2 条（§123／§338），",
          "**覆盖面极小**；0 冲突可能只是说明这 2 条很少被触发，**不代表五机制无冲突**。", ""]

open(os.path.join(B, "case_layer", "三档判分与联调.md"), "w", encoding="utf-8").write("\n".join(L))
json.dump(dict(n=n, comp=comp, mod=mod, plain=plain, t1=t1, t2=t2, t3=t3,
               solo=solo_ok, comb=comb_ok, dd=dd, conflicts=len(conf_cases)),
          open(os.path.join(B, "case_layer", "_tier_score.json"), "w"), ensure_ascii=False, indent=1)

print("案中方形态：合方 %d(%.0f%%)｜加减 %d(%.0f%%)｜单方原方 %d(**%.0f%%**)" % (
    comp, 100.0*comp/max(1,n), mod, 100.0*mod/max(1,n), plain, 100.0*plain/max(1,n)))
print("三档复现率：①单方原方 **%.1f%%** ／ ②基方 **%.1f%%** ／ ③合方主方 **%.1f%%**" % (
    100.0*t1/max(1,n), 100.0*t2/max(1,n), 100.0*t3/max(1,n)))
print("  ②−① = %+.1f 点｜③−① = %+.1f 点" % (100.0*(t2-t1)/max(1,n), 100.0*(t3-t1)/max(1,n)))
print("联调：单跑 %.1f%% → 五机制 %.1f%%（%+.1f 点）｜**冲突实例 %d 例**" % (
    100.0*solo_ok/max(1,dd), 100.0*comb_ok/max(1,dd),
    100.0*(comb_ok-solo_ok)/max(1,dd), len(conf_cases)))
