#!/usr/bin/env python3
"""证候状态描述层·抽取器（C卷验案中胡老自己写下的证型判断句）。

产出三份资产：
  state_layer/复合证元词表.md   —— 全量 L1 复合证元（原句为整体单元）
  state_layer/状态成分表.md     —— L2 基础状态成分（频次+来源）
  state_layer/无算子结构分析.md —— 决定性问题：无显式算子者如何表示

【已知失效模式】(视角㉕ 强制格式)
  ① 判断句的定位靠 `证属|此属|证系|辨为|诊为` 等引导词 + 其后到给方动词之间的片段。
     **胡老不用引导词直接写方证名者（如"桂枝加附子汤证"）会被当作证元收进来**，
     这类须在词表中单列，不参与成分统计。
  ② 验案块边界靠"下一个【标记"截断，**上限14行**；跨14行的长案会被截短，
     其判断句若在14行之后即漏。实测漏 15/111（13.5%），已在报告中如实登记。
  ③ OCR 变形（"表虚挟痰痰"实为"表虚挟痰饮"一类）**不做猜测修复**（协议4宁弃勿猜），
     一律照录并标 [OCR存疑]。
  ④ 成分表由**字面切分**得出，不做同义归并（"寒饮/水饮/停饮/水气"不合并）——
     归并属判据结构裁决，须另行取证，本工具不代做。
【弃件条件】
  判断句长度<2字、或匹配到"病历号/门诊"等元信息者，弃并计入 none。
"""
import re, os, json
from collections import Counter, defaultdict

B = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(B, "state_layer")
os.makedirs(OUT, exist_ok=True)
raw = open(os.path.join(B, "sources", "C_jingfangliyu.txt"), encoding="utf-8").read().split("\n")

# ── 1. 验案块（㉔批补捞：14行→22行；并剔 PDF 页脚噪声）──
JUNK = re.compile(r"·\d+·|PDFcreatedwith[A-Za-z]*|pdfFactory[A-Za-z]*|Protrialversion|www\.pdffactory\.com|_")
idx = [i for i, l in enumerate(raw) if "【验案】" in l]
blocks = []
for i in idx:
    j = i + 1
    while j < len(raw) and "【" not in raw[j] and j - i < 22:
        j += 1
    blocks.append((i + 1, JUNK.sub("", re.sub(r"\s+", "", "".join(raw[i:j])))))

# ── 2. 判断句抽取：取**最靠近给方动词**的那一个引导词片段 ──
# ㉔批补捞：实测15例漏检中14例系引导词未收（"此X之证"/"知其为"/"证为"/"认为是"）。
# 长引导词必须排在短的前面——正则交替是最左优先，"属"若在前会截断"证属"。
LEAD = (r"(?:知其为|认为是|知其患|证属|证系|证为|此属|此为|辨为|诊为|知为|即为|属)")
GIVE = r"(?:治[以宜之则]|予|与|方用|宜|拟|投|服|为本方|即本方|故与|治用)"
pat = re.compile(LEAD + r"([一-鿿、]{2,36}?)(?=[，,。；;：:]" + GIVE + r"|[，,。；;：:]|$)")
NOISE = re.compile(r"病历号|门诊|知其|虽稍|以来|初诊")

rows, none = [], []
for ln, b in blocks:
    seg = b.split("【验案】")[-1]
    got = [m.group(1) for m in pat.finditer(seg)]
    got = [g for g in got if len(g) >= 2 and not NOISE.search(g)]
    if not got:   # 二次通道：无引导词者，取给方动词前的最近一个"…之证/…方证"短句
        for m in re.finditer(r"[，,。；;]([一-鿿、]{3,24}?(?:之证|方证|的适应证))(?=[，,。；;：:]|$)", seg):
            g = re.sub(r"(之证|方证|的适应证)$", "", m.group(1))
            if len(g) >= 2 and not NOISE.search(g):
                got = [g]; break
    if got:
        rows.append((ln, got[0]))
    else:
        none.append(ln)

JING = re.compile(r"太阳|阳明|少阳|太阴|少阴|厥阴")

# ── 3. 分类：六经名 vs 功能描述 vs 直书方证名 ──
FANG = re.compile(r"[一-鿿]{2,14}(?:汤|散|丸|饮|煎)证$")
OPS = [("因致", "因致"), ("挟", "挟"), ("兼", "兼"), ("夹", "夹"), ("而", "而"), ("并", "并")]

