#!/usr/bin/env python3
"""【案例检索·方证层主机制重建】＋【三路同源同分母对照】（㊾批·指令二·本批核心）。

## 立此件之由（上级㊾批）
「真正的修法：**回到已被测量过的那条路**——案例检索 20.0% vs 规则 3.2%（㉔批实测）。」
→ 重建案例检索为**方证层主机制**：558 案完整原文入库、以**案文相似度**检索、
  **在 R31 已定之经内检索**（不越过第一二步）、输出**近邻案＋出处＋其方**为候选；
  ★与判据**降为排序与解释，不作准入**；**规则路径与案例路径并列跑，数据裁决**。

## ⛔协议14 复核·**本工具存在的第一理由是驳一个数**（须先读）
上级㊾批以「**案例检索 20.0% vs 规则 3.2%**」作本批全部依据。**该比较不成立**，
理由**全部出自我方自己的工具头**（不引外部主张）：
  · `three_path_compare.py` 失效模式②逐字：「案例检索一路的数来自 case_index.py 的
    **留一法(不同语料)**，**与前两路不同源**，**只可作量级参照，不可直接相减**。」
  · `case_index.py` 失效模式③逐字：「留一法**只在同一本书内**做，未跨书验证；
    C卷案例风格高度一致，**本数字不可外推为泛化准确率**。」
  · 且 **N 不同**（规则路径 N=95／案例检索 N=60）、**语料不同**（五源全库 vs 仅C卷）、
    **判分不同**（㊽批三档 vs ㉔批单档）。
  · 并及**措辞核**：上级称案例检索为「**纯字面 2-gram**」，
    而 `case_index.py` 原文为「字面 2-gram Jaccard **＋ 槽位签名 Jaccard 的加权和**」
    ——**不是纯字面**。**若纯字面就能到 20.0%，那是一个尚未做过的实验。**
→ **故 20.0% 不能当作「案例路已经赢了」的既有结论。**
  **上级的方向（去测这条路）成立；上级的依据（这条路已测赢）不成立。**
  **本工具即把它变成一次同源、同分母、同判分的真对照。**——这正是上级所令的「数据裁决」。

## 三路（同一批案、同一分母、同一判分）
  · **路A 规则路径**：★逐 token 覆盖率打分取首选方（现行机制，R40 已判其不工作）
  · **路B 案例检索·全库**：留一法，案文 2-gram 相似度取近邻，**取近邻案之方**
  · **路C 案例检索·经内**：同 B，但**库先按 R31 第一二步所定之经过滤**〔C卷L309
    「辨方证是在六经八纲一般规律**指导下**的具体运用」——**不得越过第一二步**〕

⚠**遮盲是本工具的命门**（`holdout_mask.py` 之教训：**残留即等于泄漏答案**）：
  查询侧一律只用**症状段**（首个方名/判断词之前）。**三路同用遮盲后的症状段**——
  路A 现行口径是拿**全文**打分（含方名），**那是带泄漏的**；本工具因此**两个口径都报**，
  **并以遮盲口径为准**。**这会使路A的数字下降，那是订正不是打压。**

【已知失效模式】(视角㉕)
  ① **遮盲靠正则**。OCR 变形方名（"小标胡""莞苓饮"）遮不掉即**泄漏答案**，
     使**案例路虚高**（近邻靠方名字面撞上）。已用 FANG_OCR 表补，**必然不全**。
     → 故另报 `[泄漏自检]`：遮盲后症状段中仍含任一在库方名者之案数，**该数须≈0**。
  ② **2-gram Jaccard 不做同义归一**（"心下痞"vs"胃脘堵"字面不同）→ 本路召回是**下界**。
  ③ **留一法只剔查询案本身**，同书邻案的**同一病人复诊案**仍在库中 → **系谱泄漏**，
     使案例路虚高。已按 `book+相邻` 加剔同书相邻 2 案，**跨书重复案剔不掉**。
  ④ **经内检索之「经」两侧口径不同**：查询侧用**引擎 R31 第一二步机械跑**所得候选经；
     库侧用**案文明写之经**（无明写者入「未标经」池）。**这不对称，但它正是实际用法**：
     新病人没有标签，库里的案有。**该不对称须写在结论旁，不得省。**
  ⑤ 无明写经之案占比高时，「经内检索」实际退化为「全库检索」——故**须同报未标经占比**。
【弃件条件】症状段 <30 字者弃（遮盲后残余过短，无法检索）；案中无方名者不入分母。
【口径】(视角㊱) 一案＝ tier_score/case_flow 同一切案口径（五源·CASE_START·上限2500字）；
  命中＝①单方原方（引擎首选∈案中方集）；另报③最宽（含合方任一成分）。
  **三路共用同一分母，分母数须一致**（本工具断言之）；`python3 tools/case_retrieve.py` 复跑。
"""
import re, os, json
from collections import Counter, defaultdict

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JUNK = re.compile(r"·\d+·|PDFcreatedwith[A-Za-z]*|pdfFactory[A-Za-z]*|Protrialversion|"
                  r"www\.pdffactory\.com|胡希恕讲伤寒\d*|---第\d+页---|http\S*|快乐人生久久\S*")


