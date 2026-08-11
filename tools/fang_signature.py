#!/usr/bin/env python3
"""230方辨证要点 → 六槽位签名（机械标注，不推理）＋ 签名覆盖回归。

产出：
  state_layer/方证槽位签名表.md   —— 219 条★的槽位签名（含增量式二次解析）
  state_layer/签名覆盖回归.md     —— **真正的机械回归**：
      拿 95 条「胡老自书证型判断 → 他实际所开之方」作金标准，
      问：按槽位签名覆盖去检索，能不能命中他开的那个方？

【已知失效模式】(视角㉕)
  ① ★写的是**症状语言**，六槽位是**状态语言**，二者不是同一层。
     机械切分只能抓到★里**恰好用了状态词**的部分（实测 83.1%）；
     纯症状★（如"汗出恶风脉缓"）**必须走附录U映射**，本工具抓不到，如实计入缺口。
  ② 增量式★（"小柴胡汤证而见…"）靠二次解析继承基方签名；
     **基方名 OCR 变形或不在库者，继承失败**，标 [基方未解析]。
  ③ 覆盖判定用**集合包含**（案签名 ⊆ 方签名 视为覆盖）。
     这是**最宽松**的判据——它只能证伪（不覆盖即真不覆盖），
     **不能据其命中率宣称辨证正确**。回归结论须按此读。
  ④ 金标准来自 `state_layer/_raw.json` 的 fang 栏（正则抽取，95/106 解析成功），
     其中合方/加味串可能含 OCR 噪声，**未人工校**。
【弃件条件】
  ★段缺失、或★为"【缺——原书无本段】"登记者，跳过并计入 no_star。
"""
import re, os, json
from collections import Counter, defaultdict

B = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(B, "state_layer")
E = open(os.path.join(B, "hxs_engine_v79_full.md"), encoding="utf-8").read().split("\n")

COMP = {"病位": ["半表半里", "心下", "项背", "肌肤", "四肢", "表", "里", "内", "外", "上", "下", "胸", "腹"],
        "正气载体": ["营卫", "津液", "胃气", "心气", "血", "气", "阳", "卫", "营"],
        "虚实态": ["俱虚", "不和", "失调", "不足", "虚", "实", "衰", "弱"],
        "寒热": ["化热", "寒", "热", "温"],
        "病理产物": ["寒饮", "水饮", "停饮", "水气", "湿", "瘀", "痰", "饮", "食"],
        "动向": ["上冲", "上犯", "上扰", "上逆", "内停", "内盛", "外溢", "外郁", "流注", "内陷", "不降", "郁", "逆"]}
ORD = sorted([(g, w) for g in COMP for w in COMP[g]], key=lambda x: -len(x[1]))
JING = re.compile(r"太阳|阳明|少阳|太阴|少阴|厥阴")

def sig(s):
    t, out = JING.sub(lambda m: "\x01" * len(m.group()), s), []
    for g, w in ORD:
        if w in t:
            out.append("%s:%s" % (g, w)); t = t.replace(w, "\x00" * len(w))
    return set(out)

# ── 1. 取★ ──
hdr = re.compile(r"^【([^】·|]*?(?:汤|散|丸|饮|煎))[^】]*】")
ents = [(i, hdr.match(l).group(1)) for i, l in enumerate(E) if hdr.match(l) and "附录" not in l]
star, no_star = {}, []
for k, (i, nm) in enumerate(ents):
    e = ents[k + 1][0] if k + 1 < len(ents) else len(E)
    t = None
    for j in range(i, e):
        if "经方理论·辨证要点" in E[j]:
            t = re.sub(r"^.*?辨证要点[^：:]*[：:]", "", E[j]).strip().strip('"“”'); break
    # ㉔批：★是**症状语言**，六槽位是**状态语言**——两边不同语，故首轮回归 83.2% 未命中。
    # 修法有锚：A4.9 冻结后，引擎已定「规范性读法唯三来源，第一为②方解『故治…者』句」。
    # **方解的『故治…者』本来就是状态语言**（"故治调胃承气汤方证气上冲，而有瘀血者"），
    # 故方侧签名源改为 ★ ∪ 方解故治句。
    jie = []
    for j in range(i, e):
        if "经方理论·方解" in E[j] or "经方理论·注解" in E[j]:
            jie += re.findall(r"故[治主此][^。；\n]{4,80}", E[j])
    j2 = "；".join(jie)
    if (t is None or t.startswith("【缺")) and not j2:
        no_star.append(nm)
    else:
        star.setdefault(nm, (t or "") + ("｜[方解故治句]" + j2 if j2 else ""))

INC = re.compile(r"([一-鿿]{2,16}(?:汤|散|丸|饮|煎))(?:方)?证")

# ── 2. 两遍解析：先自有签名，再继承增量式基方 ──
own = {nm: sig(t) for nm, t in star.items()}
base_of = {nm: [b for b in INC.findall(t) if b != nm] for nm, t in star.items()}
final, note = dict(own), {}
for _ in range(3):                       # 至多三级继承（柴胡桂枝干姜←小柴胡）
    for nm, bs in base_of.items():
        for b in bs:
            if b in final:
                final[nm] = final[nm] | final[b]
                note[nm] = "继承基方[%s]" % b
            elif b not in note.get(nm, ""):
                note.setdefault(nm, "基方[%s]未解析" % b)