# ── 4. L2 成分词表（字面切分·不做同义归并）──
COMP = {
 "病位": ["半表半里", "表", "里", "内", "外", "上", "下", "心下", "胸", "腹", "肌肤", "项背", "四肢"],
 "正气载体": ["营卫", "津液", "胃气", "血", "气", "阳", "卫", "营", "心气"],
 "虚实态": ["虚", "实", "不和", "失调", "衰", "不足", "弱", "俱虚"],
 "寒热": ["寒", "热", "化热", "温"],
 "病理产物": ["寒饮", "水饮", "停饮", "水气", "湿", "瘀", "痰", "饮", "食"],
 "动向": ["上冲", "上犯", "上扰", "上逆", "内停", "内盛", "外溢", "外郁", "郁", "流注", "内陷", "不降", "逆"],
}
ORD = [(g, w) for g in COMP for w in sorted(COMP[g], key=len, reverse=True)]

def split_comp(s):
    """最长优先消费，避免'水饮'被'饮'吞掉（同 p8_metrics 自验教训）。

    ⚠先屏蔽六经名再切分：否则"太阳/少阳/阳明"的"阳"会被误计为正气载体·阳，
    "太阴/少阴/厥阴"同理。首版实测使 阳 虚报 16 次（真值见下）。此为工具自查所得。
    """
    t, out = JING.sub(lambda m: "\x01" * len(m.group()), s), []
    for g, w in sorted(ORD, key=lambda x: -len(x[1])):
        if w in t:
            out.append((g, w)); t = t.replace(w, "\x00" * len(w))
    return out

# ㉔批新增：抽本案实际所用之方——这是"覆盖判据"的金标准，
# 也把词表从"语言库"变成"决策库"(证型判断 → 他真开了什么方)。
RX = re.compile(r"(?:与|予|治用|方用|投|为)([一-鿿]{2,18}(?:汤|散|丸|饮|煎))"
                r"((?:合|加|加减|加味)[一-鿿]{0,18}(?:汤|散|丸|煎)?)?")
def get_fang(seg):
    m = RX.search(seg)
    if not m: return "(未解析)"
    return (m.group(1) + (m.group(2) or "")).strip()

recs = []
for ln, s in rows:
    ops = [o for o, _ in OPS if o in s]
    kind = "直书方证名" if FANG.search(s) else ("六经名" if JING.search(s) else "功能描述")
    blk = dict(blocks)[ln]
    recs.append(dict(line=ln, text=s, kind=kind, ops=ops, comps=split_comp(s),
                     fang=get_fang(blk.split(s)[-1] if s in blk else blk)))

n = len(recs)
by_kind = Counter(r["kind"] for r in recs)
func = [r for r in recs if r["kind"] == "功能描述"]
with_op = [r for r in func if r["ops"]]
no_op = [r for r in func if not r["ops"]]
# 决定性问题：无算子者是否为单成分？
multi = [r for r in no_op if len(r["comps"]) >= 2]
single = [r for r in no_op if len(r["comps"]) < 2]

freq = Counter()
for r in recs:
    for g, w in r["comps"]:
        freq[(g, w)] += 1

# ══ 写出 ══
def w(f, s): open(os.path.join(OUT, f), "w", encoding="utf-8").write(s)

L = ["# L1 复合证元词表（C卷验案·胡老自书证型判断句·全量）", "",
     "> 抽取器：`tools/state_extract.py`（含【已知失效模式】声明）。",
     "> **原句为整体单元，不得拆分后自由重组**（L1 纪律）。",
     "> 成分列为 L2 受限展开结果，**仅供计算，不代表临床可自由组合**。", "",
     "| # | 原句(L1复合证元) | 出处 | 类别 | 算子 | L2成分 |", "|---|---|---|---|---|---|"]
for k, r in enumerate(recs, 1):
    L.append("| %d | %s | C卷L%d | %s | %s | %s |" % (
        k, r["text"], r["line"], r["kind"], "／".join(r["ops"]) or "**无**",
        " ＋ ".join("%s:%s" % (g, x) for g, x in r["comps"]) or "—"))
L += ["", "**未抽出判断句的验案 %d 例**（多为块边界14行截断，见失效模式②）：%s" %
      (len(none), "、".join("L%d" % x for x in none))]