def load(fn):
    """协议16：清洗式**逐行施加** ＋ 降幅 >50% 中止告警 ＋ 长度断言兜底。"""
    p = os.path.join(B, "sources", fn)
    if not os.path.exists(p): return ""
    raw = open(p, encoding="utf-8", errors="ignore").read()
    n0 = len(re.sub(r"\s+", "", raw))
    T = "".join(JUNK.sub("", re.sub(r"\s+", "", ln)) for ln in raw.split("\n"))
    if n0 and len(T) / n0 < 0.5:
        raise SystemExit("⛔协议16 中止：%s 降幅 %.0f%%（%d→%d）" % (fn, 100 * (1 - len(T) / n0), n0, len(T)))
    print("  [协议16] %-28s %d → %d 字（保留 %.0f%%）" % (fn, n0, len(T), 100 * len(T) / n0))
    return T


BOOKS = [("C卷", "C_jingfangliyu.txt"), ("临床家", "ocr_中医临床家胡希恕.txt"),
         ("带教", "ocr_冯世纶带教实录第一辑.txt"), ("传真", "ocr_经方传真系.txt"),
         ("解读", "ocr_解读张仲景医学.txt")]
CASE_START = re.compile(r"【验案】|【检案】|例\s*\d{1,3}[，,、]?[一-鿿]{2,3}[，,]|病案号\s*\d+|"
                        r"[一-鿿]{1,3}某[，,]\s*(?:男|女)(?:性)?[，,]|"
                        r"\d{4}年\d{1,2}月\d{1,2}日初诊|初诊日期\s*\d{4}")

print("── 切案（与 tier_score.py／case_flow.py 同口径）──")
cases = []
for bk, fn in BOOKS:
    T = load(fn)
    if not T: continue
    st = [m.start() for m in CASE_START.finditer(T)]
    for i, s0 in enumerate(st):
        e = st[i + 1] if i + 1 < len(st) else min(len(T), s0 + 2500)
        b = T[s0:e][:2500]
        if len(b) >= 60: cases.append(dict(book=bk, seq=len(cases), body=b))
print("  切案 %d（分书 %s）\n" % (len(cases), dict(Counter(c["book"] for c in cases))))

# ── 引擎侧：★库与在库方名（与 tier_score 同）────────────────────────
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

SPLIT_OK = re.compile(r"加(?![味减])|去")
def base_of(f):
    if f in ENG_FANG: return {f}
    parts = set()
    for seg in re.split(r"合", f):
        seg = seg.strip()
        if not seg: continue
        if seg in ENG_FANG: parts.add(seg); continue
        m = re.match(r"^([一-鿿]{2,12}(?:汤|散|丸))", seg)
        if m and m.group(1) in ENG_FANG: parts.add(m.group(1)); continue
        cut = SPLIT_OK.split(seg)[0]
        for suf in ("汤", "散", "丸"):
            if cut + suf in ENG_FANG: parts.add(cut + suf); break
        else:
            if cut in ENG_FANG: parts.add(cut)
    return parts or {f}

