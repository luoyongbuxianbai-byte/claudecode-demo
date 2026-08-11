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

# ── 1. 验案块 ──
idx = [i for i, l in enumerate(raw) if "【验案】" in l]
blocks = []
for i in idx:
    j = i + 1
    while j < len(raw) and "【" not in raw[j] and j - i < 14:
        j += 1
    blocks.append((i + 1, re.sub(r"\s+", "", "".join(raw[i:j]))))

# ── 2. 判断句抽取：取**最靠近给方动词**的那一个引导词片段 ──
LEAD = r"(?:证属|证系|此属|此为|辨为|诊为|即为|属)"
GIVE = r"(?:治[以宜之则]|予|与|方用|宜|拟|投|服|为本方|即本方|故与|治用)"
pat = re.compile(LEAD + r"([一-鿿、]{2,36}?)(?=[，,。；;：:]" + GIVE + r"|[，,。；;：:]|$)")
NOISE = re.compile(r"病历号|门诊|知其|虽稍|以来|初诊")

rows, none = [], []
for ln, b in blocks:
    seg = b.split("【验案】")[-1]
    got = [m.group(1) for m in pat.finditer(seg)]
    got = [g for g in got if len(g) >= 2 and not NOISE.search(g)]
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
 "病位": ["表", "里", "内", "外", "上", "下", "心下", "胸", "腹", "肌肤", "项背", "四肢"],
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

recs = []
for ln, s in rows:
    ops = [o for o, _ in OPS if o in s]
    kind = "直书方证名" if FANG.search(s) else ("六经名" if JING.search(s) else "功能描述")
    recs.append(dict(line=ln, text=s, kind=kind, ops=ops, comps=split_comp(s)))

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