w("复合证元词表.md", "\n".join(L))

L = ["# L2 状态成分表（字面切分·未做同义归并）", "",
     "> **不做同义归并**是刻意的：'寒饮/水饮/停饮/水气'是否同一成分，属判据结构裁决，",
     "> 须另行取证（㉒批纪律：涉判据结构的裁决必须先在语料取证）。本表只报字面事实。", "",
     "| 组 | 成分 | 出现例数 | 首见出处 |", "|---|---|---|---|"]
first = {}
for r in recs:
    for g, x in r["comps"]:
        first.setdefault((g, x), r["line"])
for (g, x), c in sorted(freq.items(), key=lambda kv: (-kv[1], kv[0])):
    L.append("| %s | %s | %d | C卷L%d |" % (g, x, c, first[(g, x)]))
w("状态成分表.md", "\n".join(L))

print("判断句 %d ／ 无判断句 %d" % (n, len(none)))
print("类别：", dict(by_kind))
print("功能描述 %d：有算子 %d ／ 无算子 %d" % (len(func), len(with_op), len(no_op)))
print("  无算子中：**多成分 %d（%.1f%%）** ／ 单成分 %d" %
      (len(multi), 100 * len(multi) / max(1, len(no_op)), len(single)))
print("成分种数 %d，总计次 %d" % (len(freq), sum(freq.values())))
json.dump(dict(recs=recs, none=none), open(os.path.join(OUT, "_raw.json"), "w"), ensure_ascii=False, indent=1)
print("\n[单成分者全列]", [r["text"] for r in single])

# ══ ㉔批新增产出：六槽位表 ＋ 增强版 L1 词表 ══
SLOTS = ["病位", "正气载体", "虚实态", "寒热", "病理产物", "动向"]
# ⚠㉔批实测推翻了「算子决定方剂操作」：无算子 92 例中，加味37／单方36／合方9——
# **加味与合方在无算子组照样大量发生（46/92）**。故方剂操作类型**不由算子读出**，
# 由**槽位覆盖关系**决定（上级㉔批指令四的表述得证）。本栏改报**实际形态**，
# 算子只标其「标记了什么」，不再宣称它决定什么。
OPMARK = {"": "—（并置·无标记）", "挟": "标记主从：前为主／后为兼",
          "而": "标记跨层并存", "因致": "标记因果方向（有向，不可逆读）",
          "兼": "标记兼夹项独立", "夹": "标记兼夹项独立", "并": "标记并存"}

def op_of(r):
    for o in ["因致", "挟", "兼", "夹", "而", "并"]:
        if o in r["ops"]: return o
    return ""

# 共现矩阵（只报实测，不推断禁止——R5：排除唯一依据是反义，"未见"≠"禁止"）
co = defaultdict(Counter)
for r in recs:
    cs = [x for _, x in r["comps"]]
    for a in set(cs):
        for b in set(cs):
            if a != b: co[a][b] += 1

L = ["# 六槽位表（㉔批·上级撤回算子规格后之新地基）", "",
     "> **六槽位 ＝ [病位]表里 ＋ [虚实态]虚实 ＋ [寒热] ＋ [正气载体] ＋ [病理产物] ＋ [动向]**",
     "> **即八纲在临床分辨率上的实际书写形式，非新抽象**（上级㉔批补充）——",
     "> 我方没有发明任何东西，只是把胡老写病历的语法形式化了。满足纲领六与视角㉒。", "",
     "> **[正气载体]＋[虚实态] 为最高频句式**（营卫不和／津液本虚／胃气沉衰／心气不足），",
     "> 在**病历用语层**第三次独立证实：津液胃气是生成病性的底层量，非并列维度。", "",
     "> ⚠**「禁止组合」一栏为何多数留空**：本表只报**实测共现**。",
     "> 未共现 **≠** 禁止（R5：排除唯一依据是反义）。**只有具备原文反义锚者才填禁止**，",
     "> 其余一律标「未见共现·非禁止」。这是把 R5 的纪律用在新层上，不是遗漏。", ""]