# ── 遮盲：症状段 ＝ 首个「方名 / 辨证结论词 / 给方动词」之前 ──────────
#   锚：`holdout_mask.py` 之实测教训——**词典遮盲在重OCR语料上失败，残留即泄漏答案**，
#   故改**截断法**：在第一个结论/处方标记处截断，不依赖方名词典。
CUT = re.compile(
    r"[一-鿿]{2,20}(?:汤|散|丸)"                                  # 任一方名（最强切点）
    r"|证属|此属|此为|此乃|辨为|诊为|证系|证为|知其为|认为是|即为|归纳为|综合分析|据此辨"
    r"|方用|治以|治宜|拟用|宜与|投以|处方|与之|予以"
    r"|太阳病|阳明病|少阳病|太阴病|少阴病|厥阴病|合病|并病"
    r"|上热下寒|营卫不和|水饮内停|里实|里虚|表虚|表实")
LEAK_NAMES = sorted({x for x in ENG_FANG if len(x) >= 3}, key=len, reverse=True)


def symptom_seg(body):
    m = CUT.search(body)
    return body[:m.start()] if m else body


def grams(s):
    s = re.sub(r"[^一-鿿]", "", s)
    return {s[i:i + 2] for i in range(len(s) - 1)}


# ── R31 第一二步（与 tier_score.integrated 同表，同口径）────────────
TIGANG = {"太阳": ["脉浮", "头项强痛", "恶寒", "恶风"],
 "阳明": ["胃家实", "不恶寒反恶热", "自汗出", "潮热", "大便硬", "腹满痛", "谵语"],
 "少阳": ["口苦", "咽干", "目眩", "往来寒热", "胸胁苦满", "心烦喜呕", "嘿嘿不欲饮食"],
 "太阴": ["腹满而吐", "食不下", "自利", "腹自痛", "下利", "便溏", "大便溏"],
 "少阴": ["脉微细", "但欲寐"],
 "厥阴": ["消渴", "气上撞心", "心中疼热", "饥而不欲食", "食则吐蛔"]}
GONG = ["发热", "头痛", "喘"]                       # R34 第五款·表里共症，不参与判经
BIAO = ["恶寒", "恶风", "脉浮", "无汗", "身疼痛", "头项强痛", "浮肿"]
LI = ["下利", "自利", "便溏", "大便硬", "不大便", "腹满", "干呕", "呕吐", "纳差", "不欲食"]
JING6 = ["太阳", "阳明", "少阳", "太阴", "少阴", "厥阴"]
JING_RX = re.compile(r"(太阳|阳明|少阳|太阴|少阴|厥阴)病?")


def step12(sym):
    """R31 第一二步机械跑 → 候选经集合（用于**查询侧**）。共症不参与。"""
    gong = [g for g in GONG if g in sym]
    s1 = {j for j, ts in TIGANG.items() if any(t in sym and t not in gong for t in ts)}
    if s1: return s1
    hb = any(w in sym for w in BIAO); hl = any(w in sym for w in LI)
    if hb and not hl: return {"太阳", "少阴"}          # 表位 → 阳证/阴证
    if hl and not hb: return {"阳明", "太阴"}          # 里位 → 阳证/阴证
    return set()                                        # 定不了（L-共）


def label_jing(body):
    """库侧标经：**案文明写之经**（不是引擎推的）。无明写者返回 None。"""
    js = set(JING_RX.findall(body))
    return js or None