# ── 3. 写签名表 ──
L = ["# 方证槽位签名表（219 条★·机械标注·不推理）", "",
     "> 生成：`tools/fang_signature.py`（文件头带【已知失效模式】）。",
     "> **增量式★天然对应签名加法**：「小柴胡汤证**而见**口干渴明显」＝ 小柴胡签名 ⊕ 增量成分。", "",
     "| 方 | ★辨证要点原文 | 槽位签名 | 增量继承 |", "|---|---|---|---|"]
for nm in sorted(star, key=lambda x: -len(final[x])):
    L.append("| %s | %s | %s | %s |" % (
        nm, star[nm][:70].replace("|", "／"),
        " ＋ ".join(sorted(final[nm])) or "**空**（纯症状语言·须走附录U）",
        note.get(nm, "—")))
n_empty = sum(1 for nm in star if not final[nm])
L += ["", "**统计**：有★条目 %d ｜ 签名非空 %d（%.1f%%）｜ 签名为空(纯症状语言) %d ｜ 无★段 %d"
      % (len(star), len(star) - n_empty, 100 * (len(star) - n_empty) / len(star), n_empty, len(no_star))]
open(os.path.join(OUT, "方证槽位签名表.md"), "w", encoding="utf-8").write("\n".join(L))

# ── 4. 机械回归：胡老自书证型判断 → 他实际所开之方 ──
raw = json.load(open(os.path.join(OUT, "_raw.json")))
cases = [r for r in raw["recs"] if r["fang"] != "(未解析)"]

def norm(f):
    """把'桂枝加芍药汤'/'大柴胡汤合桂枝茯苓丸'/'猪苓汤加减'切成方名列表。"""
    f = re.sub(r"(加减|加味)$", "", f)
    return [x for x in re.split(r"合|与", f) if x]

hit_exact = hit_in3 = miss = nosig = 0
detail = []
for r in cases:
    cs = sig(r["text"])
    golds = norm(r["fang"])
    if not cs:
        nosig += 1; detail.append((r, "案签名为空", golds, [])); continue
    # 候选 = 案签名 ⊆ 方签名 者，按签名大小升序（最小充分覆盖优先，同 公理A7 最小干预）
    cand = sorted([nm for nm in final if cs and cs <= final[nm]], key=lambda n: len(final[n]))
    if any(g in cand[:1] for g in golds):
        hit_exact += 1; k = "CS首选命中"
    elif any(g in cand[:3] for g in golds):
        hit_in3 += 1; k = "PC前三命中"
    elif any(g in cand for g in golds):
        hit_in3 += 1; k = "PC候选内(第4位后)"
    else:
        miss += 1; k = "未命中"
    detail.append((r, k, golds, cand[:5]))

N = len(cases)
L = ["# 签名覆盖回归（机械·95 例胡老自书判断 → 他实际所开之方）", "",
     "> **这是本层第一个真数，也是唯一一个不靠执行器、纯机械可复跑的验证。**",
     "> 金标准不是我们判的，是**胡老自己在同一段话里开出的方**。", "",
     "> ⚠**判据是最宽松的集合包含**（案签名 ⊆ 方签名）。",
     "> 故本回归**只能证伪，不能证成**：未命中即真未命中；命中**不等于**辨证正确",
     "> ——因为一个只含 `[病位:表]` 的签名会被几十个方包含。**命中率须按此折读。**", "",
     "| 项 | 数 | 占比 |", "|---|---|---|",
     "| 可测案例 | %d | — |" % N,
     "| **CS 首选命中** | %d | %.1f%% |" % (hit_exact, 100 * hit_exact / N),
     "| PC 候选内命中 | %d | %.1f%% |" % (hit_in3, 100 * hit_in3 / N),
     "| 未命中 | %d | %.1f%% |" % (miss, 100 * miss / N),
     "| 案签名为空(切分器未覆盖) | %d | %.1f%% |" % (nosig, 100 * nosig / N), "",
     "## 逐例", "", "| 证型判断 | 出处 | 判定 | 胡老实际用方 | 签名检索前五 |", "|---|---|---|---|---|"]
for r, k, g, c in detail:
    L.append("| %s | L%d | %s | %s | %s |" % (r["text"], r["line"], k, "／".join(g), "／".join(c) or "—"))
open(os.path.join(OUT, "签名覆盖回归.md"), "w", encoding="utf-8").write("\n".join(L))

print("★条目 %d（签名非空 %d/%.1f%%，空 %d）｜无★段 %d" %
      (len(star), len(star) - n_empty, 100 * (len(star) - n_empty) / len(star), n_empty, len(no_star)))
print("回归 N=%d ｜ CS %d(%.1f%%) ｜ PC %d(%.1f%%) ｜ 未命中 %d(%.1f%%) ｜ 案签名空 %d" %
      (N, hit_exact, 100 * hit_exact / N, hit_in3, 100 * hit_in3 / N, miss, 100 * miss / N, nosig))