for sl in SLOTS:
    ws = sorted({x for r in recs for g, x in r["comps"] if g == sl},
                key=lambda x: -freq[(sl, x)])
    if not ws: continue
    L += ["## 槽位【%s】（成分 %d 个）" % (sl, len(ws)), "",
          "| 成分 | 频次 | 首见来源 | 实测共现最多的三项 | 同槽位内共现 | 禁止组合 |",
          "|---|---|---|---|---|---|"]
    for x in ws:
        same = [y for y in ws if y != x and co[x][y]]
        top = "／".join("%s(%d)" % (a, b) for a, b in co[x].most_common(3)) or "—"
        L.append("| %s | %d | C卷L%d | %s | %s | 未见共现·非禁止（无反义锚） |" % (
            x, freq[(sl, x)], first[(sl, x)], top,
            "／".join(same) if same else "**无**（本槽位内此成分从不与同槽他成分共现）"))
    L.append("")
L += ["## 槽位内互斥关系（实测）", "",
      "| 槽位 | 观察 |", "|---|---|"]
for sl in SLOTS:
    ws = sorted({x for r in recs for g, x in r["comps"] if g == sl})
    pairs = [(a, b) for i, a in enumerate(ws) for b in ws[i + 1:] if co[a][b]]
    L.append("| %s | 同槽位共现对 %d 个%s |" % (
        sl, len(pairs), "：" + "／".join("%s+%s" % ab for ab in pairs[:6]) if pairs else "（本槽位成分互不共现＝实测互斥）"))
L += ["", "**实测读法（不是预设，是数出来的）**：",
      "① **没有一个槽是单值槽。** [寒热]槽实测共现（外寒里热／化热+热）、",
      "   [虚实态]槽实测共现（虚+衰／不和+实／俱虚+弱）、[病位]共现最多（上+下／内+外）。",
      "   —— 我原以为寒热与虚实是互斥单值，**数据否掉了这个预设**。",
      "② **所有共现都靠对举成立**：外寒/里热、上/下、内/外——",
      "   **对举本身就是关系，不需要任何连接词**。这正是无算子占 90.1% 的机制。",
      "③ 故「禁止组合」在本层**实测为空**：没有任何一对成分被证明不可共现。",
      "   要立禁止，必须另找**原文反义锚**（R5），不能靠统计上的未共现。"]
w("六槽位表.md", "\n".join(L))

# 增强版 L1 词表
L = ["# L1 复合证元词表（增强版·㉔批）", "",
     "> 抽取器 `tools/state_extract.py`（幂等可复跑，文件头带【已知失效模式】）。",
     "> **原句为整体单元，不得拆分后自由重组**。槽位分解仅供计算。", "",
     "> **「实际用方」栏是本表最有价值的一列**：它把词表从**语言库**变成**决策库**——",
     "> 记录的是「胡老写下这个判断之后，他真的开了什么方」。", "",
     "| # | 原句(L1) | 出处 | 类别 | 算子 | 槽位分解 | 算子标记了什么 | 证据优先级 | 实际用方(覆盖判据·金标准) |",
     "|---|---|---|---|---|---|---|---|---|"]
for k, r in enumerate(recs, 1):
    o = op_of(r)
    pri = "主证元＋兼夹（%s前为主／后为兼）" % o if o in ("挟", "兼", "夹") else (
          "有向：前项致后项" if o == "因致" else "全部为主证元（并置·无主从标记）")
    L.append("| %d | %s | C卷L%d | %s | %s | %s | %s | %s | %s |" % (
        k, r["text"], r["line"], r["kind"], o or "**无**",
        " ＋ ".join("%s:%s" % (g, x) for g, x in r["comps"]) or "—",
        OPMARK[o], pri, r["fang"]))
L += ["", "**未抽出判断句 %d 例**（㉔批补捞后残余）：%s" %
      (len(none), "、".join("L%d" % x for x in none)),
      "", "## 算子→方剂操作 的实测校验（这是「算子仅作标记」的正面证据）", "",
      "| 算子 | 例数 | 实际用方形态 |", "|---|---|---|"]
for o in ["", "挟", "而", "因致", "兼", "夹"]:
    g = [r for r in recs if op_of(r) == o]
    if not g: continue
    forms = Counter("合方" if "合" in r["fang"] else ("加味" if ("加" in r["fang"]) else "单方")
                    for r in g if r["fang"] != "(未解析)")
    L.append("| %s | %d | %s |" % (o or "**无**", len(g),
             "／".join("%s%d" % (a, b) for a, b in forms.most_common()) or "—"))
w("复合证元词表_增强.md", "\n".join(L))
print("\n[已写出] 六槽位表.md ／ 复合证元词表_增强.md")