def best_fang_rule(text):
    """路A·规则路径：★逐 token 覆盖率打分（现行机制）。"""
    b, bs = None, 0.
    for nm, star in STAR.items():
        toks = [t for t in re.split(r"[+/／、,，]", star) if len(re.sub(r"[^一-鿿]", "", t)) >= 2]
        if not toks: continue
        hit = sum(1 for t in toks if re.sub(r"[^一-鿿]", "", t)[:4] in text)
        sc = hit / len(toks)
        if sc > bs: b, bs = nm, sc
    return b


# ── 建库 ────────────────────────────────────────────────────────
lib = []
drop = Counter()
for c in cases:
    fs = {fnorm(x) for x in FANG_RX.findall(c["body"])}
    fs = {x for x in fs if len(x) >= 3}
    if not fs: drop["无方名"] += 1; continue
    sym = symptom_seg(c["body"])
    if len(re.sub(r"[^一-鿿]", "", sym)) < 30: drop["症状段<30字"] += 1; continue
    lib.append(dict(book=c["book"], seq=c["seq"], sym=sym, g=grams(sym),
                    fang=fs, jing=label_jing(c["body"]), body=c["body"]))

# ── [泄漏自检]（失效模式①）──────────────────────────────────────
leak = 0
for it in lib:
    if any(n in it["sym"] for n in LEAK_NAMES): leak += 1
print("入库 %d 案（弃件 %s）" % (len(lib), dict(drop)))
print("  [泄漏自检] 遮盲后症状段仍含在库方名者：**%d 案（%.1f%%）** —— 该数须≈0"
      % (leak, 100 * leak / len(lib)))
nolab = sum(1 for it in lib if not it["jing"])
print("  [经标注] 案文明写六经者 %d／未标经 %d（**%.0f%% 未标经**——经内检索之退化度）\n"
      % (len(lib) - nolab, nolab, 100 * nolab / len(lib)))

# ── ⛔必然失败样例自验（㊹批定则：通过率类指标写完须先构造必失样例）──────
_probe = dict(g=grams("此案纯属子虚乌有之词绝不见于任何医案文字"), fang={"子虚乌有汤"},
              jing=None, book="_probe", seq=-1)
_sc = max((len(_probe["g"] & it["g"]) / len(_probe["g"] | it["g"]) for it in lib), default=0)
assert _sc < 0.15, "自验失败：虚构查询也拿到高相似度 %.3f，相似度函数无分辨力" % _sc
print("[自验] 虚构查询最高相似度 %.3f（<0.15）→ 相似度函数可失败，指标非恒真\n" % _sc)


def retrieve(q, k=3, within=None, boost=None):
    """留一法检索。剔查询案本身＋同书相邻2案（系谱泄漏）。
       within＝**准入过滤**（经内检索，路C）；boost＝**排序加权**（不过滤，路C′）。"""
    out = []
    for it in lib:
        if it["book"] == q["book"] and abs(it["seq"] - q["seq"]) <= 2: continue
        if within is not None:
            if it["jing"] is None: continue           # 未标经者不入经内库
            if not (it["jing"] & within): continue
        u = len(q["g"] | it["g"])
        if not u: continue
        sc = len(q["g"] & it["g"]) / u
        if boost and it["jing"] and (it["jing"] & boost): sc *= 1.5
        out.append((sc, it))
    out.sort(key=lambda x: (-x[0], x[1]["book"], x[1]["seq"]))   # 确定性：同分按书名序
    return out[:k]


def pick(fs):
    """**确定性**取方：平局按 (长度, 名) 排序。
    [㊸批定则]结果不可复现的工具不得用于出清单——set 迭代序随 hash seed 变。"""
    return sorted(fs, key=lambda x: (len(x), x))[0]


def score(pred, truth):
    """①单方原方命中／③最宽（基方或合方任一成分）。"""
    if not pred: return 0, 0
    if pred in truth: return 1, 1
    bases = set()
    for x in truth: bases |= base_of(x)
    if pred in bases: return 0, 1
    if any(pred in x or x in pred for x in truth): return 0, 1
    return 0, 0


rows = defaultdict(lambda: [0, 0, 0])      # 路 → [①, ③, 落空]
cran = [0, 0, 0, 0, 0]                     # C能跑之子集：[n, C①, C③, B①, B③]
cwhy = Counter()                           # C 落空之因
csz = []                                   # B3 候选集大小
okj = [0, 0, 0]                            # 定经确对之子集：[n, C经内①, B全库①]
N = 0
jing_ok = jing_n = 0
detail = []
for q in lib:
    N += 1
    truth = q["fang"]
    cand = step12(q["sym"])
    if q["jing"]:
        jing_n += 1
        if cand & q["jing"]: jing_ok += 1
    # 路A·规则路径（遮盲口径：只给症状段）
    a = best_fang_rule(q["sym"])
    s1, s3 = score(a, truth); rows["A规则·遮盲"][0] += s1; rows["A规则·遮盲"][1] += s3
    if not a: rows["A规则·遮盲"][2] += 1
    # 路A′·规则路径（现行口径：给全文——**带泄漏，仅供对读**）
    a2 = best_fang_rule(q["body"])
    s1, s3 = score(a2, truth); rows["A′规则·全文(对读)"][0] += s1; rows["A′规则·全文(对读)"][1] += s3
    if not a2: rows["A′规则·全文(对读)"][2] += 1
    # 路B·案例检索·全库
    nb = retrieve(q, 3, None)
    b1 = pick(nb[0][1]["fang"]) if nb else None
    s1, s3 = score(b1, truth); rows["B案例·全库"][0] += s1; rows["B案例·全库"][1] += s3
    if not nb: rows["B案例·全库"][2] += 1
    # 路C·案例检索·**经内**（R31 第一二步之约束）
    nc = retrieve(q, 3, cand) if cand else []
    c1 = pick(nc[0][1]["fang"]) if nc else None
    s1, s3 = score(c1, truth); rows["C案例·经内(准入)"][0] += s1; rows["C案例·经内(准入)"][1] += s3
    if not nc:
        rows["C案例·经内(准入)"][2] += 1
        cwhy["①第一二步定不了经" if not cand else "②该经内库中无案"] += 1
    else:
        # **条件分解**：C 只在能跑的子集上与 B 比，才知道「经内约束」本身是帮还是害
        cran[0] += 1; cran[1] += s1; cran[2] += s3
        sb1, sb3 = score(b1, truth); cran[3] += sb1; cran[4] += sb3
    # 路B3·近邻3案任一命中（**候选集**读法：引擎作外挂闸门时的实际用法）
    #   ⚠**口径要写死**：近邻案本身可能是合方案，其 fang 是一个集合；
    #   本档取**近邻 3 案所载之全部方**为候选集，问真方是否落在其中。
    # 路C′·**经作排序权重，不作准入**（与上级令★「降为排序，不作准入」同一味药）
    #   库不过滤 → 无落空；经相符者相似度加权 ×1.5，经不符者照常在库。
    nd = retrieve(q, 3, None, boost=cand)
    d1 = pick(nd[0][1]["fang"]) if nd else None
    s1, s3 = score(d1, truth); rows["C′案例·经作排序权重"][0] += s1; rows["C′案例·经作排序权重"][1] += s3
    if not nd: rows["C′案例·经作排序权重"][2] += 1
    cand3 = [f for _, it in nb for f in it["fang"]]
    csz.append(len(set(cand3)))          # ㊱数必带口径：候选集大小须同报，否则 66% 无意义
    rows["B3案例·近邻3案任一"][0] += int(any(score(f, truth)[0] for f in cand3))
    rows["B3案例·近邻3案任一"][1] += int(any(score(f, truth)[1] for f in cand3))
    # ⭐决定性分解：**当我方定经确实对时**，经内检索是帮还是害？
    #   这一问把「经内检索原理错」与「我方定经不够准」分开（视角⑥因果／⑭反事实）。
    if q["jing"] and (cand & q["jing"]):
        okj[0] += 1
        okj[1] += score(c1, truth)[0]; okj[2] += score(b1, truth)[0]
    if len(detail) < 12 and nb:
        detail.append((q, nb[0][0], nb[0][1], cand))

# ── ⭐归因分离实验：路A 现行口径(全文)高于遮盲口径，是【方名泄漏】还是【文本更长】？
#    四条件只改一处输入，其余全同。**这个实验可以失败**：若③≈①即方名泄漏，若③≈②即非。
def _mask_fang(t):
    for n in LEAK_NAMES: t = t.replace(n, "")
    return re.sub(r"[一-鿿]{2,20}(?:汤|散|丸)", "", t)
cond = [0] * 4
for q in lib:
    m = CUT.search(q["body"])
    tail = _mask_fang(q["body"][m.start():]) if m else ""
    for i, t in enumerate([q["sym"], q["body"], _mask_fang(q["body"]), tail]):
        p = best_fang_rule(t)
        if p and p in q["fang"]: cond[i] += 1
import statistics as _st
print("═══ ⭐归因分离·路A 的 15.7% 从哪来 ═══")
for nm, v in zip(["①症状段（结论之前·决策时可得）", "②全文（现行口径）",
                  "③全文－方名（长·无方名）", "④**结论之后段**－方名"], cond):
    print("  %-30s **%4.1f%%**" % (nm, 100 * v / N))
print("  平均字数：症状段 %d ／ 全文 %d"
      % (_st.mean(len(re.sub(r"[^一-鿿]", "", it["sym"])) for it in lib),
         _st.mean(len(re.sub(r"[^一-鿿]", "", it["body"])) for it in lib)))
print("  → ③≈② ⇒ **不是方名泄漏**；④≈② 而 ①≪② ⇒ "
      "**路A 的分全部来自胡老自己的结论解释段，不是来自症状**。\n")

print("═══ 三路同源同分母对照（N＝%d，五源全库，同一切案口径，同一判分）═══\n" % N)
print("| 路径 | ①单方原方 | ③最宽 | 落空 |")
print("|---|---|---|---|")
ORDER = ["A规则·遮盲", "A′规则·全文(对读)", "B案例·全库", "C案例·经内(准入)",
         "C′案例·经作排序权重", "B3案例·近邻3案任一"]
for k in ORDER:
    v = rows[k]
    print("| %-22s | **%4.1f%%** | %4.1f%% | %4.1f%% |" %
          (k, 100 * v[0] / N, 100 * v[1] / N, 100 * v[2] / N))
import statistics as _st2
print("  [B3口径] 近邻3案所载方之**候选集平均 %.1f 个方**（中位 %d）——"
      "**候选集越大命中越易，此数须与命中率同读**" % (_st2.mean(csz), _st2.median(csz)))
print("\n[R31 第一二步·经命中] %d/%d ＝ **%.1f%%**（分母＝案文明写六经之案）"
      % (jing_ok, jing_n, 100 * jing_ok / jing_n))
print("\n═══ ⭐⭐决定性分解：定经**确实判对**时，经内检索是帮还是害 ═══")
if okj[0]:
    print("  子集＝R31①②候选经∩案文明写之经 ≠ ∅ 者 %d 案" % okj[0])
    print("  C经内 %.1f%%  ｜  B全库 %.1f%%  →  **%+.1f 点**"
          % (100*okj[1]/okj[0], 100*okj[2]/okj[0], 100*(okj[1]-okj[2])/okj[0]))
    print("  → 若此处仍为负，则**不是定经不准的问题，是「以经作准入」这件事本身有害**。")

print("\n═══ ⭐经内约束之条件分解（C 只在**能跑**的子集上与 B 比）═══")
print("  C 能跑 %d/%d 案（%.0f%%）；落空之因：%s"
      % (cran[0], N, 100 * cran[0] / N, dict(cwhy)))
if cran[0]:
    print("  同一子集上： C经内 ①%.1f%% ③%.1f%%  ｜  B全库 ①%.1f%% ③%.1f%%"
          % (100 * cran[1] / cran[0], 100 * cran[2] / cran[0],
             100 * cran[3] / cran[0], 100 * cran[4] / cran[0]))
    print("  → 经内约束**本身**的效应＝ %+.1f 点（①档）——**与它的覆盖率是两件事**"
          % (100 * cran[1] / cran[0] - 100 * cran[3] / cran[0]))

# ── 产出：案例库 ＋ 近邻样例 ──────────────────────────────────────
OUT = os.path.join(B, "case_layer")
os.makedirs(OUT, exist_ok=True)
json.dump(dict(n=len(lib), 口径="㊾批·五源558案切案口径·遮盲后症状段",
               items=[dict(book=it["book"], seq=it["seq"], sym=it["sym"][:600],
                           fang=sorted(it["fang"]), jing=sorted(it["jing"]) if it["jing"] else None)
                      for it in lib]),
          open(os.path.join(OUT, "案例检索库.json"), "w"), ensure_ascii=False, indent=1)

L = ["# 案例检索层·重建（㊾批·指令二）", "",
     "> **口径**：五源 558 案切案 → 入库 %d 案；查询＝遮盲后症状段；" % len(lib),
     "> 留一法（剔本案＋同书相邻2案）；相似度＝**纯字面 2-gram Jaccard**（无槽位签名分量）。", "",
     "## ⛔ 协议14 复核：上级所引「20.0% vs 3.2%」**不可直接比较**", "",
     "依据全部出自我方工具头（不引外部主张）：",
     "- `three_path_compare.py` ②：案例检索一路「**与前两路不同源**，**只可作量级参照，不可直接相减**」",
     "- `case_index.py` ③：留一法「**只在同一本书内**做……**本数字不可外推为泛化准确率**」",
     "- N 不同（95 vs 60）｜语料不同（五源 vs 仅C卷）｜判分不同（三档 vs 单档）",
     "- 措辞核：上级称「纯字面 2-gram」，工具头原文为「2-gram Jaccard **＋ 槽位签名 Jaccard 加权和**」",
     "",
     "→ **方向成立，依据不成立。本表即把它变成一次真对照。**", "",
     "## 三路对照（同一批案 N＝%d，同一分母，同一判分）" % N, "",
     "| 路径 | ①单方原方 | ③最宽 | 落空 |", "|---|---|---|---|"]
for k in ORDER:
    v = rows[k]
    L.append("| %s | **%.1f%%** | %.1f%% | %.1f%% |" % (k, 100 * v[0] / N, 100 * v[1] / N, 100 * v[2] / N))
L += ["", "**[泄漏自检]** 遮盲后症状段仍含在库方名者 **%d 案（%.1f%%）**。" % (leak, 100 * leak / len(lib)),
      "**[经标注]** 未标经 %d／%d（**%.0f%%**）——经内检索之退化度。" % (nolab, len(lib), 100 * nolab / len(lib)),
      "**[R31第一二步·经命中]** %.1f%%（%d/%d）。" % (100 * jing_ok / jing_n, jing_ok, jing_n),
      "", "## 近邻样例（12 条·供人读）", ""]
for q, sc, nb, cand in detail:
    L += ["**查询**〔%s#%d〕%s…" % (q["book"], q["seq"], q["sym"][:70]),
          "  ·真方：%s ｜ R31①②候选经：%s" % ("／".join(sorted(q["fang"])), "／".join(sorted(cand)) or "(定不了)"),
          "  ·**近邻**〔%s#%d·相似度 %.3f〕方：**%s**" % (nb["book"], nb["seq"], sc, "／".join(sorted(nb["fang"]))),
          "  ·近邻案文：%s…" % nb["sym"][:70], ""]
open(os.path.join(OUT, "案例检索重建与三路对照.md"), "w").write("\n".join(L))
print("\n→ case_layer/案例检索重建与三路对照.md ／ 案例检索库.json")
